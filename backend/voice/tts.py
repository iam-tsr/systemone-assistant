from functools import lru_cache

from gnani.tts import GnaniTTSClient

from ..config import gnani_settings

# The SDK default (timbre-v2.0) is no longer served; every call must name the model.
TTS_MODEL = "timbre-v2.5"
ENGLISH_LANGUAGE = "en-IN"
DEFAULT_VOICE = "Pranav"
# English voices on timbre-v2.5, from the Gnani TTS docs (en-IN row).
ENGLISH_VOICES = frozenset({"Kaveri", "Trupti", "Devika", "Pranav", "Shlok", "Girish"})


@lru_cache(maxsize=1)
def _client() -> GnaniTTSClient:
    return GnaniTTSClient(api_key=gnani_settings.api_key)


def synthesize(text: str, voice: str) -> bytes:
    """Synthesize English text to WAV bytes with Gnani REST TTS.

    Callers must pass a voice from ENGLISH_VOICES. Raises
    gnani.tts.exceptions.GnaniTTSError subclasses on API failure.
    """
    return _client().synthesize(
        text,
        voice=voice,
        model=TTS_MODEL,
        language=ENGLISH_LANGUAGE,
    )
