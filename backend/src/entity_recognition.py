from typing import Optional, List
from pydantic import BaseModel, Field

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from .config import client, systemone_predict


class OrderEntity(BaseModel):
    order_id: Optional[int] = Field(
        default=None,
        description="The order ID mentioned in the conversation."
    )
    new_address: Optional[str] = Field(
        default=None,
        description="The new street/city address associated with that order, if mentioned."
    )
    postal_code: Optional[int] = Field(
        default=None,
        description="The postal/zip code associated with the address, converted to an integer."
    )


class EntityRecognition(BaseModel):
    orders: List[OrderEntity] = Field(
        default_factory=list,
        description="All orders mentioned in the conversation, with associated address information if available."
    )

agent = create_agent(
    model=client(),
    response_format=ToolStrategy(
        schema=EntityRecognition,
        tool_message_content="Extract all order entities from the conversation."
    )
)

def extract_entity(conversation: list[dict]) -> EntityRecognition:
    transcript = _conversation_to_text(conversation)

    prompt = f"""
        You are an expert data extraction AI. Your task is to extract order IDs, new addresses, and postal codes from a customer service transcript.

        ### EXTRACTION RULES:
        1. **Identify Orders:** Extract every distinct order mentioned. Group all information under a single object per unique `order_id`.
        2. **Address Linking:** 
        - Only extract a `new_address` or `postal_code` if the transcript *explicitly* links it to that specific `order_id`.
        - If an address/zip is mentioned but not linked to an order, ignore it.
        3. **Data Normalization (Crucial for Transcripts):**
        - **Order IDs:** Convert spelled-out or phonetic numbers into standard digits (e.g., "one zero zero zero one" -> 10001). If the ID contains letters, format them as uppercase without spaces (e.g., "order a b c one two three" -> "ABC123").
        - **Postal/Zip Codes:** Extract the postal or zip code and convert it strictly into an integer (e.g., "double one double zero five eight" -> 110058). Ensure this is placed in the `postal_code` field. Convert double x2, triple x3, and quadruple x4 to repeated digits (e.g., "double one" -> 11, "triple zero" -> 000, "quadruple zero" -> 0000).

        ### TRANSCRIPT:
        {transcript}
    """.strip()

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    )

    output = EntityRecognition.model_validate(response["structured_response"])
    return _clean_order_entities(output.orders)

def _conversation_to_text(conversation: list[dict]) -> str:
    """Convert your custom conversation format into a plain text transcript."""
    lines = []

    for turn in conversation:
        if not isinstance(turn, dict):
            continue

        human_message = turn.get("HumanMessage")
        ai_message = turn.get("AIMessage")

        if human_message:
            lines.append(f"HumanMessage: {human_message}")

        if ai_message:
            lines.append(f"AIMessage: {ai_message}")

    return "\n".join(lines)

def _clean_order_entities(orders: List[OrderEntity]) -> Optional[OrderEntity]:
    """
    Clean extracted order entities.
    """
    if not orders:
        return None

    # Remove None values just in case
    valid_orders = [order for order in orders if order is not None]
    if not valid_orders:
        return None

    first = valid_orders[0]
    last = valid_orders[-1]

    cleaned_order_id = (
        last.order_id
        if last.order_id is not None
        else first.order_id
    )

    cleaned_new_address = (
        last.new_address
        if last.new_address not in (None, "")
        else first.new_address
    )
    
    cleaned_postal_code = (
        last.postal_code
        if last.postal_code is not None
        else first.postal_code
    )

    address_parts = [cleaned_new_address] if cleaned_new_address else []
    if cleaned_postal_code is not None:
        address_parts.append(str(cleaned_postal_code))

    return {
        "order_id": cleaned_order_id,
        "new_address": " ".join(address_parts),
    }

# ------------------------------------------------------------------------

def fast_entity_recon(state: list) -> dict:
    """Extract contact information from the given state."""
    questions = {
        "order_id_score": {"type": "noul", "instructions": "Does this message contain an order ID?"},

        "new_address_score": {"type": "noul", "instructions": "Does this message contain a address?"},
    }

    state = _conversation_to_text(state)
    result = systemone_predict(state, questions)
    order_id_score = result["answers"]["order_id_score"]["noul"]
    new_address_score = result["answers"]["new_address_score"]["noul"]

    return {
        "order_id": order_id_score,
        "new_address": new_address_score,
    }