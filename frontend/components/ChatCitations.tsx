"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { ChatCitation } from "@/lib/chat-stream";
import { cn } from "@/lib/utils";

type Props = {
  citations: ChatCitation[];
  defaultOpen?: boolean;
  selectedChunkId?: string | null;
  onSelectCitation?: (citation: ChatCitation) => void;
};

export function ChatCitations({ citations, defaultOpen = false, selectedChunkId, onSelectCitation }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  if (!citations.length) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="chat-cites-panel">
      <CollapsibleTrigger asChild>
        <button type="button" className="chat-cites-trigger">
          <span className="chat-cites-trigger-label">Sources</span>
          <span className="chat-cites-count">{citations.length}</span>
          <ChevronDown className={cn("chat-cites-chevron size-4", open && "is-open")} />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent className="chat-cites-content">
        <div className="mock-cites">
          {citations.map((c, i) => {
            const active = selectedChunkId && c.chunk_id === selectedChunkId;
            return (
              <button
                key={`${c.chunk_id ?? c.document_name ?? i}-${i}`}
                type="button"
                className={cn("mock-cite mock-cite-btn", active && "is-active")}
                onClick={() => onSelectCitation?.(c)}
              >
                <div className="mock-cnum">{i + 1}</div>
                <div className="min-w-0 text-left">
                  <div className="mock-cdoc">{c.document_name ?? "Document"}</div>
                  {c.snippet ? <div className="mock-csnip">{c.snippet}</div> : c.label ? <div className="mock-csnip">{c.label}</div> : null}
                  <div className="mock-cpg">{c.page_number != null ? `p. ${c.page_number}` : "p. n/a"}</div>
                </div>
              </button>
            );
          })}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
