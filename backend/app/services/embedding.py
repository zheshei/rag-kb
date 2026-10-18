"""向量化服务：本地 BGE-small-zh-v1.5（fastembed，CPU 推理）。

注意：首次使用会下载模型。国内网络访问 HuggingFace 不稳定，
默认走 hf-mirror 镜像（可用环境变量 HF_ENDPOINT 覆盖）。
"""
import os
from functools import lru_cache

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from app.core.config import get_settings  # noqa: E402


@lru_cache(maxsize=1)
def get_embedding():
    """全局共享 Embedding 实例（模型只加载一次）。"""
    from fastembed import TextEmbedding

    settings = get_settings()
    return TextEmbedding(model_name=settings.EMBEDDING_MODEL)


@lru_cache(maxsize=1024)
def embed_query_cached(query: str) -> list[float]:
    """查询向量缓存：相同问题不重复推理。"""
    emb = get_embedding()
    return list(emb.embed(query))[0]
