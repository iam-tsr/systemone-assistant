from typing import Optional
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from .config import client


class EntityRecognition(BaseModel):
    """A Pydantic model for the structured response of the entity recognition."""
    order_id: Optional[int] = Field(
        default=None,
        description="The order ID associated with the person"
    )
    address: Optional[str] = Field(
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