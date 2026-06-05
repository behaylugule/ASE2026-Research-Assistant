"""RAG runtime configuration helpers (fast vs deep chat modes)."""

from django.conf import settings

VALID_MODES = frozenset({"fast", "deep"})


def normalize_mode(mode: str | None) -> str:
    m = (mode or settings.DEFAULT_CHAT_MODE or "fast").strip().lower()
    return m if m in VALID_MODES else "fast"


def retrieve_top_k_for_mode(mode: str) -> int:
    if normalize_mode(mode) == "deep":
        return settings.DEEP_RETRIEVE_TOP_K
    return settings.FAST_RETRIEVE_TOP_K


def chat_model_for_mode(mode: str) -> str:
    if normalize_mode(mode) == "deep":
        return settings.OPENAI_CHAT_MODEL
    return settings.OPENAI_CHAT_MODEL_FAST


def chat_history_limit_for_mode(mode: str) -> int:
    if normalize_mode(mode) == "deep":
        return settings.CHAT_HISTORY_LIMIT
    return settings.FAST_CHAT_HISTORY_LIMIT
