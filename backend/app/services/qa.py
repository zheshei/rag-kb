"""问答组装与流式生成：把检索片段拼进 Prompt，交给 LLM 流式回答。"""
from app.services.llm import get_chat_llm

SYSTEM_PROMPT = (
    "你是电商平台商品知识库问答助手。请严格基于【知识库内容】回答问题，"
    "不要编造知识库中不存在的信息；回答中引用对应片段时用 [编号] 标注（如 [1]、[2]）。"
    "如果知识库内容不足以回答，请如实说明。回答使用简体中文，条理清晰。"
)


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    """组装带编号引用的对话消息。"""
    context = "\n\n".join(f"[{i + 1}] {c['content']}" for i, c in enumerate(chunks))
    user = (
        f"【知识库内容】\n{context}\n\n"
        f"【问题】\n{question}\n\n"
        "请结合知识库内容回答问题，并在引用处标注对应编号。"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


async def stream_answer(question: str, chunks: list[dict]):
    """异步流式生成回答，逐段产出文本。"""
    llm = get_chat_llm()
    messages = build_messages(question, chunks)
    async for chunk in llm.astream(messages):
        text = getattr(chunk, "content", "") or ""
        if text:
            yield text
