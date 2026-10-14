from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

from ..config import mongodb_settings, cors_settings
from ..database import OrderMongoDBHandler, UserMongoDBHandler
from .routes import voice
from .routes import orders
from .routes import profile


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # tz_aware: datetimes come back with UTC tzinfo, so they serialize with +00:00.
    # Naive values would be read as local time by the browser.
    client = MongoClient(mongodb_settings.uri, tz_aware=True)
    # Fail fast at startup if Mongo is unreachable, not on the first request.
    client.admin.command("ping")
    app.state.mongo = client
    app.state.db = client[mongodb_settings.database]

    order_handler = OrderMongoDBHandler()
    user_handler = UserMongoDBHandler()
    app.state.order_handler = order_handler
    app.state.user_handler = user_handler

    try:
        order_handler.load_orders()
        user_handler.load_users()
        yield
    finally:
        order_handler.close_connection()
        user_handler.close_connection()
        client.close()


def create_app() -> FastAPI:
    app = FastAPI(title="SystemOne Assistant API", lifespan=lifespan)

    # The Next.js dev server calls the API from the browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_credentials=True,
        allow_headers=["*"], # allow all headers, only for dev server, not for production
    )

    app.include_router(profile.router, prefix="/api")
    app.include_router(orders.router, prefix="/api")
    app.include_router(voice.router, prefix="/api")
    return app