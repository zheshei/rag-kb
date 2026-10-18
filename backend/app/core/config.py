"""全局配置：pydantic-settings 从环境变量 / .env 读取。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 应用
    APP_NAME: str = "RAG 企业级知识库问答系统"
    SECRET_KEY: str = "change-me-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 数据存储（SQLite 单机版，无需外部服务）
    DATABASE_URL: str = "sqlite:///./rag.db"
    DATA_DIR: str = "data"

    # 上传限制
    MAX_UPLOAD_MB: int = 50
    ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx", ".txt", ".md")

    # 分块参数：父子分块（父块用于上下文，子块用于检索）
    PARENT_CHUNK_SIZE: int = 800
    CHILD_CHUNK_SIZE: int = 200
    CHILD_CHUNK_OVERLAP: int = 40

    # 向量化：本地 BGE-small-zh-v1.5（512 维，CPU 推理，无需显卡）
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DIM: int = 512
    CHROMA_COLLECTION: str = "kb_documents"

    # 云端大模型（M3 接入智谱 GLM，OpenAI 兼容）
    ZHIPU_API_KEY: str = ""
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    ZHIPU_MODEL: str = "glm-4-flash"

    # LLM 提供方：zhipu（智谱，默认）/ ollama（本地备选，OpenAI 兼容）
    LLM_PROVIDER: str = "zhipu"
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # 重排增强（可选）：fastembed Rerank，开启会额外下载模型
    RERANK_ENABLED: bool = False
    RERANK_MODEL: str = "BAAI/bge-reranker-base"

    # 性能优化：检索结果缓存
    RETRIEVAL_CACHE_TTL: int = 300  # 秒
    RETRIEVAL_CACHE_MAXSIZE: int = 128


@lru_cache
def get_settings() -> Settings:
    return Settings()
