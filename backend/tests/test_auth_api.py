"""认证接口测试：注册/登录/me/改密码，含正常、边界、异常。"""
from tests.conftest import auth


class TestRegister:
    def test_register_and_login_ok(self, client):
        r = client.post("/api/v1/auth/register", json={"username": "bob", "password": "pass123"})
        assert r.status_code == 201
        assert r.json()["role"] == "user"

        r = client.post("/api/v1/auth/login", json={"username": "bob", "password": "pass123"})
        assert r.status_code == 200
        assert r.json()["token_type"] == "bearer"
        assert r.json()["user"]["username"] == "bob"

    def test_duplicate_username_409(self, client):
        client.post("/api/v1/auth/register", json={"username": "dup", "password": "pass123"})
        r = client.post("/api/v1/auth/register", json={"username": "dup", "password": "pass123"})
        assert r.status_code == 409

    def test_short_password_422(self, client):
        r = client.post("/api/v1/auth/register", json={"username": "short", "password": "123"})
        assert r.status_code == 422

    def test_empty_username_422(self, client):
        r = client.post("/api/v1/auth/register", json={"username": "", "password": "pass123"})
        assert r.status_code == 422


class TestLogin:
    def test_wrong_password_401(self, client):
        client.post("/api/v1/auth/register", json={"username": "carol", "password": "pass123"})
        r = client.post("/api/v1/auth/login", json={"username": "carol", "password": "wrongxx"})
        assert r.status_code == 401

    def test_unknown_user_401(self, client):
        r = client.post("/api/v1/auth/login", json={"username": "ghost", "password": "pass123"})
        assert r.status_code == 401


class TestMe:
    def test_me_ok(self, client, admin_token):
        r = client.get("/api/v1/auth/me", headers=auth(admin_token))
        assert r.status_code == 200
        assert r.json()["username"] == "admin"
        assert r.json()["role"] == "admin"

    def test_me_without_token_401(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_invalid_token_401(self, client):
        assert client.get("/api/v1/auth/me", headers=auth("not-a-jwt")).status_code == 401


class TestChangePassword:
    def test_change_password_ok_and_relogin(self, client, admin_token):
        r = client.post(
            "/api/v1/auth/change-password",
            headers=auth(admin_token),
            json={"old_password": "123456", "new_password": "newpass9"},
        )
        assert r.status_code == 200

        r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "newpass9"})
        assert r.status_code == 200
        # 恢复密码，避免影响其他用例
        t2 = r.json()["access_token"]
        client.post(
            "/api/v1/auth/change-password",
            headers=auth(t2),
            json={"old_password": "newpass9", "new_password": "123456"},
        )

    def test_change_password_wrong_old_400(self, client, admin_token):
        r = client.post(
            "/api/v1/auth/change-password",
            headers=auth(admin_token),
            json={"old_password": "wrong", "new_password": "newpass9"},
        )
        assert r.status_code == 400

    def test_change_password_short_new_422(self, client, admin_token):
        r = client.post(
            "/api/v1/auth/change-password",
            headers=auth(admin_token),
            json={"old_password": "123456", "new_password": "123"},
        )
        assert r.status_code == 422
