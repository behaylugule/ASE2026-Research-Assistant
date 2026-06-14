"""Full-document hierarchical summarization (map-reduce, all chunks)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from django.conf import settings

from apps.rag.llm import generate_raw
from apps.rag.models import DocumentChunk
from apps.rag.prompts_modes import SUMMARIZE_CHUNK_PROMPT, SUMMARIZE_FINAL_PROMPT, SUMMARIZE_MERGE_PROMPT

logger = logging.getLogger(__name__)


def _load_all_chunks(document_id: str | UUID) -> list[dict]:
    rows = (
        DocumentChunk.objects.filter(document_id=document_id)
        .select_related("document")
        .order_by("chunk_index")
    )
    out: list[dict] = []
    for row in rows:
        meta = row.metadata or {}
        out.append(
            {
                "chunk_id": str(row.id),
                "content": row.content,
                "page_number": row.page_number,
                "chunk_index": row.chunk_index,
                "document_name": meta.get("document_name") or row.document.original_filename,
            }
        )
    return out


def _summarize_chunk(content: str, page: int | None, model: str) -> str:
    page_label = page if page is not None else "n/a"
    prompt = SUMMARIZE_CHUNK_PROMPT.format(page=page_label, content=content[:6000])
    return generate_raw(
        system="You summarize document excerpts as bullet points only.",
        user=prompt,
        model=model,
    )


def _merge_section_bullets(bullets: list[str], model: str) -> str:
    joined = "\n\n".join(f"Chunk batch:\n{b}" for b in bullets)
    prompt = SUMMARIZE_MERGE_PROMPT.format(bullets=joined)
    return generate_raw(
        system="You merge bullet summaries without adding new facts.",
        user=prompt,
        model=model,
    )


def _final_summary(section_summaries: list[str], model: str) -> str:
    sections = "\n\n---\n\n".join(section_summaries)
    prompt = SUMMARIZE_FINAL_PROMPT.format(sections=sections)
    return generate_raw(
        system="You write structured academic summaries using only provided section summaries.",
        user=prompt,
        model=model,
    )


def run_document_summarize(*, document_id: str | UUID, model: str | None = None) -> dict[str, Any]:
    """
    Hierarchical map-reduce over ALL chunks (no vector top-k).
    Returns structured summary + markdown body.
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")

    from apps.documents.models import Document

    doc = Document.objects.get(pk=document_id)
    llm_model = model or settings.OPENAI_CHAT_MODEL
    chunks = _load_all_chunks(document_id)
    if not chunks:
        raise ValueError("No chunks found for document")

    chunk_summaries: list[str] = []
    batch_size = settings.SUMMARIZE_SECTION_BATCH

    for i, ch in enumerate(chunks):
        if i > 0 and i % 20 == 0:
            logger.info("Summarize progress: %s/%s chunks", i, len(chunks))
        chunk_summaries.append(_summarize_chunk(ch["content"], ch.get("page_number"), llm_model))

    section_summaries: list[str] = []
    for i in range(0, len(chunk_summaries), batch_size):
        batch = chunk_summaries[i : i + batch_size]
        section_summaries.append(_merge_section_bullets(batch, llm_model))

    final_md = _final_summary(section_summaries, llm_model)

    structured = _parse_structured(final_md)
    return {
        "document_id": str(document_id),
        "document_name": doc.original_filename,
        "chunk_count": len(chunks),
        "summary_markdown": final_md,
        "summary": structured,
        "status": "completed",
        "pipeline_mode": "summarize",
    }


def _parse_structured(markdown: str) -> dict[str, Any]:
    """Light parse of final markdown into JSON fields."""
    sections = {
        "objective": "",
        "methodology": "",
        "key_findings": [],
        "limitations": [],
        "conclusion": "",
    }
    current = None
    for line in markdown.splitlines():
        low = line.strip().lower()
        if low.startswith("## objective"):
            current = "objective"
            continue
        if low.startswith("## methodology"):
            current = "methodology"
            continue
        if low.startswith("## key findings"):
            current = "key_findings"
            continue
        if low.startswith("## limitations"):
            current = "limitations"
            continue
        if low.startswith("## conclusion"):
            current = "conclusion"
            continue
        if not line.strip() or line.startswith("#"):
            continue
        text = line.lstrip("- ").strip()
        if not text:
            continue
        if current in ("key_findings", "limitations"):
            sections[current].append(text)
        elif current in sections:
            sections[current] = (sections[current] + " " + text).strip()
    return sections


def format_summary_for_chat(result: dict[str, Any]) -> str:
    s = result.get("summary") or {}
    return result.get("summary_markdown") or (
        f"## Objective\n{s.get('objective', 'not mentioned in document')}\n\n"
        f"## Methodology\n{s.get('methodology', 'not mentioned in document')}\n\n"
        f"## Key Findings\n" + "\n".join(f"- {x}" for x in s.get("key_findings", [])) + "\n\n"
        f"## Limitations\n" + "\n".join(f"- {x}" for x in s.get("limitations", [])) + "\n\n"
        f"## Conclusion\n{s.get('conclusion', 'not mentioned in document')}"
    )
