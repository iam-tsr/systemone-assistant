from typing import Any
from .guardrails import r


ACTIONS = {
    "order_status": "Customer asks about the status, location, or delivery date of an order.",
    "cancel_order": "Customer asks to cancel an order.",
    "change_address": "Customer asks to change the shipping address of an order.",
    "escalate_to_human": "Request needs a human agent: refund disputes, complaints needing a decision, legal issues, or anything the tools above cannot do.",
    "chitchat": "Greeting, thanks, or small talk such as 'hi', 'hey', or 'thanks' with no request.",
    "other": "Customer service question that none of the other actions cover.",
}

DEPARTMENT_CRITERIA = {
    "billing": "invoices, payments, refunds",
    "technical": "bugs, outages, system errors",
    "sales": "pricing, new contracts",
    "other": "everything else",
}

def _route(message: str) -> dict[str, Any]:
    """Laya picks one action and one department in a single forward pass."""
    questions = {
        "action": {
            "type": "choice",
            "instructions": "Which action should handle this customer message?",
            "criteria": ACTIONS,
        },
        "department": {
            "type": "choice",
            "instructions": "Which department should handle this request?",
            "criteria": DEPARTMENT_CRITERIA,
        },
    }
    result = r.predict(message, questions)
    action = result["answers"]["action"]
    department = result["answers"]["department"]
    return {
        "action": action["choice"],
        "action_confidence": action["answer_confidence"],
        "department": department["choice"],
    }