from functools import lru_cache
from typing import Any

from gnani.stt import GnaniSTTClient

from ..config import gnani_settings

ENGLISH_LANGUAGE = "en-IN"


@lru_cache(maxsize=1)
def _client() -> GnaniSTTClient:
    return GnaniSTTClient(api_key=gnani_settings.api_key)


def transcribe(audio: bytes, filename: str) -> dict[str, Any]:
    """Transcribe one English recording with Gnani REST STT.

    Returns the SDK response dict; the transcript is under "transcript".
    Raises gnani.stt.exceptions.GnaniSTTError subclasses on failure.
    """
    return _client().transcribe_bytes(
        audio,
        filename=filename,
        language_code=ENGLISH_LANGUAGE,
    )
