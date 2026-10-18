"""会话管理接口测试（M4）：创建/列表/重命名/删除/消息/用户隔离。"""
from tests.conftest import auth


class TestConversations:
    def test_create_and_list(self, client, user_token):
        r = client.post("/api/v1/conversations", headers=auth(user_token), json={"title": "我的会话"})
        assert r.status_code == 201
        conv_id = r.json()["id"]
        assert r.json()["title"] == "我的会话"

        r = client.get("/api/v1/conversations", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        assert any(c["id"] == conv_id for c in r.json()["items"])

    def test_create_default_title(self, client, user_token):
        r = client.post("/api/v1/conversations", headers=auth(user_token), json={})
        assert r.status_code == 201
        assert r.json()["title"] == "新会话"

    def test_rename(self, client, user_token):
        conv_id = client.post("/api/v1/conversations", headers=auth(user_token), json={}).json()["id"]
        r = client.patch(f"/api/v1/conversations/{conv_id}", headers=auth(user_token), json={"title": "改名后"})
        assert r.status_code == 200
        assert r.json()["title"] == "改名后"

    def test_rename_others_404(self, client, admin_token, user_token):
        conv_id = client.post("/api/v1/conversations", headers=auth(admin_token), json={}).json()["id"]
        assert client.patch(f"/api/v1/conversations/{conv_id}", headers=auth(user_token), json={"title": "x"}).status_code == 404

    def test_delete(self, client, user_token):
        conv_id = client.post("/api/v1/conversations", headers=auth(user_token), json={}).json()["id"]
        assert client.delete(f"/api/v1/conversations/{conv_id}", headers=auth(user_token)).status_code == 200
        assert client.get(f"/api/v1/conversations/{conv_id}/messages", headers=auth(user_token)).status_code == 404

    def test_delete_others_404(self, client, admin_token, user_token):
        conv_id = client.post("/api/v1/conversations", headers=auth(admin_token), json={}).json()["id"]
        assert client.delete(f"/api/v1/conversations/{conv_id}", headers=auth(user_token)).status_code == 404

    def test_messages_isolated(self, client, admin_token, user_token):
        """用户隔离：B 看不到 A 的会话消息。"""
        conv_id = client.post("/api/v1/conversations", headers=auth(admin_token), json={}).json()["id"]
        assert client.get(f"/api/v1/conversations/{conv_id}/messages", headers=auth(user_token)).status_code == 404
        assert client.get(f"/api/v1/conversations/{conv_id}/messages", headers=auth(admin_token)).status_code == 200


class TestMessages:
    def test_empty_conversation_messages(self, client, user_token):
        conv_id = client.post("/api/v1/conversations", headers=auth(user_token), json={}).json()["id"]
        r = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=auth(user_token))
        assert r.status_code == 200 and r.json() == []

    def test_message_persistence_roundtrip(self, client, user_token, db):
        """直接落库两条消息，读取应原样返回（含引用 JSON）。"""
        from app.crud import conversation as conv_crud

        conv_id = client.post("/api/v1/conversations", headers=auth(user_token), json={}).json()["id"]
        conv_crud.add_message(db, conv_id, "user", "耳机续航多久")
        conv_crud.add_message(
            db, conv_id, "assistant", "8 小时 [1]",
            refs=[{"index": 1, "filename": "a.txt", "text": "续航 8 小时"}],
        )
        r = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=auth(user_token))
        assert r.status_code == 200
        msgs = r.json()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user" and msgs[0]["content"] == "耳机续航多久"
        assert msgs[1]["role"] == "assistant" and "8 小时" in msgs[1]["content"]
        assert msgs[1]["refs"][0]["filename"] == "a.txt"
