import logging
from pathlib import Path
from urllib.parse import quote

import httpx
from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from pymongo.errors import PyMongoError

from gnani.stt.exceptions import APIError as STTAPIError, GnaniSTTError, InvalidAudioError
from gnani.tts.exceptions import APIError as TTSAPIError, GnaniTTSError

from ...pipeline import handle_message
from ...voice import synthesize, transcribe

logger = logging.getLogger(__name__)
router = APIRouter()

# Extensions the Gnani REST STT endpoint accepts.
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}


def _read_audio(file: UploadFile) -> tuple[bytes, str]:
    filename = file.filename or "audio.wav"
    if Path(filename).suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported audio type")
    audio = file.file.read()
    if not audio:
        raise HTTPException(status_code=400, detail="Audio file is empty")
    return audio, filename


def _transcribe_or_raise(audio: bytes, filename: str) -> str:
    try:
        return transcribe(audio, filename=filename)["transcript"]
    except InvalidAudioError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except STTAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Gnani STT returned {exc.status_code}") from exc
    except GnaniSTTError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _synthesize_or_raise(text: str) -> bytes:
    try:
        return synthesize(text)
    except TTSAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Gnani TTS returned {exc.status_code}") from exc
    except GnaniTTSError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _handle_message_or_raise(session_id: str, transcript: str) -> dict:
    """Run the pipeline. Dependency failures become 503 so the UI can say what is down."""
    try:
        return handle_message(session_id, transcript)
    except httpx.ConnectError as exc:
        logger.error("SystemOne model server unreachable: %s", exc)
        raise HTTPException(status_code=503, detail="SystemOne model server is not reachable") from exc
    except httpx.HTTPStatusError as exc:
        logger.error("SystemOne model server error: %s", exc)
        raise HTTPException(status_code=502, detail=f"SystemOne model server returned {exc.response.status_code}") from exc
    except PyMongoError as exc:
        logger.error("MongoDB unavailable during pipeline: %s", exc)
        raise HTTPException(status_code=503, detail="MongoDB is not reachable") from exc


@router.post("/voice/agent/{session_id}", response_class=Response, responses={200: {"content": {"audio/wav": {}}}})
def voice_agent(session_id: str, file: UploadFile = File(...)) -> Response:
    """One voice turn: user audio -> STT -> pipeline.handle_message -> TTS reply audio.

    Transcript, reply, and action come back in response headers, percent-encoded
    (UTF-8) because HTTP header values must be ASCII. Decode with decodeURIComponent.
    """
    audio, filename = _read_audio(file)
    transcript = _transcribe_or_raise(audio, filename)
    if not transcript.strip():
        raise HTTPException(status_code=422, detail="No speech detected")

    result = _handle_message_or_raise(session_id, transcript)
    reply_audio = _synthesize_or_raise(result["reply"])

    return Response(
        content=reply_audio,
        media_type="audio/wav",
        headers={
            "X-Transcript": quote(transcript),
            "X-Reply": quote(result["reply"]),
            "X-Action": quote(result["action"]),
        },
    )


@router.get("/health")
def health_check() -> dict:
    """Health check endpoint for the voice API."""
    return {"status": "ok"}