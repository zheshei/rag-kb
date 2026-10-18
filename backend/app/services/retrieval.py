"""混合检索：向量召回 + 关键词召回（BM25+jieba）→ RRF 融合 → 可选 Rerank。

- 向量检索：Chroma 语义相似度
- 关键词检索：对全量分块做 BM25 打分，弥补语义检索对专有名词/型号不敏感的问题
- RRF 融合：按排名加权合并两路结果，提升召回稳健性
- M5 性能优化：检索结果进程内缓存（知识库版本变化时自动失效）
"""
import jieba
from rank_bm25 import BM25Okapi

from app.core.config import get_settings
from app.services import vectorstore as vs
from app.services.cache import get_retrieval_cache, retrieval_cache_key
from app.services.embedding import embed_query_cached

RRF_K = 60  # RRF 常数，控制排名权重


def _tokenize(text: str) -> list[str]:
    return [t.strip() for t in jieba.cut(text) if t.strip()]


def vector_search(query: str, top_k: int = 10) -> list[dict]:
    """Chroma 向量召回。"""
    qv = embed_query_cached(query)
    col = vs.get_collection()
    r = col.query(
        query_embeddings=[qv], n_results=top_k, include=["documents", "metadatas", "distances"]
    )
    out = []
    for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0]):
        out.append({"content": doc, "metadata": meta, "score": 1.0 / (1.0 + dist)})
    return out


def keyword_search(query: str, top_k: int = 10) -> list[dict]:
    """BM25 关键词召回。"""
    col = vs.get_collection()
    data = col.get(include=["documents", "metadatas"])
    docs, metas = data["documents"], data["metadatas"]
    if not docs:
        return []
    corpus = [_tokenize(d) for d in docs]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))
    out = []
    for i in sorted(range(len(scores)), key=lambda j: -scores[j]):
        if scores[i] <= 0:
            continue
        out.append({"content": docs[i], "metadata": metas[i], "score": float(scores[i])})
        if len(out) >= top_k:
            break
    return out


def rrf_fusion(vec: list[dict], kw: list[dict], top_k: int = 10) -> list[dict]:
    """Reciprocal Rank Fusion：按排名倒数加权合并两路结果。"""
    merged: dict[str, dict] = {}

    def add(items: list[dict]) -> None:
        for rank, item in enumerate(items):
            key = item["content"]
            entry = merged.setdefault(
                key, {"content": item["content"], "metadata": item["metadata"], "rrf": 0.0}
            )
            entry["rrf"] += 1.0 / (RRF_K + rank)

    add(vec)
    add(kw)
    ranked = sorted(merged.values(), key=lambda x: -x["rrf"])
    return ranked[:top_k]


def _rerank(query: str, items: list[dict]) -> list[dict]:
    """Cross-encoder 重排（fastembed Rerank，CPU 可跑）。"""
    from fastembed import TextReranking

    reranker = TextReranking(model_name=get_settings().RERANK_MODEL)
    scores = list(reranker.rerank(query, [i["content"] for i in items]))
    for item, s in zip(items, scores):
        item["rerank_score"] = float(s.score)
    return sorted(items, key=lambda x: -x["rerank_score"])


def _retrieve_inner(query: str, top_k: int) -> list[dict]:
    """实际检索逻辑（不带缓存）。"""
    n = max(top_k * 3, 10)
    vec = vector_search(query, top_k=n)
    kw = keyword_search(query, top_k=n)
    fused = rrf_fusion(vec, kw, top_k=max(top_k * 2, 10))
    settings = get_settings()
    if settings.RERANK_ENABLED and fused:
        fused = _rerank(query, fused)
    return fused[:top_k]


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """带缓存的完整检索流程（M5）。"""
    cache = get_retrieval_cache()
    key = retrieval_cache_key(query, top_k)
    hit = cache.get(key)
    if hit is not None:
        return hit
    result = _retrieve_inner(query, top_k)
    cache.set(key, result)
    return result
