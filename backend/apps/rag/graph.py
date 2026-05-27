"""LangGraph RAG pipeline: memory → embed → retrieve → aggregate → generate → cite → save."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any, TypedDict
from uuid import UUID

from django.conf import settings
from django.db import transaction
from langgraph.graph import END, START, StateGraph

from apps.chat.models import ChatMessage, ChatRole
from apps.projects.models import Project
from apps.rag.llm import generate_with_context, stream_generate_with_context
from apps.rag.retrieval import retrieve_chunks
from apps.rag.services.embeddings import embed_query

logger = logging.getLogger(__name__)


class RAGState(TypedDict, total=False):
    project_id: str
    user_id: int
    query: str
    chat_history: list[dict]
    query_embedding: list[float]
    retrieved_chunks: list[dict]
    selected_chunks: list[dict]
    context_text: str
    final_answer: str
    citations: list[dict]
    error: str
    assistant_message_id: str


def _load_memory(state: RAGState) -> dict:
    pid = state["project_id"]
    limit = settings.CHAT_HISTORY_LIMIT
    qs = ChatMessage.objects.filter(project_id=pid).order_by("-created_at")[:limit]
    msgs = list(reversed(list(qs)))
    history = [{"role": m.role, "content": m.content} for m in msgs]
    return {"chat_history": history}


def _embed_query(state: RAGState) -> dict:
    vec = embed_query(state["query"])
    return {"query_embedding": vec}


def _retrieve(state: RAGState) -> dict:
    chunks = retrieve_chunks(
        state["project_id"],
        state["query_embedding"],
        limit=settings.RETRIEVE_TOP_K,
    )
    return {"retrieved_chunks": chunks}

def _select_chunks(state: RAGState) -> dict:
    # No reranking: keep retrieval results as-is to reduce latency/cost.
    return {"selected_chunks": list(state.get("retrieved_chunks") or [])}


def _aggregate_multidoc(state: RAGState) -> dict:
    chunks = state.get("selected_chunks") or []
    by_doc: dict[str, list[dict]] = {}
    for c in chunks:
        did = c.get("document_id", "")
        by_doc.setdefault(did, []).append(c)
    blocks: list[str] = []
    for did, items in by_doc.items():
        name = items[0].get("document_name", "Unknown")
        lines = [f"### Document: {name} (id={did})"]
        for it in items:
            page = it.get("page_number")
            page_label = page if page is not None else "n/a"
            lines.append(f"--- Excerpt (page {page_label}) ---\n{it['content']}")
        blocks.append("\n".join(lines))
    context = "\n\n".join(blocks) if blocks else "(no retrieved context)"
    return {"context_text": context}


def _generate(state: RAGState) -> dict:
    if not settings.OPENAI_API_KEY:
        return {
            "error": "OPENAI_API_KEY is not configured",
            "final_answer": "The assistant is not configured (set OPENAI_API_KEY for the API container).",
        }
    try:
        answer = generate_with_context(
            context=state.get("context_text") or "",
            query=state["query"],
            chat_history=state.get("chat_history") or [],
        )
        return {"final_answer": answer}
    except Exception as exc:
        logger.exception("LLM generation failed")
        return {"error": str(exc), "final_answer": "The assistant could not generate an answer. Please try again later."}


def _build_citations(chunks: list[dict]) -> list[dict]:
    seen: set[tuple[str, str | int | None]] = set()
    out: list[dict] = []
    for c in chunks:
        name = c.get("document_name", "")
        page = c.get("page_number")
        key = (name, page)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "label": f"[{name} – Page {page}]" if page is not None else f"[{name} – n/a]",
                "document_name": name,
                "page_number": page,
                "chunk_id": c.get("chunk_id"),
            }
        )
    return out


def _format_citations(state: RAGState) -> dict:
    chunks = state.get("selected_chunks") or []
    return {"citations": _build_citations(chunks)}


def _save_memory(state: RAGState) -> dict:
    project = Project.objects.get(pk=state["project_id"])
    citations = state.get("citations") or []
    with transaction.atomic():
        ChatMessage.objects.create(
            project=project,
            role=ChatRole.USER,
            content=state["query"],
        )
        assistant = ChatMessage.objects.create(
            project=project,
            role=ChatRole.ASSISTANT,
            content=state.get("final_answer") or "",
            citations=citations,
        )
    return {"assistant_message_id": str(assistant.id)}


def build_graph():
    g = StateGraph(RAGState)
    g.add_node("load_memory", _load_memory)
    g.add_node("embed_query", _embed_query)
    g.add_node("retrieve", _retrieve)
    g.add_node("select", _select_chunks)
    g.add_node("aggregate", _aggregate_multidoc)
    g.add_node("generate", _generate)
    g.add_node("format_citations", _format_citations)
    g.add_node("save_memory", _save_memory)
    g.add_edge(START, "load_memory")
    g.add_edge("load_memory", "embed_query")
    g.add_edge("embed_query", "retrieve")
    g.add_edge("retrieve", "select")
    g.add_edge("select", "aggregate")
    g.add_edge("aggregate", "generate")
    g.add_edge("generate", "format_citations")
    g.add_edge("format_citations", "save_memory")
    g.add_edge("save_memory", END)
    return g.compile()


_compiled = None


def get_compiled_graph():
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled


def run_research_graph(*, project_id: str | UUID, user_id: int, query: str) -> dict:
    initial: RAGState = {
        "project_id": str(project_id),
        "user_id": user_id,
        "query": query.strip(),
    }
    graph = get_compiled_graph()
    final = graph.invoke(initial)
    return {
        "final_answer": final.get("final_answer", ""),
        "citations": final.get("citations", []),
        "assistant_message_id": final.get("assistant_message_id"),
        "error": final.get("error"),
    }


def _merge_state(state: RAGState, patch: dict) -> RAGState:
    merged: RAGState = dict(state)
    merged.update(patch)  # type: ignore[typeddict-item]
    return merged


def iter_research_graph_stream(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
) -> Iterator[dict[str, Any]]:
    """
    Run the RAG pipeline and yield structured events for SSE:
    - {"type": "status", "stage": "..."}
    - {"type": "token", "content": "..."}
    - {"type": "done", "answer", "citations", "message_id", "error"}
    """
    state: RAGState = {
        "project_id": str(project_id),
        "user_id": user_id,
        "query": query.strip(),
    }

    try:
        yield {"type": "status", "stage": "memory"}
        state = _merge_state(state, _load_memory(state))

        yield {"type": "status", "stage": "embed"}
        state = _merge_state(state, _embed_query(state))

        yield {"type": "status", "stage": "retrieve"}
        state = _merge_state(state, _retrieve(state))

        yield {"type": "status", "stage": "select"}
        state = _merge_state(state, _select_chunks(state))

        yield {"type": "status", "stage": "aggregate"}
        state = _merge_state(state, _aggregate_multidoc(state))

        yield {"type": "status", "stage": "generate"}
        if not settings.OPENAI_API_KEY:
            state = _merge_state(
                state,
                {
                    "error": "OPENAI_API_KEY is not configured",
                    "final_answer": "The assistant is not configured (set OPENAI_API_KEY for the API container).",
                },
            )
        else:
            parts: list[str] = []
            try:
                for delta in stream_generate_with_context(
                    context=state.get("context_text") or "",
                    query=state["query"],
                    chat_history=state.get("chat_history") or [],
                ):
                    parts.append(delta)
                    yield {"type": "token", "content": delta}
                state = _merge_state(state, {"final_answer": "".join(parts)})
            except Exception as exc:
                logger.exception("LLM streaming generation failed")
                state = _merge_state(
                    state,
                    {
                        "error": str(exc),
                        "final_answer": "The assistant could not generate an answer. Please try again later.",
                    },
                )

        state = _merge_state(state, _format_citations(state))

        yield {"type": "status", "stage": "save"}
        state = _merge_state(state, _save_memory(state))

        yield {
            "type": "done",
            "answer": state.get("final_answer", ""),
            "citations": state.get("citations", []),
            "message_id": state.get("assistant_message_id"),
            "error": state.get("error"),
        }
    except Exception as exc:
        logger.exception("RAG streaming pipeline failed")
        yield {"type": "error", "detail": str(exc)}
