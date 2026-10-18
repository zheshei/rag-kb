"""会话与消息模型（M4 多会话 + 历史持久化）。"""
from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=128)


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=128)


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    refs: list[dict] = []
    created_at: datetime

    model_config = {"from_attributes": True}
