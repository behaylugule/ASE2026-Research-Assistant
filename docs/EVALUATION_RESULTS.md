# Evaluation Results — Fast vs Deep

Benchmarks from project **AI in Health Care** (3 indexed PDFs, 193 chunks):

| Document | Chunks |
|----------|-------:|
| `artificial-intelligence-applications-in-healthcare-epf.pdf` | 17 |
| `R48319.1.pdf` | 67 |
| `9a31d8af-en.pdf` | 109 |

Environment: Docker Compose, local CPU embeddings, OpenAI `gpt-4o-mini`.

> **Method:** Citation counts and answer lengths are taken from **saved chat history** on this project. Latency is from warm **`/chat/benchmark/`** re-runs (June 2026) using the same queries. First query after backend restart can add ~10 s for embedding model load.

## How to reproduce

1. Open `http://localhost:3000/projects/{id}/demo`
2. Select pipeline mode (Q&A, Literature, or Synthesis)
3. Enter a query and click **Run Fast + Deep**

Or via API:

```http
POST /api/projects/{project_id}/chat/benchmark/
Authorization: Bearer <token>
Content-Type: application/json

{
  "query": "what is the problem statment",
  "pipeline_mode": "qa"
}
```

## Q&A mode (`qa`)

| Query | Mode | Latency (ms) | Citations | Answer length (chars) |
|-------|------|-------------:|----------:|----------------------:|
| what is the problem statment | Fast | 2,005 | 3 | 1,323 |
| what is the problem statment | Deep | 2,249 | 10 | 1,362 |
| What are the Solutions | Fast | 2,005 | 3 | 1,670 |
| What are the Solutions | Deep | 4,400 | 10 | 1,670 |
| What methodology is described in the documents? | Fast | 3,376 | 3 | 1,553 |
| What methodology is described in the documents? | Deep | 3,803 | 10 | 1,532 |

**Observations:**

- Deep retrieves more chunks (k=10 vs k=3) → more citations (10 vs 3)
- Fast Q&A on warm queries is typically **2–4 s** — suitable for interactive chat
- Answers on AI-in-healthcare topics (problem statement, solutions) were grounded with inline citations in chat

## Literature search mode (`literature_search`)

| Query | Mode | Latency (ms) | Citations | Answer length (chars) |
|-------|------|-------------:|----------:|----------------------:|
| What themes appear across these papers? | Fast | 5,047 | 15 | 2,528 |
| What themes appear across these papers? | Deep | 6,644 | 25 | 2,839 |
| What are the main findings across my uploaded papers? | Fast | 8,564 | 15 | 3,431 |
| What are the main findings across my uploaded papers? | Deep | 10,654 | 25 | 4,045 |

**Observations:**

- Deep mode retrieves 25 chunks vs 15 → longer thematic reports
- Fast Literature produces a usable exploration report in **~5–9 s**
- Deep adds source coverage with modest latency increase on this corpus (not the ~4× seen on smaller early tests)

## Synthesis mode (`synthesis`)

| Query | Mode | Latency (ms) | Citations | Answer length (chars) |
|-------|------|-------------:|----------:|----------------------:|
| Compare agreements and contradictions on methodology | Fast | 6,225 | 20 | 3,633 |
| Compare agreements and contradictions on methodology | Deep | 7,342 | 40 | 3,836 |

**Observations:**

- Deep doubles citation count (k=40 vs k=20) with similar total latency
- Both modes produce structured markdown (Themes, Agreements, Contradictions, Conclusion)

## Summarize mode

Summarize reads **all chunks** of one document (map-reduce). No Fast/Deep toggle.

| Document | Chunks | Latency (ms) | Output length (chars) |
|----------|-------:|-------------:|----------------------:|
| EPF AI in healthcare brief | 17 | 45,273 | 2,416 |
| R48319.1 | 67 | 158,805 | 2,543 |
| 9a31d8af-en | 109 | 263,353 | 2,153 |

Chat session also produced full summaries (~2,521–3,376 chars) via **Summarize** / **Summarize this document**.

Output sections: Objective, Methodology, Key Findings, Limitations, Conclusion.

## Trust / grounding metrics (qualitative)

| Behavior | Result |
|----------|--------|
| Answers cite uploaded documents | Yes — inline `[DocumentName – Page N]` |
| "Not found" when topic absent from docs | Yes — e.g. *What are the conclusions?* returned not-found in chat |
| Citation click → excerpt highlight | Yes — chunk API + document panel |
| Project isolation | Yes — retrieval filtered by project_id |

## Suggested metrics for presentation

| Mode | Fast | Deep |
|------|------|------|
| **Q&A** — problem statement | ~2 s · 3 citations | ~2 s · 10 citations |
| **Literature** — themes | ~5 s · 15 citations | ~7 s · 25 citations |
| **Synthesis** — methodology compare | ~6 s · 20 citations | ~7 s · 40 citations |
| **Summarize** — 17-chunk PDF | — | ~45 s |

## Future evaluation (optional extension)

- User study: task completion time vs manual PDF reading
- Citation precision: % of citations that support the claim (manual audit on 20 answers)
- Retrieval recall@k on a labeled question set
- Compare Fast → Refine with Deep vs single Deep call
