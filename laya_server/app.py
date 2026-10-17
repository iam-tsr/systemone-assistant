"""Laya typed decisions as a FastAPI service.

One forward pass per state returns typed `choice` / `score` / `noul` answers with calibrated
probabilities -- no generated text. `POST /v1/systemone` is the endpoint
`backend/src/config/systemone.py` calls: it takes a state and its questions and returns the
engine's own payload, `{"model", "answers", "usage", "routing"}`.
"""
import os
import threading
import traceback

# Must be set before `laya` pulls in the tokenizers.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from laya import Agent, Router

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_REPO = "convaiinnovations/laya"

# The Router's whole job is picking between these two by script detection. `typed-decisions` is
# deliberately absent: it is fine-tuned on four synthetic workflows and should not be a silent
# default. This mirrors the library's own DEFAULT_MODELS.
CHECKPOINTS = {"english": None, "multilingual": "multilingual"}

ROUTER = None
LOAD_ERROR = None

# One process owns one GPU. Concurrent requests would contend for VRAM and for the Router's loaded
# checkpoints, so forward passes are serialised.
GPU_LOCK = threading.Lock()


def _build():
    """Build both checkpoints once and hand them to the Router.

    `attach` registers an already-built Agent instead of letting the Router load a second copy,
    so the same weights are not held twice.
    """
    router = Router(device=DEVICE, max_loaded=2)
    for name, subfolder in CHECKPOINTS.items():
        router.attach(name, Agent(MODEL_REPO, subfolder=subfolder, device=DEVICE))
    return router


try:
    ROUTER = _build()
except Exception:
    LOAD_ERROR = traceback.format_exc()


class SystemOneRequest(BaseModel):
    """One decision request.

    `state` is what to decide on: text, a JSON document, or a list of conversation turns. Question
    instructions name the field they read (`prompt`, `message`, ...), so send a mapping such as
    `{"prompt": "..."}` when the questions reference a field by name.

    `questions` maps a question id to its definition -- `choice` (with `criteria`), `score` (with
    `criteria`) or `noul`, each with `instructions`.

    `model` optionally pins a checkpoint by name -- `english` or `multilingual` -- instead of
    letting the Router choose one by script detection. Anything else (a product name like
    `laya-latest`, or null) is ignored and the Router decides, so a caller written against a
    hosted API can keep sending its own model name unchanged.
    """

    state: str | dict | list
    questions: dict
    model: str | None = None


app = FastAPI(title="Laya", description="Typed System 1 decisions in a single forward pass.")


@app.get("/health")
def health() -> dict:
    """Liveness and readiness for a reverse proxy or a container healthcheck.

    Cheap and GPU-free: it reports whether the checkpoints loaded, which is the only thing that
    can be broken while the port is still accepting connections. Because `app.py` builds the
    checkpoints at import, uvicorn does not bind until they are either loaded or known to have
    failed -- so reaching this route at all means the server finished starting.
    """
    if ROUTER is None:
        raise HTTPException(503, "The checkpoints failed to load. See the server logs.")
    return {"status": "ok", "device": DEVICE}


@app.post("/v1/systemone")
def systemone(request: SystemOneRequest) -> dict:
    """Route, then answer every question in one forward pass on the chosen checkpoint.

    The response is the engine's payload verbatim: `model` (the checkpoint that answered),
    `answers` (one entry per question id), `usage` (token counts) and `routing` (why that
    checkpoint was chosen).
    """
    if ROUTER is None:
        raise HTTPException(503, "The checkpoints failed to load. See the server logs.\n\n%s"
                            % LOAD_ERROR)
    if not request.questions:
        raise HTTPException(400, "Questions must be a non-empty object of question_id -> definition.")
    # Only a name this server actually hosts is a pin. `model` is a free-form field in the caller's
    # config (JEV_MODEL), routinely set to a product name the Router has never heard of; passing
    # that through would raise on every request, so anything unrecognised falls back to routing.
    model = request.model if request.model in CHECKPOINTS else None
    try:
        with GPU_LOCK:
            return ROUTER.predict(request.state, request.questions, model=model)
    except ValueError as exc:
        # A malformed question definition: the caller's problem, and the library's message says why.
        raise HTTPException(400, str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))