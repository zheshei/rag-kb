"""知识库接口测试：权限、上传、列表、删除、统计。"""
from tests.conftest import auth


class TestKbPermissions:
    def test_upload_requires_login(self, client):
        r = client.post("/api/v1/kb/documents/upload", files={"file": ("a.txt", b"hello", "text/plain")})
        assert r.status_code == 401

    def test_upload_forbidden_for_user(self, client, user_token):
        r = client.post(
            "/api/v1/kb/documents/upload",
            headers=auth(user_token),
            files={"file": ("a.txt", b"hello", "text/plain")},
        )
        assert r.status_code == 403

    def test_list_forbidden_for_user(self, client, user_token):
        assert client.get("/api/v1/kb/documents", headers=auth(user_token)).status_code == 403

    def test_stats_allowed_for_user(self, client, user_token):
        r = client.get("/api/v1/kb/stats", headers=auth(user_token))
        assert r.status_code == 200
        assert "kb_name" in r.json()


class TestKbUpload:
    def test_upload_rejects_bad_type(self, client, admin_token):
        r = client.post(
            "/api/v1/kb/documents/upload",
            headers=auth(admin_token),
            files={"file": ("evil.exe", b"MZ", "application/octet-stream")},
        )
        assert r.status_code == 400

    def test_upload_txt_and_process(self, client, admin_token, monkeypatch):
        """上传 txt，入库管道以桩替代（避免测试期间下载模型）。"""
        from app.api.v1.endpoints import kb as kb_mod
        from app.services import ingestion

        calls = {}

        def fake_ingest(file_path, file_type, doc_id, filename):
            calls["args"] = (file_type, doc_id, filename)
            return 2

        monkeypatch.setattr(ingestion, "ingest_document", fake_ingest)
        r = client.post(
            "/api/v1/kb/documents/upload",
            headers=auth(admin_token),
            files={"file": ("商品.txt", "无线蓝牙耳机续航8小时".encode("utf-8"), "text/plain")},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["status"] == "processing" or body["status"] == "completed"
        assert calls["args"][1] == body["id"]
        assert calls["args"][2] == "商品.txt"


class TestKbDelete:
    def test_delete_missing_404(self, client, admin_token):
        assert client.delete("/api/v1/kb/documents/99999", headers=auth(admin_token)).status_code == 404

    def test_delete_ok(self, client, admin_token, db):
        from app.crud import kb as kb_crud

        kb = kb_crud.ensure_default_kb(db)
        doc = kb_crud.create_document(db, kb.id, "d.txt", "txt", 10)
        r = client.delete(f"/api/v1/kb/documents/{doc.id}", headers=auth(admin_token))
        assert r.status_code == 200
        assert kb_crud.get_document(db, doc.id) is None
