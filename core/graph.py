from langchain_neo4j import Neo4jGraph

from .base import GraphNodesBase, LLMBase


class GraphAgent(GraphNodesBase):
    def __init__(self, graph: Neo4jGraph, llm: LLMBase):
        self._graph = graph
        self._llm = llm

    async def search(self, state: dict) -> dict:
        """
        Search the graph based on the current state and return a list of Document objects.
        :param state:
        :return:
        """
        print(f"Searching graph with state: {state}")
        question = state["question"]
        # Search the graph using the LLM
        documents = await self._llm.search(question)
        return {
            "documents": documents,
            "question": question
        }

    async def generate(self, state: dict) -> dict:
        """
        Generate a response based on the current state of the graph.
        :param state:
        :return:
        """
        print(f"Generating response for state: {state}")
        question = state["question"]
        documents = state["documents"]

        # RAG generation using the graph
        pass

    async def route(self, state: dict) -> dict:
        """
        Route the state to the appropriate nodes in the graph.
        :param state:
        :return:
        """
        print(f"Routing state: {state}")
        pass

    async def subquery(self, state: dict) -> dict:
        """
        Generate sub-queries based on the current state of the graph.
        :param state:
        :return:
        """
        print(f"Generating sub-queries for state: {state}")
        pass