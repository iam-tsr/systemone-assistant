import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Any

import httpx

load_dotenv()

@dataclass(frozen=True)
class Endpoint:
    base_url: str
    api_key: str
    model: str


def slm_endpoint() -> Endpoint:
    return Endpoint(
        base_url=os.environ.get("SLM_BASE_URL").rstrip("/"),
        api_key=os.environ.get("SLM_API_KEY"),
        model=os.environ.get("SLM_MODEL"),
    )


def llm_endpoint() -> Endpoint:
    return Endpoint(
        base_url=os.environ.get("LLM_BASE_URL").rstrip("/"),
        api_key=os.environ.get("LLM_API_KEY"),
        model=os.environ.get("LLM_MODEL"),
    )


def chat(
    endpoint: Endpoint,
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    max_tokens: int = 512,
    json_mode: bool = False,
    timeout: float = 60.0,
) -> str:
    payload: dict[str, Any] = {
        "model": endpoint.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    response = httpx.post(
        f"{endpoint.base_url}/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {endpoint.api_key}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
