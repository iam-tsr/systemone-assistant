from typing import Any, Literal
from pydantic import BaseModel, Field

from .config import systemone_predict, client


ACTIONS = {
    "order_status": "Customer asks about the status, location, or delivery date of an order.",
    "cancel_order": "Customer asks to cancel an order.",
    "change_address": "Customer asks to change the shipping address of an order.",
    "greeting": "Greeting, thanks, or small talk such as 'hi', 'hey', or 'thanks' with no request.",
    "other": "Everything else that doesn't fit into the other categories.",
}

def systemone_route(conversation: str) -> dict[str, Any]:
    """Laya picks one action and one department in a single forward pass."""
    questions = {
        "action": {
            "type": "choice",
            "instructions": "Which action should handle this customer message?",
            "criteria": ACTIONS,
        },
    }
    result = systemone_predict(conversation, questions)
    action = result["answers"]["action"]
    return {
        "action": action["choice"],
        "action_confidence": action["confidence"],
    }

# -------------------------------------------------------------------------------------

ActionType = Literal["order_status", "cancel_order", "change_address", "greeting", "other"]

class RouteDecision(BaseModel):
    """A fallback routing method to route the user's inquiry to the most relevant tool."""
    action: ActionType = Field(
        description=f"Classify the user input into exactly one of these actions"
    )
    action_confidence: float = Field(
        description="A confidence score between 0.0 and 1.0 indicating how confident the model is in its action choice."
    )

route_model = client().with_structured_output(RouteDecision)

def slm_route(conversation: str) -> dict[str, Any]:
    """Route the user's inquiry to the most relevant tool using a language model."""

    result = route_model.invoke(conversation)
    
    return result.model_dump()