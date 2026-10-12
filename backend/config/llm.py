from langchain_openai import ChatOpenAI

from .settings import openai_settings


def client(
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> ChatOpenAI:
    return ChatOpenAI(
        model=model or openai_settings.model,
        base_url=base_url or openai_settings.base_url,
        api_key=api_key or openai_settings.api_key,
        max_completion_tokens=max_tokens,
        temperature=temperature,
    )
