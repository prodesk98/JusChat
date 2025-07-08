from abc import ABC, abstractmethod
from typing import Literal, TypedDict

from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

from config import env

class LLMBase(ABC):
    @abstractmethod
    async def invoke(self, question: str, **kwargs) -> str:
        """
        Generate a response based on the input question.
        :param question: The input question to generate a response for.
        :param kwargs: Additional parameters for the generation.
        :return: The generated response as a string.
        """
        raise NotImplementedError(
            "Generation is not implemented. Please implement the generate method in the subclass."
        )


class LLMBedRockBase(LLMBase):
    def __init__(self, model_id: str, region: str, aws_access_key_id: str, aws_secret_access_key: str):
        self._model_id = model_id
        self._region = region
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._llm = ChatBedrock(
            model=self._model_id,
            region=self._region,
            aws_access_key_id=self._aws_access_key_id,          # type: ignore
            aws_secret_access_key=self._aws_secret_access_key,  # type: ignore
            temperature=0,
        )

    @abstractmethod
    async def invoke(self, question: str, **kwargs) -> str:
        """
        Asynchronous wrapper for the invoke method.
        :param question: The input question to generate a response for.
        :param kwargs: Additional parameters for the generation.
        :return: The generated response as a string.
        """
        raise NotImplementedError(
            "Asynchronous generation is not implemented. Please implement the generate method in the subclass."
        )

    @property
    def model_id(self) -> str:
        return self._model_id


class GraphNodesBase(ABC):
    @abstractmethod
    async def search(self, state: dict) -> dict:
        """
        Search the graph based on the current state and return a list of Document objects.
        :return: A list of Document objects.
        """
        raise NotImplementedError("This method should be implemented in a subclass.")

    @abstractmethod
    async def route(self, state: dict) -> dict:
        """
        Route the state to the appropriate nodes in the graph.
        :param state: The current state of the graph.
        :return: A list of Document objects representing the routed nodes.
        """
        raise NotImplementedError("This method should be implemented in a subclass.")

    @abstractmethod
    async def subqueries(self, state: dict) -> dict:
        """
        Generate sub-queries based on the current state of the graph.
        :param state: The current state of the graph.
        :return: A list of sub-queries.
        """
        raise NotImplementedError("This method should be implemented in a subclass.")


class GraphState(TypedDict):
    """
    Represents the state of the graph, including the current node and the list of nodes.
    """

    question: str
    answer: str
    route: str
    subqueries: list[str]
    documents: list[str]
    depth: int