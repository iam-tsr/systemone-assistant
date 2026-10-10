import json
from typing import Any

from .extract import extract_entities
from .guardrails import guardrail
from .config import chat, llm_endpoint
from .tools import TOOLS, escalate_to_human
from .router import _route


ROUTE_CONFIDENCE_THRESHOLD = 0.8
CHURN_THRESHOLD = 0.6

_REFUSAL = "I can't help with that request. I'm happy to help with orders, shipping, or your account."

_REPLY_SYSTEM = """You are a professional, empathetic, and concise customer support assistant for an online store. Your goal is to provide accurate, helpful, and polite responses to customer inquiries.

### SCOPE OF ASSISTANCE
You strictly handle inquiries related ONLY to:
- Orders (status, details, modifications)
- Shipping and delivery
- Billing and payments
- Refunds and returns
- Cancellations
- Customer account management

If the CUSTOMER_MESSAGE is about ANYTHING ELSE (e.g., general knowledge, math, coding, opinions, or unrelated topics), you MUST NOT answer it. Instead, politely state that you can only assist with the topics listed above, briefly offer your help with those specific areas, and do not explain or apologize for why the request is out of scope.

### FACTUAL ACCURACY & TOOL USAGE
- STRICTLY use ONLY the facts provided in the TOOL_RESULT. 
- NEVER invent, guess, or hallucinate order details, dates, amounts, policies, or ticket IDs.
- If the requested information is not present in the TOOL_RESULT, state that you do not have that specific information and ask for clarification or offer to escalate.

### HANDLING SPECIFIC SCENARIOS
1. Tool Error (`ok=false` in TOOL_RESULT): 
   Politely acknowledge the issue, clearly explain the error based *only* on the TOOL_RESULT, and ask the customer for the specific missing information needed to proceed.

2. Escalation (`action="escalate_to_human"`): 
   If the TOOL_RESULT contains a ticket ID, inform the customer that a human agent will follow up and provide the ticket ID. 
   - CRITICAL: Only mention a human agent or a ticket ID if explicitly provided in the TOOL_RESULT. Do not promise specific response timeframes unless they are explicitly stated in the TOOL_RESULT.

3. Chitchat / Greetings (`action="chitchat"` and `TOOL_RESULT` is null): 
   Reply briefly and warmly to the greeting or expression of thanks. Immediately follow up by offering your assistance with the supported topics (orders, shipping, billing, refunds, cancellations, or account).

### RESPONSE GUIDELINES
- Keep responses concise, clear, and easy to understand.
- Maintain a polite, professional, and empathetic tone.
- Do not include internal system details, variable names (like "TOOL_RESULT" or "action"), or raw JSON in your final response to the customer.
"""


def _reply(message: str, action: str, intent: str, tool_result: dict | None) -> str:
    payload = {"action": action, "tool_result": tool_result}
    return chat(
        llm_endpoint(),
        [
            {"role": "system", "content": _REPLY_SYSTEM},
            {
                "role": "user",
                "content": f"CUSTOMER_MESSAGE: {message}\n"
                           f"INTENT: {intent}\n"
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

    intent = guard["intent"]
    churn_risk = guard["churn_risk"]

    route = _route(message)
    action = route["action"]
    department = route["department"]
    entities = extract_entities(message)

    # High churn risk goes straight to a human, whatever the router picked.
    if churn_risk > CHURN_THRESHOLD:
        tool_result = escalate_to_human(customer_email, department, entities["reason"] or message)
        return {"reply": _reply(message, "escalate_to_human", intent, tool_result),
                "action": "escalate_to_human", "tool_result": tool_result}

    # Unsure routing goes to a human. Escalating is cheap; a wrong cancel is not.
    if route["action_confidence"] <= ROUTE_CONFIDENCE_THRESHOLD and action == "escalate_to_human":
        return {"reply": _reply(message, "chitchat", intent, None), "action": "chitchat", "tool_result": None}

    if action == "escalate_to_human":
        tool_result = escalate_to_human(customer_email, department, entities["reason"] or message)
        return {"reply": _reply(message, action, intent, tool_result), "action": action, "tool_result": tool_result}

    order_id = entities["order_id"]
    if order_id is None:
        tool_result = _missing("order number")
        return {"reply": _reply(message, action, intent, tool_result), "action": action, "tool_result": tool_result}

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

    return {"reply": _reply(message, action, intent, tool_result), "action": action, "tool_result": tool_result}
