"""管理员看板接口（M6）：系统运行统计。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.crud import conversation as conv_crud
from app.crud import kb as kb_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.services import vectorstore as vs

router = APIRouter(prefix="/dashboard", dependencies=[Depends(require_admin)])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    kb = kb_crud.ensure_default_kb(db)
    _, docs = kb_crud.list_documents(db, kb.id, page=1, page_size=100)
    return {
        "users": user_crud.count_users(db),
        "documents": kb_crud.stats(db)["document_count"],
        "chunks": kb_crud.stats(db)["chunk_count"],
        "conversations": conv_crud.count_conversations(db),
        "messages": conv_crud.count_all_messages(db),
        "vector_count": vs.collection_size(vs.get_collection()),
        "recent_documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "size": d.size,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
    }
