"""向量库：Chroma 持久化（本地文件，无需外部服务）。"""
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_collection():
    """返回全局共享的 Chroma 集合（data/chroma 持久化）。"""
    import chromadb

    settings = get_settings()
    persist_dir = Path(settings.DATA_DIR) / "chroma"
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    return client.get_or_create_collection(settings.CHROMA_COLLECTION)


def add_chunks(collection, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict]) -> None:
    """批量写入分块。embeddings 为 list[list[float]]，直接入库。"""
    collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)


def delete_by_document(collection, document_id: int) -> None:
    """按文档删除其全部分块。"""
    data = collection.get(where={"document_id": document_id})
    ids = data["ids"]
    if ids:
        collection.delete(ids=ids)


def collection_size(collection) -> int:
    return collection.count()
