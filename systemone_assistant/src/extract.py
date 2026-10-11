"""Entity extraction with the SLM (OpenAI-compatible). Returns only the fields the chosen action needs."""
from typing import Any

from .config import client
from .prompt import ENTITY_SYSTEM_PROMPT


def extract_entities(message: str) -> dict[str, Any]:
    pass