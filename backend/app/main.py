"""FastAPI 应用入口：中间件、启动初始化（建表 + 种子管理员）。"""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.crud import kb as kb_crud
from app.crud import user as user_crud
from app.db.base import Base
from app.db.session import SessionLocal, engine

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")

# M5 性能优化：GZip 压缩响应
app.add_middleware(GZipMiddleware, minimum_size=1024)

# 开发期跨域（前端 5173）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timing(request: Request, call_next):
    """M5 性能优化：请求耗时监控（响应头 X-Process-Time）。"""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed * 1000:.1f}ms"
    return response


def init_db() -> None:
    """建表 + 种子管理员 admin/123456。"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if user_crud.get_by_username(db, "admin") is None:
            user_crud.create_user(db, "admin", "123456", role="admin")
            print("[seed] 管理员账号已创建 admin/123456")
        else:
            print("[seed] 管理员账号已存在，跳过")
        kb_crud.ensure_default_kb(db)
    finally:
        db.close()


init_db()

app.include_router(api_router, prefix="/api/v1")
