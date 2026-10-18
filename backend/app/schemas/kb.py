"""知识库相关响应模型。"""
from datetime import datetime

from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    knowledge_base_id: int
    filename: str
    file_type: str
    size: int
    status: str
    error_message: str = ""
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListOut(BaseModel):
    total: int
    items: list[DocumentOut]


class StatsOut(BaseModel):
    kb_name: str
    document_count: int
    chunk_count: int
