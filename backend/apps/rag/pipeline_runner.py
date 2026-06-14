"""Dispatch chat pipelines by mode."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from uuid import UUID

from apps.rag.pipeline_modes import normalize_pipeline_mode
from apps.rag.pipelines.literature import iter_literature_stream, run_literature_search
from apps.rag.pipelines.qa import iter_qa_stream, run_qa
from apps.rag.pipelines.summarize import format_summary_for_chat, run_document_summarize
from apps.rag.pipelines.synthesis import iter_synthesis_stream, run_synthesis


def run_pipeline(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "fast",
    pipeline_mode: str = "qa",
    document_id: str | None = None,
) -> dict[str, Any]:
    pm = normalize_pipeline_mode(pipeline_mode)
    if pm == "qa":
        return run_qa(project_id=project_id, user_id=user_id, query=query, mode=mode)
    if pm == "literature_search":
        return run_literature_search(project_id=project_id, user_id=user_id, query=query, mode=mode)
    if pm == "synthesis":
        return run_synthesis(project_id=project_id, user_id=user_id, query=query, mode=mode)
    if pm == "summarize":
        if not document_id:
            return {
                "final_answer": "document_id is required for summarize mode.",
                "citations": [],
                "error": "document_id required",
                "pipeline_mode": "summarize",
            }
        result = run_document_summarize(document_id=document_id)
        answer = format_summary_for_chat(result)
        from apps.rag.pipelines.qa import _save_chat

        msg_id = _save_chat(str(project_id), query or f"Summarize {result['document_name']}", answer, [])
        return {
            "final_answer": answer,
            "citations": [],
            "structured": result,
            "assistant_message_id": msg_id,
            "pipeline_mode": "summarize",
        }
    return run_qa(project_id=project_id, user_id=user_id, query=query, mode=mode)


def iter_pipeline_stream(
    *,
    project_id: str | UUID,
    user_id: int,
    query: str,
    mode: str = "fast",
    pipeline_mode: str = "qa",
    document_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    pm = normalize_pipeline_mode(pipeline_mode)
    if pm == "literature_search":
        yield from iter_literature_stream(
            project_id=project_id, user_id=user_id, query=query, mode=mode
        )
        return
    if pm == "synthesis":
        yield from iter_synthesis_stream(
            project_id=project_id, user_id=user_id, query=query, mode=mode
        )
        return
    if pm == "summarize":
        yield {"type": "status", "stage": "summarize", "message": "Running full-document map-reduce…"}
        if not document_id:
            yield {"type": "error", "detail": "document_id is required for summarize mode"}
            return
        try:
            result = run_document_summarize(document_id=document_id)
            answer = format_summary_for_chat(result)
            yield {"type": "token", "content": answer}
            from apps.rag.pipelines.qa import _save_chat

            msg_id = _save_chat(
                str(project_id),
                query or f"Summarize {result['document_name']}",
                answer,
                [],
            )
            yield {
                "type": "done",
                "answer": answer,
                "citations": [],
                "structured": result,
                "message_id": msg_id,
                "pipeline_mode": "summarize",
            }
        except Exception as exc:
            yield {"type": "error", "detail": str(exc)}
        return
    yield from iter_qa_stream(project_id=project_id, user_id=user_id, query=query, mode=mode)
