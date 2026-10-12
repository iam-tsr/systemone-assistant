from typing import Optional
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from .config import client, systemone_predict


class EntityRecognition(BaseModel):
    """A Pydantic model for the structured response of the entity recognition."""
    order_id: int = Field(
        default=None,
        description="The order ID associated with the person"
    )
    new_address: Optional[str] = Field(
        default=None,
        description="The address of the person"
    )

agent = create_agent(
    model=client(),
    response_format=ToolStrategy(
        schema=EntityRecognition,
        tool_message_content="Entity recognized and extracted successfully!"
    )
)

def extract_entity(text: str) -> EntityRecognition:
    """Extract contact information from the given text."""
    response = agent.invoke({
        "messages": [{"role": "user", "content": text}]
    })
    return dict(response['structured_response'])


# ------------------------------------------------------------------------

def fast_entity_recon(state: list) -> dict:
    """Extract contact information from the given state."""
    questions = {
        "order_id": {"type": "noul", "instructions": "Does this message contain an order ID?"},

        "new_address": {"type": "noul", "instructions": "Does this message contain a address?"},
    }

    result = systemone_predict(str(state), questions)
    order_id = result["answers"]["order_id"]["noul"]
    new_address = result["answers"]["new_address"]["noul"]

    return {
        "order_id": order_id,
        "new_address": new_address,
    }