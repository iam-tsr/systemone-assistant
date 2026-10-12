from typing import Any

import httpx

from .settings import systemone_settings


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
    headers = {"Content-Type": "application/json"}
    if systemone_settings.api_key:
        headers["Authorization"] = f"Bearer {systemone_settings.api_key}"
    response = httpx.post(
        f"{systemone_settings.base_url}/v1/systemone",
        json={"state": state, "model": systemone_settings.model, "questions": questions},
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()
