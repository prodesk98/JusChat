import asyncio

from .connection import app


@app.task(
    name="knowledge.upload_knowledge_base",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    countdown=60,
)
def _upload_knowledge_base(self, key: str):
    """
    Update the knowledge base with the given ID.
    """
    from .knowledge import KnowledgeService
    try:
        service = KnowledgeService()
        service.update(key)
    except Exception as e:
        self.retry(exc=e)



async def aupload_knowledge_base(key: str) -> str:
    """
    Asynchronous wrapper for updating the knowledge base.
    :param key: The S3 object ID to update the knowledge base with.
    """
    return (await asyncio.to_thread(_upload_knowledge_base.delay, key=key)).id
