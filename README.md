
## Task list (status)

### Completed — core platform

- [x] Django backend (DRF) with JWT auth (`/api/auth/*`)
- [x] Project CRUD (`/api/projects/*`) with per-user project isolation
- [x] Document upload/list/delete endpoints (`/api/projects/{id}/documents/*`)
- [x] Async ingestion (Celery + Redis): extract PDF/DOCX → chunk (300–500 tokens) → embed → store chunks + metadata
- [x] PostgreSQL + pgvector storage for chunks/embeddings + relational entities
- [x] Docker Compose stack: `db`, `redis`, `backend`, `worker`, `frontend`
- [x] CPU-only PyTorch in Docker (no NVIDIA/CUDA required)
- [x] LangGraph RAG pipeline: load memory → embed query → project-scoped cosine retrieval → multi-doc aggregation → generate → citations → save memory
- [x] Chat API + history (`/api/projects/{id}/chat/*`)
- [x] Next.js UI (auth, projects, upload/status, chat with citations)
- [x] Dark theme support (default: light) with UI toggle
- [x] Home route redirect: `/` → `/login` if unauthenticated, otherwise `/projects`
- [x] Upload fixes:
  - [x] Increased `Document.file` max length (avoids `SuspiciousFileOperation`)
  - [x] Fixed tokenizer selection for chunking (`encoding_name="cl100k_base"`)

### Completed — real-time interaction (project focus)

Professor feedback: optimize for **fast, interactive research chat** instead of slow “wait for perfect answer” UX.

- [x] **SSE streaming chat** — token-by-token answers (`POST /api/projects/{id}/chat/stream/`)
- [x] **Removed rerank step** — lower latency, no cross-encoder cost
- [x] **Fast vs Deep chat modes** — `{ "mode": "fast" | "deep" }` on chat endpoints
  - Fast: `FAST_RETRIEVE_TOP_K=3`, shorter history (`FAST_CHAT_HISTORY_LIMIT=6`)
  - Deep: `DEEP_RETRIEVE_TOP_K=10`, full history (`CHAT_HISTORY_LIMIT=20`)
- [x] **Latency metrics in SSE `done` event** — `ttft`, `pregenerate`, `total` (milliseconds)
- [x] **Rich status messages** during pipeline (`Found N excerpts…`, etc.)
- [x] **UI: Fast/Deep toggle**, live stage text, latency summary, **Stop** button (abort stream)
- [x] **HNSW pgvector index** on `DocumentChunk.embedding` (migration `0002_hnsw_embedding_index`)
- [x] **Embedding model warm-up** on backend startup (reduces first-query cold start)
- [x] **Four pipeline modes** via `pipeline_mode` on chat + dedicated endpoints:
  - **Q&A RAG** (`qa`) — strict top-k retrieval, citations, no full-doc traversal
  - **Full document summarize** (`summarize`) — map-reduce over ALL chunks (hierarchical)
  - **Literature search** (`literature_search`) — explore project docs by relevance
  - **Multi-paper synthesis** (`synthesis`) — literature-review style cross-doc synthesis

### Remaining

All core items below are implemented. Optional polish for production:

- [ ] Production `SECRET_KEY` ≥ 32 bytes (see `.env.example`)
- [ ] PDF viewer with true page scroll (current: excerpt panel + highlight)
- [ ] Benchmark runs save chat history — use a dedicated eval project if you want a clean transcript

### Recently completed

- [x] Citation precision — per-chunk snippets, `char_start`/`char_end`, `document_id`, chunk API
- [x] Auto JWT refresh on 401 (`authFetch` in frontend)
- [x] Ingestion monitoring — progress %, stage label, retry failed uploads
- [x] Citation click → excerpt panel with highlight in document column
- [x] Two-phase answer — **Refine with Deep** on Fast Q&A replies
- [x] Demo page — `/projects/{id}/demo` Fast vs Deep side-by-side benchmark
- [x] Project edit — rename (PATCH) and delete from projects list and workspace sidebar

See also [Pipeline modes guide](docs/PIPELINE_MODES.md).

## Submission materials (paper & presentation)

| Document | Purpose |
|----------|---------|
| [docs/PROJECT_REPORT.md](docs/PROJECT_REPORT.md) | Full project report / paper (Markdown) |
| [docs/paper/main.tex](docs/paper/main.tex) | **ACM SIGPLAN paper** (POPL-style — export PDF via Overleaf) |
| [docs/paper/README.md](docs/paper/README.md) | How to compile the LaTeX paper to PDF |
| [docs/PRESENTATION.md](docs/PRESENTATION.md) | Slide deck (Marp — export to PDF/PPTX) |
| [docs/PRESENTATION_QA.md](docs/PRESENTATION_QA.md) | **Q&A prep** — likely professor questions with answers |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture diagrams (Mermaid) |
| [docs/EVALUATION_RESULTS.md](docs/EVALUATION_RESULTS.md) | Fast vs Deep benchmark tables |

**Before submitting:** replace `[Your Name]` in the report and presentation.

**Export slides:** install [Marp for VS Code](https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode), open `docs/PRESENTATION.md`, export to PDF or PowerPoint.

**Export paper:**

```bash
pandoc docs/PROJECT_REPORT.md -o PROJECT_REPORT.pdf --metadata title="ASE2026 Project Report"
```




# ASE2026 — Real-Time Academic Research Assistant

### Title

Real-Time Interactive Academic Research Assistant with RAG and Citations

### Project angle

Most research assistants optimize for answer quality at the cost of speed. This project optimizes for **time-to-first-response** and **continuous conversation flow**: users get immediate pipeline feedback, streaming tokens, and a **Fast mode** for low-latency interaction while researching.

### 1. Introduction

The rapid growth of academic publications has made it increasingly difficult for researchers and students to efficiently locate, analyze, and synthesize relevant information. Traditional research methods require extensive manual effort to search for papers, evaluate their relevance, and extract key insights. While recent advances in artificial intelligence have introduced tools to assist with these tasks, many of these systems lack reliability, often generating responses without verifiable sources or producing inaccurate information.

### 2. Problem Statement

The primary problem addressed in this project is the inefficiency and lack of trust in current academic research workflows. Researchers face information overload due to the vast number of available academic papers. The process of reviewing and summarizing literature is time-consuming and labor-intensive. Existing AI-based tools often produce unreliable or non-cited responses, limiting their usefulness in academic contexts.

### 3. Proposed Solution

This project proposes an AI-powered academic research assistant based on a Retrieval-Augmented Generation (RAG) architecture. The system integrates document retrieval with generative AI to provide accurate, context-aware, and source-grounded responses. It includes retrieval of relevant documents, grounded answer generation, automatic citations, and a scalable backend.

### 4. Objectives

The objectives are to reduce research time, improve accuracy of AI-generated responses, ensure scalability, and enhance user trust through verifiable citations.

### 5. Methodology

The system will use a RAG pipeline including data ingestion, embedding and indexing, retrieval, generation, and a user interface. A scalable architecture ensures performance and reliability.

### 6. Expected Outcomes

The system is expected to reduce research time, improve trust in AI outputs, enhance academic workflows, and demonstrate the effectiveness of RAG in research applications.

### 7. Conclusion

This project combines retrieval and generative AI to address challenges in academic research, ensuring outputs are grounded in real sources and improving both efficiency and reliability.


Django REST API, Celery workers, PostgreSQL + pgvector, and a Next.js UI for project-scoped document chat with retrieval, streaming, and citations.

## Prerequisites

- Docker and Docker Compose
- Node.js 20+ (optional, only if running Next.js outside Docker)

## Quick start

1. Copy environment files:

   ```bash
   cp .env.example .env
   cp frontend/.env.local.example frontend/.env.local
   ```

2. Set `OPENAI_API_KEY` in `.env` for chat answers (embeddings use local `sentence-transformers` models on first run).

3. Start the stack:

   ```bash
   docker compose up --build
   ```

   The backend image installs **CPU-only PyTorch** from [download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu), so no NVIDIA GPU drivers or CUDA wheels are required on your machine.

   - API: `http://localhost:8000` (Postgres and Redis are **not** published to the host by default; only the API port is mapped.)
   - Health: `http://localhost:8000/health/`
   - Admin: `http://localhost:8000/admin/` (create a superuser with `docker compose exec backend python manage.py createsuperuser`)
   - Frontend: `http://localhost:3000`

4. Optional: run the frontend locally instead of Docker:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

   Open `http://localhost:3000` (ensure `NEXT_PUBLIC_API_URL` points at your backend).

## API overview (Completed)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register/` | Register `{ username, email, password }` |
| POST | `/api/auth/token/` | JWT `{ username, password }` |
| POST | `/api/auth/token/refresh/` | Refresh token |
| GET/POST | `/api/projects/` | List / create projects |
| GET/PATCH/DELETE | `/api/projects/{id}/` | Project detail / **edit name** / delete |
| GET/POST | `/api/projects/{id}/documents/` | List / upload PDF or DOCX |
| GET/DELETE | `/api/projects/{id}/documents/{doc_id}/` | Document detail / delete |
| POST | `/api/projects/{id}/chat/` | `{ "message", "mode", "pipeline_mode", "document_id?" }` — JSON response |
| POST | `/api/projects/{id}/chat/stream/` | Same body — **SSE** stream (`status` → `token` → `done`) |
| POST | `/api/projects/{id}/literature-search/` | `{ "query", "mode" }` — exploration report |
| POST | `/api/projects/{id}/synthesis/` | `{ "query", "mode" }` — multi-paper synthesis |
| POST | `/api/projects/{id}/documents/{doc_id}/summarize/` | Start async full-document summarize (Celery) |
| GET | `/api/projects/{id}/documents/{doc_id}/summary/` | Stored hierarchical summary |
| POST | `/api/projects/{id}/documents/{doc_id}/retry/` | Re-queue failed/pending ingestion |
| GET | `/api/projects/{id}/chunks/{chunk_id}/` | Full chunk text for citation highlight |
| POST | `/api/projects/{id}/chat/refine/stream/` | `{ "assistant_message_id" }` — Deep refine SSE |
| POST | `/api/projects/{id}/chat/benchmark/` | `{ "query", "pipeline_mode" }` — Fast vs Deep comparison |
| GET | `/api/projects/{id}/chat/messages/` | Chat history |

All project routes require `Authorization: Bearer <access>`.

## Configuration

Key variables in `.env`:

- `DATABASE_URL` — overridden in Compose to point at the `db` service
- `EMBEDDING_DIMENSION` — must match the embedding model (384 for `all-MiniLM-L6-v2`)
- `DEFAULT_CHAT_MODE` — default chat mode (`fast` or `deep`)
- `FAST_RETRIEVE_TOP_K` / `DEEP_RETRIEVE_TOP_K` — retrieval sizes per mode
- `FAST_CHAT_HISTORY_LIMIT` / `CHAT_HISTORY_LIMIT` — history window per mode
- `OPENAI_CHAT_MODEL` / `OPENAI_CHAT_MODEL_FAST` — LLM per mode (can be the same model)
- `CORS_ALLOWED_ORIGINS` — include your Next.js origin

## Architecture

- **Ingestion**: Celery task chunks PDF/DOCX, embeds with sentence-transformers, stores rows in `DocumentChunk` with pgvector (HNSW cosine index).
- **Query**: LangGraph nodes — load memory → embed query → project-filtered cosine retrieval → multi-document context → OpenAI chat → citation list → persist messages.
- **Streaming chat**: `POST /api/projects/{id}/chat/stream/` returns **SSE** (`text/event-stream`): `status` (pipeline stage + message) → `token` (answer deltas) → `done` (full answer, citations, `message_id`, `latency_ms`). The Next.js UI uses `fetch` + `ReadableStream` (not `EventSource`) so JWT and JSON body work cleanly.
- **Pipeline modes** (`pipeline_mode` on chat body):
  - `qa` — vector top-k Q&A with citations (Fast k=3, Deep k=10)
  - `summarize` — hierarchical map-reduce over **all** chunks of `document_id` (Objective / Methodology / Key Findings / Limitations / Conclusion)
  - `literature_search` — ranked exploration across project (Fast k=15, Deep k=25)
  - `synthesis` — cross-document literature review (Fast k=20, Deep k=40)
- **Fast mode**: fewer chunks + shorter history for lower time-to-first-token; **Deep mode**: more context for thorough answers.

## Demo script (for presentation)

1. Upload 2 PDFs and wait until indexed.
2. Select **Fast** mode → ask a question → point out status messages + streaming tokens + latency (`first token … · total …`).
3. Ask a follow-up immediately (show conversation flow).
4. Switch to **Deep** mode → ask a harder question → compare latency vs quality.
5. Show citations tied to uploaded documents.
