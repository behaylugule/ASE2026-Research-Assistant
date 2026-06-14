"""Pipeline mode identifiers for chat and document workflows."""

VALID_PIPELINE_MODES = frozenset({"qa", "summarize", "literature_search", "synthesis"})


def normalize_pipeline_mode(mode: str | None) -> str:
    m = (mode or "qa").strip().lower()
    return m if m in VALID_PIPELINE_MODES else "qa"
