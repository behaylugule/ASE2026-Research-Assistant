"use client";

import { useEffect, useState } from "react";
import type { ChatCitation } from "@/lib/chat-stream";
import { fetchChunkDetail, type ChunkDetail } from "@/lib/api";

type Props = {
  projectId: string;
  citation: ChatCitation | null;
  onClose?: () => void;
};

export function DocumentExcerptPanel({ projectId, citation, onClose }: Props) {
  const [chunk, setChunk] = useState<ChunkDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!citation?.chunk_id) {
      setChunk(null);
      return;
    }
    setLoading(true);
    setError(null);
    void fetchChunkDetail(projectId, citation.chunk_id)
      .then(setChunk)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load excerpt"))
      .finally(() => setLoading(false));
  }, [projectId, citation?.chunk_id]);

  if (!citation) {
    return (
      <div className="doc-excerpt-empty">
        <p className="text-xs text-muted-foreground">Click a source to preview the excerpt here.</p>
      </div>
    );
  }

  const start = citation.char_start ?? 0;
  const end = citation.char_end ?? start;
  const full = chunk?.content ?? citation.snippet ?? "";
  const before = full.slice(0, start);
  const highlight = full.slice(start, end || full.length);
  const after = full.slice(end || full.length);

  return (
    <div className="doc-excerpt-panel">
      <div className="doc-excerpt-hdr">
        <div className="min-w-0">
          <div className="doc-excerpt-title">{citation.document_name ?? "Document"}</div>
          <div className="doc-excerpt-meta">
            {citation.page_number != null ? `Page ${citation.page_number}` : "Page n/a"}
            {citation.chunk_index != null ? ` · chunk ${citation.chunk_index}` : ""}
          </div>
        </div>
        {onClose ? (
          <button type="button" className="doc-excerpt-close" onClick={onClose} aria-label="Close excerpt">
            ×
          </button>
        ) : null}
      </div>
      {loading ? <p className="text-xs text-muted-foreground">Loading excerpt…</p> : null}
      {error ? <p className="text-xs text-destructive">{error}</p> : null}
      {!loading && !error ? (
        <div className="doc-excerpt-body">
          {before}
          <mark className="doc-excerpt-mark">{highlight || full}</mark>
          {after}
        </div>
      ) : null}
    </div>
  );
}
