"""Per-customer chat memory. Older turns are summarized once the prompt nears the context limit.

Limits (all overridable by env):
  LLM_CONTEXT_TOKENS  context window; default 68352 (n_ctx reported by the LLM server)
  TRIGGER_RATIO       summarize when the full prompt would exceed this share of the window (0.7)
Token counts are estimates (len / CHARS_PER_TOKEN) because no tokenizer is available here.
"""
import math
import os
from dataclasses import dataclass, field
from typing import Literal

from .config import chat, llm_endpoint
from .prompt import SUMMARY_SYSTEM, summary_user_message


DEFAULT_CONTEXT_TOKENS = 68352
TRIGGER_RATIO = 0.7
CHARS_PER_TOKEN = 3  # conservative: English is usually about 4 characters per token
KEEP_RECENT = 4  # newest turns kept verbatim after a summarization
SUMMARY_MAX_TOKENS = 300


@dataclass
class Message:
    role: Literal["human", "ai"]
    content: str


@dataclass
class Session:
    messages: list[Message] = field(default_factory=list)
    summary: str = ""


_sessions: dict[str, Session] = {}


def get_session(customer_email: str) -> Session:
    return _sessions.setdefault(customer_email, Session())


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def trigger_tokens() -> int:
    return int(int(os.environ.get("LLM_CONTEXT_TOKENS", DEFAULT_CONTEXT_TOKENS)) * TRIGGER_RATIO)


def _summarize(prior_summary: str, turns: list[Message]) -> str:
    return chat(
        llm_endpoint(),
        [
            {"role": "system", "content": SUMMARY_SYSTEM},
            {"role": "user", "content": summary_user_message(prior_summary, [(m.role, m.content) for m in turns])},
        ],
        temperature=0.0,
        max_tokens=SUMMARY_MAX_TOKENS,
    ).strip()


def compact_if_needed(session: Session, reserved_tokens: int) -> None:
    """Summarize all but the newest KEEP_RECENT turns if the next prompt would exceed the trigger.

    `reserved_tokens` is everything else the next call sends: system prompt, current message,
    tool result, and the output budget.
    """
    used = (
        estimate_tokens(session.summary)
        + sum(estimate_tokens(m.content) for m in session.messages)
        + reserved_tokens
    )
    if used <= trigger_tokens() or len(session.messages) <= KEEP_RECENT:
        return
    old, session.messages = session.messages[:-KEEP_RECENT], session.messages[-KEEP_RECENT:]
    session.summary = _summarize(session.summary, old)
