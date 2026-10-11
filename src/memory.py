import os
from dotenv import load_dotenv

from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.mongodb import MongoDBSaver

from .config import client

load_dotenv()


model = client()

MONGODB_ATLAS_URI = os.environ["MONGO_URI"]
DATABASE_NAME = os.environ["MONGO_DB"]

def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": response}

builder = StateGraph(MessagesState)
builder.add_node(call_model)
builder.add_edge(START, "call_model")


def chat(thread_id: int, messages: str) -> dict:
    """Invoke the model with the given messages and configuration, returning the model's response."""
    with MongoDBSaver.from_conn_string(MONGODB_ATLAS_URI, DATABASE_NAME) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)

        config = {"configurable": {"thread_id": thread_id}}

        stream = graph.invoke(
            {"messages": [{"role": "user", "content": messages}]},
            config,
        )
        return stream["messages"][-1].content


def get_chat_history(thread_id: int) -> list:
    """Retrieve the chat history for a given thread ID from the MongoDB database."""
    with MongoDBSaver.from_conn_string(MONGODB_ATLAS_URI, DATABASE_NAME) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        # Get the current state of the graph
        snap = graph.get_state(config)

        history = []
        for m in snap.values.get("messages", []):
            # print("-", type(m).__name__, ":", m.content)
            history.append(m.content)

        return history

def clear_chat_history(thread_id: int) -> None:
    """Clear the chat history for a given thread ID in the MongoDB database."""
    with MongoDBSaver.from_conn_string(MONGODB_ATLAS_URI, DATABASE_NAME) as checkpointer:
        config = {"configurable": {"thread_id": thread_id}}
        # Delete the thread from the database
        checkpointer.delete_thread(config)