import json
from typing import Any

from .extract import extract_entities
from .guardrails import guardrail
from .config import chat, llm_endpoint
from .tools import TOOLS, escalate_to_human
from .router import _route


# Below this Laya answer confidence the route is not trusted; the message goes to a human.
ROUTE_CONFIDENCE_THRESHOLD = 0.6

_REFUSAL = "I can't help with that request. I'm happy to help with orders, shipping, or your account."

_REPLY_SYSTEM = """You are a customer support assistant for an online store.
Write a short, polite reply to the customer.
Use only facts from the TOOL_RESULT JSON. Do not invent order details, dates, or amounts.
If TOOL_RESULT has ok=false, explain the error and ask for whatever is missing.
If the request was escalated, tell the customer a human agent will follow up and give the ticket id."""



def _reply(message: str, action: str, tool_result: dict | None) -> str:
    payload = {"action": action, "tool_result": tool_result}
    return chat(
        llm_endpoint(),
        [
            {"role": "system", "content": _REPLY_SYSTEM},
            {
                "role": "user",
                "content": f"CUSTOMER_MESSAGE: {message}\n"
                           f"TOOL_RESULT: {json.dumps(payload, ensure_ascii=False)}",
            },
        ],
        temperature=0.3,
        max_tokens=300,
    ).strip()


def _missing(field: str) -> dict:
    return {"ok": False, "error": f"Missing {field}."}


def handle_message(message: str, customer_email: str) -> dict[str, Any]:
    """Handle one message from an authenticated customer.

    `customer_email` must come from the session, not from the message text. It is the only
    identity the tools trust.
    """
    guard = guardrail(message)
    if guard["safety_score"] == 1:
        return {"reply": _REFUSAL, "action": "blocked", "tool_result": None}

    route = _route(message)
    action = route["action"]
    department = route["department"]

    # Off-topic applies to everything except greetings, which the router labels as chitchat.
    if action != "chitchat" and guard["on_topic"] < 0.7:
        return {"reply": _REFUSAL, "action": "blocked", "tool_result": None}

    # Unsure routing goes to a human. Escalating is cheap; a wrong cancel is not.
    if route["action_confidence"] < ROUTE_CONFIDENCE_THRESHOLD:
        action = "escalate_to_human"

    if action in ("chitchat", "other"):
        return {"reply": _reply(message, action, None), "action": action, "tool_result": None}

    entities = extract_entities(message)

    if action == "escalate_to_human":
        tool_result = escalate_to_human(customer_email, department, entities["reason"] or message)
        return {"reply": _reply(message, action, tool_result), "action": action, "tool_result": tool_result}

    order_id = entities["order_id"]
    if order_id is None:
        tool_result = _missing("order number")
        return {"reply": _reply(message, action, tool_result), "action": action, "tool_result": tool_result}

    if action == "order_status":
        tool_result = TOOLS[action](order_id, customer_email)
    elif action == "cancel_order":
        tool_result = TOOLS[action](order_id, customer_email, entities["reason"])
    elif action == "change_address":
        if entities["new_address"] is None:
            tool_result = _missing("new shipping address")
        else:
            tool_result = TOOLS[action](order_id, customer_email, entities["new_address"])
    else:
        raise ValueError(f"no handler for action {action!r}")

    return {"reply": _reply(message, action, tool_result), "action": action, "tool_result": tool_result}
