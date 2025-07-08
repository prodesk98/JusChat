from typing import Optional

from fastapi import UploadFile
from pydantic import BaseModel


class KnowledgeUploadSchema(BaseModel):
    files: list[UploadFile]


class KnowledgeUpdateResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    job_ids: list[str] = []


class AgentGraphRAGRequest(BaseModel):
    question: str


class AgentGraphRAGResponse(BaseModel):
    result: str
