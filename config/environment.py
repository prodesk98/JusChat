from pydantic import Field
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import Optional
from kombu.utils.url import safequote
load_dotenv()

class Environment(BaseSettings):
    # Access key
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=os.getenv("AWS_ACCESS_KEY_ID"))
    # Secret key
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=os.getenv("AWS_SECRET_ACCESS_KEY"))
    # Region
    AWS_REGION: Optional[str] = Field(default=os.getenv("AWS_REGION", "us-east-1"))
    # SQS Broker URL
    SQS_BROKER_URL: Optional[str] = Field(
        default=f"sqs://{safequote(os.getenv("AWS_ACCESS_KEY_ID"))}:{safequote(os.getenv("AWS_SECRET_ACCESS_KEY"))}@")
    SQS_DEFAULT_QUEUE_URL: Optional[str] = Field(default=os.getenv("SQS_DEFAULT_QUEUE_URL"))
    # S3
    S3_BUCKET_NAME: Optional[str] = Field(default=os.getenv("S3_BUCKET_NAME"))
    # Neo4j
    NEO4J_URL: Optional[str] = Field(default=os.getenv("NEO4J_URL"))
    NEO4J_USERNAME: Optional[str] = Field(default=os.getenv("NEO4J_USERNAME"))
    NEO4J_PASSWORD: Optional[str] = Field(default=os.getenv("NEO4J_PASSWORD"))
    # Bedrock
    ## Generative Model
    BEDROCK_MODEL_ID: Optional[str] = Field(
        default=os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20240620-v1:0"))
    ## Embedding Model
    BEDROCK_EMBEDDING_MODEL_ID: Optional[str] = Field(
        default=os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"))
    # MongoDB
    MONGO_URI: Optional[str] = Field(default=os.getenv("MONGO_URI", "mongodb://root:pwd@127.0.0.1:27017?authSource=admin"))
    MONGO_DB_NAME: Optional[str] = Field(default=os.getenv("MONGO_DB_NAME", "db0"))
    # QDrant
    QDRANT_URL: Optional[str] = Field(default=os.getenv("QDRANT_URL", "http://localhost:6333"))
    QDRANT_API_KEY: Optional[str] = Field(default=os.getenv("QDRANT_API_KEY"))