from typing import Optional

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter
from ._embedding import embeddings
from .base import VectorDBManagerBase
from config import env


class QdrantClientManager(VectorDBManagerBase):
    COLLECTION_NAME = "documents"

    def __init__(self):
        self._client = QdrantClient(
            url=env.QDRANT_URL,
            api_key=env.QDRANT_API_KEY,
            prefer_grpc=True,
        )
        self._client_vector_store: Optional[QdrantVectorStore] = None
        self._initialize()

    def _initialize(self) -> None:
        """
        Initializes the Qdrant client with the necessary parameters.
        This method is called during the instantiation of the class.
        """
        self._client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=1024,                  # Bedrock embedding size
                distance=Distance.COSINE,   # Distance metric
            ),
        )
        self._client_vector_store = QdrantVectorStore(
            client=self._client,
            collection_name=self.COLLECTION_NAME,
            embedding=embeddings,
        )

    def search(self, query: str, k: int = 10, filters: Optional[Filter] = None) -> list:
        return self._client_vector_store.similarity_search(query, k=k, filter=filters)

    def add_document(self, documents: list[Document]) -> None:
        self._client_vector_store.add_documents(documents)

    async def asearch(self, query: str, k: int = 10, filters: Optional[Filter] = None) -> list:
        """
        Asynchronous search method to find similar vectors.
        :param query: The query vector or text to search for.
        :param k: The number of similar vectors to return.
        :param filters: Optional filters to apply to the search.
        :return: A list of metadata associated with the found vectors.
        """
        return await self._client_vector_store.asimilarity_search(query, k=k, filter=filters)

    @property
    def client(self) -> QdrantVectorStore:
        """
        Returns the Qdrant client instance.
        If the client is not initialized, it will be created.
        :return: QdrantVectorStore instance.
        """
        return self._client_vector_store

    @property
    def collection_name(self) -> str:
        """
        Returns the name of the collection.
        :return:
        """
        return self.COLLECTION_NAME