"""Server-Sent Events helpers for streaming chat."""

from __future__ import annotations

import json
from typing import Any


def sse_event(event: str, data: dict[str, Any]) -> str:
    """Format one SSE message (event + JSON data, double newline terminated)."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"
