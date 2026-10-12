from uuid import uuid4
from .guardrails import guardrail
from .memory import chat, get_chat_history, clear_chat_history

REFUSAL = "I'm sorry, but I cannot assist with that request."

thread_id = uuid4()

def handle_message(message: str):

    guard = guardrail(message)
    if guard["safety_score"] == 1:
        # Blocked messages are not stored in memory.
        return {"reply": REFUSAL, "action": "blocked"}

    response = chat(thread_id, message)

    return response

