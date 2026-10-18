"""问答接口测试：鉴权、配置缺失提示、参数校验、会话归属。"""
from app.core.config import get_settings
from tests.conftest import auth


def _ask(client, token=None, question="耳机续航", top_k=3, conversation_id=None):
    headers = {}
    if token:
        headers = auth(token)
    payload = {"question": question, "top_k": top_k}
    if conversation_id is not None:
        payload["conversation_id"] = conversation_id
    return client.post("/api/v1/chat/ask", json=payload, headers=headers)


class TestChatApi:
    def test_ask_requires_auth(self, client):
        assert _ask(client).status_code == 401

    def test_ask_without_api_key_400(self, client, admin_token, monkeypatch):
        """未配置智谱 Key 时给出明确提示（不真正调用外部模型）。"""
        s = get_settings()
        monkeypatch.setattr(s, "LLM_PROVIDER", "zhipu")
        monkeypatch.setattr(s, "ZHIPU_API_KEY", "")
        r = _ask(client, token=admin_token)
        assert r.status_code == 400
        assert "ZHIPU_API_KEY" in r.json()["detail"]

    def test_ask_empty_question_422(self, client, admin_token):
        assert _ask(client, token=admin_token, question="").status_code == 422

    def test_ask_top_k_out_of_range_422(self, client, admin_token):
        assert _ask(client, token=admin_token, top_k=99).status_code == 422

    def test_ask_unknown_conversation_404(self, client, admin_token):
        assert _ask(client, token=admin_token, conversation_id=99999).status_code == 404


class TestConversationOwnership:
    def test_user_cannot_use_others_conversation(self, client, admin_token, user_token):
        """A 用户建的会话，B 用户不可使用。"""
        r = client.post("/api/v1/conversations", headers=auth(admin_token), json={"title": "admin 的会话"})
        conv_id = r.json()["id"]
        resp = _ask(client, token=user_token, conversation_id=conv_id)
        assert resp.status_code == 404
