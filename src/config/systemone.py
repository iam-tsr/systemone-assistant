import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Any

import httpx

load_dotenv()

@dataclass(frozen=True)
class SystemOneConfig:
    base_url: str
    api_key: str | None
    model: str


def systemone_config() -> SystemOneConfig:
    return SystemOneConfig(
        base_url=os.environ.get("JEV_BASE_URL").rstrip("/"),
        api_key=os.environ.get("JEV_API_KEY"),
        model=os.environ.get("JEV_MODEL"),
    )


def systemone_predict(
    state: str,
    questions: dict[str, Any],
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """POST one state and its questions to /v1/systemone.

    Returns the server payload: {"model", "answers", "usage", "routing"}. Raises
    httpx.HTTPStatusError on 4xx/5xx so callers see the server's own detail.
    """
    cfg = systemone_config()
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    response = httpx.post(
        f"{cfg.base_url}/v1/systemone",
        json={"state": state, "model": cfg.model, "questions": questions},
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()
