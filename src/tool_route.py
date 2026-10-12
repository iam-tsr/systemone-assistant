from typing import Any, ClassVar
from .config import systemone_predict


ACTIONS = {
    "order_status": "Customer asks about the status, location, or delivery date of an order.",
    "cancel_order": "Customer asks to cancel an order.",
    "change_address": "Customer asks to change the shipping address of an order.",
    "greeting": "Greeting, thanks, or small talk such as 'hi', 'hey', or 'thanks' with no request.",
    "other": "Everything else that doesn't fit into the other categories.",
}

def systemone_route(message: str) -> dict[str, Any]:
    """Laya picks one action and one department in a single forward pass."""
    questions = {
        "action": {
            "type": "choice",
            "instructions": "Which action should handle this customer message?",
            "criteria": ACTIONS,
        },
    }
    result = systemone_predict(message, questions)
    action = result["answers"]["action"]
    return {
        "action": action["choice"],
        "action_confidence": action["confidence"],
    }

# -------------------------------------------------------------------------------------

from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from .config import client

class RouteDecision(BaseModel):
    """A fallback routing method to route the user's inquiry to the most relevant tool."""
    keys: ClassVar[list[str]] = ['order_status', 'cancel_order', 'change_address', 'greeting', 'escalate_to_human']
    action: str = Field(
        description=f"Must be exactly one of: {keys}"
    )
    action_confidence: float = Field(
        description="A confidence score between 0 and 1 indicating how confident the model is in its action choice."
    )

def llm_route(message: str) -> dict[str, Any]:
    """Route the user's inquiry to the most relevant tool using a language model."""

    agent = create_agent(
        model=client(),
        response_format=ToolStrategy(
            schema=RouteDecision,
            tool_message_content="You are a intent routing engine. Classify the user input strictly into one of the allowed destinations.",
        )
    )        

    result = agent.invoke({"messages": [{"role": "user", "content": message}]})
    return dict(result['structured_response'])