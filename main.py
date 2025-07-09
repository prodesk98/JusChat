import os

from fastapi import FastAPI, Depends, Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from schemas import (
    KnowledgeUploadSchema, KnowledgeUpdateResponse,
    AgentGraphRAGRequest, AgentGraphRAGResponse,
)
from core import AgentGraphRAGBedRock, ChatManager
from server import SocketManager

app = FastAPI(
    title="Chat GraphRAG API",
    description="API for interacting with a chat system that utilizes a knowledge base.",
    version="1.0.0",
)
sio = SocketManager()
sio.mount_to("/socket.io", app)

path__ = os.path.dirname(os.path.abspath(__file__))

app.mount("/public", StaticFiles(directory="%s/public" % path__), name="static")
templates = Jinja2Templates(directory="%s/public/templates" % path__)


@sio.on("chat_history")
async def chat_history(sid, data):
    """
    Handle a user joining a chat room.
    :param data:
    :param sid: The session ID of the user.
    """
    chat_id = data.get("chat_id")
    if not chat_id:
        return await sio.emit("error", {"message": "Chat ID is required to join."}, room=sid)
    chat_manager = ChatManager(chat_id)
    return await sio.emit(
        "history_updated",
        {
            "history": [
                {
                    "content": h.content,
                    "role": "user"
                    if h.type == "human" else "assistant"
                }
                for h in await chat_manager.get_history()
            ]
        },
        room=sid,
    )

@sio.on("invoke_agent")
async def invoke_agent(sid, data):
    """
    Handle a request to invoke an agent with a chat message.
    :param data: The data containing the chat message and any additional information.
    :param sid: The session ID of the user.
    """
    chat_id = data.get("chat_id")
    if not chat_id:
        return await sio.emit("error", {"message": "Chat ID is required."}, room=sid)

    question = data.get("question")
    if not question:
        return await sio.emit("error", {"message": "Question is required."}, room=sid)

    agent = AgentGraphRAGBedRock(chat_id)
    response = await agent.invoke(question)

    return await sio.emit(
        "agent_response",
        {"result": response},
        room=sid,
    )

@app.get("/")
async def root(request: Request):
    """
    Root endpoint that serves the main HTML page.
    :return: The rendered HTML template.
    """
    return templates.TemplateResponse(request, "index.html", {})


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
