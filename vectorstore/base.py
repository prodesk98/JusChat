from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.documents import Document
from qdrant_client.http.models import Filter


class VectorDBManagerBase(ABC):
    @abstractmethod
    def search(self, query: str, k: int = 10, filters: Optional[Filter] = None) -> list:
        """
        Search for vectors similar to the query vector.
        :param query: The query vector or text to search for.
        :param k: The number of similar vectors to return.
        :param filters: Optional filters to apply to the search.
        :return: A list of metadata associated with the found vectors.
        """
        pass

    @abstractmethod
    def add_document(self, documents: list[Document]) -> None:
        """
        Add a document to the database.
        :param documents: A list of Document objects to add.
        :return: None
        """
        pass