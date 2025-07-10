from typing import Optional

from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from neo4j.exceptions import CypherSyntaxError

from schemas import AgentGraphSubquery, AgentGraphRoute, AgentGraphStart
from server import SocketManager
from .base import GraphNodesBase
from .manager import ChatManager
from .prompt import (
    QA_PROMPT,
    CYPHER_PROMPT,
    SUBQUERIES_PROMPT,
    ROUTING_PROMPT,
    ASSISTANT_PROMPT,
    ROUTING_CONSTANTS,
    START_PROMPT,
)


class GraphAgent(GraphNodesBase):
    def __init__(
        self,
        graph: Neo4jGraph,
        llm: ChatBedrock,
        chat_manager: ChatManager,
        sio: Optional[SocketManager] = None
    ):
        self._chat_manager = chat_manager
        self._graph = graph
        self._llm = llm
        self._sio = sio

    async def _emit(self, event: str, data: dict) -> None:
        """
        Emit an event to the Socket.IO server.
        :param event: The event name to emit.
        :param data: The data to send with the event.
        """
        if self._sio: await self._sio.emit(event, data)

    async def start(self, state: dict) -> dict:
        """
        Start the agent and initialize the state.
        :return: The initial state of the agent.
        """
        print("--STARTING AGENT--")
        information_text = 'Iniciando o agente...'
        await self._emit("agent_updated", {"status": information_text})
        structured = self._llm.with_structured_output(AgentGraphStart)
        route_chain = START_PROMPT | structured
        result: AgentGraphStart = await route_chain.ainvoke(state)  # type: ignore
        return {"route": result.route}

    async def search_vector(self, state: dict) -> dict:
        """
        Search the vector database based on the current state and return a list of Document objects.
        :param state:
        :return:
        """
        print("--SEARCHING VECTOR--")
        depth: int = state["depth"]
        depth += 1
        return {"documents": state["documents"], "depth": depth}

    async def search_graph(self, state: dict) -> dict:
        """
        Search the graph based on the current state and return a list of Document objects.
        :param state:
        :return:
        """
        print(f"--SEARCHING GRAPH--")
        information_text = 'Buscando relacionamentos em grafos...'
        await self._emit("agent_updated", {"status": information_text})
        documents: list[dict] = state["documents"]
        subqueries: list[dict] = state["subqueries"]
        depth: int = state["depth"]
        cypher_prompt_copy = CYPHER_PROMPT.model_copy()
        cypher_prompt_copy.template = cypher_prompt_copy.template.replace(
            "{{chat_history}}", await self._chat_manager.get_history_as_string())
        # Search the graph using the LLM
        for query in subqueries:
            print(f"Processing query: {query}")
            information_text += f"\n- Consultando: {query}"
            try:
                cypher_chain = GraphCypherQAChain.from_llm(
                    self._llm,
                    graph=self._graph,
                    qa_prompt=QA_PROMPT,
                    cypher_prompt=cypher_prompt_copy,
                    verbose=True,
                    top_k=10,
                    allow_dangerous_requests=True,
                    validate_cypher=True,
                )
                document = await cypher_chain.ainvoke(query)
                documents.append(document)
                information_text += " **OK**"
            except CypherSyntaxError as e:
                print(f"Cypher syntax error: {e}")
                information_text += f"\n- Erro de sintaxe Cypher: {e}"
            await self._emit("agent_updated", {"status": information_text})
        depth += 1
        return {"documents": documents, "depth": depth}

    async def route(self, state: dict) -> dict:
        """
        Route the state to the appropriate nodes in the graph.
        :param state:
        :return:
        """
        print("--ROUTING--")
        information_text = 'Roteando o estado para os nós apropriados...'
        await self._emit("agent_updated", {"status": information_text})
        structured = self._llm.with_structured_output(AgentGraphRoute)
        route_chain = ROUTING_PROMPT | structured
        result: AgentGraphRoute = await route_chain.ainvoke(state) # type: ignore
        await self._emit(
            "agent_updated",
             {"status": f"Roteamento: {ROUTING_CONSTANTS.get(result.route, 'Desconhecido')}"}
        )
        return {"route": result.route}

    async def subqueries(self, state: dict) -> dict:
        """
        Generate sub-queries based on the current state of the graph.
        :param state:
        :return:
        """
        print("--SUBQUERIES--")
        information_text = 'Gerando sub-consultas...'
        structured = self._llm.with_structured_output(AgentGraphSubquery)
        subquery_chain = SUBQUERIES_PROMPT | structured
        result: AgentGraphSubquery = await subquery_chain.ainvoke(state) # type: ignore
        information_text += f"\n- Sub-consultas geradas: {', '.join(result.subquestions)}"
        await self._emit("agent_updated", {"status": information_text})
        return {"subqueries": result.subquestions}

    async def answer(self, state: dict) -> dict:
        """
        Generate the final answer based on the current state of the graph.
        :param state:
        :return: The final answer as a string.
        """
        print("--ANSWERING--")
        await self._chat_manager.add_message(state["question"], role="user")
        messages = await self._chat_manager.get_history()
        system_prompt = SystemMessagePromptTemplate(prompt=ASSISTANT_PROMPT)
        prompt = ChatPromptTemplate.from_messages(
            [
                system_prompt,
                *messages,
            ]
        )
        chain = prompt | self._llm
        response = await chain.ainvoke({"context": state["documents"]})
        await self._chat_manager.add_message(response.content, role="agent")
        return {"answer": response.content}
