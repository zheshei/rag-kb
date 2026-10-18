"""qa 组装测试：Prompt 含上下文、编号与问题。"""
from app.services.qa import build_messages


class TestBuildMessages:
    def test_messages_contain_system_and_user(self):
        chunks = [{"content": "蓝牙耳机续航 8 小时", "metadata": {}}, {"content": "手表支持心率监测", "metadata": {}}]
        msgs = build_messages("耳机续航多久", chunks)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    def test_context_with_indexes_and_question(self):
        chunks = [{"content": "A 内容", "metadata": {}}, {"content": "B 内容", "metadata": {}}]
        user = build_messages("测试问题", chunks)[1]["content"]
        assert "[1]" in user and "[2]" in user
        assert "A 内容" in user and "B 内容" in user
        assert "测试问题" in user

    def test_single_chunk(self):
        chunks = [{"content": "唯一内容", "metadata": {}}]
        user = build_messages("Q", chunks)[1]["content"]
        assert "[1]" in user
