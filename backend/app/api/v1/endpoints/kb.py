"""知识库接口：管理（仅管理员）+ 统计（登录用户）。"""
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.config import get_settings
from app.crud import kb as kb_crud
from app.db.session import get_db
from app.models import Document
from app.schemas import DocumentListOut, DocumentOut, StatsOut
from app.services import ingestion

router = APIRouter(prefix="/kb")


def _process_upload(file_path: Path, file_type: str, doc_id: int, filename: str) -> None:
    """后台任务：解析 + 分块 + 向量化 + 入库。"""
    from app.db.session import SessionLocal

    try:
        chunk_count = ingestion.ingest_document(file_path, file_type, doc_id, filename)
        db = SessionLocal()
        try:
            kb_crud.update_document_status(db, doc_id, "completed", chunk_count=chunk_count)
        finally:
            db.close()
    except Exception as e:  # 入库失败 → 标记文档状态
        db = SessionLocal()
        try:
            kb_crud.update_document_status(db, doc_id, "failed", error_message=str(e)[:500])
        finally:
            db.close()


@router.post("/documents/upload", response_model=DocumentOut, status_code=201, dependencies=[Depends(require_admin)])
async def upload_document(file: UploadFile, background: BackgroundTasks, db: Session = Depends(get_db)):
    settings = get_settings()
    filename = file.filename or "unnamed"
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件类型 {ext}，仅支持 {', '.join(settings.ALLOWED_EXTENSIONS)}")

    content = await file.read()
    size = len(content)
    if size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"文件超过 {settings.MAX_UPLOAD_MB}MB 限制")

    kb = kb_crud.ensure_default_kb(db)
    doc = kb_crud.create_document(db, kb.id, filename, ext.lstrip("."), size)

    upload_dir = Path(settings.DATA_DIR) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{doc.id}_{filename}"
    file_path.write_bytes(content)

    background.add_task(_process_upload, file_path, ext.lstrip("."), doc.id, filename)
    return doc


@router.get("/documents", response_model=DocumentListOut, dependencies=[Depends(require_admin)])
def list_documents(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    kb = kb_crud.ensure_default_kb(db)
    total, items = kb_crud.list_documents(db, kb.id, page=max(page, 1), page_size=min(max(page_size, 1), 100))
    return DocumentListOut(total=total, items=[DocumentOut.model_validate(d) for d in items])


@router.delete("/documents/{doc_id}", response_model=DocumentOut, dependencies=[Depends(require_admin)])
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = kb_crud.get_document(db, doc_id)
    if doc is None:
        raise HTTPException(404, "文档不存在")
    ingestion.remove_document_vectors(doc_id)
    kb_crud.delete_document(db, doc_id)
    return DocumentOut.model_validate(doc)


@router.get("/stats", response_model=StatsOut)
def stats(_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return StatsOut(**kb_crud.stats(db))
