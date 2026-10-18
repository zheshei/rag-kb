"""用户 CRUD 测试：正常、边界、异常。"""
import pytest

from app.core.security import hash_password, verify_password
from app.crud import user as crud


class TestPassword:
    def test_hash_and_verify_ok(self):
        h = hash_password("pass123")
        assert h != "pass123"
        assert verify_password("pass123", h)

    def test_verify_wrong_password_false(self):
        h = hash_password("pass123")
        assert not verify_password("wrong", h)

    def test_verify_invalid_hash_false(self):
        assert not verify_password("pass123", "not-a-bcrypt-hash")

    def test_hash_is_salted(self):
        assert hash_password("same") != hash_password("same")


class TestUserCrud:
    def test_create_and_get_by_username(self, db):
        u = crud.create_user(db, "crud_user", "pass123")
        got = crud.get_by_username(db, "crud_user")
        assert got is not None and got.username == "crud_user" and got.role == "user"

    def test_get_missing_returns_none(self, db):
        assert crud.get_by_username(db, "no_such_user") is None

    def test_update_password_changes_hash(self, db):
        u = crud.create_user(db, "crud_pass", "oldpass1")
        old_hash = u.password_hash
        crud.update_password(db, u, "newpass2")
        assert u.password_hash != old_hash
        assert verify_password("newpass2", u.password_hash)

    def test_count_users(self, db):
        before = crud.count_users(db)
        crud.create_user(db, f"count_user_{before}", "pass123")
        assert crud.count_users(db) == before + 1

    def test_duplicate_username_raises(self, db):
        crud.create_user(db, "dup_user", "pass123")
        with pytest.raises(Exception):
            crud.create_user(db, "dup_user", "pass123")
