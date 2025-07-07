from typing import Optional

from langchain_core.messages import BaseMessage
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph

from .base import LLMBedRockBase, ChatManagerBase
from .prompt import QA_PROMPT, CYPHER_PROMPT
from config import env


class AgentGraphRAGBedRock(LLMBedRockBase, ChatManagerBase):
    def __init__(
        self,
        chat_id: str,
        model_id: Optional[str] = env.BEDROCK_MODEL_ID,
        region: Optional[str] = env.AWS_REGION,
        aws_access_key_id: Optional[str] = env.AWS_ACCESS_KEY_ID,
        aws_secret_access_key: Optional[str] = env.AWS_SECRET_ACCESS_KEY,
    ):
        LLMBedRockBase.__init__(
            self,
            model_id=model_id,
            region=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        ChatManagerBase.__init__(self, chat_id)
        self._chat_histories: list[BaseMessage] = []
        self._graph = Neo4jGraph(
            url=env.NEO4J_URL,
            username=env.NEO4J_USERNAME,
            password=env.NEO4J_PASSWORD,
        )

    async def generate(self, answer: str, **kwargs) -> str:
        raise NotImplementedError(
            "The generate method is not implemented for AgentGraphRAGBedRock. "
            "Please implement this method to generate a response based on the provided answer."
        )

    async def search(self, question: str) -> dict:
        chain = GraphCypherQAChain.from_llm(
            self.llm,
            graph=self._graph,
            qa_prompt=QA_PROMPT,
            cypher_prompt=CYPHER_PROMPT,
            verbose=True,
            top_k=3,
            allow_dangerous_requests=True,
            validate_cypher=True,
        )
        return await chain.ainvoke(question)
