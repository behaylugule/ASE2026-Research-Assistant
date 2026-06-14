"""Shared helpers for RAG pipelines."""

from __future__ import annotations

_SNIPPET_MAX = 320


def _snippet(text: str) -> tuple[str, int, int]:
    content = (text or "").strip()
    if len(content) <= _SNIPPET_MAX:
        return content, 0, len(content)
    return content[:_SNIPPET_MAX].rstrip() + "…", 0, _SNIPPET_MAX


def build_citations(chunks: list[dict]) -> list[dict]:
    """One citation per retrieved chunk with snippet offsets for UI highlighting."""
    out: list[dict] = []
    seen: set[str] = set()
    for c in chunks:
        chunk_id = c.get("chunk_id")
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(str(chunk_id))
        name = c.get("document_name", "")
        page = c.get("page_number")
        snippet, char_start, char_end = _snippet(c.get("content") or "")
        page_label = page if page is not None else "n/a"
        out.append(
            {
                "label": f"[{name} – Page {page_label}]",
                "document_name": name,
                "document_id": c.get("document_id"),
                "page_number": page,
                "chunk_id": str(chunk_id),
                "chunk_index": c.get("chunk_index"),
                "snippet": snippet,
                "char_start": char_start,
                "char_end": char_end,
            }
        )
    return out


def format_prompt_with_context(template: str, context: str) -> str:
    """Insert context without breaking on literal braces in document text."""
    return template.replace("{context}", context)


def is_not_found_answer(answer: str) -> bool:
    normalized = " ".join(answer.strip().lower().split())
    return "not found in the provided documents" in normalized


def aggregate_chunks_multidoc(chunks: list[dict]) -> str:
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
    return "\n\n".join(blocks) if blocks else "(no retrieved context)"


def group_chunks_by_document(chunks: list[dict]) -> dict[str, list[dict]]:
    by_doc: dict[str, list[dict]] = {}
    for c in chunks:
        did = c.get("document_id", "")
        by_doc.setdefault(did, []).append(c)
    return by_doc
