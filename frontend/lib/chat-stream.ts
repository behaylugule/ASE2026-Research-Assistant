import { getAccessToken } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type ChatMode = "fast" | "deep";

export type ChatCitation = {
  label?: string;
  document_name?: string;
  page_number?: number | null;
  chunk_id?: string;
};

export type ChatLatencyMs = {
  ttft?: number | null;
  pregenerate?: number | null;
  total?: number | null;
};

export type ChatStreamHandlers = {
  onStatus?: (stage: string, message?: string) => void;
  onToken?: (content: string) => void;
  onDone?: (payload: {
    answer: string;
    citations: ChatCitation[];
    message_id?: string;
    mode?: ChatMode;
    latency_ms?: ChatLatencyMs;
    error?: string | null;
  }) => void;
  onError?: (detail: string) => void;
};

function parseSseBlock(block: string): { event: string; data: string } | null {
  const lines = block.split("\n").filter((l) => l.length > 0);
  if (!lines.length) return null;
  let event = "message";
  const dataLines: string[] = [];
  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }
  if (!dataLines.length) return null;
  return { event, data: dataLines.join("\n") };
}

function dispatchPayload(payload: Record<string, unknown>, handlers: ChatStreamHandlers) {
  const type = payload.type as string | undefined;
  if (type === "status" && typeof payload.stage === "string") {
    handlers.onStatus?.(
      payload.stage,
      typeof payload.message === "string" ? payload.message : undefined,
    );
    return;
  }
  if (type === "token" && typeof payload.content === "string") {
    handlers.onToken?.(payload.content);
    return;
  }
  if (type === "done") {
    handlers.onDone?.({
      answer: typeof payload.answer === "string" ? payload.answer : "",
      citations: Array.isArray(payload.citations) ? (payload.citations as ChatCitation[]) : [],
      message_id: typeof payload.message_id === "string" ? payload.message_id : undefined,
      mode: payload.mode === "deep" ? "deep" : "fast",
      latency_ms:
        payload.latency_ms && typeof payload.latency_ms === "object"
          ? (payload.latency_ms as ChatLatencyMs)
          : undefined,
      error: typeof payload.error === "string" ? payload.error : null,
    });
    return;
  }
  if (type === "error" && typeof payload.detail === "string") {
    handlers.onError?.(payload.detail);
  }
}

/**
 * POST + SSE (fetch ReadableStream). Prefer over EventSource for JWT + JSON body.
 */
export async function streamProjectChat(
  projectId: string,
  message: string,
  handlers: ChatStreamHandlers,
  options: { signal?: AbortSignal; mode?: ChatMode } = {},
): Promise<void> {
  const { signal, mode = "fast" } = options;
  const token = getAccessToken();
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/chat/stream/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message, mode }),
    signal,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const err = (await res.json()) as { detail?: unknown };
      if (typeof err.detail === "string") detail = err.detail;
      else if (Array.isArray(err.detail)) detail = JSON.stringify(err.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }

  if (!res.body) {
    throw new Error("Streaming not supported by this browser");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sep = buffer.indexOf("\n\n");
      while (sep !== -1) {
        const block = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        const parsed = parseSseBlock(block);
        if (parsed) {
          try {
            const payload = JSON.parse(parsed.data) as Record<string, unknown>;
            dispatchPayload(payload, handlers);
          } catch {
            /* malformed frame */
          }
        }
        sep = buffer.indexOf("\n\n");
      }
    }

    if (buffer.trim()) {
      const parsed = parseSseBlock(buffer);
      if (parsed) {
        try {
          const payload = JSON.parse(parsed.data) as Record<string, unknown>;
          dispatchPayload(payload, handlers);
        } catch {
          /* ignore */
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export function chatStageLabel(stage: string, message?: string): string {
  if (message) return message;
  switch (stage) {
    case "memory":
      return "Loading history…";
    case "embed":
      return "Embedding query…";
    case "retrieve":
      return "Retrieving sources…";
    case "select":
      return "Selecting sources…";
    case "aggregate":
      return "Building context…";
    case "generate":
      return "Generating…";
    case "save":
      return "Saving…";
    default:
      return "Working…";
  }
}

export function formatLatencyMs(ms?: number | null): string {
  if (ms == null || Number.isNaN(ms)) return "";
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatLatencySummary(latency?: ChatLatencyMs): string {
  if (!latency) return "";
  const parts: string[] = [];
  if (latency.ttft != null) parts.push(`first token ${formatLatencyMs(latency.ttft)}`);
  if (latency.total != null) parts.push(`total ${formatLatencyMs(latency.total)}`);
  return parts.join(" · ");
}
