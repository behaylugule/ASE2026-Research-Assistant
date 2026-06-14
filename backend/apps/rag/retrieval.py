"""Project-scoped vector retrieval."""

import re
from uuid import UUID

from django.conf import settings
from pgvector.django import CosineDistance

from apps.documents.models import DocumentStatus
from apps.rag.models import DocumentChunk

_OVERVIEW_PATTERNS = (
    r"\bsummar",
    r"\boverview\b",
    r"\babstraction\b",
    r"\babstract\b",
    r"\bwhat is this (book|document|paper|text|file)\b",
    r"\bwhat is .+ about\b",
    r"\bwhat's .+ about\b",
    r"\bgist\b",
    r"\bdescribe\b",
    r"\bmain idea\b",
    r"\bthemes?\b",
    r"\bplot\b",
    r"\btopic of\b",
    r"\bsubject of\b",
)


_CHARACTER_PATTERNS = (
    r"\bcharacters?\b",
    r"\bactors?\b",
    r"\bprotagonist\b",
    r"\blist all\b",
    r"\bwho is\b",
    r"\bmain (character|actor|person)\b",
    r"\bnames?\b",
)


def is_overview_query(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in _OVERVIEW_PATTERNS)


def is_character_query(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in _CHARACTER_PATTERNS)


def _row_to_chunk(row: DocumentChunk) -> dict:
    meta = row.metadata or {}
    return {
        "chunk_id": str(row.id),
        "content": row.content,
        "document_id": str(row.document_id),
        "document_name": meta.get("document_name") or row.document.original_filename,
        "page_number": row.page_number,
<<<<<<< HEAD
        "chunk_index": row.chunk_index,
=======
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
        "distance": None,
    }


def _intro_chunks(project_id: str | UUID, *, per_document: int = 2) -> list[dict]:
    """First chunks of each document — useful for titles, intros, and summaries."""
    doc_ids = (
<<<<<<< HEAD
        DocumentChunk.objects.filter(
            document__project_id=project_id,
            document__status=DocumentStatus.READY,
        )
=======
        DocumentChunk.objects.filter(document__project_id=project_id)
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
        .values_list("document_id", flat=True)
        .distinct()
    )
    out: list[dict] = []
    for doc_id in doc_ids:
        rows = (
            DocumentChunk.objects.filter(document_id=doc_id)
            .select_related("document")
            .order_by("chunk_index")[:per_document]
        )
        out.extend(_row_to_chunk(row) for row in rows)
    return out


def _early_page_chunks(
    project_id: str | UUID,
    *,
    per_document: int = 3,
    max_page: int = 50,
) -> list[dict]:
    """Opening pages where characters are usually introduced (avoid late-book pages like 1080)."""
    doc_ids = (
<<<<<<< HEAD
        DocumentChunk.objects.filter(
            document__project_id=project_id,
            document__status=DocumentStatus.READY,
        )
=======
        DocumentChunk.objects.filter(document__project_id=project_id)
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
        .values_list("document_id", flat=True)
        .distinct()
    )
    out: list[dict] = []
    for doc_id in doc_ids:
        rows = (
            DocumentChunk.objects.filter(document_id=doc_id, page_number__lte=max_page)
            .select_related("document")
            .order_by("chunk_index")[:per_document]
        )
        if not rows:
            rows = (
                DocumentChunk.objects.filter(document_id=doc_id)
                .select_related("document")
                .order_by("chunk_index")[:per_document]
            )
        out.extend(_row_to_chunk(row) for row in rows)
    return out


def _merge_chunks(*groups: list[dict], limit: int) -> list[dict]:
    seen: set[str] = set()
    merged: list[dict] = []
    for group in groups:
        for chunk in group:
            cid = chunk["chunk_id"]
            if cid in seen:
                continue
            seen.add(cid)
            merged.append(chunk)
            if len(merged) >= limit:
                return merged
    return merged


def retrieve_chunks(
    project_id: str | UUID,
    query_embedding: list[float],
    limit: int | None = None,
    *,
    query: str | None = None,
<<<<<<< HEAD
    pipeline_mode: str = "qa",
) -> list[dict]:
    k = limit if limit is not None else settings.RETRIEVE_TOP_K
    base_qs = DocumentChunk.objects.filter(
        document__project_id=project_id,
        document__status=DocumentStatus.READY,
    ).select_related("document")
    qs = base_qs.annotate(distance=CosineDistance("embedding", query_embedding)).order_by("distance")[:k]
=======
) -> list[dict]:
    k = limit if limit is not None else settings.RETRIEVE_TOP_K
    qs = (
        DocumentChunk.objects.filter(document__project_id=project_id)
        .select_related("document")
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:k]
    )
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
    vector_chunks = []
    for row in qs:
        chunk = _row_to_chunk(row)
        chunk["distance"] = float(row.distance) if row.distance is not None else None
        vector_chunks.append(chunk)

<<<<<<< HEAD
    if not query:
        return vector_chunks

    if is_character_query(query):
=======
    if query and is_character_query(query):
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
        # Prefer early pages for names; limit vector hits so late pages (e.g. 1080) don't dominate.
        intro = _intro_chunks(project_id, per_document=2)
        early = _early_page_chunks(project_id, per_document=2, max_page=50)
        vector_tail = vector_chunks[: min(k, 2)]
        cap = min(k + 3, 7)
        return _merge_chunks(intro, early, vector_tail, limit=cap)

    if query and is_overview_query(query):
        intro = _intro_chunks(project_id, per_document=2)
        cap = max(k + 4, 8) if k <= 5 else k + 2
        return _merge_chunks(intro, vector_chunks, limit=cap)

    return vector_chunks
