"""LangGraph RAG pipeline: memory → embed → retrieve → aggregate → generate → cite → save."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any, TypedDict
from uuid import UUID

from django.conf import settings
from django.db import transaction
from langgraph.graph import END, START, StateGraph

from apps.chat.models import ChatMessage, ChatRole
from apps.projects.models import Project
from apps.rag.config import (
    chat_history_limit_for_mode,
    chat_model_for_mode,
    normalize_mode,
    retrieve_top_k_for_mode,
)
from apps.rag.llm import generate_with_context, stream_generate_with_context
from apps.rag.retrieval import retrieve_chunks
from apps.rag.services.embeddings import embed_query

logger = logging.getLogger(__name__)


class RAGState(TypedDict, total=False):
    project_id: str
    user_id: int
    query: str
    mode: str
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
    mode = normalize_mode(state.get("mode"))
    limit = chat_history_limit_for_mode(mode)
    qs = ChatMessage.objects.filter(project_id=pid).order_by("-created_at")[:limit]
    msgs = list(reversed(list(qs)))
    history = [{"role": m.role, "content": m.content} for m in msgs]
    return {"chat_history": history}


def _embed_query(state: RAGState) -> dict:
    from apps.rag.query_enhance import enhance_query_for_retrieval

    vec = embed_query(enhance_query_for_retrieval(state["query"]))
    return {"query_embedding": vec}


def _retrieve(state: RAGState) -> dict:
    mode = normalize_mode(state.get("mode"))
    k = retrieve_top_k_for_mode(mode)
    chunks = retrieve_chunks(
        state["project_id"],
        state["query_embedding"],
        limit=k,
        query=state.get("query"),
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
            model=chat_model_for_mode(state.get("mode")),
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


def _is_not_found_answer(answer: str) -> bool:
    normalized = " ".join(answer.strip().lower().split())
    return "not found in the provided documents" in normalized


def _format_citations(state: RAGState) -> dict:
    answer = (state.get("final_answer") or "").strip()
    chunks = state.get("selected_chunks") or []
    if not chunks or _is_not_found_answer(answer):
        return {"citations": []}
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


def run_research_graph(*, project_id: str | UUID, user_id: int, query: str, mode: str = "fast") -> dict:
    initial: RAGState = {
        "project_id": str(project_id),
        "user_id": user_id,
        "query": query.strip(),
        "mode": normalize_mode(mode),
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
    mode: str = "fast",
) -> Iterator[dict[str, Any]]:
    """
    Run the RAG pipeline and yield structured events for SSE:
    - {"type": "status", "stage": "...", "message": "..."}
    - {"type": "token", "content": "..."}
    - {"type": "done", "answer", "citations", "message_id", "latency_ms", "error"}
    """
    state: RAGState = {
        "project_id": str(project_id),
        "user_id": user_id,
        "query": query.strip(),
        "mode": normalize_mode(mode),
    }
    started = time.perf_counter()
    ttft_ms: float | None = None
    pregenerate_ms: float | None = None

    try:
        yield {"type": "status", "stage": "memory", "message": "Loading recent chat…"}
        state = _merge_state(state, _load_memory(state))

        yield {"type": "status", "stage": "embed", "message": "Embedding your question…"}
        state = _merge_state(state, _embed_query(state))

        top_k = retrieve_top_k_for_mode(state.get("mode"))
        yield {
            "type": "status",
            "stage": "retrieve",
            "message": f"Searching top {top_k} excerpts ({state.get('mode', 'fast')} mode)…",
        }
        state = _merge_state(state, _retrieve(state))

        chunks = state.get("retrieved_chunks") or []
        yield {
            "type": "status",
            "stage": "select",
            "message": f"Found {len(chunks)} relevant excerpt{'s' if len(chunks) != 1 else ''}…",
        }
        state = _merge_state(state, _select_chunks(state))

        yield {"type": "status", "stage": "aggregate", "message": "Building answer context…"}
        state = _merge_state(state, _aggregate_multidoc(state))

        pregenerate_ms = round((time.perf_counter() - started) * 1000, 1)
        yield {"type": "status", "stage": "generate", "message": "Generating answer…"}
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
                chat_model = chat_model_for_mode(state.get("mode"))
                for delta in stream_generate_with_context(
                    context=state.get("context_text") or "",
                    query=state["query"],
                    chat_history=state.get("chat_history") or [],
                    model=chat_model,
                ):
                    if ttft_ms is None:
                        ttft_ms = round((time.perf_counter() - started) * 1000, 1)
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

        yield {"type": "status", "stage": "save", "message": "Saving conversation…"}
        state = _merge_state(state, _save_memory(state))

        total_ms = round((time.perf_counter() - started) * 1000, 1)
        yield {
            "type": "done",
            "answer": state.get("final_answer", ""),
            "citations": state.get("citations", []),
            "message_id": state.get("assistant_message_id"),
            "mode": state.get("mode", "fast"),
            "latency_ms": {
                "ttft": ttft_ms,
                "pregenerate": pregenerate_ms,
                "total": total_ms,
            },
            "error": state.get("error"),
        }
    except Exception as exc:
        logger.exception("RAG streaming pipeline failed")
        yield {"type": "error", "detail": str(exc)}
