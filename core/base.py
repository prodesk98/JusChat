from abc import ABC, abstractmethod
from typing import Literal, TypedDict

from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

from config import env

class LLMBase(ABC):
    @abstractmethod
    async def generate(self, answer: str, **kwargs) -> str:
        """
        Generate a response based on the input answer.
        :param answer: The input answer to generate a response for.
        :param kwargs: Additional parameters for the generation.
        :return: The generated response as a string.
        """
        raise NotImplementedError(
            "Generation is not implemented. Please implement the generate method in the subclass."
        )

    @abstractmethod
    async def search(self, question: str) -> dict:
        """
        Search for relevant information based on the provided question.
        :param question:
        :return:
        """
        raise NotImplementedError(
            "Search is not implemented. Please implement the search method in the subclass."
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
    async def generate(self, answer: str, **kwargs) -> str:
        """
        Asynchronous wrapper for the generate method.
        :param answer: The input answer to generate a response for.
        :param kwargs: Additional parameters for the generation.
        :return: The generated response as a string.
        """
        raise NotImplementedError(
            "Asynchronous generation is not implemented. Please implement the agenerate method in the subclass."
        )

    @abstractmethod
    async def search(self, question: str) -> dict:
        """
        Asynchronous wrapper for the search method.
        :param question: The question to search for relevant information.
        :return: A dictionary containing the search results.
        """
        raise NotImplementedError(
            "Asynchronous search is not implemented. Please implement the asearch method in the subclass."
        )

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def llm(self) -> ChatBedrock:
        return self._llm


class ChatManagerBase(ABC):
    DEFAULT_COLLECTION_NAME: str = "chat_histories"

    def __init__(self, chat_id: str, history_size: int = 25):
        self._chat_id = chat_id
        self._chat_manager_history = MongoDBChatMessageHistory(
            session_id=self._chat_id,
            connection_string=env.MONGO_URI,
            database_name=env.MONGO_DB_NAME,
            collection_name=self.DEFAULT_COLLECTION_NAME,
            history_size=history_size,
        )

    async def get_history(self) -> list[BaseMessage]:
        """
        Retrieve the chat history for the current chat session.
        :return: A list of messages representing the chat history.
        """
        return await self._chat_manager_history.aget_messages()

    async def add_message(self, content: str, role: Literal["user", "agent"], **kwargs) -> None:
        """
        Add a message to the chat history.
        :param role: The role of the message sender, either "user" or "agent".
        :param content: The content of the message to be added.
        """
        if role == "user":
            return await self._chat_manager_history.aadd_messages([HumanMessage(content, **kwargs)])
        return await self._chat_manager_history.aadd_messages([AIMessage(content, **kwargs)])


class GraphNodesBase(ABC):
    @abstractmethod
    async def search(self, state: dict) -> dict:
        """
        Search the graph based on the current state and return a list of Document objects.
        :return: A list of Document objects.
        """
        raise NotImplementedError("This method should be implemented in a subclass.")

    @abstractmethod
    async def generate(self, state: dict) -> dict:
        """
        Generate a response based on the current state of the graph.
        :param state: The current state of the graph.
        :return: A string representing the generated response.
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
    async def subquery(self, state: dict) -> dict:
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
    generation: str
    sub_questions: list[str]
    documents: list[str]