"""管理员看板接口测试（M6）：权限 + 统计字段。"""
from tests.conftest import auth


class TestDashboard:
    def test_requires_login(self, client):
        assert client.get("/api/v1/dashboard/stats").status_code == 401

    def test_forbidden_for_user(self, client, user_token):
        assert client.get("/api/v1/dashboard/stats", headers=auth(user_token)).status_code == 403

    def test_stats_ok_for_admin(self, client, admin_token):
        r = client.get("/api/v1/dashboard/stats", headers=auth(admin_token))
        assert r.status_code == 200
        body = r.json()
        for field in ("users", "documents", "chunks", "conversations", "messages", "vector_count", "recent_documents"):
            assert field in body
        assert body["users"] >= 1
