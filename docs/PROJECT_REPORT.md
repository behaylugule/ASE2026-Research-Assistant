# Real-Time Interactive Academic Research Assistant with RAG and Citations

**ASE2026 — Advanced Software Engineering Project Report**

| | |
|---|---|
| **Author** | *Behaylu Gebrekidan* |
| **Course** | ASE2026 |
| **Date** | June 2026 |
| **Repository** | ASE2026 |

---

## Abstract

The volume of academic publications has made literature review increasingly time-consuming, while many AI assistants produce answers without verifiable sources. This project implements a **Retrieval-Augmented Generation (RAG)** platform that lets researchers upload PDF and DOCX documents, ask questions in natural language, and receive **streaming, citation-grounded** responses. The system supports four pipeline modes—Q&A, full-document Summarize, Literature search, and multi-paper Synthesis—and offers **Fast** and **Deep** retrieval settings to trade latency against thoroughness. Built with Django REST, Celery, PostgreSQL with pgvector, and a Next.js frontend, the platform demonstrates how interactive research workflows can combine generative AI with source traceability. Evaluation on project **AI in Health Care** (3 PDFs, 193 chunks) shows Fast Q&A in ~2–4 s with three citations versus Deep with ten citations at comparable latency; Literature and Synthesis modes run in ~5–11 s with 15–40 citations depending on depth; full-document Summarize takes ~45 s–4 min depending on PDF size.

**Keywords:** RAG, academic research assistant, citations, pgvector, streaming LLM, literature review

---

## 1. Introduction

The rapid growth of academic publications has made it increasingly difficult for researchers and students to efficiently locate, analyze, and synthesize relevant information. Traditional research methods require extensive manual effort to search for papers, evaluate their relevance, and extract key insights. While recent advances in artificial intelligence have introduced tools to assist with these tasks, many systems lack reliability—often generating responses without verifiable sources or producing inaccurate information.

This project addresses these challenges by building an **AI-powered academic research assistant** based on a RAG architecture. Unlike generic chatbots, the system restricts answers to **user-uploaded documents**, attaches **inline citations** with page numbers, and optimizes for **real-time interaction** through server-sent event (SSE) streaming and a Fast mode with reduced retrieval depth.

### 1.1 Contributions

Beyond the original project proposal, this implementation adds:

1. **Four specialized pipeline modes** for distinct research tasks (fact lookup, single-paper summary, cross-paper exploration, literature synthesis).
2. **Fast vs Deep modes** with configurable top-k retrieval and measurable latency tradeoffs.
3. **Streaming UX** with pipeline stage feedback (embed → retrieve → generate) and time-to-first-token metrics.
4. **Citation precision** including per-chunk snippets, character offsets, and click-to-highlight excerpt panels.
5. **Two-phase refinement** — users can upgrade a Fast Q&A draft with a Deep refine pass on demand.

---

## 2. Related Work

**Retrieval-Augmented Generation (RAG)** [Lewis et al., 2020] combines dense retrieval with large language models to ground generation in external documents. This project applies RAG in a project-scoped academic setting rather than open-web search.

**Academic research tools** such as Semantic Scholar, Elicit, and Connected Papers focus on discovery across published corpora. Our system complements these by operating on a **private document library** per project—useful for course readings, thesis bibliographies, or confidential drafts.

**Citation-grounded QA** systems (e.g., Perplexity, Bing Chat) provide source links but often search the public web. We enforce grounding through prompt design, retrieval scope, and explicit "not found" responses when excerpts do not support an answer.

**Interactive LLM applications** increasingly use streaming to improve perceived latency. Our design explicitly targets **time-to-first-response** as a first-class metric, aligning with professor feedback that research chat should feel conversational, not batch-oriented.

---

## 3. Problem Statement

Researchers face three interrelated problems:

1. **Information overload** — too many papers to read in available time.
2. **Untrusted AI outputs** — hallucinated facts and missing citations limit academic use.
3. **Slow AI UX** — systems that prioritize answer perfection over interaction speed disrupt research flow.

### 3.1 Requirements

**Functional requirements**

- User registration and JWT authentication
- Project-scoped document upload (PDF, DOCX)
- Async ingestion: extract → chunk → embed → index
- Chat with streaming responses and history
- Automatic inline citations
- Multiple research modes (Q&A, summarize, literature, synthesis)

**Non-functional requirements**

- Sub-10 s response for Fast Q&A on warm queries
- Verifiable source tracing (document name, page, excerpt)
- Horizontal scalability via worker queue
- CPU-only deployment (no GPU required for embeddings)

---

## 4. Proposed Solution (Proposal Alignment)

The original proposal specified an RAG-based platform with document retrieval, grounded generation, automatic citations, and a scalable backend. Table 1 maps each proposal objective to the implementation.

**Table 1 — Proposal objectives vs implementation**

| Proposal objective | Implementation |
|--------------------|----------------|
| Reduce research time | Fast mode (k=3), SSE streaming, async Celery ingestion |
| Improve accuracy | RAG with project-scoped vector retrieval; no open-web hallucination |
| Ensure scalability | Docker Compose stack; Celery workers; HNSW pgvector index |
| Enhance trust via citations | Inline `[Doc – Page N]`; Sources panel; excerpt highlight API |

The solution integrates document retrieval with generative AI to provide accurate, context-aware, and source-grounded responses within a project workspace.

---

## 5. System Architecture

Figure 1 (see [ARCHITECTURE.md](./ARCHITECTURE.md)) shows the high-level components:

- **Next.js frontend** — auth, project workspace, document list, streaming chat, citation panel
- **Django REST API** — JWT auth, project/document CRUD, chat and SSE endpoints
- **Celery worker** — background ingestion and full-document summarize jobs
- **PostgreSQL + pgvector** — relational data and 384-dimensional embeddings with HNSW cosine index
- **Redis** — Celery broker
- **sentence-transformers** — local CPU embeddings (`all-MiniLM-L6-v2`)
- **OpenAI Chat API** — answer generation (`gpt-4o-mini`)

### 5.1 Data model

- **Project** — container for documents and chat; user-isolated
- **Document** — uploaded file with status (`pending` → `processing` → `ready` / `failed`)
- **DocumentChunk** — text segment with embedding, page number, chunk index, metadata
- **ChatMessage** — user/assistant turns with citations JSON and mode metadata

### 5.2 Security

All project routes require JWT authentication and project membership. Retrieval queries filter by `project_id` and `document.status = ready`, preventing access to incomplete or other users' data.

---

## 6. Methodology — RAG Pipeline

### 6.1 Ingestion

1. User uploads PDF or DOCX (max 50 MB)
2. Celery task extracts text per page
3. Text is split into chunks of 300–500 tokens (`cl100k_base` tokenizer)
4. Each chunk is embedded with `all-MiniLM-L6-v2` (normalized vectors, 384 dims)
5. Chunks stored in `DocumentChunk` with HNSW index for cosine similarity search

### 6.2 Query processing (Q&A mode)

1. **Memory** — load recent chat history (Fast: 6 turns, Deep: 20 turns)
2. **Embed** — enhance query for retrieval heuristics, embed with same model
3. **Retrieve** — pgvector cosine search, top-k chunks, project-scoped
4. **Aggregate** — group excerpts by document with page labels
5. **Generate** — system prompt + context + history → OpenAI chat
6. **Cite** — build citation list from retrieved chunks (snippet, offsets, chunk_id)
7. **Persist** — save user and assistant messages

Overview and character-style queries merge intro/early-page chunks with vector results to improve recall for broad questions.

### 6.3 Prompt design

The Q&A system prompt instructs the model to:

- Answer only from retrieved excerpts and conversation history
- Provide partial answers when excerpts are relevant but incomplete
- Respond exactly **"Not found in the provided documents."** only when context truly lacks support
- Add inline citations in the form `[DocumentName – Page N]`

---

## 7. Pipeline Modes

Detailed user guide: [PIPELINE_MODES.md](./PIPELINE_MODES.md)

### 7.1 Q&A (`qa`)

Answers specific questions using top-k vector retrieval. Best for fact lookup, definitions, methods, and follow-ups. Fast: k=3; Deep: k=10.

### 7.2 Summarize (`summarize`)

Hierarchical map-reduce over **all chunks** of one selected document. Produces structured sections: Objective, Methodology, Key Findings, Limitations, Conclusion. Runs asynchronously via Celery for long documents.

### 7.3 Literature search (`literature_search`)

Exploration report across all project documents. Output sections: Thematic clusters, Paper-level summaries, Key insights. Fast: k=15; Deep: k=25.

### 7.4 Synthesis (`synthesis`)

Multi-paper literature review style output: themed sections, Agreements, Contradictions, Conclusion. Fast: k=20; Deep: k=40.

**Table 2 — Mode selection guide**

| Research goal | Recommended mode |
|---------------|------------------|
| "What page says X?" | Q&A |
| "Summarize this PDF" | Summarize |
| "What do I have on topic Y?" | Literature |
| "Write related work for topic Z" | Synthesis |

---

## 8. Implementation Highlights

### 8.1 Streaming chat (SSE)

`POST /api/projects/{id}/chat/stream/` returns `text/event-stream` events:

| Event | Payload |
|-------|---------|
| `status` | Pipeline stage and human-readable message |
| `token` | Answer text delta |
| `done` | Full answer, citations, `message_id`, `latency_ms` |

The frontend uses `fetch` + `ReadableStream` (not `EventSource`) to support JWT headers and JSON request bodies.

### 8.2 Fast vs Deep

| Parameter | Fast | Deep |
|-----------|------|------|
| Q&A top-k | 3 | 10 |
| History limit | 6 | 20 |
| Literature top-k | 15 | 25 |
| Synthesis top-k | 20 | 40 |

Reranking was intentionally removed to reduce latency and API cost.

### 8.3 Citation precision

Each citation includes: `document_name`, `document_id`, `page_number`, `chunk_id`, `snippet`, `char_start`, `char_end`. The frontend fetches full chunk text via `GET /api/projects/{id}/chunks/{chunk_id}/` for highlight rendering.

### 8.4 Refine with Deep

After a Fast Q&A answer, users can trigger `POST /api/projects/{id}/chat/refine/stream/` to regenerate with Deep retrieval without re-asking the question.

---

## 9. Evaluation

Benchmarks were run on project **AI in Health Care** (3 indexed PDFs, 193 chunks). Queries and citation counts from saved chat history; latency from warm `/chat/benchmark/` runs. See [EVALUATION_RESULTS.md](./EVALUATION_RESULTS.md) for full tables.

**Table 3 — Q&A (chat queries + benchmark latency)**

| Query | Fast (ms) | Deep (ms) | Fast citations | Deep citations |
|-------|----------:|----------:|---------------:|---------------:|
| what is the problem statment | 2,005 | 2,249 | 3 | 10 |
| What are the Solutions | 2,005 | 4,400 | 3 | 10 |
| What methodology is described? | 3,376 | 3,803 | 3 | 10 |

**Table 4 — Literature search**

| Query | Fast (ms) | Deep (ms) | Fast citations | Deep citations |
|-------|----------:|----------:|---------------:|---------------:|
| What themes appear across these papers? | 5,047 | 6,644 | 15 | 25 |
| What are the main findings across my uploaded papers? | 8,564 | 10,654 | 15 | 25 |

**Table 5 — Synthesis**

| Query | Fast (ms) | Deep (ms) | Fast citations | Deep citations |
|-------|----------:|----------:|---------------:|---------------:|
| Compare agreements and contradictions on methodology | 6,225 | 7,342 | 20 | 40 |

**Table 6 — Summarize (single document, all chunks)**

| Document | Chunks | Latency (ms) |
|----------|-------:|-------------:|
| EPF AI in healthcare brief | 17 | 45,273 |
| R48319.1 | 67 | 158,805 |
| 9a31d8af-en | 109 | 263,353 |

**Findings**

- **Fast Q&A** delivers interactive responses (~2–4 s warm) with 3 citations for quick checks.
- **Deep Q&A** retrieves 3× more chunks (10 vs 3 citations) at similar latency on short answers.
- **Literature / Synthesis** scale with corpus size; Deep adds citations (25 vs 15, 40 vs 20) with modest latency increase on 3 papers.
- **Summarize** latency grows with document size (~45 s for 17 chunks up to ~4 min for 109 chunks).
- **Cold start** (first embed after restart) can add ~10 s; mitigated by embedding warm-up on backend startup.

Qualitative trust checks: citations map to real uploaded pages; unsupported questions return the exact not-found phrase; citation clicks open highlighted excerpts.

---

## 10. Demo Script

Recommended presentation flow:

1. Register/login → create project → upload PDFs → wait for **Indexed**
2. Q&A (Fast): *what is the problem statment* — show streaming and citations
3. Follow-up: *What are the Solutions* — compare Fast vs Deep citation count
4. Click citation — show excerpt highlight panel
5. Literature (Fast): *What themes appear across these papers?*
6. Synthesis (Deep): *Compare agreements and contradictions on methodology*
7. Select one PDF → Summarize → show structured output

Benchmark UI: `http://localhost:3000/projects/{id}/demo`

Presentation slides: [PRESENTATION.md](./PRESENTATION.md)

---

## 11. Limitations

1. **Scope** — searches only uploaded project documents, not external databases.
2. **Ingestion quality** — depends on PDF text extraction; scanned images require OCR (not implemented).
3. **API dependency** — generation requires OpenAI API key and network access.
4. **Evaluation** — benchmark is qualitative/small-scale; no formal user study or citation-precision audit.
5. **Summarize latency** — proportional to document length; not suitable for real-time chat.

---

## 12. Future Work

- Production hardening (HTTPS, secrets management, monitoring)
- Full PDF page viewer with scroll-to-page
- Formal evaluation: citation precision@k, user task-completion study
- Hybrid retrieval (BM25 + dense vectors)
- Optional cross-encoder reranking in Deep mode only
- Multi-tenant deployment and team-shared projects

---

## 13. Conclusion

This project delivers an AI-powered academic research assistant that fulfills and extends the original proposal. By combining RAG with streaming interaction, four specialized pipeline modes, and verifiable citations, the system demonstrates how generative AI can support academic workflows without sacrificing trust or responsiveness. The Fast/Deep tradeoff provides a practical pattern for balancing latency and thoroughness in research tools.

The implementation is available as open source in the ASE2026 repository, with Docker Compose for reproducible deployment and documentation for pipeline modes, architecture, and evaluation.

---

## References

1. Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS.
2. Johnson, J., Douze, M., & Jégou, H. (2019). *Billion-scale similarity search with GPUs.* IEEE Transactions on Big Data (HNSW).
3. Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP.
4. pgvector — Open-source vector similarity search for PostgreSQL. https://github.com/pgvector/pgvector
5. LangChain / LangGraph — LLM application framework. https://langchain.com

---

## Appendix A — API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/token/` | Obtain JWT |
| GET/POST | `/api/projects/` | List/create projects |
| POST | `/api/projects/{id}/documents/` | Upload PDF/DOCX |
| POST | `/api/projects/{id}/chat/stream/` | Streaming chat (all modes) |
| POST | `/api/projects/{id}/chat/benchmark/` | Fast vs Deep comparison |
| POST | `/api/projects/{id}/chat/refine/stream/` | Deep refine of Fast answer |
| GET | `/api/projects/{id}/chunks/{chunk_id}/` | Chunk text for citation highlight |

Full API table: [README.md](../README.md)

---

## Appendix B — Export to PDF

**Recommended (POPL / ACM SIGPLAN format):** use the LaTeX paper in [docs/paper/](paper/main.tex):

- **Ready PDF:** [docs/paper/main.pdf](paper/main.pdf) or [PROJECT_REPORT.pdf](../PROJECT_REPORT.pdf) at repo root
- **Edit source:** [docs/paper/main.tex](paper/main.tex) — replace `Your Name` and email
- **Compile:** see [docs/paper/README.md](paper/README.md) (Overleaf or Docker)

**Markdown fallback:**

```bash
pandoc docs/PROJECT_REPORT.md -o PROJECT_REPORT.pdf --metadata title="ASE2026 Project Report"
# Requires a PDF engine (pdflatex, wkhtmltopdf, etc.)
```

---

*Replace [Your Name] and [Date] before submission.*
