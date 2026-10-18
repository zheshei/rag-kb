"""问答组装与流式生成：把检索片段拼进 Prompt，交给 LLM 流式回答。"""
from app.services.llm import get_chat_llm

SYSTEM_PROMPT = (
    "你是电商平台商品问答助手。请依据下方【资料】回答用户关于商品的问题，"
    "不要编造资料中不存在的信息；直接、自然地给出答案，回答中不要出现"
    "『根据知识库』『引用』『依据资料』等说明性字样；"
    "如果资料不足以回答，请如实说明。回答使用简体中文，条理清晰。"
)


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    """组装对话消息：检索片段（带编号）作为资料，问题作为用户输入。"""
    context = "\n\n".join(f"[{i + 1}] {c['content']}" for i, c in enumerate(chunks))
    user = (
        f"【资料】\n{context}\n\n"
        f"【问题】\n{question}\n\n"
        "请回答问题。"
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
