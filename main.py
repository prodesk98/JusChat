from fastapi import FastAPI, Depends
from schemas import (
    KnowledgeUploadSchema, KnowledgeUpdateResponse,
    AgentGraphRAGRequest, AgentGraphRAGResponse,
)
from core import AgentGraphRAGBedRock

app = FastAPI(
    title="Chat GraphRAG API",
    description="API for interacting with a chat system that utilizes a knowledge base.",
    version="1.0.0",
)

@app.post("/chat/{chat_id}", response_model=AgentGraphRAGResponse)
async def chat(chat_id: str, data: AgentGraphRAGRequest) -> AgentGraphRAGResponse:
    """
    Endpoint to handle chat messages.
    :param data: The data containing the chat message and any additional information.
    :param chat_id: The message to process.
    :return: A response containing the processed message.
    """
    agent = AgentGraphRAGBedRock(chat_id)
    response = await agent.invoke(data.question)
    return AgentGraphRAGResponse(**{"result": response})


@app.post("/knowledge/update", response_model=KnowledgeUpdateResponse)
async def update_knowledge(upload: KnowledgeUploadSchema = Depends(KnowledgeUploadSchema)) -> KnowledgeUpdateResponse:
    """
    Endpoint to update the knowledge base with a new document.
    :param upload: The uploaded files containing the knowledge base document.
    :return: A confirmation message.
    """
    from workers import aupload_knowledge_base
    if len(upload.files) == 0:
        return KnowledgeUpdateResponse(
            success=False,
            message="No files uploaded."
        )
    job_ids: list[str] = []
    for file in upload.files:
        if not file.filename.endswith(('.pdf', '.txt', '.md')):
            return KnowledgeUpdateResponse(
                success=False,
                message="Unsupported file type. Only PDF, TXT, and MD files are allowed."
            )
        job_id = await aupload_knowledge_base(key=file.filename)
        job_ids.append(job_id)
    return KnowledgeUpdateResponse(
        success=True,
        message="Knowledge base updated successfully.",
        job_ids=job_ids
    )
