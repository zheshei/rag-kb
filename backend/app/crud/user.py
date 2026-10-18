"""用户 CRUD。"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str, role: str = "user") -> User:
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: User, new_password: str) -> None:
    user.password_hash = hash_password(new_password)
    db.commit()


def count_users(db: Session) -> int:
    return db.query(User).count()
