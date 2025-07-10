from typing import Optional

from langchain_core.messages import BaseMessage
from langchain_neo4j import Neo4jGraph
from langgraph.constants import START, END
from langgraph.graph import StateGraph

from server import SocketManager
from .base import LLMBedRockBase, GraphState
from .graph import GraphAgent
from .manager import ChatManager
from config import env


class AgentGraphRAGBedRock(LLMBedRockBase):
    def __init__(
        self,
        chat_id: str,
        sio: Optional[SocketManager] = None,
        model_id: Optional[str] = env.BEDROCK_MODEL_ID,
        region: Optional[str] = env.AWS_REGION,
        aws_access_key_id: Optional[str] = env.AWS_ACCESS_KEY_ID,
        aws_secret_access_key: Optional[str] = env.AWS_SECRET_ACCESS_KEY,
    ):
        super().__init__(
            model_id=model_id,
            region=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self._chat_manager = ChatManager(chat_id)
        self._chat_histories: list[BaseMessage] = []
        self._graph = Neo4jGraph(
            url=env.NEO4J_URL,
            username=env.NEO4J_USERNAME,
            password=env.NEO4J_PASSWORD,
        )
        self._agent = GraphAgent(
            graph=self._graph,
            llm=self._llm,
            chat_manager=self._chat_manager,
            sio=sio,
        )

    @staticmethod
    def check_status(state: GraphState) -> str:
        """
        Determine the routing status based on the state of the graph.
        :param state: The current state of the graph.
        :return: A string indicating the routing status.
        """
        if state["depth"] >= 3:
            return "answer_final"
        return state["route"]

    async def invoke(self, question: str, **kwargs) -> str:
        workflow = StateGraph(GraphState) # type: ignore
        workflow.add_node("Search", self._agent.search) # type: ignore
        workflow.add_node("Route", self._agent.route) # type: ignore
        workflow.add_node("Subqueries", self._agent.subqueries) # type: ignore
        workflow.add_node("Answer", self._agent.answer) # type: ignore
        # Edges
        workflow.add_edge(START, "Search")
        workflow.add_edge("Search", "Route")
        workflow.add_edge("Subqueries", "Search")
        workflow.add_edge("Answer", END)
        # Conditional
        workflow.add_conditional_edges(
            "Route",
            self.check_status,
            {
                "generate_subqueries": "Subqueries",
                "answer_final": "Answer",
            }
        )
        # Compile the workflow
        app = workflow.compile()
        # Run the workflow
        result = await app.ainvoke(
            {"question": question, "documents": [], "subqueries": [question], "route": "", "depth": 0, "answer": "I don't know"}) # type: ignore
        return result["answer"]
