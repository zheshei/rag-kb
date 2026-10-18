"""问答请求模型。"""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, description="用户问题")
    top_k: int = Field(5, ge=1, le=10, description="引用片段数量")
    conversation_id: int | None = Field(default=None, description="所属会话；为空则自动创建新会话")
