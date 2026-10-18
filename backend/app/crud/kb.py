"""知识库 CRUD。"""
from sqlalchemy.orm import Session

from app.models import Document, KnowledgeBase


def ensure_default_kb(db: Session) -> KnowledgeBase:
    kb = db.query(KnowledgeBase).order_by(KnowledgeBase.id.asc()).first()
    if kb is None:
        kb = KnowledgeBase(name="商品知识库", description="电商平台商品相关信息")
        db.add(kb)
        db.commit()
        db.refresh(kb)
    return kb


def create_document(db: Session, kb_id: int, filename: str, file_type: str, size: int) -> Document:
    doc = Document(
        knowledge_base_id=kb_id,
        filename=filename,
        file_type=file_type,
        size=size,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, doc_id: int) -> Document | None:
    return db.query(Document).filter(Document.id == doc_id).first()


def list_documents(db: Session, kb_id: int | None = None, page: int = 1, page_size: int = 20) -> tuple[int, list[Document]]:
    q = db.query(Document)
    if kb_id is not None:
        q = q.filter(Document.knowledge_base_id == kb_id)
    total = q.count()
    items = q.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return total, items


def update_document_status(db: Session, doc_id: int, status: str, error_message: str = "", chunk_count: int = 0) -> Document | None:
    doc = get_document(db, doc_id)
    if doc is None:
        return None
    doc.status = status
    doc.error_message = error_message
    doc.chunk_count = chunk_count
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, doc_id: int) -> Document | None:
    doc = get_document(db, doc_id)
    if doc is None:
        return None
    db.delete(doc)
    db.commit()
    return doc


def stats(db: Session) -> dict:
    kb = ensure_default_kb(db)
    doc_count = db.query(Document).filter(Document.knowledge_base_id == kb.id).count()
    chunk_count = db.query(Document).filter(Document.knowledge_base_id == kb.id).with_entities(Document.chunk_count).all()
    total_chunks = sum(c[0] for c in chunk_count)
    return {"kb_name": kb.name, "document_count": doc_count, "chunk_count": total_chunks}
