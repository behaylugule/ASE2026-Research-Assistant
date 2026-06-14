# Pipeline Modes — User Guide

This app offers **four pipeline modes** for working with your uploaded PDFs and DOCX files. Each mode answers a different kind of research question.

Open a project at **http://localhost:3000/projects/{id}** and use the tabs in the chat header:

| Tab | Mode ID | Best for |
|-----|---------|----------|
| **Q&A** | `qa` | Quick, cited answers to specific questions |
| **Summarize** | `summarize` | Full structured summary of **one** document |
| **Literature** | `literature_search` | Discover themes and papers across your project |
| **Synthesis** | `synthesis` | Multi-paper literature review (agreements & contradictions) |

You can also switch **Fast** vs **Deep** for speed vs. thoroughness.

---

## Before you start

1. **Register or log in** at `/register` or `/login`.
2. **Create a project** and **upload** PDF or DOCX files (max 50 MB each).
3. Wait until each document shows **Indexed** (green status) before chatting.
4. Open the project workspace — documents on the left, chat on the right.

---

## Fast vs Deep

| Setting | Q&A | Literature | Synthesis | Summarize |
|---------|-----|------------|-----------|-----------|
| **Fast** | Top 3 chunks | Top 15 chunks | Top 20 chunks | All chunks |
| **Deep** | Top 10 chunks | Top 25 chunks | Top 40 chunks | All chunks |

- **Fast** — lower latency, good for demos and quick checks.
- **Deep** — more context, better for complex or nuanced questions.

The active setting is shown in the chat header (e.g. `top-k 3`, `lit 15`, `syn 40`, `all chunks`).

---

## 1. Q&A (`qa`)

### What it does

Answers a **specific question** using only the most relevant excerpts from your project. Responses include inline citations like `[PaperName – Page 12]`.

If the answer is not in your documents, the assistant replies:

> Not found in the provided documents.

### When to use it

- Fact lookup: authors, methods, results, definitions
- Follow-up questions in a conversation
- Quick checks while reading a paper

### How to use (UI)

1. Click the **Q&A** tab.
2. Choose **Fast** or **Deep**.
3. Type your question in the chat box and press **Enter** or click **Send**.
4. Watch streaming tokens and citations appear below the answer.

**Document selection:** optional. If you select a document in the sidebar, Q&A still searches the whole project by default (retrieval is project-scoped).

### Example questions

| Scenario | Example prompt |
|----------|----------------|
| Method | *What evaluation metrics does this paper use?* |
| Result | *What accuracy did the authors report on the test set?* |
| Definition | *How is "attention" defined in these documents?* |
| Comparison (light) | *Which paper uses a transformer architecture?* |
| Follow-up | *Can you elaborate on the training procedure you mentioned?* |

### Example flow

```
You:  What dataset was used for pre-training?

AI:   The authors used a corpus of 45M scientific abstracts [Smith2024 – Page 3].
      Data was filtered to English-only entries [Smith2024 – Page 4].
```

---

## 2. Summarize (`summarize`)

### What it does

Produces a **full structured summary of one document** by reading **every chunk** (hierarchical map-reduce). Output sections:

- **Objective**
- **Methodology**
- **Key Findings**
- **Limitations**
- **Conclusion**

This is the slowest mode but the most complete for a single paper.

### When to use it

- You uploaded one long PDF and want the gist without reading it all
- You need a standard academic summary for notes or a presentation
- You want to compare summaries of several papers (run once per document)

### How to use (UI)

**Option A — Chat (streaming)**

1. Click the **Summarize** tab.
2. **Select exactly one document** in the document list (click to highlight).
3. Optionally type a message, or leave the box **empty** and press **Send**.
   - Empty input sends: *"Summarize this document"*
4. Wait for the full summary to stream in.

**Option B — Background summarize (async)**

1. Find an **Indexed** document in the list.
2. Click the small **Summarize** button under that document.
3. The task runs in the background (Celery). Status updates to `summary pending` → `summary completed`.
4. Fetch the stored summary via API: `GET /api/projects/{id}/documents/{doc_id}/summary/`

### Example prompts

| Scenario | Example prompt |
|----------|----------------|
| Default | *(leave empty and send)* |
| Focused | *Summarize this document with emphasis on methodology* |
| Short brief | *Give me a concise executive summary of this paper* |

### Example output shape

```markdown
## Objective
Evaluate whether retrieval-augmented generation improves citation accuracy…

## Methodology
The study uses pgvector cosine search with MiniLM embeddings…

## Key Findings
- RAG reduced hallucinated citations by 34%
- Latency under 2s with Fast mode (top-k 3)

## Limitations
Evaluation limited to computer science abstracts…

## Conclusion
RAG is viable for academic assistants when citations are required…
```

---

## 3. Literature (`literature_search`)

### What it does

**Explores your entire project** by semantic search. It groups relevant excerpts by document and produces a **discovery report** — not a deep cross-paper review.

Output sections:

- **Thematic clusters**
- **Paper-level summaries**
- **Key insights**

### When to use it

- You have many papers and want to see what relates to a topic
- Starting a new research direction and mapping existing uploads
- Finding which documents mention a keyword, method, or author area

### How to use (UI)

1. Click the **Literature** tab.
2. Choose **Fast** (15 chunks) or **Deep** (25 chunks).
3. Enter a **broad research query** and send.

No document selection needed — it searches across all indexed files in the project.

### Example queries

| Scenario | Example prompt |
|----------|----------------|
| Topic scan | *Papers about climate model bias and uncertainty* |
| Method hunt | *Which documents discuss transformer fine-tuning?* |
| Author area | *Research on retrieval-augmented generation for academia* |
| Survey start | *What themes appear across my uploaded NLP papers?* |

### Example flow

```
You:  What work in my library addresses hallucination in LLMs?

AI:   ## Thematic clusters
      - **Citation grounding** — 2 papers use explicit retrieval…
      - **Evaluation benchmarks** — 1 paper proposes FaithScore…

      ## Paper-level summaries
      - **Smith2024.pdf** — RAG pipeline with pgvector…
      - **Jones2023.pdf** — Benchmark for factual consistency…

      ## Key insights
      - Most papers tie hallucination reduction to retrieved context [Smith2024 – Page 7]
      …
```

---

## 4. Synthesis (`synthesis`)

### What it does

Writes a **multi-paper literature review** that connects findings across documents. It retrieves more chunks than Literature mode and focuses on **integration and comparison**.

Output sections:

- **Theme 1, Theme 2, …** (with supporting papers)
- **Agreements**
- **Contradictions**
- **Conclusion**

### When to use it

- Writing a related-work or literature-review section
- Comparing how different papers approach the same problem
- Identifying consensus vs. open disagreements in your corpus

### How to use (UI)

1. Click the **Synthesis** tab.
2. Prefer **Deep** (40 chunks) for thorough reviews; **Fast** (20) for quicker drafts.
3. Enter a **synthesis topic or review question** and send.

Works across all documents in the project — upload at least **2 papers** for meaningful synthesis.

### Example queries

| Scenario | Example prompt |
|----------|----------------|
| Review section | *Synthesize how these papers evaluate RAG systems* |
| Method comparison | *Compare the retrieval approaches used across my documents* |
| Find gaps | *What limitations do these papers share, and where do they disagree?* |
| Thematic review | *Write a literature review on embedding models for scientific search* |

### Example flow

```
You:  Synthesize the evaluation methodologies across my uploaded papers.

AI:   ## Theme 1: Automated metrics
      Smith2024 and Lee2025 both use precision@k… [Smith2024 – Page 9]

      ## Theme 2: Human evaluation
      Only Jones2023 includes expert annotators… [Jones2023 – Page 12]

      ## Agreements
      All three papers agree that citation grounding is essential…

      ## Contradictions
      Smith2024 claims reranking is necessary; Lee2025 finds negligible gains…

      ## Conclusion
      A hybrid evaluation (automatic + human) appears most defensible…
```

---

## Which mode should I pick?

```text
One specific fact or question     →  Q&A
One paper, full overview          →  Summarize
Many papers, what's relevant?   →  Literature
Many papers, how do they relate? →  Synthesis
```

| Goal | Mode |
|------|------|
| "What page says X?" | Q&A |
| "Summarize this PDF for me" | Summarize |
| "What do I have on topic Y?" | Literature |
| "Write related work for topic Z" | Synthesis |

---

## API usage (optional)

All endpoints require `Authorization: Bearer <access_token>`.

### Unified chat (all four modes)

```http
POST /api/projects/{project_id}/chat/stream/
Content-Type: application/json

{
  "message": "What dataset was used?",
  "mode": "fast",
  "pipeline_mode": "qa"
}
```

| `pipeline_mode` | Extra fields | Notes |
|-----------------|--------------|-------|
| `qa` | — | Default if omitted |
| `summarize` | `"document_id": "<uuid>"` | Required |
| `literature_search` | — | Project-wide search |
| `synthesis` | — | Project-wide, more chunks |

### Dedicated endpoints

```http
POST /api/projects/{id}/literature-search/
{ "query": "climate model bias", "mode": "deep" }

POST /api/projects/{id}/synthesis/
{ "query": "Compare evaluation methods", "mode": "deep" }

POST /api/projects/{id}/documents/{doc_id}/summarize/
{}

GET /api/projects/{id}/documents/{doc_id}/summary/
```

---

## Tips

1. **Upload first, chat second** — wait for **Indexed** status; processing runs in the background.
2. **Summarize needs a selection** — pick one document in the sidebar before sending.
3. **Use Fast for demos** — switch to Deep when quality matters more than speed.
4. **Citations** — click or note `[DocumentName – Page N]` to trace answers back to sources.
5. **Stop generation** — use the **Stop** button if a long Summarize or Synthesis run is taking too long.
6. **Latency** — after each reply, the UI shows time-to-first-token and total time (useful for presentations).

---

## Quick demo script

1. Upload 2–3 PDFs and wait until indexed.
2. **Q&A (Fast):** *What is the main contribution of the first paper?*
3. **Literature (Fast):** *What themes appear across these papers?*
4. **Synthesis (Deep):** *Synthesize agreements and contradictions on methodology.*
5. Select one PDF → **Summarize:** send with empty input for a full structured summary.
