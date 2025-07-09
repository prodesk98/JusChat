from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from neo4j.exceptions import CypherSyntaxError

from schemas import AgentGraphSubquery, AgentGraphRoute
from .base import GraphNodesBase
from .manager import ChatManager
from .prompt import QA_PROMPT, CYPHER_PROMPT, SUBQUERIES_PROMPT, ROUTING_PROMPT, ASSISTANT_PROMPT


class GraphAgent(GraphNodesBase):
    def __init__(self, graph: Neo4jGraph, llm: ChatBedrock, chat_manager: ChatManager):
        self._chat_manager = chat_manager
        self._graph = graph
        self._llm = llm

    async def search(self, state: dict) -> dict:
        """
        Search the graph based on the current state and return a list of Document objects.
        :param state:
        :return:
        """
        print(f"--SEARCHING GRAPH--")
        documents: list[dict] = state["documents"]
        subqueries: list[dict] = state["subqueries"]
        depth: int = state["depth"]
        cypher_prompt_copy = CYPHER_PROMPT.model_copy()
        cypher_prompt_copy.template = cypher_prompt_copy.template.replace(
            "{{chat_history}}", await self._chat_manager.get_history_as_string())
        # Search the graph using the LLM
        for query in subqueries:
            print(f"Processing query: {query}")
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
            except CypherSyntaxError as e:
                print(f"Cypher syntax error: {e}")
        depth += 1
        return {"documents": documents, "depth": depth}

    async def route(self, state: dict) -> dict:
        """
        Route the state to the appropriate nodes in the graph.
        :param state:
        :return:
        """
        print("--ROUTING--")
        structured = self._llm.with_structured_output(AgentGraphRoute)
        route_chain = ROUTING_PROMPT | structured
        result: AgentGraphRoute = await route_chain.ainvoke(state) # type: ignore
        return {"route": result.route}

    async def subqueries(self, state: dict) -> dict:
        """
        Generate sub-queries based on the current state of the graph.
        :param state:
        :return:
        """
        print("--SUBQUERIES--")
        structured = self._llm.with_structured_output(AgentGraphSubquery)
        subquery_chain = SUBQUERIES_PROMPT | structured
        result: AgentGraphSubquery = await subquery_chain.ainvoke(state) # type: ignore
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
