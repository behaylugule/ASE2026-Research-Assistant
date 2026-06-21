# Presentation Q&A — Researcher Perspective

Questions your professor may ask after your **submitted proposal** presentation.  
Focus: **research motivation, impact, and outcomes** — not low-level implementation.

Use this to rehearse short spoken answers (30–60 seconds each).

---

## 1. About your proposal and what you delivered

### Q1. You submitted a proposal at the start. Did you achieve what you promised?

**Answer:** Yes. The proposal promised an RAG-based academic assistant with document retrieval, grounded answers, automatic citations, and a scalable backend. We delivered that and went further: real-time streaming chat, four research modes (Q&A, Summarize, Literature search, Synthesis), Fast vs Deep settings, and a working demo with evaluation benchmarks. Every objective from the proposal—reduce research time, improve accuracy through grounding, ensure scalability, and enhance trust via citations—is addressed in the implementation.

---

### Q2. What changed between the proposal and the final system?

**Answer:** The core idea stayed the same: RAG + citations + scalable architecture. What we added based on feedback was a stronger focus on **interactive research**—streaming responses, faster first answers, and different modes for different literature tasks (quick fact lookup vs full summary vs multi-paper synthesis). So the proposal was the foundation; the final system is richer in how researchers actually work day to day.

---

### Q3. In one sentence, what is the research contribution of this project?

**Answer:** We show that an academic research assistant can combine **trustworthy, citation-grounded answers** with **fast, interactive conversation** over a private document library—not just one-shot chat without sources.

---

## 2. Problem and motivation (research view)

### Q4. Why is this problem important for researchers?

**Answer:** Researchers and students face two pressures at once: the number of papers is growing quickly, and AI tools are tempting but often unreliable. Reading everything manually does not scale, but using AI without citations is risky in academic work. Our problem sits in the middle—we need tools that **speed up** literature work without **sacrificing** verifiability.

---

### Q5. Who is the target user?

**Answer:** Primarily **students and researchers** working on a defined set of readings—course papers, thesis bibliographies, or a literature review folder. They upload PDFs or DOCX files for one project and ask questions, summarize, or compare papers within that collection. It is not meant to replace large public search engines like Google Scholar.

---

### Q6. You mention “lack of trust” in AI. What do you mean specifically?

**Answer:** In academia, a claim is only useful if you can **verify** it. Generic chatbots often give fluent answers without pointing to a page or paper. That creates hallucination risk and makes the output hard to use in assignments, reviews, or thesis writing. Trust, for us, means every answer is tied to **retrieved excerpts** from the user’s own documents, with citations the user can check.

---

### Q7. Is “slow AI UX” really a research problem?

**Answer:** For **interactive** literature work, yes. Research is iterative—you ask, read, follow up, refine. If each question takes a long time with no feedback, the workflow feels like batch processing, not conversation. That disrupts flow when you are exploring ideas. For a one-time full summary, slower is acceptable; for Q&A while reading, speed matters. Our system supports both through Fast and Deep modes.

---

## 3. Solution and methodology (conceptual)

### Q8. Why RAG? Why not just use ChatGPT or similar tools?

**Answer:** ChatGPT and similar tools are strong for general knowledge but are not built around **your specific papers** with **mandatory citations**. RAG retrieves relevant passages from uploaded documents first, then generates an answer from those passages. That aligns better with academic needs: answers grounded in sources the user chose, not the open internet.

---

### Q9. Explain RAG in simple terms for a non-technical audience.

**Answer:** RAG means: **Retrieve** relevant parts of your documents, then **Augment** the AI prompt with those parts, then **Generate** the answer. The model does not rely on memory alone—it reads selected excerpts from your library before answering, similar to a research assistant who opens the right pages before speaking.

---

### Q10. What does “scalable system architecture” mean in your project?

**Answer:** At research level, it means the design can handle **more documents and more users** without collapsing: background processing for uploads, separate workers for heavy tasks, and a database that stores both project data and vector embeddings efficiently. For a course project we demonstrate the architecture with Docker; in production it could grow with more workers and servers.

---

### Q11. Why four modes (Q&A, Summarize, Literature, Synthesis)?

**Answer:** Because **one chat interface is not enough** for all research tasks. A fact question needs quick, cited answers. A single paper needs a full structured summary. Many papers need exploration of themes or a literature-review-style synthesis. Splitting modes matches how researchers actually work instead of forcing every question through the same pipeline.

---

### Q12. What is the difference between Literature search and Synthesis?

**Answer:** **Literature search** is exploratory—“what themes or topics appear across my papers?” **Synthesis** is analytic—“how do these papers agree, disagree, or relate on methodology or findings?” One helps discovery; the other helps writing related work or discussion sections.

---

## 4. Results, evaluation, and evidence

### Q13. How do you know the system works?

**Answer:** We have a **working end-to-end prototype**: upload documents, wait until indexed, ask questions, receive cited answers, and demo all four modes. We also ran **preliminary benchmarks** comparing Fast vs Deep on latency and citation coverage on a sample project with two papers. The results support our design choices—Fast is suitable for interactive Q&A; Deep retrieves more sources for thorough answers.

---

### Q14. Did you measure whether answers are actually correct?

**Answer:** Not with a formal accuracy study—that would require expert labeling on many questions. We did **qualitative checks**: citations point to real pages, unsupported questions return “not found,” and users can click a citation to read the excerpt. For a course project this demonstrates feasibility; a full research study would measure citation precision and user task completion time.

---

### Q15. How much did you reduce research time? Can you give a number?

**Answer:** We did not run a controlled user study with before/after timing. Conceptually, the system reduces time by letting users **ask directly** instead of manually searching PDFs, and by offering **summaries and synthesis** across papers quickly. Our benchmarks show Fast Q&A answers in roughly **3–5 seconds** on warm queries, which supports interactive use. A precise “X% faster” claim would need a formal evaluation with real participants.

---

### Q16. What was the most interesting finding from your evaluation?

**Answer:** Fast and Deep Q&A can have **similar total latency** on short answers, but Deep provides **many more citations** (e.g., 3 vs 10 chunks). So the tradeoff is not always speed vs quality—it is sometimes **breadth of source coverage** vs lighter retrieval. Literature search in Deep mode took longer but produced richer thematic reports.

---

## 5. Limitations and honesty (professors often ask this)

### Q17. What are the main limitations of your work?

**Answer:**  
1. Scope is limited to **uploaded project documents**, not the whole web or arXiv.  
2. Answer quality depends on **PDF text extraction**; scanned papers are weak without OCR.  
3. Evaluation is **small-scale and preliminary**, not a user study.  
4. Generation depends on an **external LLM API**.  
5. The model can still misinterpret retrieved text—we reduce risk with citations but do not eliminate it.

---

### Q18. Can the system still hallucinate?

**Answer:** Yes, potentially—if retrieval returns weak excerpts or the model over-interprets them. We reduce hallucination by restricting answers to retrieved context, requiring citations, and returning “not found” when context is insufficient. The user should always verify critical claims against the cited pages. That is why citations are central to the design.

---

### Q19. Why should we trust your system more than ChatGPT with PDF upload?

**Answer:** Our system is **designed around verification**: project-scoped retrieval, inline citations, a Sources panel, and click-to-view excerpts. The workflow assumes the user **checks sources**. ChatGPT can discuss a file but is not built as a structured literature tool with multiple research modes and explicit grounding rules. Trust comes from design for academic workflow, not from claiming the model is never wrong.

---

## 6. Comparison and related work

### Q20. How does your work compare to tools like Elicit, Semantic Scholar, or Connected Papers?

**Answer:** Those tools focus on **discovery across published corpora**. Our tool focuses on a **private library** the user uploads for one project—course readings, thesis sources, or confidential drafts. We complement discovery tools: you find papers elsewhere, upload them here, then question, summarize, and synthesize within your collection with citations.

---

### Q21. Is this novel research or an engineering project?

**Answer:** It is primarily an **applied research / engineering project**: we apply known RAG ideas to an academic use case and study the tradeoffs (speed vs depth, modes for different tasks, citation-grounded interaction). The novelty is in the **combination and workflow** for interactive literature research, not a new machine learning algorithm.

---

### Q22. What papers or ideas influenced your approach?

**Answer:** The RAG framework for grounding LLMs in external documents (Lewis et al., 2020), dense retrieval and embeddings for semantic search, and the general move toward **attribution and citation** in AI assistants. Our contribution is applying these to a multi-mode academic assistant with interactive UX.

---

## 7. Future work and impact

### Q23. What would you do next if you had more time?

**Answer:**  
- Run a **user study** with students doing a real literature review task.  
- Measure **citation precision** (do citations support the claim?).  
- Add **hybrid retrieval** (keywords + vectors) for better recall.  
- Build a **full PDF page viewer** for easier verification.  
- Deploy for production with proper security and monitoring.

---

### Q24. Could this be used in real universities or research labs?

**Answer:** Yes, with further work. The core workflow—upload papers, ask cited questions, summarize, synthesize—is useful for courses and early-stage literature review. Production deployment would need stronger security, multi-user teams, larger-scale evaluation, and possibly integration with reference managers or institutional repositories.

---

### Q25. What impact do you expect on academic workflows?

**Answer:** For targeted tasks—understanding a reading list, drafting related work, checking what papers say about a method—it can **save time** and **improve confidence** because answers link to sources. It does not replace reading critical papers in depth or expert judgment; it assists exploration and first-pass synthesis.

---

## 8. Personal and presentation questions

### Q26. What was the hardest part of the project?

**Answer:** *(Personalize this.)* Example: Balancing **speed and quality**—making chat feel interactive while keeping answers grounded and cited. Another challenge was designing **different modes** so each research task had the right retrieval strategy, not one generic chat for everything.

---

### Q27. What did you learn from this project?

**Answer:** *(Personalize this.)* Example: I learned that for research tools, **trust and UX matter as much as the model**—citations, streaming, and mode selection shape whether researchers actually use the system. I also learned how to connect a research proposal to a working prototype with measurable evaluation.

---

### Q28. Walk me through a typical use case.

**Answer:** A graduate student creates a project “Thesis chapter 2,” uploads five PDFs, waits until they are indexed, then uses **Q&A** to check definitions and methods, **Literature search** to see common themes, **Synthesis** to draft related work, and **Summarize** on one key paper for a structured overview—all with citations they can verify before writing.

---

### Q29. Why should I give you a good grade?

**Answer:** Because we moved from **proposal to working system**: clear research problem, implemented solution aligned with objectives, demo-ready platform, documentation, paper, and honest evaluation with stated limitations. The project shows both **research thinking** and **engineering execution**.

---

### Q30. Any questions for me?

**Answer:** *(Prepare 1–2 sincere questions.)* Examples:  
- “Do you think citation-grounded assistants should be integrated into how we teach literature review?”  
- “What evaluation would you consider strong enough for this to move beyond a course project?”

---

## Quick cheat sheet (memorize these)

| If they ask… | Say in one line |
|--------------|-----------------|
| Problem? | Information overload + untrusted, uncited AI |
| Solution? | RAG over uploaded papers with citations |
| Contribution? | Interactive, multi-mode, citation-grounded research assistant |
| Why RAG? | Ground answers in user’s documents, not open web |
| Evidence? | Working demo + Fast vs Deep benchmarks |
| Limitation? | Small eval, project-scoped only, model can still err |
| Future work? | User study, citation precision, production deploy |

---

## Tips for the presentation room

1. **Lead with the proposal** — “We promised X; we built X plus Y.”  
2. **Demo beats slides** — show upload → Q&A → citation click.  
3. **Be honest about limits** — researchers respect that.  
4. **Avoid jargon** unless they ask — say “retrieval from your papers” not “HNSW pgvector.”  
5. **Keep answers under 1 minute** — then offer: “I can show that in the demo if helpful.”

---

*Replace “we” with “I” if this is a solo project. Add your name and date before rehearsing.*
