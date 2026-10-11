import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain.chat_models import init_chat_model

load_dotenv()

model = init_chat_model(
    model="gpt-5.5",
    stream_usage=True
)

MONGODB_ATLAS_URI = os.environ["MONGO_URI"]
DATABASE_NAME = os.environ["MONGO_DB"]

with MongoDBSaver.from_conn_string(MONGODB_ATLAS_URI, DATABASE_NAME) as checkpointer:
    def call_model(state: MessagesState):
        response = model.invoke(state["messages"])
        return {"messages": response}
    
    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_edge(START, "call_model")

    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "1"}}
    checkpointer.delete_thread(config["configurable"]["thread_id"])
    stream = graph.invoke(
        {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
        config,
    )

    stream = graph.invoke(
        {"messages": [{"role": "user", "content": "what's my name?"}]},
        config,
    )

    print(stream["messages"][-1].content)

    snap = graph.get_state(config)
    for m in snap.values.get("messages", []):
        print("-", type(m).__name__, ":", m.content)