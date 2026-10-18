"""pytest 全局夹具：临时数据库 + 临时数据目录 + 测试客户端。

注意：必须在导入 app 之前设置环境变量，保证配置与数据完全隔离。
"""
import os
import tempfile
from pathlib import Path

import pytest

_tmp = tempfile.mkdtemp(prefix="rag_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["DATA_DIR"] = _tmp
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ZHIPU_API_KEY"] = ""
os.environ["LLM_PROVIDER"] = "zhipu"

from fastapi.testclient import TestClient  # noqa: E402

import app.main  # noqa: E402  (import 时完成建表 + 种子 admin)

from app.db.session import SessionLocal  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app.main.app) as c:
        yield c


@pytest.fixture()
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def admin_token(client) -> str:
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "123456"})
    assert r.status_code == 200
    return r.json()["access_token"]


@pytest.fixture()
def user_token(client) -> str:
    """注册（若已存在则跳过）并登录 alice。"""
    r = client.post("/api/v1/auth/register", json={"username": "alice", "password": "secret123"})
    if r.status_code != 201:
        assert r.status_code == 409  # 已注册（会话内共享临时库）
    r = client.post("/api/v1/auth/login", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
