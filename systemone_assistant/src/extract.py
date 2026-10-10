"""Entity extraction with the SLM (OpenAI-compatible). Returns only the fields the chosen action needs."""
import re
import json
from typing import Any

from .config import chat, slm_endpoint

ORDER_ID_RE = re.compile(r"^\d{6,12}$")

_SYSTEM = """You extract entities from a customer support message.
Reply with a single JSON object with exactly these keys:
  "order_id": the order number as a string of digits, or null if none is stated.
  "new_address": the full new shipping address the customer wants, or null if none is stated.
  "reason": a short reason for cancelling or escalating, or null.
Only use text that appears in the message. Never invent values."""


def extract_entities(message: str) -> dict[str, Any]:
    reply = chat(
        slm_endpoint(),
        [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": message},
        ],
        temperature=0.0,
        max_tokens=200,
        json_mode=True,
    )
    raw = parse_json_object(reply)
    order_id = raw.get("order_id")
    # Accept only a plain digit string; anything else is treated as missing so the tool is never
    # called with a value the SLM invented.
    if not (isinstance(order_id, str) and ORDER_ID_RE.match(order_id)):
        order_id = None
    new_address = raw.get("new_address")
    reason = raw.get("reason")
    return {
        "order_id": order_id,
        "new_address": new_address.strip() if isinstance(new_address, str) and new_address.strip() else None,
        "reason": reason.strip() if isinstance(reason, str) and reason.strip() else None,
    }


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse the first JSON object in a model reply, tolerating code fences and prose."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in model output: {text!r}")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object, got {type(value).__name__}")
    return value