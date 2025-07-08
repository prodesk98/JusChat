from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_mongodb import MongoDBChatMessageHistory

from config import env


class ChatManager:
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
