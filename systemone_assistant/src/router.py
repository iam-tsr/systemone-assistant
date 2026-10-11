from typing import Any
from .config.systemone import systemone_predict


ACTIONS = {
    "order_status": "Customer asks about the status, location, or delivery date of an order.",
    "cancel_order": "Customer asks to cancel an order.",
    "change_address": "Customer asks to change the shipping address of an order.",
    "greeting": "Greeting, thanks, or small talk such as 'hi', 'hey', or 'thanks' with no request.",
    "other": "Everything else that doesn't fit into the other categories.",
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
    result = systemone_predict(message, questions)
    action = result["answers"]["action"]
    department = result["answers"]["department"]
    print(f"Route: {action['choice']}, {department['choice']}, {action['confidence']:.2f}\n\n")
    return {
        "action": action["choice"],
        "action_confidence": action["confidence"],
        "department": department["choice"],
    }