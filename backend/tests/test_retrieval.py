"""retrieval 单元测试：RRF 融合纯函数 + 真实检索召回（隔离 Chroma）。"""
import pytest

from app.services import retrieval, vectorstore as vs


def _clear_collection():
    col = vs.get_collection()
    ids = col.get()["ids"]
    if ids:
        col.delete(ids=ids)


@pytest.fixture()
def seeded_collection():
    """向隔离的 Chroma 注入三条测试分块。"""
    _clear_collection()
    vs.add_chunks(
        vs.get_collection(),
        ids=["r1", "r2", "r3"],
        documents=[
            "无线蓝牙耳机支持主动降噪，单次续航 8 小时",
            "智能手表支持 100 种运动模式，内置心率监测",
            "充电宝 20000mAh，符合民航规定可带上飞机",
        ],
        embeddings=[[0.1] * 512, [0.2] * 512, [0.3] * 512],
        metadatas=[{"document_id": 1, "filename": "t.txt"}] * 3,
    )
    yield
    _clear_collection()


class TestRrfFusion:
    def test_two_way_hit_ranks_first(self):
        vec = [{"content": "a", "metadata": {}, "score": 1.0}, {"content": "b", "metadata": {}, "score": 0.5}]
        kw = [{"content": "b", "metadata": {}, "score": 2.0}, {"content": "c", "metadata": {}, "score": 1.0}]
        fused = retrieval.rrf_fusion(vec, kw, top_k=3)
        assert fused[0]["content"] == "b"
        assert {f["content"] for f in fused} == {"a", "b", "c"}

    def test_empty_inputs(self):
        assert retrieval.rrf_fusion([], [], top_k=5) == []

    def test_dedup_by_content(self):
        vec = [{"content": "x", "metadata": {}, "score": 1.0}, {"content": "x", "metadata": {}, "score": 0.9}]
        kw = [{"content": "x", "metadata": {}, "score": 0.8}]
        fused = retrieval.rrf_fusion(vec, kw, top_k=5)
        assert len(fused) == 1


class TestRetrieve:
    def test_relevant_query_finds_chunk(self, seeded_collection):
        res = retrieval.retrieve("蓝牙耳机续航多长时间", top_k=2)
        assert res
        assert "耳机" in res[0]["content"]

    def test_top_k_respected(self, seeded_collection):
        res = retrieval.retrieve("商品 耳机 手表 充电宝", top_k=2)
        assert len(res) <= 2

    def test_empty_kb_returns_empty(self):
        _clear_collection()
        assert retrieval.retrieve("随便问问") == []
