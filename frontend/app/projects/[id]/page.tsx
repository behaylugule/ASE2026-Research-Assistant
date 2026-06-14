"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArxivTopBar } from "@/components/ArxivTopBar";
<<<<<<< HEAD
import { ChatCitations } from "@/components/ChatCitations";
import { ChatMessageBody } from "@/components/ChatMessageBody";
import { PipelineModeDropdown } from "@/components/PipelineModeDropdown";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { DocumentExcerptPanel } from "@/components/DocumentExcerptPanel";
import { apiJson, getAccessToken, retryDocument, uploadDocument } from "@/lib/api";
import {
  chatStageLabel,
  formatLatencySummary,
  streamProjectChat,
  streamRefineChat,
  type ChatCitation,
  type ChatLatencyMs,
  type ChatMessageMeta,
  type ChatMode,
  type PipelineMode,
} from "@/lib/chat-stream";
import { Download, FlaskConical, RotateCcw, Send, Sparkles, Square, Upload } from "lucide-react";
=======
import { apiJson, getAccessToken, uploadDocument } from "@/lib/api";
import { chatStageLabel, formatLatencySummary, streamProjectChat, type ChatCitation, type ChatLatencyMs, type ChatMode } from "@/lib/chat-stream";
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db

type ProjectRow = {
  id: string;
  name: string;
  created_at: string;
};

type DocumentRow = {
  id: string;
  original_filename: string;
  status: string;
  error_message?: string;
  mime_type?: string;
  page_count?: number | null;
  created_at: string;
  updated_at: string;
  summary_status?: string;
  chunk_count?: number;
  ingestion_progress?: number;
  ingestion_stage?: string;
};

type Citation = ChatCitation;

type ChatMessage = {
  id: string;
  role: string;
  content: string;
  citations?: Citation[] | null;
  meta?: ChatMessageMeta | null;
  created_at: string;
};

const PROJECT_EMOJIS = ["🌍", "🤖", "🧬", "⚛️", "📚", "🔬"];

function initialsFromToken(): string {
  const t = getAccessToken();
  if (!t) return "U";
  try {
    const payload = JSON.parse(atob(t.split(".")[1])) as { email?: string; username?: string; sub?: string };
    const s = (payload.email || payload.username || payload.sub || "U") as string;
    const clean = s.replace(/[^a-zA-Z0-9]/g, "");
    if (clean.length >= 2) return clean.slice(0, 2).toUpperCase();
    return s.slice(0, 2).toUpperCase();
  } catch {
    return "U";
  }
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
  } catch {
    return "";
  }
}

function formatShortDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

function isPdf(name: string, mime?: string): boolean {
  return name.toLowerCase().endsWith(".pdf") || (mime?.includes("pdf") ?? false);
}

function isDocx(name: string, mime?: string): boolean {
  return name.toLowerCase().endsWith(".docx") || (mime?.includes("word") ?? false);
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [project, setProject] = useState<ProjectRow | null>(null);
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [docs, setDocs] = useState<DocumentRow[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatError, setChatError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [chatMode, setChatMode] = useState<ChatMode>("fast");
<<<<<<< HEAD
  const [pipelineMode, setPipelineMode] = useState<PipelineMode>("qa");
=======
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
  const [streamDraft, setStreamDraft] = useState<{
    content: string;
    stage: string;
    statusMessage?: string;
    citations: Citation[];
    latencyMs?: ChatLatencyMs;
  } | null>(null);
  const chatAbortRef = useRef<AbortController | null>(null);
  const [uploading, setUploading] = useState(false);
  const [docTab, setDocTab] = useState<"all" | "pdf" | "docx">("all");
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [selectedCitation, setSelectedCitation] = useState<ChatCitation | null>(null);
  const [refiningId, setRefiningId] = useState<string | null>(null);
  const [userAv, setUserAv] = useState("U");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const refreshDocs = useCallback(async () => {
    try {
      const d = await apiJson<DocumentRow[]>(`/api/projects/${id}/documents/`);
      setDocs(d);
    } catch {
      /* ignore */
    }
  }, [id]);

  const refreshMessages = useCallback(async () => {
    try {
      const m = await apiJson<ChatMessage[]>(`/api/projects/${id}/chat/messages/`);
      setMessages(m);
    } catch {
      /* ignore */
    }
  }, [id]);

  const refreshProject = useCallback(async () => {
    try {
      const p = await apiJson<ProjectRow>(`/api/projects/${id}/`);
      setProject(p);
    } catch {
      setProject(null);
    }
  }, [id]);

  const refreshProjectList = useCallback(async () => {
    try {
      const list = await apiJson<ProjectRow[]>(`/api/projects/`);
      setProjects(list);
    } catch {
      setProjects([]);
    }
  }, []);

  useEffect(() => {
    setUserAv(initialsFromToken());
  }, []);

  useEffect(() => {
    if (!getAccessToken()) {
      router.replace("/login");
      return;
    }
    void refreshProject();
    void refreshProjectList();
    void refreshDocs();
    void refreshMessages();
    pollRef.current = setInterval(() => {
      void refreshDocs();
    }, 4000);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [id, router, refreshDocs, refreshMessages, refreshProject, refreshProjectList]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, sending, streamDraft?.content, streamDraft?.stage]);

  useEffect(() => {
    return () => {
      chatAbortRef.current?.abort();
    };
  }, []);

  const filteredDocs = docs.filter((d) => {
    if (docTab === "all") return true;
    if (docTab === "pdf") return isPdf(d.original_filename, d.mime_type);
    return isDocx(d.original_filename, d.mime_type);
  });

  const indexedCount = docs.filter((d) => d.status === "ready").length;

  const lastUpdatedIso = useMemo(
    () => docs[0]?.updated_at ?? project?.created_at ?? "",
    [docs, project?.created_at],
  );

  async function uploadFilesList(files: File[] | FileList | null) {
    const list = files == null ? [] : Array.from(files);
    if (list.length === 0) return;
    setUploading(true);
    try {
      for (const file of list) {
        await uploadDocument(id, file);
      }
      await refreshDocs();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const input = e.target;
    const picked = input.files?.length ? Array.from(input.files) : [];
    input.value = "";
    await uploadFilesList(picked);
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    void uploadFilesList(e.dataTransfer.files);
  }

  function onDragOver(e: React.DragEvent) {
    e.preventDefault();
  }

  function stopChatMessage() {
    chatAbortRef.current?.abort();
  }

<<<<<<< HEAD
  function onCitationSelect(c: ChatCitation) {
    setSelectedCitation(c);
    if (c.document_id) setSelectedDocId(c.document_id);
  }

  async function refineMessage(assistantMessageId: string) {
    if (refiningId || sending) return;
    setChatError(null);
    setSending(true);
    setRefiningId(assistantMessageId);
    setStreamDraft({ content: "", stage: "retrieve", citations: [] });
    chatAbortRef.current?.abort();
    const controller = new AbortController();
    chatAbortRef.current = controller;
    try {
      await streamRefineChat(
        id,
        assistantMessageId,
        {
          onStatus: (stage, message) => {
            setStreamDraft((prev) => (prev ? { ...prev, stage, statusMessage: message } : prev));
          },
          onToken: (content) => {
            setStreamDraft((prev) => (prev ? { ...prev, content: prev.content + content } : prev));
          },
          onDone: (payload) => {
            if (payload.error) setChatError(payload.error);
            setStreamDraft((prev) =>
              prev
                ? {
                    ...prev,
                    content: payload.answer || prev.content,
                    citations: payload.citations,
                    latencyMs: payload.latency_ms,
                    stage: "done",
                  }
                : prev,
            );
          },
          onError: (detail) => setChatError(detail),
        },
        { signal: controller.signal },
      );
      await refreshMessages();
    } catch (err) {
      if (err instanceof Error && err.name !== "AbortError") {
        setChatError(err instanceof Error ? err.message : "Refine failed");
      }
    } finally {
      setStreamDraft(null);
      setSending(false);
      setRefiningId(null);
      chatAbortRef.current = null;
    }
  }

  async function retryIngest(docId: string) {
    try {
      await retryDocument(id, docId);
      await refreshDocs();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Retry failed");
    }
  }

=======
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
  async function sendChatMessage() {
    const text = chatInput.trim();
    if (pipelineMode === "summarize" && !selectedDocId) {
      setChatError("Select a document in the sidebar for Summarize mode.");
      return;
    }
    if (!text && pipelineMode !== "summarize") return;
    if (sending) return;
    const userText = text || (pipelineMode === "summarize" ? "Summarize this document" : "");
    setChatError(null);
    setSending(true);
    setChatInput("");

    const optimisticUser: ChatMessage = {
      id: `tmp-user-${Date.now()}`,
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);
    setStreamDraft({ content: "", stage: "memory", citations: [] });

    chatAbortRef.current?.abort();
    const controller = new AbortController();
    chatAbortRef.current = controller;

    try {
      await streamProjectChat(
        id,
        userText,
        {
          onStatus: (stage, message) => {
            setStreamDraft((prev) => (prev ? { ...prev, stage, statusMessage: message } : prev));
          },
          onToken: (content) => {
            setStreamDraft((prev) => (prev ? { ...prev, content: prev.content + content } : prev));
          },
          onDone: (payload) => {
            if (payload.error) {
              setChatError(payload.error);
            }
            setStreamDraft((prev) =>
              prev
                ? {
                    ...prev,
                    content: payload.answer || prev.content,
                    citations: payload.citations,
                    latencyMs: payload.latency_ms,
                    stage: "done",
                  }
                : prev,
            );
          },
          onError: (detail) => {
            setChatError(detail);
          },
        },
<<<<<<< HEAD
        { signal: controller.signal, mode: chatMode, pipelineMode, documentId: selectedDocId },
=======
        { signal: controller.signal, mode: chatMode },
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
      );
      await refreshMessages();
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setMessages((prev) => prev.filter((m) => m.id !== optimisticUser.id));
        return;
      }
      setChatError(err instanceof Error ? err.message : "Chat failed");
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUser.id));
    } finally {
      setStreamDraft(null);
      setSending(false);
      chatAbortRef.current = null;
    }
  }

  async function triggerDocSummarize(docId: string) {
    try {
      await apiJson(`/api/projects/${id}/documents/${docId}/summarize/`, { method: "POST" });
      await refreshDocs();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Summarize failed");
    }
  }

  function pipelineTopKLabel(): string {
    if (pipelineMode === "literature_search") return chatMode === "fast" ? "lit 15" : "lit 25";
    if (pipelineMode === "synthesis") return chatMode === "fast" ? "syn 20" : "syn 40";
    if (pipelineMode === "summarize") return "all chunks";
    return chatMode === "fast" ? "top-k 3" : "top-k 10";
  }

  function pipelineHint(): string {
    switch (pipelineMode) {
      case "summarize":
        return "Select one document, then ask or send empty to summarize (uses ALL chunks).";
      case "literature_search":
        return "Explore themes and papers across your project.";
      case "synthesis":
        return "Multi-paper literature review synthesis.";
      default:
        return "Ask a specific question — grounded Q&A with citations.";
    }
  }

  function onComposerKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendChatMessage();
    }
  }

  async function exportChat() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(messages, null, 2));
    } catch {
      /* ignore */
    }
  }

  function docStatusRow(d: DocumentRow) {
    if (d.status === "failed") {
      return (
        <div className="flex flex-col gap-1" style={{ marginTop: 3 }}>
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="mock-sdot fail" />
            <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}>
              Failed{d.error_message ? ` · ${d.error_message.slice(0, 40)}` : ""}
            </span>
            <Button type="button" variant="ghost" size="xs" className="h-6 px-2 text-[10px]" onClick={(e) => { e.stopPropagation(); void retryIngest(d.id); }}>
              <RotateCcw className="size-3" />
              Retry
            </Button>
          </div>
        </div>
      );
    }
    if (d.status === "ready") {
      return (
        <div style={{ marginTop: 3 }}>
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="mock-sdot ready" />
            <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}>
              Indexed · {formatShortDate(d.updated_at)}
              {d.chunk_count != null ? ` · ${d.chunk_count} chunks` : ""}
              {d.summary_status && d.summary_status !== "none" ? ` · summary ${d.summary_status}` : ""}
            </span>
            <Button
              type="button"
              variant="ghost"
              size="xs"
              className="h-6 px-2 text-[10px]"
              onClick={(e) => {
                e.stopPropagation();
                void triggerDocSummarize(d.id);
              }}
            >
              Summarize
            </Button>
          </div>
        </div>
      );
    }
    const progress = d.ingestion_progress ?? (d.status === "pending" ? 5 : 25);
    return (
      <>
        <div className="ingest-pbar">
          <div className="ingest-pbar-fill" style={{ width: `${Math.min(100, progress)}%` }} />
        </div>
        <div style={{ display: "flex", alignItems: "center", marginTop: 3, gap: 6 }}>
          <span className="mock-sdot proc" />
          <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}>
            {d.ingestion_stage || (d.status === "pending" ? "Queued…" : "Processing…")} · {progress}%
          </span>
        </div>
      </>
    );
  }

  function docMetaLine(d: DocumentRow): string {
    const pages = d.page_count != null ? `${d.page_count} pages` : "—";
    if (d.status === "ready") return pages;
    if (d.status === "processing") return `${pages} · indexing…`;
    return pages;
  }

  return (
    <div className="arxiv-mock arxiv-app-shell">
      <h2 className="mock-sr">Project workspace: documents and chat with citations</h2>

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        multiple
        hidden
        onChange={onUpload}
        disabled={uploading}
      />

      <ArxivTopBar userInitials={userAv} />

      <div className="app-proj-hdr">
        <div>
          <div className="app-proj-title">{project?.name ?? "…"}</div>
          <div className="app-proj-meta">
            {indexedCount} indexed · {docs.length} documents · updated {lastUpdatedIso ? formatShortDate(lastUpdatedIso) : "—"}
          </div>
        </div>
        <div className="app-hdr-acts flex gap-2">
          <Button type="button" variant="outline" size="sm" asChild>
            <Link href={`/projects/${id}/demo`}>
              <FlaskConical className="size-3.5" />
              Fast vs Deep
            </Link>
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            <Upload className="size-3.5" />
            {uploading ? "Uploading…" : "Upload"}
          </Button>
          <Button type="button" size="sm" onClick={() => void exportChat()}>
            <Download className="size-3.5" />
            Export chat
          </Button>
        </div>
      </div>

      <div className="mock-ws flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="mock-ws-grid min-h-0 flex-1">
          <aside className="mock-ws-side">
            <div className="mock-side-lbl">Projects</div>
            <Link href="/projects" className="mock-new-dash">
              <span style={{ color: "var(--color-accent)" }}>+</span> New project
            </Link>
            {projects.map((p, i) => (
              <Link key={p.id} href={`/projects/${p.id}`} className={`mock-proj-row ${p.id === id ? "is-active" : ""}`}>
                <span className="mock-proj-ico">{PROJECT_EMOJIS[i % PROJECT_EMOJIS.length]}</span>
                <span className="mock-proj-name">{p.name}</span>
                <span className="mock-proj-cnt">{p.id === id ? docs.length : "—"}</span>
              </Link>
            ))}
            <div style={{ height: 0.5, background: "var(--color-border)", margin: "8px 12px" }} />
            <div style={{ padding: "8px 12px", marginTop: "auto", display: "flex", flexDirection: "column", gap: 6 }}>
              <Link
                href="/projects"
                style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--color-accent)", textDecoration: "none", padding: "4px 0" }}
              >
                All projects
              </Link>
            </div>
          </aside>

          <div className="mock-ws-docs">
            <div className="mock-doc-ph flex items-center gap-1.5">
              <span className="flex-1 text-xs font-medium">Documents</span>
              {(["all", "pdf", "docx"] as const).map((tab) => (
                <Button
                  key={tab}
                  type="button"
                  variant={docTab === tab ? "secondary" : "ghost"}
                  size="xs"
                  className="h-6 px-2 text-[10px] uppercase"
                  onClick={() => setDocTab(tab)}
                >
                  {tab}
                </Button>
              ))}
            </div>

            <div
              className="mock-drop"
              role="button"
              tabIndex={0}
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
              onDrop={onDrop}
              onDragOver={onDragOver}
            >
              <div>
                <strong>Drop files here</strong> or click to upload
              </div>
              <div style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-muted)", marginTop: 4 }}>PDF · DOCX — max 50 MB each</div>
            </div>

            <div className="mock-doc-scroll">
              {filteredDocs.length === 0 ? (
                <div style={{ padding: 12, fontSize: 11, color: "var(--color-text-muted)", textAlign: "center" }}>No documents in this filter.</div>
              ) : (
                filteredDocs.map((d) => {
                  const pdf = isPdf(d.original_filename, d.mime_type);
                  return (
                    <div
                      key={d.id}
                      className={`mock-doc-item ${selectedDocId === d.id ? "is-sel" : ""}`}
                      aria-selected={selectedDocId === d.id}
                      onClick={() => setSelectedDocId(d.id === selectedDocId ? null : d.id)}
                    >
                      <div className={`mock-dtype ${pdf ? "pdf" : "docx"}`}>{pdf ? "PDF" : "DOCX"}</div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 11, fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.original_filename}</div>
                        <div className="mock-doc-meta">{docMetaLine(d)}</div>
                        {docStatusRow(d)}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <DocumentExcerptPanel
              projectId={id}
              citation={selectedCitation}
              onClose={() => setSelectedCitation(null)}
            />
          </div>

          <div className="mock-ws-chat flex min-h-0 flex-col">
            <div className="mock-chat-hdr">
              <span>Chat</span>
<<<<<<< HEAD
              <PipelineModeDropdown
                pipelineMode={pipelineMode}
                chatMode={chatMode}
                topKLabel={pipelineTopKLabel()}
                disabled={sending}
                onPipelineChange={setPipelineMode}
                onChatModeChange={setChatMode}
              />
            </div>
            <div className="mock-chat-hint border-b px-3 py-2">
              <Badge variant="outline" className="max-w-full truncate font-mono text-[10px] font-normal">
                {pipelineHint()}
              </Badge>
=======
              <div className="mock-set-nav" style={{ marginLeft: "auto", marginRight: 8 }}>
                <button
                  type="button"
                  className={chatMode === "fast" ? "is-on" : ""}
                  onClick={() => setChatMode("fast")}
                  disabled={sending}
                  title="Fast mode: fewer chunks, lower latency"
                >
                  Fast
                </button>
                <button
                  type="button"
                  className={chatMode === "deep" ? "is-on" : ""}
                  onClick={() => setChatMode("deep")}
                  disabled={sending}
                  title="Deep mode: more context, slower"
                >
                  Deep
                </button>
              </div>
              <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}>
                {chatMode === "fast" ? "top-k 3" : "top-k 10"}
              </span>
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
            </div>

            <ScrollArea className="mock-chat-scroll">
              <div className="chat-thread">
              {messages.length === 0 && !sending ? (
                <div className="py-6 text-center text-xs text-muted-foreground">
                  Upload documents, then ask a question. Answers include citations when sources are found.
                </div>
              ) : null}

              {messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.id} className="mock-msg user">
                    <div className="mock-mav user">{userAv}</div>
                    <div className="mock-mbody">
                      <div className="mock-mmeta">{formatTime(m.created_at)}</div>
                      <ChatMessageBody content={m.content} variant="user" />
                    </div>
                  </div>
                ) : (
                  <div key={m.id} className="mock-msg ai-full">
                    <div className="mock-mav ai">A</div>
                    <div className="mock-mbody">
                      <div className="mock-mmeta flex flex-wrap items-center gap-2">
                        <span>
                          Arxiv · {formatTime(m.created_at)} · {m.citations?.length ?? 0} sources
                          {m.meta?.refined ? " · refined" : m.meta?.mode === "fast" ? " · fast" : m.meta?.mode === "deep" ? " · deep" : ""}
                        </span>
                        {m.meta?.mode === "fast" && !m.meta?.refined && pipelineMode === "qa" ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="xs"
                            className="h-6 text-[10px]"
                            disabled={sending}
                            onClick={() => void refineMessage(m.id)}
                          >
                            <Sparkles className="size-3" />
                            Refine with Deep
                          </Button>
                        ) : null}
                      </div>
                      <ChatMessageBody content={m.content} variant="ai" />
                      <ChatCitations
                        citations={m.citations ?? []}
                        selectedChunkId={selectedCitation?.chunk_id}
                        onSelectCitation={onCitationSelect}
                      />
                    </div>
                  </div>
                ),
              )}

              {sending && streamDraft ? (
                <div className="mock-msg ai-full">
                  <div className="mock-mav ai">A</div>
                  <div className="mock-mbody">
                    <div className="mock-mmeta">
                      Arxiv · {chatStageLabel(streamDraft.stage, streamDraft.statusMessage)}
                      {streamDraft.citations.length > 0 ? ` · ${streamDraft.citations.length} sources` : ""}
                      {streamDraft.latencyMs ? ` · ${formatLatencySummary(streamDraft.latencyMs)}` : ""}
                    </div>
                    {streamDraft.content ? (
                      <ChatMessageBody content={streamDraft.content} variant="ai" />
                    ) : (
                      <div className="mock-thinker">
                        <div className="mock-td" />
                        <div className="mock-td" />
                        <div className="mock-td" />
                      </div>
                    )}
                    <ChatCitations
                      citations={streamDraft.citations}
                      defaultOpen={streamDraft.stage === "done"}
                      selectedChunkId={selectedCitation?.chunk_id}
                      onSelectCitation={onCitationSelect}
                    />
                  </div>
                </div>
              ) : null}

              <div ref={chatEndRef} />
              </div>
            </ScrollArea>

            <div className="mock-inp-area border-t bg-background/80 p-3 backdrop-blur-sm">
              <div className="chat-composer">
              {chatError ? <p className="mb-2 font-mono text-xs text-destructive">{chatError}</p> : null}
              <div className="flex items-end gap-2">
                <Textarea
                  className="min-h-[44px] max-h-[180px] resize-none text-sm shadow-xs"
                  rows={1}
                  placeholder="Ask a question about your documents…"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={onComposerKeyDown}
                  disabled={sending}
                />
                {sending ? (
<<<<<<< HEAD
                  <Button type="button" variant="outline" size="sm" onClick={stopChatMessage}>
                    <Square className="size-3.5 fill-current" />
                    Stop
                  </Button>
                ) : null}
                <Button
                  type="button"
                  size="icon"
                  aria-label="Send"
                  disabled={sending || (!chatInput.trim() && pipelineMode !== "summarize")}
                  onClick={() => void sendChatMessage()}
                >
                  <Send className="size-4" />
                </Button>
=======
                  <button type="button" className="mock-btn-ghost" style={{ flexShrink: 0, padding: "6px 10px" }} onClick={stopChatMessage}>
                    Stop
                  </button>
                ) : null}
                <button type="button" className="mock-snd" aria-label="Send" disabled={sending || !chatInput.trim()} onClick={() => void sendChatMessage()}>
                  <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="2" y1="14" x2="14" y2="2" />
                    <polyline points="6 2 14 2 14 10" />
                  </svg>
                </button>
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
              </div>
              <div className="mt-2 flex items-center justify-between text-[10px] font-mono text-muted-foreground">
                <span>⏎ send · shift+⏎ newline</span>
                <div className="flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-primary" />
                  <span>Searching: {project?.name ?? "this project"}</span>
                </div>
              </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
