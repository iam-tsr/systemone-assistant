from dotenv import load_dotenv

from src.config import client
from pydantic import BaseModel

load_dotenv()

def get_weather(location: str) -> None:
    """Get weather at a location."""
    return "It's sunny."


class OutputSchema(BaseModel):
    """Schema for response."""

    answer: str
    justification: str

llm = client()

structured_llm = llm.bind_tools(
    [get_weather],
    response_format=OutputSchema,
    strict=True,
)

if __name__ == "__main__":
    # Response contains tool calls:
    tool_call_response = structured_llm.invoke("What is the weather in SF?")

    # structured_response.additional_kwargs["parsed"] contains parsed output
    structured_response = structured_llm.invoke(
        "What weighs more, a pound of feathers or a pound of gold?"
    )
    print(tool_call_response)
    # print(structured_response)