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

    Authenticates with `JEV_API_KEY` as `Authorization: Bearer <key>`, which the model server
    requires; its `LAYA_API_KEY` must hold the same value.

    Returns the server payload: {"model", "answers", "usage", "routing"}. Raises
    httpx.HTTPStatusError on 4xx/5xx so callers see the server's own detail -- 401 when the key is
    wrong, 503 when the server has none configured or its checkpoints did not load.
    """
    response = httpx.post(
        f"{systemone_settings.base_url}/v1/systemone",
        json={"state": state, "model": systemone_settings.model, "questions": questions},
        headers={"Authorization": f"Bearer {systemone_settings.api_key}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()
