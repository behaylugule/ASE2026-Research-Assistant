"""Multi-paper synthesis pipeline — literature review style."""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any
from uuid import UUID

from django.conf import settings

from apps.rag.config import chat_model_for_mode, normalize_mode, synthesis_top_k
from apps.rag.llm import generate_raw, stream_raw
from apps.rag.pipeline_utils import build_citations, group_chunks_by_document
from apps.rag.pipelines.qa import _save_chat
from apps.rag.prompts_modes import SYNTHESIS_SYSTEM_PROMPT
from apps.rag.retrieval import retrieve_chunks
from apps.rag.services.embeddings import embed_query


def _build_synthesis_context(chunks: list[dict]) -> str:
    by_doc = group_chunks_by_document(chunks)
    blocks: list[str] = []
    for did, items in by_doc.items():
        name = items[0].get("document_name", "Unknown")
        excerpts = "\n".join(
            f"  (page {it.get('page_number', 'n/a')}): {it['content'][:400]}…" for it in items
        )
        blocks.append(f"## Document: {name} (id={did})\n{excerpts}")
    return "\n\n".join(blocks) if blocks else "(no retrieved context)"


def run_synthesis(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "deep",
) -> dict[str, Any]:
    del user_id
    mode = normalize_mode(mode)
    k = synthesis_top_k(mode)
    embedding = embed_query(query)
    chunks = retrieve_chunks(str(project_id), embedding, limit=k, pipeline_mode="synthesis")
    context = _build_synthesis_context(chunks)
    system = SYNTHESIS_SYSTEM_PROMPT.format(context=context)
    user = f"Synthesis topic / question: {query}\n\nWrite the literature review synthesis."
    answer = generate_raw(system=system, user=user, model=chat_model_for_mode(mode))
    citations = build_citations(chunks)
    msg_id = _save_chat(str(project_id), query, answer, citations)
    return {
        "final_answer": answer,
        "citations": citations,
        "assistant_message_id": msg_id,
        "pipeline_mode": "synthesis",
    }


def iter_synthesis_stream(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "deep",
) -> Iterator[dict[str, Any]]:
    del user_id
    mode = normalize_mode(mode)
    k = synthesis_top_k(mode)
    started = time.perf_counter()
    ttft_ms: float | None = None

    yield {"type": "status", "stage": "embed", "message": "Embedding synthesis query…"}
    embedding = embed_query(query)

    yield {"type": "status", "stage": "retrieve", "message": f"Synthesis: retrieving top {k} excerpts…"}
    chunks = retrieve_chunks(str(project_id), embedding, limit=k, pipeline_mode="synthesis")
    context = _build_synthesis_context(chunks)
    system = SYNTHESIS_SYSTEM_PROMPT.format(context=context)
    user = f"Synthesis topic / question: {query}\n\nWrite the literature review synthesis."

    yield {"type": "status", "stage": "generate", "message": "Synthesizing across documents…"}
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
            answer = "Synthesis failed."
            error = str(exc)
            citations = []

    msg_id = _save_chat(str(project_id), query, answer, citations)
    yield {
        "type": "done",
        "answer": answer,
        "citations": citations,
        "message_id": msg_id,
        "mode": mode,
        "pipeline_mode": "synthesis",
        "latency_ms": {"ttft": ttft_ms, "total": round((time.perf_counter() - started) * 1000, 1)},
        "error": error,
    }
