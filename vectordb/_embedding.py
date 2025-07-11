from langchain_aws import BedrockEmbeddings

from config import env

embeddings = BedrockEmbeddings(
    model_id=env.BEDROCK_EMBEDDING_MODEL_ID,
    region_name=env.AWS_REGION,
    aws_access_key_id=env.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
)