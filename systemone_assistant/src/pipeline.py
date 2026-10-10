from typing import Any

from .extract import extract_entities
from .guardrails import guardrail
from .prompt import REFUSAL, reply_user_message
from .router import _route
from .session import chat_turn
from .tools import TOOLS, escalate_to_human


ROUTE_CONFIDENCE_THRESHOLD = 0.8
CHURN_THRESHOLD = 0.6


def _reply(customer_email: str, message: str, action: str, intent: str, tool_result: dict | None) -> str:
    # The stored turn is the raw customer message; the tool-augmented prompt is for this call only.
    return chat_turn(
        customer_email,
        message,
        reply_user_message(message, action, intent, tool_result),
    )


def handle_message(message: str, customer_email: str) -> dict[str, Any]:
    """Handle one message from an authenticated customer.

    `customer_email` must come from the session, not from the message text. It is the only
    identity the tools trust. Chat memory is keyed by the same email.
    """

    guard = guardrail(message)
    if guard["safety_score"] == 1:
        # Blocked messages are not stored in memory.
        return {"reply": REFUSAL, "action": "blocked", "tool_result": None}

    intent = guard["intent"]
    churn_risk = guard["churn_risk"]

    route = _route(message)
    action = route["action"]
    department = route["department"]
    entities = extract_entities(message)

    # High churn risk goes straight to a human, whatever the router picked.
    if churn_risk > CHURN_THRESHOLD:
        tool_result = escalate_to_human(customer_email, department, entities["reason"] or message)
        return {"reply": _reply(customer_email, message, "escalate_to_human", intent, tool_result),
                "action": "escalate_to_human", "tool_result": tool_result}

    # Unsure routing goes to a human. Escalating is cheap; a wrong cancel is not.
    if route["action_confidence"] <= ROUTE_CONFIDENCE_THRESHOLD and action == "escalate_to_human":
        return {"reply": _reply(customer_email, message, "chitchat", intent, None), "action": "chitchat", "tool_result": None}

    if action == "escalate_to_human":
        tool_result = escalate_to_human(customer_email, department, entities["reason"] or message)
        return {"reply": _reply(customer_email, message, action, intent, tool_result), "action": action, "tool_result": tool_result}

    order_id = entities["order_id"]
    if order_id is None:
        tool_result = _missing("order number")
        return {"reply": _reply(customer_email, message, action, intent, tool_result), "action": action, "tool_result": tool_result}

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

    return {"reply": _reply(customer_email, message, action, intent, tool_result), "action": action, "tool_result": tool_result}


def _missing(field: str) -> dict:
    return {"ok": False, "error": f"Missing {field}."}
