"""文档入库管道：LangChain 解析 → 父子分块 → BGE 向量化 → Chroma 写入。"""
from pathlib import Path

from app.core.config import get_settings
from app.services.cache import bump_kb_version
from app.services import vectorstore as vs
from app.services.embedding import get_embedding


def load_document(file_path: Path, file_type: str) -> list[str]:
    """按类型选择 LangChain 加载器，返回原始文本列表。"""
    if file_type == "pdf":
        from langchain_community.document_loaders import PyMuPDFLoader

        return [d.page_content for d in PyMuPDFLoader(str(file_path)).load() if d.page_content.strip()]

    if file_type == "docx":
        from langchain_community.document_loaders import Docx2txtLoader

        return [d.page_content for d in Docx2txtLoader(str(file_path)).load() if d.page_content.strip()]

    from langchain_community.document_loaders import TextLoader

    return [d.page_content for d in TextLoader(str(file_path), encoding="utf-8").load() if d.page_content.strip()]


def split_texts(texts: list[str]) -> tuple[list[str], list[str]]:
    """父子分块：父块 800 / 子块 200，子块用于检索、父块用于返回上下文。"""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    settings = get_settings()
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.PARENT_CHUNK_SIZE, chunk_overlap=60, separators=["\n\n", "\n", "。", "！", "？", "；", " "]
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHILD_CHUNK_SIZE, chunk_overlap=settings.CHILD_CHUNK_OVERLAP, separators=["\n", "。", "！", "？", "；", "，", " "]
    )

    parents: list[str] = []
    for t in texts:
        parents.extend(parent_splitter.split_text(t))
    # 子块继承父块编号，父块本身作为检索内容兜底
    child_docs = []
    for parent in parents:
        children = child_splitter.split_text(parent)
        child_docs.extend(children if children else [parent])
    return parents, child_docs


def ingest_document(file_path: Path, file_type: str, document_id: int, filename: str) -> int:
    """完整入库：加载 → 分块 → 向量化 → 写入 Chroma，返回分块数。

    抛出的任何异常由调用方捕获并标记文档状态为 failed。
    """
    settings = get_settings()
    texts = load_document(file_path, file_type)
    if not texts:
        raise ValueError("文档解析后无有效文本内容")

    _, child_docs = split_texts(texts)

    emb = get_embedding()
    # fastembed 返回 list[list[float]]（Python 列表），直接入库
    embeddings = list(emb.embed(child_docs))

    collection = vs.get_collection()
    ids = [f"doc-{document_id}-{i}" for i in range(len(child_docs))]
    metadatas = [{"document_id": document_id, "filename": filename} for _ in child_docs]
    vs.add_chunks(collection, ids=ids, documents=child_docs, embeddings=embeddings, metadatas=metadatas)

    bump_kb_version()  # 知识库变更 → 检索缓存失效
    return len(child_docs)


def remove_document_vectors(document_id: int) -> None:
    collection = vs.get_collection()
    vs.delete_by_document(collection, document_id)
    bump_kb_version()
