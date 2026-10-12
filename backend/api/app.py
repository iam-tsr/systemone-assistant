from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

from ..config import mongodb_settings
from .routes import orders, profile, voice


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # tz_aware: datetimes come back with UTC tzinfo, so they serialize with +00:00.
    # Naive values would be read as local time by the browser.
    client = MongoClient(mongodb_settings.uri, tz_aware=True)
    # Fail fast at startup if Mongo is unreachable, not on the first request.
    client.admin.command("ping")
    app.state.mongo = client
    app.state.db = client[mongodb_settings.database]
    try:
        yield
    finally:
        client.close()


def create_app(allowed_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(title="SystemOne Assistant API", lifespan=lifespan)

    # The Next.js dev server calls the API from the browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["http://localhost:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app.include_router(profile.router, prefix="/api")
    app.include_router(orders.router, prefix="/api")
    app.include_router(voice.router, prefix="/api")
    return app


app = create_app()
