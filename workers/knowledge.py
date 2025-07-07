from langchain_community.document_loaders import S3FileLoader
from langchain_community.document_loaders import AmazonTextractPDFLoader
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_aws import ChatBedrock
from langchain_neo4j import Neo4jGraph

from config import env


class KnowledgeService:
    def __init__(self):
        self._splitter = CharacterTextSplitter.from_tiktoken_encoder(
            encoding_name="cl100k_base",
            chunk_size=300,
            chunk_overlap=0,
        )

    @staticmethod
    def _read(key: str) -> str:
        _ext = key.split('.')[-1].lower()
        if _ext == 'pdf':
            loader = AmazonTextractPDFLoader(
                f"s3://{env.S3_BUCKET_NAME}/{key}",
                region_name=env.AWS_REGION,
            )
            return "\n".join([page.page_content for page in loader.load()])
        elif _ext == 'txt' or _ext == 'md':
            s3_file_loader = S3FileLoader(
                env.S3_BUCKET_NAME,
                key=key,
                region_name=env.AWS_REGION,
                aws_access_key_id=env.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
            )
            return "\n".join([page.page_content for page in s3_file_loader.load()])
        raise RuntimeError(f"Unsupported file type: {_ext}")

    def update(self, key: str):
        """
        Update the knowledge base with the given S3 object ID.
        :param key:
        :return:
        """
        # Load the document from S3
        contents = self._read(key)
        # Split the document into smaller chunks
        texts = self._splitter.split_text(contents)
        # Create Document objects from the split texts
        documents = [Document(page_content=text, source=key.split('/')[-1]) for text in texts]
        print(f"{len(documents)} Chunks created from {key}.")

        # Convert the documents to graph documents using LLMGraphTransformer
        llm = ChatBedrock(
            temperature=0,
            model=env.BEDROCK_MODEL_ID,
            region=env.AWS_REGION,
            aws_access_key_id=env.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
        )
        llm_graph = LLMGraphTransformer(llm)
        graph_documents = llm_graph.convert_to_graph_documents(documents)

        # Connect to Neo4j and add the graph documents
        graph = Neo4jGraph(url=env.NEO4J_URL, username=env.NEO4J_USERNAME, password=env.NEO4J_PASSWORD)
        graph.add_graph_documents(graph_documents, include_source=True)
        # Refresh the schema to ensure the new documents are indexed
        graph.refresh_schema()
        print(f"Knowledge base updated with {len(graph_documents)} documents from {key}.")