---
marp: true
theme: default
paginate: true
title: Research Assistant — ASE2026
---

# Research Assistant
## Real-Time Academic Research Assistant with RAG and Citations

*Behaylu Gebrekidan* · ASE2026 · *21/06/2026*

---

## Agenda

1. Problem
2. Solution
3. Evaluation
4. Limitations
5. Future work
6. Conclusion

---

## Problem

- **Information overload** — too many papers, too little time
- **Untrusted AI** — fluent answers often lack **verifiable citations**
- **Slow interaction** — long waits break iterative research (ask → read → follow up)

**Target users:** students & researchers working on a **defined set of uploaded papers**.

---

## Solution

**Research Assistant** — RAG-based platform over **your own documents**:

- Upload PDFs/DOCX → ask in natural language
- **Four modes:** Q&A · Summarize · Literature · Synthesis
- **Citations** on every answer — click to view the source excerpt
- **Fast / Deep** — quick exploration vs thorough answers
- **Streaming chat** — real-time responses while you research

*Retrieve relevant passages first, then generate — grounded in your library, not the open web.*

---

## Evaluation

Preliminary benchmarks (**AI in Health Care**, 3 PDFs, 193 chunks — chat history + warm runs):

| Mode | Fast | Deep |
|------|------|------|
| **Q&A** — problem statement | ~2 s · 3 citations | ~2 s · 10 citations |
| **Q&A** — solutions | ~2 s · 3 citations | ~4 s · 10 citations |
| **Literature** — themes across papers | ~5 s · 15 citations | ~7 s · 25 citations |
| **Literature** — main findings | ~9 s · 15 citations | ~11 s · 25 citations |
| **Synthesis** — agreements & contradictions | ~6 s · 20 citations | ~7 s · 40 citations |
| **Summarize** — EPF brief (17 chunks) | — | ~45 s *(all chunks; no Fast/Deep)* |

**Findings:** Fast suits interactive Q&A (~2–4 s); Deep adds **more source coverage**; Literature/Synthesis scale with corpus size; Summarize is slower by design (map-reduce over the whole PDF).

*Preliminary evaluation — not a formal user study.*

---

## Limitations

- Only **uploaded project documents** (not web / arXiv search)
- **Small-scale evaluation** — no user study or citation-precision audit
- PDF text quality varies; scanned pages need OCR (not included)
- Model can still misread context — **user must verify citations**
- Full-document Summarize is slower by design

---

## Future work

- Formal **user study** (task time vs manual reading)
- Measure **citation precision**
- Full PDF page viewer
- Production deployment for courses / research labs
- Hybrid keyword + semantic retrieval

---

## Conclusion

We built a **citation-grounded research assistant** that addresses the proposal goals:

- ✅ Reduce research time (Fast mode, streaming, four workflows)
- ✅ Improve accuracy through **RAG** on user documents
- ✅ Enhance **trust** with inline citations and source excerpts

**Claim:** Interactive literature work needs AI that is **fast enough to use** and **trustworthy enough for academia**.

---

## Thank you — Questions?

**Research Assistant** · Demo: `http://localhost:3000`

Q&A prep: [PRESENTATION_QA.md](./PRESENTATION_QA.md)
