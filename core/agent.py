from typing import Optional

from .base import LLMBedRockBase, ChatManagerBase
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

    async def agenerate(self, answer: str, **kwargs) -> str:
        await self.add_message(answer, role="user", **kwargs)
        chat_history = await self.get_history()
        return "Test"
