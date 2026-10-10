"""Shared MongoDB client for orders, escalations, and conversation checkpoints.

Read from the environment at call time:
  MONGO_URI   e.g. mongodb://user:pass@localhost:27017/?authSource=admin
  MONGO_DB    database name, default "systemone"
"""
import os

from pymongo import MongoClient
from pymongo.database import Database

_client: MongoClient | None = None


def get_db() -> Database:
    global _client
    if _client is None:
        _client = MongoClient(os.environ.get("MONGO_URI", "mongodb://root:tarun@localhost:27017"))
    return _client[os.environ.get("MONGO_DB", "systemone")]


def get_client() -> MongoClient:
    get_db()
    assert _client is not None
    return _client
