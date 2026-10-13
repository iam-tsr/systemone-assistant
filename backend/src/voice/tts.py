from functools import lru_cache

from gnani.tts import GnaniTTSClient

from ..config import gnani_settings



TTS_MODEL = "timbre-v2.5"
ENGLISH_LANGUAGE = "en-IN"
DEFAULT_VOICE = "Kaveri"

ENGLISH_VOICES = frozenset({"Pranav", "Trupti", "Devika", "Pranav", "Shlok", "Girish"})


@lru_cache(maxsize=1)
def _client() -> GnaniTTSClient:
    return GnaniTTSClient(api_key=gnani_settings.api_key)


def synthesize(text: str) -> bytes:
    """Synthesize English text to WAV bytes with Gnani REST TTS.

    Callers must pass a voice from ENGLISH_VOICES. Raises
    gnani.tts.exceptions.GnaniTTSError subclasses on API failure.
    """
    return _client().synthesize(
        text,
        voice=DEFAULT_VOICE,
        model=TTS_MODEL,
        language=ENGLISH_LANGUAGE,
    )
