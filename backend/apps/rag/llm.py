import logging
from collections.abc import Iterator
from typing import Any

from django.conf import settings
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


def _build_messages(*, context: str, query: str, chat_history: list[dict]) -> list:
    from apps.rag.prompts import SYSTEM_PROMPT

    system = SYSTEM_PROMPT.format(context=context)
    messages: list = [SystemMessage(content=system)]
    for turn in chat_history:
        role = turn.get("role")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=query))
    return messages


def _chat_llm(*, streaming: bool = False) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_CHAT_MODEL,
        temperature=0,
        api_key=settings.OPENAI_API_KEY,
        streaming=streaming,
    )


def _chunk_text(chunk: Any) -> str:
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return ""


def generate_with_context(
    *,
    context: str,
    query: str,
    chat_history: list[dict],
) -> str:
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    llm = _chat_llm(streaming=False)
    messages = _build_messages(context=context, query=query, chat_history=chat_history)
    result = llm.invoke(messages)
    return result.content


def stream_generate_with_context(
    *,
    context: str,
    query: str,
    chat_history: list[dict],
) -> Iterator[str]:
    """Yield answer text deltas from the chat model."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    llm = _chat_llm(streaming=True)
    messages = _build_messages(context=context, query=query, chat_history=chat_history)
    for chunk in llm.stream(messages):
        text = _chunk_text(chunk)
        if text:
            yield text
