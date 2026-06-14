"""Literature search pipeline — explore project documents by relevance."""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any
from uuid import UUID

from django.conf import settings

from apps.rag.config import chat_model_for_mode, literature_top_k, normalize_mode
from apps.rag.llm import generate_raw, stream_raw
from apps.rag.pipeline_utils import build_citations, group_chunks_by_document
from apps.rag.pipelines.qa import _save_chat
from apps.rag.prompts_modes import LITERATURE_SYSTEM_PROMPT
from apps.rag.retrieval import retrieve_chunks
from apps.rag.services.embeddings import embed_query


def _build_literature_context(chunks: list[dict]) -> str:
    by_doc = group_chunks_by_document(chunks)
    parts: list[str] = []
    for did, items in by_doc.items():
        name = items[0].get("document_name", "Unknown")
        dist = items[0].get("distance")
        score = f" (relevance distance: {dist:.4f})" if dist is not None else ""
        parts.append(f"### {name}{score}\n")
        for it in items:
            page = it.get("page_number", "n/a")
            parts.append(f"- Page {page}: {it['content'][:500]}…")
    return "\n".join(parts) if parts else "(no results)"


def _structured_from_chunks(chunks: list[dict]) -> dict[str, Any]:
    by_doc = group_chunks_by_document(chunks)
    papers = []
    for did, items in by_doc.items():
        papers.append(
            {
                "document_id": did,
                "document_name": items[0].get("document_name"),
                "relevance_score": items[0].get("distance"),
                "citations": build_citations(items),
            }
        )
    return {"papers": papers, "chunk_count": len(chunks)}


def run_literature_search(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "fast",
) -> dict[str, Any]:
    del user_id
    mode = normalize_mode(mode)
    k = literature_top_k(mode)
    embedding = embed_query(query)
    chunks = retrieve_chunks(str(project_id), embedding, limit=k, pipeline_mode="literature_search")
    context = _build_literature_context(chunks)
    system = LITERATURE_SYSTEM_PROMPT.format(context=context)
    user = f"Research query: {query}\n\nProduce the exploration report."
    answer = generate_raw(system=system, user=user, model=chat_model_for_mode(mode))
    citations = build_citations(chunks)
    structured = _structured_from_chunks(chunks)
    msg_id = _save_chat(str(project_id), query, answer, citations)
    return {
        "final_answer": answer,
        "citations": citations,
        "structured": structured,
        "assistant_message_id": msg_id,
        "pipeline_mode": "literature_search",
    }


def iter_literature_stream(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "fast",
) -> Iterator[dict[str, Any]]:
    del user_id
    mode = normalize_mode(mode)
    k = literature_top_k(mode)
    started = time.perf_counter()
    ttft_ms: float | None = None

    yield {"type": "status", "stage": "embed", "message": "Embedding search query…"}
    embedding = embed_query(query)

    yield {"type": "status", "stage": "retrieve", "message": f"Literature search: top {k} across project…"}
    chunks = retrieve_chunks(str(project_id), embedding, limit=k, pipeline_mode="literature_search")
    context = _build_literature_context(chunks)
    system = LITERATURE_SYSTEM_PROMPT.format(context=context)
    user = f"Research query: {query}\n\nProduce the exploration report."

    yield {"type": "status", "stage": "generate", "message": "Building thematic overview…"}
    error: str | None = None
    if not settings.OPENAI_API_KEY:
        answer = "OPENAI_API_KEY is not configured."
        citations: list[dict] = []
        error = "OPENAI_API_KEY is not configured"
    else:
        parts: list[str] = []
        try:
            for delta in stream_raw(system=system, user=user, model=chat_model_for_mode(mode)):
                if ttft_ms is None:
                    ttft_ms = round((time.perf_counter() - started) * 1000, 1)
                parts.append(delta)
                yield {"type": "token", "content": delta}
            answer = "".join(parts)
            citations = build_citations(chunks)
        except Exception as exc:
            answer = "Literature search failed."
            error = str(exc)
            citations = []

    structured = _structured_from_chunks(chunks)
    msg_id = _save_chat(str(project_id), query, answer, citations)
    yield {
        "type": "done",
        "answer": answer,
        "citations": citations,
        "structured": structured,
        "message_id": msg_id,
        "mode": mode,
        "pipeline_mode": "literature_search",
        "latency_ms": {"ttft": ttft_ms, "total": round((time.perf_counter() - started) * 1000, 1)},
        "error": error,
    }
