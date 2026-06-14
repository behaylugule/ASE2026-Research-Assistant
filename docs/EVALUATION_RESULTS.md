# Evaluation Results — Fast vs Deep

Benchmarks run against project **AI in Health Care** (2 indexed PDFs, 140 chunks).  
Environment: Docker Compose, local CPU embeddings, OpenAI `gpt-4o-mini`.

> **Note:** First query after backend restart includes embedding model load (cold start). Subsequent queries are much faster. The backend warms up embeddings on startup to reduce this effect.

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
  "query": "What is the main contribution of the first paper?",
  "pipeline_mode": "qa"
}
```

## Q&A mode (`qa`)

| Query | Mode | Latency (ms) | Citations | Answer length (chars) |
|-------|------|-------------:|----------:|----------------------:|
| What is the main contribution of the first paper? | Fast | 15,156* | 3 | 602 |
| What is the main contribution of the first paper? | Deep | 2,124 | 10 | 584 |
| What methodology is described in the documents? | Fast | 3,520 | 3 | 1,314 |
| What methodology is described in the documents? | Deep | 3,446 | 10 | 1,249 |

\* Cold start (first query after model load). Warm queries typically 2–4 s.

**Observations:**

- Deep retrieves more chunks (k=10 vs k=3) → more citations (10 vs 3)
- Answer quality is comparable for factual questions; Deep provides broader source coverage
- Fast mode is suitable for interactive follow-ups during a reading session

## Literature search mode (`literature_search`)

| Query | Mode | Latency (ms) | Citations | Answer length (chars) |
|-------|------|-------------:|----------:|----------------------:|
| What themes appear across these papers? | Fast | 6,726 | 15 | 2,658 |
| What themes appear across these papers? | Deep | 28,767 | 25 | 3,350 |

**Observations:**

- Deep mode retrieves 25 chunks vs 15 → longer, more comprehensive thematic report
- Deep latency scales with context size (larger prompt to LLM)
- Fast mode produces a usable exploration report in ~7 s for demos

## Synthesis mode (`synthesis`)

| Query | Mode | Latency (ms) | Citations | Answer length (chars) |
|-------|------|-------------:|----------:|----------------------:|
| Compare agreements and contradictions on methodology. | Fast | 7,097 | 20 | 3,382 |
| Compare agreements and contradictions on methodology. | Deep | 6,736 | 40 | 3,314 |

**Observations:**

- Deep doubles citation count (k=40 vs k=20) with similar total latency on this dataset
- Both modes produce structured markdown (Themes, Agreements, Contradictions, Conclusion)

## Summarize mode

Summarize reads **all chunks** of one document (map-reduce). Latency depends on document length, not Fast/Deep toggle. Typical range: 30 s – 3 min for a 20–50 page PDF.

Output sections: Objective, Methodology, Key Findings, Limitations, Conclusion.

## Trust / grounding metrics (qualitative)

| Behavior | Result |
|----------|--------|
| Answers cite uploaded documents | Yes — inline `[DocumentName – Page N]` |
| "Not found" when topic absent from docs | Yes — e.g. unrelated questions return exact not-found phrase |
| Citation click → excerpt highlight | Yes — chunk API + document panel |
| Project isolation | Yes — retrieval filtered by project_id |

## Suggested metrics for your presentation

Pick 2–3 rows from the Q&A table (warm queries) and 1 Literature row to show the Fast vs Deep tradeoff:

- **Fast Q&A:** ~3.5 s, 3 citations — good for interactive chat
- **Deep Q&A:** ~3.4 s, 10 citations — better source coverage
- **Deep Literature:** ~29 s, 25 citations — thorough exploration

## Future evaluation (optional extension)

- User study: task completion time vs manual PDF reading
- Citation precision: % of citations that support the claim (manual audit on 20 answers)
- Retrieval recall@k on a labeled question set
- Compare Fast → Refine with Deep vs single Deep call
