"""会话与消息 CRUD（M4）。"""
import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Conversation, Message


def list_conversations(db: Session, user_id: int, page: int = 1, page_size: int = 50) -> tuple[int, list[Conversation]]:
    q = db.query(Conversation).filter(Conversation.user_id == user_id)
    total = q.count()
    items = q.order_by(Conversation.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def get_conversation(db: Session, conv_id: int, user_id: int) -> Conversation | None:
    return db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == user_id).first()


def create_conversation(db: Session, user_id: int, title: str = "新会话") -> Conversation:
    conv = Conversation(user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def rename_conversation(db: Session, conv: Conversation, title: str) -> Conversation:
    conv.title = title
    db.commit()
    db.refresh(conv)
    return conv


def touch_conversation(db: Session, conv: Conversation) -> None:
    conv.updated_at = func.now()
    db.commit()


def delete_conversation(db: Session, conv_id: int) -> None:
    db.query(Message).filter(Message.conversation_id == conv_id).delete()
    db.query(Conversation).filter(Conversation.id == conv_id).delete()
    db.commit()


def add_message(db: Session, conv_id: int, role: str, content: str, refs: list[dict] | None = None) -> Message:
    msg = Message(conversation_id=conv_id, role=role, content=content, refs_json=json.dumps(refs or [], ensure_ascii=False))
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def list_messages(db: Session, conv_id: int) -> list[Message]:
    return db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at.asc(), Message.id.asc()).all()


def count_messages(db: Session, conv_id: int) -> int:
    return db.query(Message).filter(Message.conversation_id == conv_id).count()


def count_conversations(db: Session, user_id: int | None = None) -> int:
    q = db.query(Conversation)
    if user_id is not None:
        q = q.filter(Conversation.user_id == user_id)
    return q.count()


def count_all_messages(db: Session) -> int:
    return db.query(Message).count()
