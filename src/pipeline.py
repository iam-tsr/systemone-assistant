import asyncio
from uuid import uuid4

from .guardrails import guardrail
from .memory import chat, get_chat_history
from .entity_recognition import extract_entity, fast_entity_recon
from .tool_route import systemone_route, slm_route
from .tools import (
    order_status, 
    cancel_order, 
    change_address, 
    escalate_to_human
)



ROUTE_CONFIDENCE = 0.85
ENTITY_PRECHECK_FLOOR = 0.5

thread_id = str(uuid4())


def handle_message(message: str) -> dict:
    guard = guardrail(message)
    if guard["risk_score"] == 1:
        # Blocked messages are not stored in memory.
        return {"reply": "I'm sorry, but I cannot assist with that request.", "action": "blocked"}

    if guard["churn_risk"] > 0.85:
        # High churn risk messages are routed to a human.
        action = "escalate_to_human"
        tool_result = _invoke(escalate_to_human, {"issue": {"message": message}})
        reply_input = f"{message}\n\nTOOL_RESULT: {tool_result}"
        reply = chat(thread_id, reply_input)
        return {"reply": reply, "action": action}

    conversation = get_chat_history(thread_id)

    action = _route(str(conversation))
    tool_result = _run_operation(action, message, conversation)

    reply_input = message if tool_result is None else f"{message}\n\nTOOL_RESULT: {tool_result}"
    reply = chat(thread_id, reply_input)

    return {"reply": reply, "action": action}



def _route(conversation: str) -> str:
    """Pick an action: systemone_route if confident, otherwise slm_route with escalation exposed."""
    decision = systemone_route(conversation)
    if decision["action_confidence"] >= ROUTE_CONFIDENCE:
        return decision["action"]

    fallback = slm_route(conversation)
    return fallback["action"]


def _run_operation(action: str, message: str, conversation: list[dict]) -> str | None:
    """Run the tool for the action. Returns the tool result, or None when no tool applies."""
    if action == "greeting":
        return None

    if action == "escalate_to_human":
        return _invoke(escalate_to_human, {"issue": {"message": message}})

    # Order actions: recon -> extract -> validate -> execute.
    entities = _extract_query_entities(conversation)
    order_id = entities.get("order_id") if entities else None
    if not order_id:
        return "Missing required information: order_id."

    if action == "order_status":
        return _invoke(order_status, {"orderid": order_id})
    if action == "cancel_order":
        return _invoke(cancel_order, {"orderid": order_id})

    # change_address
    new_address = entities.get("new_address")
    if not new_address:
        return "Missing required information: new_address."
    return _invoke(change_address, {"orderid": order_id, "new_address": new_address})


def _extract_query_entities(conversation: list[dict]) -> dict | None:
    """Cheap recon pre-check; the extractor decides. Recon scores are not reliable enough
    for a hard cutoff (real order IDs score ~0.76), so skip extraction only when recon is
    confidently negative."""
    recon = fast_entity_recon(conversation)
    if max(recon["order_id"], recon["new_address"]) < ENTITY_PRECHECK_FLOOR:
        return None
    return extract_entity(conversation)


def _invoke(tool, args: dict) -> str:
    try:
        return asyncio.run(tool.ainvoke(args))
    except Exception as e:
        return f"Tool {tool.name} failed: {e}"
