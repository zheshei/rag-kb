"""问答接口：SSE 流式返回；接入会话（M4），问答与引用自动落库持久化。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.crud import conversation as conv_crud
from app.db.session import SessionLocal, get_db
from app.models import User
from app.schemas.chat import AskRequest
from app.services import retrieval
from app.services.qa import stream_answer

router = APIRouter(prefix="/chat")


def _sse(event: str, data: dict) -> str:
    """序列化 SSE 事件帧。"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _auto_title(question: str) -> str:
    """用问题前 20 字作为新会话标题。"""
    title = question.strip().replace("\n", " ")
    return title[:20] if len(title) > 20 else (title or "新会话")


@router.post("/ask")
async def ask(data: AskRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """检索知识库并流式回答；事件序列：meta(引用+会话) → delta* → done/error。"""
    # 先校验会话归属（404 优先于配置类错误）
    conv = None
    if data.conversation_id is not None:
        conv = conv_crud.get_conversation(db, data.conversation_id, user.id)
        if conv is None:
            raise HTTPException(404, "会话不存在或不属于当前用户")
    else:
        conv = conv_crud.create_conversation(db, user.id, title=_auto_title(data.question))

    settings = get_settings()
    if settings.LLM_PROVIDER == "zhipu" and not settings.ZHIPU_API_KEY:
        raise HTTPException(
            400, "尚未配置智谱 API Key：请在 backend/.env 中设置 ZHIPU_API_KEY 后重启服务"
        )

    chunks = retrieval.retrieve(data.question, top_k=data.top_k)
    if not chunks:
        raise HTTPException(404, "知识库中暂无相关内容，请先由管理员上传商品文档")

    refs = [
        {
            "index": i + 1,
            "filename": c["metadata"].get("filename", ""),
            "document_id": c["metadata"].get("document_id"),
            "text": c["content"],
        }
        for i, c in enumerate(chunks)
    ]

    async def gen():
        yield _sse("meta", {"chunks": refs, "conversation_id": conv.id, "title": conv.title})
        answer_parts: list[str] = []
        try:
            async for text in stream_answer(data.question, chunks):
                answer_parts.append(text)
                yield _sse("delta", {"text": text})
            yield _sse("done", {})
            # 流式结束后落库：用户问题 + 助手回答 + 引用
            _persist(db=None, user_id=user.id, conv_id=conv.id, question=data.question, answer="".join(answer_parts), refs=refs)
        except Exception as e:  # LLM 调用失败等，向前端给出明确错误
            yield _sse("error", {"message": f"回答生成失败：{str(e)[:200]}"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _persist(db, user_id: int, conv_id: int, question: str, answer: str, refs: list[dict]) -> None:
    """独立会话保存问答与引用；失败不影响已返回的流式内容。"""
    session = SessionLocal()
    try:
        conv_crud.add_message(session, conv_id, "user", question, refs=None)
        conv_crud.add_message(session, conv_id, "assistant", answer, refs=refs)
        conv = conv_crud.get_conversation(session, conv_id, user_id)
        if conv is not None:
            conv_crud.touch_conversation(session, conv)
    except Exception:
        session.rollback()
    finally:
        session.close()
