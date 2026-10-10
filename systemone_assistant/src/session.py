"""Per-customer short-term chat memory: a LangGraph thread checkpointed to MongoDB.

Each customer email is one LangGraph thread (`thread_id`), so turns are isolated per customer and
survive process restarts. The `messages` channel uses `add_messages`, so every turn is appended to
the stored history by the checkpointer.

Stored turns are the customer's raw message and the assistant's reply. The per-turn prompt (which
includes tool results) is passed in config for this call only and is not persisted.
"""
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.mongodb import MongoDBSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from .config import chat, llm_endpoint, get_client
from .prompt import REPLY_SYSTEM

CHECKPOINT_DB = "systemone"
REPLY_MAX_TOKENS = 300
REPLY_TEMPERATURE = 0.3


class _ChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def _to_openai(messages: list[BaseMessage]) -> list[dict[str, str]]:
    return [
        {"role": "user" if isinstance(m, HumanMessage) else "assistant", "content": str(m.content)}
        for m in messages
    ]


def _respond(state: _ChatState, config: RunnableConfig) -> dict[str, list[AnyMessage]]:
    # The last message is this turn's raw customer message; everything before it is history.
    history = state["messages"][:-1]
    turn_prompt = config["configurable"]["turn_prompt"]
    text = chat(
        llm_endpoint(),
        [
            {"role": "system", "content": REPLY_SYSTEM},
            *_to_openai(history),
            {"role": "user", "content": turn_prompt},
        ],
        temperature=REPLY_TEMPERATURE,
        max_tokens=REPLY_MAX_TOKENS,
    ).strip()
    return {"messages": [AIMessage(content=text)]}


def build_graph(checkpointer: MongoDBSaver) -> CompiledStateGraph:
    builder = StateGraph(_ChatState)
    builder.add_node("respond", _respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile(checkpointer=checkpointer)


_graph: CompiledStateGraph | None = None


def _get_graph() -> CompiledStateGraph:
    global _graph
    if _graph is None:
        _graph = build_graph(MongoDBSaver(get_client(), db_name=CHECKPOINT_DB))
    return _graph


def chat_turn(customer_email: str, message: str, turn_prompt: str) -> str:
    """Run one customer turn through the graph and return the assistant reply.

    `message` is stored as the human turn. `turn_prompt` is what the LLM sees for this turn
    (customer message plus tool result) and is not stored.
    """
    result = _get_graph().invoke(
        {"messages": [HumanMessage(content=message)]},
        {
            "configurable": {
                "thread_id": customer_email.strip().lower(),
                "turn_prompt": turn_prompt,
            }
        },
    )
    return str(result["messages"][-1].content)
