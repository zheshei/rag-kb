"""顶层路由聚合：所有 v1 接口统一挂载到这里。"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, conversation, dashboard, kb

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(kb.router, tags=["知识库"])
api_router.include_router(chat.router, tags=["问答"])
api_router.include_router(conversation.router, tags=["会话"])
api_router.include_router(dashboard.router, tags=["看板"])
