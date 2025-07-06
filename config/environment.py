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
    AWS_REGION: str = Field(default=os.getenv("AWS_REGION", "us-east-1"))
    # SQS Broker URL
    SQS_BROKER_URL: Optional[str] = Field(
        default=f"sqs://{safequote(os.getenv("AWS_ACCESS_KEY_ID"))}:{safequote(os.getenv("AWS_SECRET_ACCESS_KEY"))}@")
    SQS_DEFAULT_QUEUE_URL: Optional[str] = Field(default=os.getenv("SQS_DEFAULT_QUEUE_URL"))