from fastapi import Request
from pymongo.database import Database


def get_db(request: Request) -> Database:
    """Dependency: the Database owned by the app lifespan."""
    return request.app.state.db
