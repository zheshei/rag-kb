"""数据库会话：SQLite + SQLAlchemy（WAL 模式 + 连接池，支撑百级并发）。"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
    # SQLite 读并发友好：扩大连接池，避免 100 并发时排队超时
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
)


if _is_sqlite:
    # WAL 是文件级持久状态：启动时用单连接设置一次，避免并发建连时
    # 多个连接同时执行 PRAGMA journal_mode=WAL 争夺文件 EXCLUSIVE 锁（会把连接池卡满）。
    try:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.commit()
    except Exception:
        pass  # 内存库等不支持 WAL 时静默降级为默认日志模式

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """连接级参数：busy_timeout（写锁等待）。无需文件锁，并发建连安全。"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
