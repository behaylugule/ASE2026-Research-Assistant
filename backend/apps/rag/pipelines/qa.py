"""Q&A RAG pipeline — vector retrieval with grounded answers and citations."""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db import transaction

from apps.chat.models import ChatMessage, ChatRole
from apps.projects.models import Project
from apps.rag.config import chat_history_limit_for_mode, chat_model_for_mode, normalize_mode, retrieve_top_k_for_mode
from apps.rag.llm import generate_raw, stream_raw
from apps.rag.pipeline_utils import (
    aggregate_chunks_multidoc,
    build_citations,
    format_prompt_with_context,
    is_not_found_answer,
)
from apps.rag.prompts_modes import QA_SYSTEM_PROMPT
from apps.rag.query_enhance import enhance_query_for_retrieval
from apps.rag.retrieval import retrieve_chunks
from apps.rag.services.embeddings import embed_query


def _load_history(project_id: str, mode: str) -> list[dict]:
    limit = chat_history_limit_for_mode(mode)
    qs = ChatMessage.objects.filter(project_id=project_id).order_by("-created_at")[:limit]
    return [{"role": m.role, "content": m.content} for m in reversed(list(qs))]


def _save_chat(
    project_id: str,
    query: str,
    answer: str,
    citations: list[dict],
    *,
    meta: dict | None = None,
    save_user: bool = True,
) -> str:
    project = Project.objects.get(pk=project_id)
    with transaction.atomic():
        if save_user:
            ChatMessage.objects.create(project=project, role=ChatRole.USER, content=query)
        assistant = ChatMessage.objects.create(
            project=project,
            role=ChatRole.ASSISTANT,
            content=answer,
            citations=citations,
            meta=meta,
        )
    return str(assistant.id)


def run_qa(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "fast",
) -> dict[str, Any]:
    del user_id
    mode = normalize_mode(mode)
    k = retrieve_top_k_for_mode(mode)
    history = _load_history(str(project_id), mode)
    retrieval_query = enhance_query_for_retrieval(query)
    embedding = embed_query(retrieval_query)
    chunks = retrieve_chunks(
        str(project_id),
        embedding,
        limit=k,
        query=query,
        pipeline_mode="qa",
    )
    context = aggregate_chunks_multidoc(chunks)

    if not settings.OPENAI_API_KEY:
        return {
            "final_answer": "The assistant is not configured (set OPENAI_API_KEY).",
            "citations": [],
            "error": "OPENAI_API_KEY is not configured",
            "pipeline_mode": "qa",
        }

    system = format_prompt_with_context(QA_SYSTEM_PROMPT, context)
    answer = generate_raw(
        system=system,
        user=query,
        model=chat_model_for_mode(mode),
        chat_history=history,
    )
    citations = [] if is_not_found_answer(answer) else build_citations(chunks)
    msg_id = _save_chat(
        str(project_id),
        query,
        answer,
        citations,
        meta={"mode": mode, "pipeline_mode": "qa"},
    )
    return {
        "final_answer": answer,
        "citations": citations,
        "assistant_message_id": msg_id,
        "pipeline_mode": "qa",
    }


def iter_qa_stream(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "fast",
) -> Iterator[dict[str, Any]]:
    del user_id
    mode = normalize_mode(mode)
    k = retrieve_top_k_for_mode(mode)
    started = time.perf_counter()
    ttft_ms: float | None = None

    yield {"type": "status", "stage": "memory", "message": "Loading recent chat…"}
    history = _load_history(str(project_id), mode)

    yield {"type": "status", "stage": "embed", "message": "Embedding your question…"}
    retrieval_query = enhance_query_for_retrieval(query)
    embedding = embed_query(retrieval_query)

    yield {"type": "status", "stage": "retrieve", "message": f"Q&A: searching top {k} excerpts…"}
    chunks = retrieve_chunks(
        str(project_id),
        embedding,
        limit=k,
        query=query,
        pipeline_mode="qa",
    )
    context = aggregate_chunks_multidoc(chunks)
    system = format_prompt_with_context(QA_SYSTEM_PROMPT, context)

    yield {"type": "status", "stage": "generate", "message": "Generating grounded answer…"}
    error: str | None = None
    if not settings.OPENAI_API_KEY:
        answer = "The assistant is not configured (set OPENAI_API_KEY)."
        citations: list[dict] = []
        error = "OPENAI_API_KEY is not configured"
    else:
        parts: list[str] = []
        try:
            for delta in stream_raw(
                system=system,
                user=query,
                model=chat_model_for_mode(mode),
                chat_history=history,
            ):
                if ttft_ms is None:
                    ttft_ms = round((time.perf_counter() - started) * 1000, 1)
                parts.append(delta)
                yield {"type": "token", "content": delta}
            answer = "".join(parts)
        except Exception as exc:
            answer = "The assistant could not generate an answer."
            error = str(exc)
            citations = []
        else:
            citations = [] if is_not_found_answer(answer) else build_citations(chunks)

    yield {"type": "status", "stage": "save", "message": "Saving conversation…"}
    msg_id = _save_chat(
        str(project_id),
        query,
        answer,
        citations,
        meta={"mode": mode, "pipeline_mode": "qa"},
    )
    total_ms = round((time.perf_counter() - started) * 1000, 1)
    yield {
        "type": "done",
        "answer": answer,
        "citations": citations,
        "message_id": msg_id,
        "mode": mode,
        "pipeline_mode": "qa",
        "latency_ms": {"ttft": ttft_ms, "total": total_ms},
        "error": error,
    }


def iter_qa_refine_stream(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    draft_answer: str,
    refined_from: str,
) -> Iterator[dict[str, Any]]:
    del user_id
    mode = "deep"
    k = retrieve_top_k_for_mode(mode)
    started = time.perf_counter()
    ttft_ms: float | None = None

    yield {"type": "status", "stage": "embed", "message": "Deep refine: embedding question…"}
    retrieval_query = enhance_query_for_retrieval(query)
    embedding = embed_query(retrieval_query)

    yield {"type": "status", "stage": "retrieve", "message": f"Deep refine: retrieving top {k} excerpts…"}
    chunks = retrieve_chunks(
        str(project_id),
        embedding,
        limit=k,
        query=query,
        pipeline_mode="qa",
    )
    context = aggregate_chunks_multidoc(chunks)
    from apps.rag.prompts_modes import QA_REFINE_USER_TEMPLATE

    system = format_prompt_with_context(QA_SYSTEM_PROMPT, context)
    user = QA_REFINE_USER_TEMPLATE.format(query=query, draft=draft_answer)

    yield {"type": "status", "stage": "generate", "message": "Refining answer with Deep mode…"}
    error: str | None = None
    if not settings.OPENAI_API_KEY:
        answer = "The assistant is not configured (set OPENAI_API_KEY)."
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
        except Exception as exc:
            answer = "The assistant could not refine the answer."
            error = str(exc)
            citations = []
        else:
            citations = [] if is_not_found_answer(answer) else build_citations(chunks)

    yield {"type": "status", "stage": "save", "message": "Saving refined answer…"}
    msg_id = _save_chat(
        str(project_id),
        query,
        answer,
        citations,
        save_user=False,
        meta={"mode": mode, "pipeline_mode": "qa", "refined_from": refined_from, "refined": True},
    )
    total_ms = round((time.perf_counter() - started) * 1000, 1)
    yield {
        "type": "done",
        "answer": answer,
        "citations": citations,
        "message_id": msg_id,
        "mode": mode,
        "pipeline_mode": "qa",
        "refined": True,
        "latency_ms": {"ttft": ttft_ms, "total": total_ms},
        "error": error,
    }
