"""会话管理接口（M4）：多用户独立会话，创建/列表/重命名/删除/历史消息。"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.crud import conversation as conv_crud
from app.db.session import get_db
from app.models import User
from app.schemas import ConversationCreate, ConversationOut, ConversationRename, MessageOut

router = APIRouter(prefix="/conversations")


def _to_out(db: Session, conv) -> ConversationOut:
    out = ConversationOut.model_validate(conv)
    out.message_count = conv_crud.count_messages(db, conv.id)
    return out


@router.get("", response_model=dict)
def list_conversations(page: int = 1, page_size: int = 50, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total, items = conv_crud.list_conversations(db, user.id, page=max(page, 1), page_size=min(max(page_size, 1), 100))
    return {"total": total, "items": [_to_out(db, c) for c in items]}


@router.post("", response_model=ConversationOut, status_code=201)
def create_conversation(data: ConversationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = conv_crud.create_conversation(db, user.id, title=(data.title or "新会话")[:128])
    return _to_out(db, conv)


@router.patch("/{conv_id}", response_model=ConversationOut)
def rename_conversation(conv_id: int, data: ConversationRename, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = conv_crud.get_conversation(db, conv_id, user.id)
    if conv is None:
        raise HTTPException(404, "会话不存在或不属于当前用户")
    conv = conv_crud.rename_conversation(db, conv, data.title[:128])
    return _to_out(db, conv)


@router.delete("/{conv_id}")
def delete_conversation(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = conv_crud.get_conversation(db, conv_id, user.id)
    if conv is None:
        raise HTTPException(404, "会话不存在或不属于当前用户")
    conv_crud.delete_conversation(db, conv_id)
    return {"message": "会话已删除"}


@router.get("/{conv_id}/messages", response_model=list[MessageOut])
def list_messages(conv_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = conv_crud.get_conversation(db, conv_id, user.id)
    if conv is None:
        raise HTTPException(404, "会话不存在或不属于当前用户")
    msgs = conv_crud.list_messages(db, conv_id)
    out = []
    for m in msgs:
        item = MessageOut.model_validate(m)
        try:
            item.refs = json.loads(m.refs_json or "[]")
        except json.JSONDecodeError:
            item.refs = []
        out.append(item)
    return out
