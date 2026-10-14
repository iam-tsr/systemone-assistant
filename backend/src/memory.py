from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage

from .config import client, mongodb_settings
from .prompt import GEN_SYSTEM_PROMPT


model = client()

MONGODB_ATLAS_URI = mongodb_settings.uri
DATABASE_NAME = mongodb_settings.database

def call_model(state: MessagesState) -> dict:
    messages = [
        SystemMessage(content=GEN_SYSTEM_PROMPT),
        *state["messages"],
    ]
    response = model.invoke(messages)
    return {"messages": response}


builder = StateGraph(MessagesState)
builder.add_node(call_model)
builder.add_edge(START, "call_model")


def _thread_config(thread_id: int) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def chat(thread_id: int, message: str) -> str:
    """Send a user message on the given thread and return the model's reply text."""
    if not message or not message.strip():
        raise ValueError("chat message must be non-empty")
    
    messages = [
        HumanMessage(content=message),
    ]

    with MongoDBSaver.from_conn_string(MONGODB_ATLAS_URI, DATABASE_NAME) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        result = graph.invoke({"messages": messages}, _thread_config(thread_id))

    return result["messages"][-1].content


def get_chat_history(thread_id: int) -> list[dict[str, str]]:
    """Return the thread's messages, oldest first, as {message type name: content} dicts."""
    with MongoDBSaver.from_conn_string(MONGODB_ATLAS_URI, DATABASE_NAME) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        snapshot = graph.get_state(_thread_config(thread_id))

    messages = snapshot.values.get("messages", [])
    return [{type(m).__name__: m.content} for m in messages]


def clear_chat_history(thread_id: int) -> None:
    """Delete the thread's stored checkpoints from the MongoDB database."""
    with MongoDBSaver.from_conn_string(MONGODB_ATLAS_URI, DATABASE_NAME) as checkpointer:
        checkpointer.delete_thread(str(thread_id))
