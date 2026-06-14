---
marp: true
theme: default
paginate: true
title: Real-Time Academic Research Assistant
description: ASE2026 Project Presentation
---

# Real-Time Interactive Academic Research Assistant with RAG and Citations

**ASE2026 — Advanced Software Engineering**

*[Your Name]* · *[Date]*

---

## Agenda

1. Problem & motivation
2. Project objectives (proposal alignment)
3. System overview & architecture
4. **Live demo**
5. Four pipeline modes
6. Fast vs Deep evaluation
7. Trust & citations
8. Limitations & future work
9. Q&A

---

## The problem

- Academic publication volume is exploding
- Literature review is **slow** and **manual**
- Generic AI chatbots:
  - Hallucinate facts
  - Provide **no verifiable citations**
  - Optimize for quality, not **interactive speed**

> *"Researchers need fast, trustworthy answers grounded in their own documents."*

---

## Our solution

An **AI-powered research assistant** built on **Retrieval-Augmented Generation (RAG)**:

- Upload PDFs/DOCX into project-scoped libraries
- Ask questions with **streaming** responses
- Get **inline citations** tied to source pages
- Four modes: Q&A · Summarize · Literature · Synthesis

**Differentiator:** optimized for **time-to-first-response** and continuous conversation flow.

---

## Proposal alignment

| Proposal objective | Implementation |
|--------------------|----------------|
| Reduce research time | Fast mode, streaming SSE, async ingestion |
| Improve accuracy | RAG + project-scoped retrieval only |
| Ensure scalability | Celery workers, pgvector HNSW, Docker Compose |
| Enhance trust | Citations, excerpt panel, "not found" when unsupported |

---

## Architecture

```
┌─────────────┐     JWT/SSE      ┌──────────────┐
│  Next.js UI │ ◄──────────────► │ Django REST  │
└─────────────┘                  └──────┬───────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              PostgreSQL            Redis              OpenAI
              + pgvector           Celery            Chat API
              (chunks/embed)      (ingestion)
```

See full diagrams: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## RAG pipeline (Q&A)

1. **Load** recent chat history
2. **Embed** user question (local sentence-transformers)
3. **Retrieve** top-k chunks (cosine similarity, project-filtered)
4. **Aggregate** excerpts grouped by document
5. **Generate** answer with inline citations (OpenAI)
6. **Stream** tokens via SSE → save to chat history

Status events: `memory → embed → retrieve → generate → save → done`

---

## Four pipeline modes

| Mode | Best for | Retrieval |
|------|----------|-----------|
| **Q&A** | Specific factual questions | Top-k chunks |
| **Summarize** | Full overview of one paper | All chunks (map-reduce) |
| **Literature** | Discover themes across papers | Top 15 / 25 |
| **Synthesis** | Multi-paper lit review | Top 20 / 40 |

```
One fact?          → Q&A
One paper overview → Summarize
What's relevant?   → Literature
How do they relate?→ Synthesis
```

---

## Live demo plan

1. Upload 2 PDFs → wait for **Indexed**
2. **Q&A (Fast):** *What is the main contribution?*
   - Show streaming + latency (TTFT / total)
3. **Follow-up question** → conversation memory
4. **Click citation** → excerpt highlight
5. **Literature:** *What themes appear across these papers?*
6. **Synthesis (Deep):** *Compare methodology agreements & contradictions*
7. **Summarize** one document → structured sections

Backup: record a 2-min screen capture beforehand.

---

## Fast vs Deep

| Setting | Q&A | Literature | Synthesis |
|---------|-----|------------|-----------|
| **Fast** | k=3 | k=15 | k=20 |
| **Deep** | k=10 | k=25 | k=40 |

**Fast** — lower latency, interactive chat  
**Deep** — more context, thorough answers  
**Refine with Deep** — upgrade a Fast draft on demand

---

## Evaluation results (sample)

**Q&A — warm queries**

| Query | Mode | Latency | Citations |
|-------|------|--------:|----------:|
| What methodology is described? | Fast | 3.5 s | 3 |
| What methodology is described? | Deep | 3.4 s | 10 |

**Literature**

| Query | Mode | Latency | Citations |
|-------|------|--------:|----------:|
| Themes across papers | Fast | 6.7 s | 15 |
| Themes across papers | Deep | 28.8 s | 25 |

Full tables: [EVALUATION_RESULTS.md](./EVALUATION_RESULTS.md)

Demo page: `/projects/{id}/demo`

---

## Trust & citations

- Every claim tied to `[DocumentName – Page N]`
- **Sources** panel below each answer (expandable)
- Click citation → **excerpt panel** with highlighted text
- **"Not found in the provided documents"** when context lacks support
- No web search — answers come only from **your uploads**

---

## Tech stack

| Component | Choice |
|-----------|--------|
| Frontend | Next.js, Tailwind, shadcn/ui |
| Backend | Django REST + JWT |
| Jobs | Celery + Redis |
| Vectors | PostgreSQL pgvector (HNSW) |
| Embeddings | sentence-transformers (local CPU) |
| LLM | OpenAI gpt-4o-mini |
| Deploy | Docker Compose |

---

## Limitations

- Project-scoped only (not Google Scholar / arXiv search)
- PDF and DOCX ingestion; quality depends on extraction
- Requires OpenAI API key for generation
- No formal user study yet (qualitative demo evaluation only)
- Summarize is slowest mode (reads entire document)

---

## Future work

- Production deployment (HTTPS, secrets, monitoring)
- PDF viewer with true page scroll
- Formal evaluation: citation precision, user study
- Hybrid retrieval (BM25 + vector)
- Optional reranking in Deep mode only

---

## Conclusion

We built a **real-time, citation-grounded research assistant** that goes beyond the original proposal:

- Four specialized pipeline modes for different research tasks
- Fast/Deep latency–quality tradeoff with measurable benchmarks
- Streaming UX with verifiable source tracing

**Repository:** ASE2026 · **Docs:** `docs/PIPELINE_MODES.md`, `docs/PROJECT_REPORT.md`

---

## Thank you — Questions?

**Demo:** http://localhost:3000  
**API health:** http://localhost:8000/health/

---

<!-- Speaker notes (not shown on slides) -->

<!--
SLIDE 1: Introduce yourself and the project title. Mention this is ASE2026 capstone work.

SLIDE 4: Emphasize trust — professors care about hallucination problem.

SLIDE 6: Walk through proposal PDF section by section — show you delivered what you promised plus more.

SLIDE 8: Don't read every step — point to the flow diagram.

SLIDE 10: This is the longest part of the presentation — LIVE DEMO. Have PDFs pre-uploaded.

SLIDE 12: Show the demo page if live API is slow.

SLIDE 13: Click a citation during demo — this is your "wow" moment.

SLIDE 16: Be honest about limitations — shows engineering maturity.

SLIDE 17: Keep future work to 3 bullets max when speaking.
-->
