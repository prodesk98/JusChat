import asyncio
from .knowledge import KnowledgeService
from .connection import app


@app.task(
    name="knowledge.upload_knowledge_base",
    bind=True,
    max_retries=3,
    countdown=60,
)
def _upload_knowledge_base(self, key: str):
    """
    Synchronous task to update the knowledge base with the given S3 object ID.
    """
    try:
        service = KnowledgeService()
        service.process(key)
    except Exception as e:
        raise self.retry(exc=e, countdown=60) # Retry after 60 seconds if an error occurs


async def aupload_knowledge_base(key: str) -> str:
    """
    Asynchronous wrapper for updating the knowledge base.
    :param key: The S3 object ID to update the knowledge base with.
    """
    return (await asyncio.to_thread(_upload_knowledge_base.delay, key=key)).id
