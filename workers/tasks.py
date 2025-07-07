from .connection import app


@app.task(
    name="knowledge.update_knowledge_base",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    countdown=60,
)
def update_knowledge_base(self, key: str):
    """
    Update the knowledge base with the given ID.
    """
    from .knowledge import KnowledgeService
    try:
        service = KnowledgeService()
        service.update(key)
    except Exception as e:
        self.retry(exc=e)
