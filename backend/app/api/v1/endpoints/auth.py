"""认证接口：注册 / 登录 / 当前用户 / 修改密码。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.crud import user as user_crud
from app.db.session import get_db
from app.models import User
from app.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if user_crud.get_by_username(db, data.username):
        raise HTTPException(409, "用户名已存在")
    return user_crud.create_user(db, data.username, data.password, role="user")


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = user_crud.get_by_username(db, data.username)
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    return TokenResponse(access_token=create_access_token(user.username), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(data: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "原密码不正确")
    user_crud.update_password(db, user, data.new_password)
    return {"message": "密码修改成功"}
