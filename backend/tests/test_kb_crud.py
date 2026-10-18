"""知识库 CRUD 测试。"""
from app.crud import kb as crud
from app.models import Document


class TestKnowledgeCrud:
    def test_ensure_default_kb_idempotent(self, db):
        kb1 = crud.ensure_default_kb(db)
        kb2 = crud.ensure_default_kb(db)
        assert kb1.id == kb2.id

    def test_create_and_get_document(self, db):
        kb = crud.ensure_default_kb(db)
        doc = crud.create_document(db, kb.id, "a.txt", "txt", 100)
        got = crud.get_document(db, doc.id)
        assert got is not None and got.filename == "a.txt" and got.status == "processing"

    def test_update_document_status(self, db):
        kb = crud.ensure_default_kb(db)
        doc = crud.create_document(db, kb.id, "b.txt", "txt", 100)
        crud.update_document_status(db, doc.id, "completed", chunk_count=3)
        got = crud.get_document(db, doc.id)
        assert got.status == "completed" and got.chunk_count == 3

    def test_update_missing_returns_none(self, db):
        assert crud.update_document_status(db, 99999, "completed") is None

    def test_list_documents_pagination(self, db):
        kb = crud.ensure_default_kb(db)
        before_total, _ = crud.list_documents(db, kb.id, page=1, page_size=100)
        for i in range(5):
            crud.create_document(db, kb.id, f"f{i}.txt", "txt", 10)
        total, items = crud.list_documents(db, kb.id, page=1, page_size=2)
        assert total == before_total + 5 and len(items) == 2

    def test_delete_document(self, db):
        kb = crud.ensure_default_kb(db)
        doc = crud.create_document(db, kb.id, "del.txt", "txt", 10)
        crud.delete_document(db, doc.id)
        assert crud.get_document(db, doc.id) is None

    def test_stats(self, db):
        kb = crud.ensure_default_kb(db)
        doc = crud.create_document(db, kb.id, "s.txt", "txt", 10)
        crud.update_document_status(db, doc.id, "completed", chunk_count=4)
        s = crud.stats(db)
        assert s["document_count"] >= 1 and s["chunk_count"] >= 4
