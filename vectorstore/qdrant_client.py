from typing import Optional

from langchain_aws import BedrockEmbeddings
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from .base import VectorDBManagerBase
from config import env

COLLECTION_NAME = "documents"

embeddings = BedrockEmbeddings(
    model_id=env.BEDROCK_EMBEDDING_MODEL_ID,
    region_name=env.AWS_REGION,
    aws_access_key_id=env.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
)

try:
    QdrantClient(
        url=env.QDRANT_URL,
        api_key=env.QDRANT_API_KEY,
        prefer_grpc=True,
    ).create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=1024,                          # Bedrock embedding size
            distance=models.Distance.COSINE,    # Distance metric
        ),
    )
except Exception: # noqa
    pass

class QdrantClientManager(VectorDBManagerBase):
    def __init__(self):
        self._vectorstore = QdrantVectorStore.from_existing_collection(
            url=env.QDRANT_URL,
            api_key=env.QDRANT_API_KEY,
            prefer_grpc=True,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
        )

    def search(self, query: str, k: int = 10, filters: Optional[models.Filter] = None) -> list:
        return self._vectorstore.similarity_search(query, k=k, filter=filters)

    def add_document(self, documents: list[Document]) -> None:
        self._vectorstore.add_documents(documents)

    async def asearch(self, query: str, k: int = 10, filters: Optional[models.Filter] = None) -> list:
        """
        Asynchronous search method to find similar vectors.
        :param query: The query vector or text to search for.
        :param k: The number of similar vectors to return.
        :param filters: Optional filters to apply to the search.
        :return: A list of metadata associated with the found vectors.
        """
        return await self._vectorstore.asimilarity_search(query, k=k, filter=filters)

    @property
    def vectorstore(self) -> QdrantVectorStore:
        """
        Returns the Qdrant client instance.
        If the client is not initialized, it will be created.
        :return: QdrantVectorStore instance.
        """
        return self._vectorstore