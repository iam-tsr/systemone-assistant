import asyncio
from uuid import uuid4

from .guardrails import guardrail
from .memory import chat, get_chat_history
from .entity_recognition import extract_entity, fast_entity_recon
from .tool_route import systemone_route, llm_route
from .tools.order_status import order_status
from .tools.cancel_order import cancel_order
from .tools.change_address import change_address
from .tools.escalate_to_human import escalate_to_human



ROUTE_CONFIDENCE = 0.85
ENTITY_PRECHECK_FLOOR = 0.5

# Actions systemone_route may decide on alone when confident.
SYSTEMONE_ACTIONS = {"order_status", "cancel_order", "change_address", "greeting"}
# Actions the llm_route fallback may return (escalate_to_human is only exposed here).
LLM_ACTIONS = SYSTEMONE_ACTIONS | {"escalate_to_human"}
# Actions that operate on an order and therefore need entity extraction.
ORDER_ACTIONS = {"order_status", "cancel_order", "change_address"}

thread_id = str(uuid4())


def handle_message(message: str) -> dict:
    guard = guardrail(message)
    if guard["risk_score"] == 1:
        # Blocked messages are not stored in memory.
        return {"reply": "I'm sorry, but I cannot assist with that request.", "action": "blocked"}

    conversation = [*get_chat_history(thread_id), {"HumanMessage": message}]

    action = _route(message)
    tool_result = _run_operation(action, message, conversation)

    reply_input = message if tool_result is None else f"{message}\n\nTOOL_RESULT: {tool_result}"
    reply = chat(thread_id, reply_input)

    return {"reply": reply, "action": action}


def _route(message: str) -> str:
    """Pick an action: systemone_route if confident, otherwise llm_route with escalation exposed."""
    decision = systemone_route(message)
    if decision["action"] in SYSTEMONE_ACTIONS and decision["action_confidence"] >= ROUTE_CONFIDENCE:
        return decision["action"]

    fallback = llm_route(message)["action"]
    return fallback if fallback in LLM_ACTIONS else "escalate_to_human"


def _run_operation(action: str, message: str, conversation: list[dict]) -> str | None:
    """Run the tool for the action. Returns the tool result, or None when no tool applies."""
    if action == "greeting":
        return None

    if action == "escalate_to_human":
        return _invoke(escalate_to_human, {"issue": {"message": message}})

    # Order actions: recon -> extract -> validate -> execute.
    entities = _extract_order_entities(conversation)
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


def _extract_order_entities(conversation: list[dict]) -> dict | None:
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
