"""LLM 工厂：按配置返回 OpenAI 兼容的 ChatOpenAI 实例（智谱 GLM / Ollama 等）。"""
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import get_settings


@lru_cache
def get_chat_llm() -> ChatOpenAI:
    """返回全局共享的 LLM 实例。智谱 GLM 走 OpenAI 兼容端点，可平滑切换其他家。"""
    settings = get_settings()
    common = {"temperature": 0.3, "streaming": True, "timeout": 60}
    if settings.LLM_PROVIDER == "ollama":
        return ChatOpenAI(
            model=settings.OLLAMA_MODEL,
            api_key="ollama",  # 本地服务任意占位
            base_url=settings.OLLAMA_BASE_URL,
            **common,
        )
    # 默认智谱（OpenAI 兼容）
    return ChatOpenAI(
        model=settings.ZHIPU_MODEL,
        api_key=settings.ZHIPU_API_KEY,
        base_url=settings.ZHIPU_BASE_URL,
        **common,
    )
