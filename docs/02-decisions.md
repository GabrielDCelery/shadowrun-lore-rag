# Design Decisions

Decisions inferred from the codebase and prior decision log. Code tells you what was chosen, not always why — verify reasoning with the team.

## Summary

**RAG Pipeline**

| #   | Question                    | Decision                                          |
| --- | --------------------------- | ------------------------------------------------- |
| D1  | RAG stack                   | LangChain + ChromaDB                              |
| D2  | Embedding model             | mxbai-embed-large via Ollama                      |
| D3  | PDF extraction tool         | marker-pdf (surya OCR)                            |
| D4  | Table chunking              | Table-aware chunking                              |
| D5  | Table embedding format      | Row-as-sentence natural language conversion       |
| D6  | Comparative queries         | DuckDB parallel store (planned, not implemented)  |
| D12 | Pipeline stages             | Separate directory per stage, no in-place edits   |
| D13 | Markdown post-processing    | Strip OCR noise, normalise with mdformat          |
| D14 | ToC/credits/index stripping | Detect and remove front/back matter               |
| D15 | Evaluation approach         | Two-pass: generate answers, then judge separately |
| D16 | Shadowtalk LLM model        | llama3.1:8b (current); gemma2:9b or qwen2.5:7b as next candidates |
| D17 | Shadowtalk retrieval query  | Topic-first: `"{topic} {persona.perspective}"` |
| D18 | Shadowtalk retrieval diversity | Chunk ID exclusion via ChromaDB `$nin` filter per persona |
| D19 | Shadowtalk own_history      | LLM-generated topic summary instead of raw previous lines |
| D20 | Shadowtalk conversation window | Window-based reply_to: last 2 non-self lines only |
| D21 | Shadowtalk character name filtering | `where_document $not_contains handle` to exclude self-referencing chunks |
| D22 | Shadowtalk persona voice    | Experiential/positional voice with distinct per-character angle |

**Infrastructure**

| #   | Question            | Decision                                      |
| --- | ------------------- | --------------------------------------------- |
| D7  | Containerisation    | Single RAG container, separate from Ollama    |
| D8  | Where to run        | Homelab only                                  |
| D9  | Data storage        | External path `/srv/shadowrun-rag/`           |
| D10 | Deployment workflow | Build image locally, push to homelab registry |
| D11 | Repo separation     | Separate repo from personal-homelab           |

---

## RAG Pipeline

### D1: RAG stack

**Decision:** LangChain + ChromaDB. ChromaDB runs file-based with no extra container. LangChain provides Ollama integration and LCEL chain composition.

**Context:** Need a stack that integrates cleanly with a self-hosted Ollama instance and keeps infrastructure minimal.

**Alternatives considered:**

- LangChain + ChromaDB — simple, good Ollama integration, no extra container; chosen
- LlamaIndex — purpose-built for RAG but less familiar; ruled out
- Custom with FAISS — more control but more work; ruled out
- Haystack — solid but less Ollama-native; ruled out

**Why:** Best balance of simplicity and features given an Ollama-first setup.

---

### D2: Embedding model

**Decision:** `mxbai-embed-large` via Ollama. Runs on homelab GPU, higher quality embeddings than `nomic-embed-text`.

**Context:** Embedding quality directly affects retrieval relevance. Model runs on the same Ollama instance as the LLM.

**Alternatives considered:**

- `mxbai-embed-large` — higher quality embeddings, shorter context (512 tokens); chosen
- `nomic-embed-text` — 8192 token context, lower quality; ruled out
- sentence-transformers locally — fast but CPU-bound on laptop, different runtime; ruled out

**Why:** Embedding quality matters more than context length for this use case — Shadowrun sourcebook chunks are typically short enough to fit within 512 tokens.

---

### D3: PDF extraction tool

**Decision:** marker-pdf with GPU acceleration. `drop_repeated_text` and `disable_ocr_math` are enabled. Image extraction must NOT be disabled. LLM-assisted re-conversion is available via `pipeline:2-convert-llm <book>` using `qwen2.5vl:3b` via Ollama, but not viable on the current RTX 3060. Even after surya releases VRAM post-OCR, the two models together leave no headroom for compute buffers — Ollama loads weights into VRAM but falls back to CPU inference, maxing out all 4 cores at ~54s/table. Practical requirement is 16GB+ VRAM to run both models with compute buffers. To use `--use_llm` today: run marker-pdf on a higher-VRAM machine, or use the default Gemini Flash backend (pay-per-use, negligible cost for a handful of books).

**Context:** Shadowrun sourcebooks are scanned PDFs of mixed quality. Some have callout boxes and styled sidebars that marker-pdf may detect as image regions but contain rules text — disabling image extraction risks silent content loss. Repeated text (headers/footers stamped on every page) and OCR-hallucinated math symbols are consistent noise in these books.

**Alternatives considered:**

- marker-pdf (surya OCR) — handles mixed-quality scans, markdown-aware output, GPU-accelerated; chosen
- OCRmyPDF + pdfminer — faster but Tesseract struggles on degraded scans; ruled out
- surya standalone — lighter but raw text output, no markdown structure; ruled out
- EasyOCR — handles medium quality but slower, less markdown-aware; ruled out

**Why:** marker-pdf produces structured markdown output which is critical for the downstream chunking pipeline.

---

### D4: Table chunking

**Decision:** Table-aware chunking — tables must be kept atomic, never split mid-row. Two-pass approach: (1) parse markdown and extract tables as atomic units, prepending the nearest preceding heading for context; (2) run normal `MarkdownTextSplitter` on non-table prose sections. Tables stay intact even if they exceed `chunk_size`.

**Context:** `MarkdownTextSplitter` splits at character boundaries with no table awareness. A chunk starting mid-table with no headers is semantically useless for retrieval.

**Alternatives considered:**

- Table-aware chunking — preserves table integrity; chosen
- MarkdownTextSplitter (current) — fast but breaks tables mid-row; ruled out

**Why:** A mid-table chunk with no headers cannot be matched by an embedding model to any meaningful query. A 2000-character table is better as one chunk than two broken halves.

---

### D5: Table embedding format

**Decision:** Convert table rows to natural language sentences during ingestion. Each row becomes a self-contained document with column headers baked in.

**Context:** Raw markdown table syntax (`| col | col |`) is noise for embedding models trained on prose. Row-as-sentence conversion improves semantic matching for item-specific queries.

**Alternatives considered:**

- Natural language sentence per row — matches how users query; chosen
- Raw markdown table — `|` characters are noise to embedding models; ruled out
- JSON per row — better than raw markdown but still not natural language; ruled out
- Column-oriented (one document per column) — adds complexity with minimal gain; ruled out

**Why:** Embedding models are trained on prose. Queries like "how much does a Predator IV cost" match a sentence like "The Predator IV pistol costs 350 nuyen" far better than a raw table row.

**Threshold rule:** Apply row conversion for tables > 5 rows with clear column headers where rows represent distinct items (weapons, gear, skills). Skip small 2-3 row reference tables — not worth the complexity.

---

### D6: Comparative queries

**Decision:** Planned future work — add DuckDB as a parallel structured store alongside ChromaDB. Tables get stored in both. A query router detects comparison intent and routes to DuckDB (SQL) vs ChromaDB (semantic). The LLM generates SQL from natural language for DuckDB queries.

**Context:** RAG alone cannot answer comparative/filtering queries ("cheapest pistol", "highest damage weapon") — these require all rows simultaneously, which conflicts with chunked retrieval.

**Alternatives considered:**

- DuckDB parallel store + query router — solves comparative queries; planned
- RAG only — cannot handle comparative queries; current state

**Why DuckDB:** In-process, no extra container, queryable directly from Python. `llama3.1:8b` can generate basic SQL from natural language.

**Open:** Not yet implemented. Implement only after table chunking and row conversion are validated.

---

### D12: Multi-stage pipeline directories

**Decision:** Each pipeline step writes to its own directory. No step modifies files in place.

```
pdfs_raw/ → pdfs_normalised/ → markdown_extracted/ → markdown_clean/ → markdown_stripped/
```

**Context:** marker-pdf is slow (minutes per book). Post-processing steps iterate frequently. Keeping stages separate means any step can be re-run without redoing earlier expensive work.

**Alternatives considered:**

- Separate directory per stage — independently inspectable, re-runnable from any point; chosen
- In-place transformation — simpler but destroys intermediate state; ruled out
- Single output directory with suffixed filenames — cluttered, no clean glob per stage; ruled out

**Why:** Being able to inspect `markdown_clean/` independently of `markdown_stripped/` is essential for debugging OCR quality and tuning post-processing rules.

**Responsibility boundary (decided 2026-04-26):**

- Step 3 (`clean_markdown.py`) — inline text normalization: fix OCR artifacts, normalize formatting, rewrite content in place. Currency symbol expansion belongs here.
- Step 4 (`strip_toc.py`) — structural decisions: which sections to keep or remove. Does not rewrite content. Name reflects current scope; rename to `strip_sections.py` if more structural operations are added.

---

### D13: Markdown post-processing (`clean_markdown.py`)

**Decision:** After marker-pdf extraction, run a cleaning pass that strips image references, navigation bar lines, malformed table rows, and collapses consecutive blank lines. Then normalise table whitespace with `mdformat`.

**Context:** marker-pdf consistently produces the same noise patterns across Shadowrun sourcebooks: `![]()` image lines, emoji-based nav bars, table rows with only punctuation, and table cells padded to PDF column widths with runs of spaces. `mdformat` with GFM extension normalises the result.

**Alternatives considered:**

- Dedicated cleaning script + mdformat — catches all known noise patterns; chosen
- Skip cleaning, rely on chunker to ignore noise — noise ends up embedded, hurts retrieval; ruled out
- Manual review per book — not scalable; ruled out

**Why:** Consistent noise patterns across the corpus make rule-based cleaning effective. mdformat table normalisation is necessary because marker-pdf pads cells to PDF column widths, which causes mdformat to misparse extremely wide tables if not pre-collapsed.

**Known gap — OCR-split table headers (identified 2026-04-26):**

Evaluation run on the full corpus revealed that table-based queries score significantly lower (0–2) than prose queries (4–5). Root cause: OCR splits multi-word column headers across lines, producing garbled cells (empty strings, fragments starting with `/` or `:`). The row-as-sentence conversion in `chunk_documents.py` then emits sentences with missing or broken labels (e.g. `": 22,000¥/1 yr"` instead of `"Possession: 22,000¥/1 yr"`).

Affected queries in baseline eval: Q3 (weapon penalties, Tir Tairngire), Q6 (airfares, Tir na nÓg), Q18 (life expectancy, Germany), Q19 (airfares/imports, Germany), Q31 (travel costs, Sprawl Survival Guide), Q33 (Big Ten HQs, Core Rules).

**Fix status (2026-04-26):**

Step 1 implemented: heuristic header repair added to `clean_markdown.py`. If a header cell is empty, starts with `/`, `:`, or a common continuation word (`and`, `or`, `of`), it is merged into the previous header cell. Re-embedded the full corpus after the fix.

Result: partial improvement. Q3 (weapon penalties, Tir Tairngire) improved from 4→5 after the fix. Q6, Q8, Q9, Q25, Q31 remain consistently failing (score 2) across all top_k and model variants tested — these are structural retrieval gaps (data spread across too many chunks) not header quality issues.

Step 2 (fallback if needed): Re-run `pipeline:2-convert` with `--use_llm` enabled on the 5 affected books only (Tir Tairngire, Tir na nÓg, Germany, Sprawl Survival Guide, Core Rules). marker-pdf's `--use_llm` flag activates LLM-assisted table post-processing; it supports Ollama so no additional infrastructure is needed. Conversion will be slower but only 5 books need re-processing. Hold until the structural retrieval failures (D6) are addressed first.

**Known gap — currency symbol expansion (identified 2026-04-26):**

Table columns use currency symbols (`¥`, `£`) rather than words. Row-as-sentence output embeds "Cost (¥): 160" but queries use natural language ("nuyen", "Irish punts"). The embedding model cannot bridge symbol-to-word gap, so prose preamble chunks (which spell out "nuyen" and "Irish punts") rank above the actual data rows. Q6 (Tir na nÓg airfares) is a confirmed case.

**Fix status (2026-04-26):** `expand_currency_symbols()` added to `clean_markdown.py`. Applies after header repair and before `mdformat`. `¥` → `nuyen (¥)` and `£` → `Irish punts (£)` globally; lookbehind guards prevent double-expansion if the word form is already present. Re-eval after re-embedding: overall score 3.90 → 4.00 (+0.10). Q37 (medkit costs) improved. Q6 retrieval fixed but LLM still fails — see below.

**Known gaps — persistent failures (updated 2026-04-26):**

| Q   | Failure mode         | Root cause                                                                          |
| --- | -------------------- | ----------------------------------------------------------------------------------- |
| Q6  | LLM terminology gap  | Retrieval now works (correct airfare rows retrieved). LLM doesn't know "the Tír" = Tir na nÓg — obscure in-world alias a 7-8B model doesn't bridge. Accepted: a larger model would handle it. |
| Q18 | Table retrieval      | Germany racial stats table; likely same currency/table issues as pre-fix            |
| Q19 | Table retrieval      | Germany airfares; may share Q6's terminology gap ("Germany" vs book's phrasing)     |
| Q31 | Vocabulary collision | "long distance travel" matches space travel section in Target: Wastelands, outranking Sprawl Survival Guide content |
| Q33 | Structural           | Answer requires 10 separate corp entries; no single top_k retrieves all             |

Q31 and Q33 require D6 (structured store / query router). Q18 and Q19 need investigation — may be retrieval gaps or LLM reasoning failures like Q6.

**Current capability assessment (2026-04-26):**

Prose-based queries work well. Inference queries and factual prose queries score 4–5 consistently. The RAG is reliable for lore, political/social context, character and faction information, and rules concepts. Groundedness is consistently 5 — when data is retrieved, the LLM uses it rather than hallucinating. Remaining failures are either structural retrieval gaps (Q31, Q33) or LLM reasoning limitations on obscure in-world terminology (Q6) that a larger model would handle.

---

### D14: ToC/credits/index stripping (`strip_toc.py`)

**Decision:** Before embedding, strip front matter (table of contents, publisher credits) and back matter (index) from cleaned markdown. Reads from `markdown_clean/`, writes to `markdown_stripped/`.

**Context:** Initial test queries returned ToC entries instead of actual content — the embedding model matched query terms to chapter titles in the ToC rather than the relevant body text. Index sections (alphabetical term lists with page numbers) produce similarly low-quality matches.

**Detection approach:**

- Front matter: find first heading matching `TABLE OF CONTENTS`, `CREDITS/CONTENTS`, or standalone `CONTENTS` (within first 15% of document only — see false positive note below). Scan forward for the first heading followed within 20 lines by a non-table prose line of 80+ characters — that heading marks where real content starts.
- Back matter: find a standalone `INDEX` heading in the last 30% of the document, strip from there to end of file.
- Safety valve: if content start cannot be detected, the file is passed through unchanged rather than destroying content.

**Alternatives considered:**

- Heuristic heading + prose detection — handles varied formatting across books; chosen
- Fixed line-count skip — brittle, each book has different front matter length; ruled out
- Manual per-book config — accurate but not scalable; ruled out

**Why:** ToC noise directly degrades retrieval quality. The detection approach is robust enough across the corpus with different formatting styles (some combine ToC and credits, some have the ToC mid-document after an opening story).

**Per-book findings (corpus as of 2026-04-25):**

Heading patterns vary across books — discovered empirically by inspecting the markdown files.

| File                  | ToC heading                  | Front | Back | Notes                                   |
| --------------------- | ---------------------------- | ----- | ---- | --------------------------------------- |
| year-of-the-comet     | `## TABLE OF CONTENTS`       | 101   | 153  | Credits inline in ToC table             |
| sprawl-survival-guide | `## TABLE OF CONTENTS`       | 65    | —    |                                         |
| state-of-the-art-2064 | `# TABLE OF CONTENTS`        | 62    | —    |                                         |
| bug-city              | `# CREDITS/CONTENTS`         | 138   | —    | Two consecutive headings; both consumed |
| tir-tairngire         | `## TABLE OF CONTENTS`       | 174   | —    | Opening story before ToC is preserved   |
| tir-na-nog            | `# TABLE OF CONTENTS`        | 198   | —    |                                         |
| aztlán                | `## CONTENTS`                | 218   | —    | Early-only match required (see below)   |
| core rules            | `# ... TABLE OF CONTENTS...` | 195   | —    | Opening story preserved                 |
| denver                | —                            | —     | 2729 | Index stripped; no ToC heading          |
| germany               | —                            | —     | —    | ToC table present but no heading anchor |
| neo-anarchists        | —                            | —     | —    | Credits then ToC, no heading anchor     |
| bullets-bandages      | —                            | —     | —    | No ToC; short supplement                |

**Known false positive — denver `# CONTENTS`:**
Denver has a `# CONTENTS` heading at line 7890 (77% through the document) which is an in-book section, not the table of contents. Matching standalone `CONTENTS` headings anywhere in the document would incorrectly strip 2200+ lines of real content. Fixed by restricting the `CONTENTS` pattern to the first 15% of lines only.

**Known gaps — germany and neo-anarchists:**
Both books have ToC tables at the start but no heading above them to anchor detection on. The safety valve passes them through unchanged. The unstripped ToC tables are modest noise (~30 lines each) and do not justify adding fragile heuristics to detect headingless tables.

---

### D15: Evaluation approach (`evaluate.py`)

**Decision:** Two-pass evaluation. Pass 1 generates RAG answers and saves them to a timestamped JSON file. Pass 2 runs a separate LLM judge against those answers and saves scores to a second timestamped file.

**Context:** Need a repeatable way to measure retrieval quality across pipeline changes (chunk size, top-k, prompt tuning, re-embedding). Manual inspection alone doesn't scale; a single-pass approach loses the ability to re-judge without re-querying.

**Two scoring dimensions:**

- **Correctness** — did the answer contain the right facts? Scored against the expected key facts in `tests/rag_queries.md`.
- **Groundedness** — did the answer come from the retrieved chunks or from the model's training data? Shadowrun lore exists in LLM training data (wikis, forums) so a model could answer correctly without using the RAG at all. Low groundedness means the pipeline is not contributing.

**Two-model setup:**

- `llm_model` (e.g. `llama3.1:8b`) generates answers
- `judge_model` (e.g. `mistral`) scores them
- Both configured separately in `config.py`; both run via Ollama
- Using a different model for judging avoids self-scoring bias (models tend to rate their own answers generously)
- Models run sequentially so no extra VRAM required

**Output files:**

- `evals/answers_<timestamp>.json` — question, retrieved chunks, generated answer
- `evals/scores_<timestamp>.json` — per-question correctness/groundedness scores with reasoning; references answer file by name

**Why two passes:**

- Answers can be inspected manually before judging — useful for catching obvious failures (wrong book retrieved, mid-sentence chunks, hallucinations) that a numeric score might not surface
- Judge can be re-run with different models or criteria without re-querying the RAG
- Historical answer files can be re-judged after scoring criteria change
- If judge pass crashes, answers are not lost

**Alternatives considered:**

- Single pass (answer + judge in one script) — simpler but loses ability to re-judge; chosen against
- Human-only evaluation — no numeric baseline, can't track improvement across runs; ruled out
- External evaluation framework (RAGAS etc.) — adds dependency, less control over judge prompt; ruled out

**Evaluation runs (2026-04-25) — `llama3.1:8b` answers, `mistral:7b-instruct` judge, `top_k=7`, Tir Tairngire only:**

Three runs were made while tuning the judge prompt. v1 used a loose rubric; v2 tightened to fact-count based scoring with explicit per-fact deduction and "must be explicitly stated, not implied"; v3 accepted 0 as a valid score (previously the model returned 0 despite a floor of 1 in the prompt).

| Q                                    | Cat       | v1  | v2  | v3  | GND | Root cause                                          |
| ------------------------------------ | --------- | --- | --- | --- | --- | --------------------------------------------------- |
| Q1 — population & racial composition | factual   | 3   | 0   | 0   | 3   | Retrieval miss — stats chunk not in top 7           |
| Q2 — Rite of Progression             | factual   | 4   | 4   | 4   | 5   | Missing results/appeal timing detail                |
| Q3 — automatic weapon penalties      | factual   | 3   | 4   | 4   | 5   | OCR split header — garbled row-as-sentence output   |
| Q4 — Portland economy decline        | inference | 5   | 4   | 4   | 5   | "Council decision is the cause" implied not stated  |
| Q5 — Ehran/Bright Water identity     | inference | 4   | 4   | 4   | 5   | Missing Bright Water terminal cancer detail         |
| **Avg**                              |           | 3.8 | 3.2 | 3.2 | 4.6 |                                                     |

**Full corpus evaluation — top_k tuning (2026-04-26):**

All runs: `llama3.1:8b` answers, `mistral:7b-instruct` judge, 41 questions across all books. Re-embedded after OCR header repair fix.

| top_k | avg correctness | notes                                                  |
| ----- | --------------- | ------------------------------------------------------ |
| 5     | 3.95            | best score; LLM handles fewer chunks better            |
| 7     | 3.90            | marginal drop; more context without much degradation   |
| 9     | 3.80            | noticeable drop; "lost in the middle" effect starts    |
| 12    | ~3.6            | further degradation; judge also returned out-of-range scores (32, 7) |
| 20    | not tested      |                                                        |

**Decision:** Use `top_k=7` as the baseline. Gains from k=5 are marginal (0.05) and k=7 provides a small buffer for harder questions. `llama3.1:8b` degrades noticeably above k=9 — small 7-8B models suffer from "lost in the middle": they struggle to synthesise information when too many retrieved chunks are present.

**Structural retrieval failures (not fixed by top_k):** Q31 (travel costs, Sprawl Survival Guide) and Q33 (Big Ten HQs, Core Rules) score consistently low regardless of top_k. Root cause: Q31 answers are spread across 5+ prose sections; Q33 answers are in 10 separate corp entries. No single top_k value can retrieve all necessary chunks simultaneously. These require D6 (query router / structured store).

**Model comparison (2026-04-26):**

Ran fair cross-model comparison using a neutral judge (`llama3.1:8b` as judge for both, `top_k=7`):

| Answer model       | Judge model        | Avg correctness | Notes                          |
| ------------------ | ------------------ | --------------- | ------------------------------ |
| mistral:7b-instruct | mistral:7b-instruct | 4.34           | Self-scoring bias — inflated   |
| mistral:7b-instruct | llama3.1:8b        | 3.76            | Fair score                     |
| llama3.1:8b         | llama3.1:8b        | 3.66            | Fair score                     |

Self-scoring bias: 0.58 point inflation when a model judges its own outputs. Under fair comparison, mistral edges llama by only 0.10 points — effectively equivalent quality.

**Decision:** Use `mistral:7b-instruct` as judge, `llama3.1:8b` as answer model (or either — quality is the same). The judge model should always differ from the answer model to avoid self-scoring bias. Judge prompt should enforce the 0-5 range strictly; out-of-range scores (e.g. 32, 7) have been observed at higher top_k values and should be capped.

**Consistently failing questions (score 2 across all model and top_k variants):**

Q6, Q8, Q9, Q25, Q31 — structural retrieval gaps. Root cause to be investigated before further model or top_k tuning.

---

### D16: Shadowtalk LLM model

**Decision:** `llama3.1:8b` (current). Produces acceptable output for the shadowtalk feature given the right topic framing. Model quality matters less than topic choice — a contested, multi-stakeholder situation with no single answer produces significantly better conversations than a how-to question regardless of model.

**Context:** Shadowtalk is a multi-turn, multi-persona creative generation task. The model must track conversation history across 7 turns, maintain distinct character voices, avoid repeating itself, and stay grounded in retrieved lore. This is harder than single-turn RAG answering, and 7-8B models hit a capability ceiling on history tracking and instruction-following under constraint pressure.

**Observed failure modes at 7-8B scale:**
- Self-repetition: model cannot reliably check what it said 4+ turns ago
- Hallucinated proper nouns: specificity pressure causes the model to invent locations and names not in the lore
- Character convergence: all characters drift toward the same point when the topic has an obvious "correct" answer
- Instruction overload: too many prompt constraints causes the model to satisfy the first few and ignore the rest

**Alternatives considered / to consider:**

| Model | VRAM (Q4) | Notes |
| --- | --- | --- |
| `llama3.1:8b` | ~5GB | Current. Decent output, acceptable history tracking |
| `mistral:7b-instruct` | ~4.5GB | Already pulled (judge model). Tested — worse formatting discipline than llama; echoes history into output |
| `gemma2:9b` | ~5.5GB | Top candidate. Google Gemma 2 punches above weight on instruction following; likely to handle the no-repeat constraints better |
| `qwen2.5:7b` | ~4.5GB | Second candidate. Alibaba model, strong at multi-constraint prompts |
| `mistral-nemo:12b` | ~7GB | Fits in 12GB VRAM with headroom. Significantly more capable but tight if embedding model is also loaded |

**Hardware constraint:** RTX 3060 12GB. During shadowtalk, marker-pdf is not loaded, so full 12GB is available to Ollama. The embedding model (`mxbai-embed-large`, ~670MB) is a minor concern.

**Status (2026-04-26):** `llama3.1:8b` accepted as baseline. `gemma2:9b` was tested and rejected — formatting is cleaner (no history echoing, no name prefixes) but conversation quality is worse. Gemma picks one thread and loops on it across multiple turns rather than ranging across the topic; characters repeat the same question or point 3+ times in 7 turns. `llama3.1:8b` hallucinates more proper nouns but actually moves the conversation forward. `qwen2.5:7b` remains untested and is the next candidate if llama quality becomes a problem.

---

### D17: Shadowtalk retrieval query order

**Decision:** Topic-first query: `f"{topic} {persona.perspective}"`. Persona perspective appended, not prepended.

**Context:** Initial design used `f"{persona.perspective} {topic}"`. Embedding models weight earlier tokens more heavily — prepending the persona caused the embedding to anchor on the persona's semantic space, pulling off-topic chunks when no lore intersection exists between the persona's angle and the topic (e.g. Coyote getting LA hearth spirit chunks when asked about corporate takeovers).

**Why:** Topic-first ensures retrieval anchors on the actual subject. The persona suffix still biases toward persona-relevant chunks when the intersection exists in the lore; when it doesn't, it falls back to on-topic content rather than off-topic persona content.

---

### D18: Shadowtalk retrieval diversity via chunk ID exclusion

**Decision:** Track which chunk IDs each persona retrieved per conversation. On subsequent turns, exclude those IDs via ChromaDB's `where={"chunk_id": {"$nin": [...]}}` filter. Chunk IDs stored as SHA1 hash of content in metadata at embedding time (`chunk_id` field in `chunk_documents.py`).

**Context:** Without exclusion, a persona gets the same top-k chunks on every turn (same query → same embedding → same nearest neighbours). The model then has identical context and reproduces identical or near-identical content despite the `own_history` prompt rule.

**Why not over-fetch + Python filter:** ChromaDB's `$nin` filter excludes at the database level before results are returned. Over-fetching (`k * 3`) and slicing in Python is redundant — the DB handles it correctly with just `k=settings.top_k`.

**Limitation:** Chunk ID exclusion prevents same-chunk retrieval but not same-topic retrieval. If the same facts appear across many chunks (common in Shadowrun sourcebooks), a persona can still get different chunks carrying identical information.

---

### D19: Shadowtalk own_history as topic summary

**Decision:** Before each persona's subsequent turn, make a lightweight LLM call to summarise their prior lines into a compact topic list ("• background count danger • ongoing banishment ritual • astral noise"). Pass this summary as `own_history` instead of raw previous lines.

**Context:** Raw previous lines in the prompt allow the model to avoid exact wording but not semantic repetition — it paraphrases the same points rather than finding genuinely different angles. A topic-level summary gives the model a map of covered territory that it must avoid regardless of phrasing.

**Cost:** One extra LLM call per persona per subsequent turn. With 4 personas and 2 turns each, at most 4 extra calls per conversation.

**Limitation:** The summary is only as good as the summariser. If the LLM collapses distinct proper nouns into vague categories ("corporate activity"), the model cannot reliably distinguish covered from uncovered ground. Prompt instructs extraction of specific proper nouns.

---

### D20: Shadowtalk window-based conversation context

**Decision:** Each character's turn prompt receives only the last 2 non-self lines as `reply_to` context, not the full conversation history.

**Context:** Full history was tried and produced incoherent output — models at 7-8B scale cannot reliably synthesise and respect a growing history list under simultaneous persona, voice, and repetition constraints. The window approach keeps the conversation flowing naturally: each character hears what was just said and responds, like a real conversation.

**Trade-off:** The narrow window means characters cannot see what was said more than 2 turns ago. A point can re-enter the conversation after it leaves the window. This is acceptable — real conversation has the same property — but means the `own_history` summary is critical to prevent self-repetition across the longer span.

---

### D21: Shadowtalk character name filtering

**Decision:** Exclude chunks mentioning the character's own handle from their retrieval results via `where_document={"$not_contains": handle}`.

**Context:** FastJack, Bull, and Coyote are canonical Shadowrun NPCs who post commentary throughout sourcebooks (JackPoint, Shadowland BBS). Retrieving a chunk where FastJack is already commenting on a topic and then asking the model to BE FastJack with that chunk as "firsthand knowledge" caused the model to reproduce or confuse the sourced content with what it should generate.

**Why:** Prevents any character from reading lore that is about themselves. Clean separation between character voice (prompt) and lore context (retrieval).

---

### D22: Shadowtalk persona voice design

**Decision:** Each persona speaks from a specific experiential angle — not "what the situation looks like" (reporting) but what they personally encountered, concluded, or fear. Each persona has a distinct second gear to avoid converging on general cynicism.

**Angles:**
- **FastJack** — cuts to motive: not what is happening but who set it up, why now, who walks away clean. Clipped fragments, never more than 10 words per sentence.
- **Bull** — reads op structure: what kind of team, whether it's official or deniable, what that composition reveals about the real objective. Speaks from ops he's run, not general cynicism about corps.
- **Coyote** — speaks from something she personally encountered in the astral: a spirit she had to dodge, a zone she couldn't push through, something that felt wrong. Mechanic talking about an engine, not a shaman philosophising.
- **Ledger** — speaks from fear and pattern recognition: she left Aztec because she knows how it ends for people who know too much. Notices when corps go quiet, when assets move, when executives disappear from agendas. Expresses risk as behaviour, never invents numbers.

**Why distinct angles matter:** Without a specific angle, personas default to general genre-appropriate output that converges across turns. A distinct angle gives the model a different dimension to explore each time, and breaks the dependency on retrieved content having new facts.

---

## Infrastructure

### D7: Containerisation

**Decision:** Single RAG container, connects to the existing Ollama container managed by `personal-homelab` repo.

**Context:** Keeps `personal-homelab` focused on infrastructure and shared services, this repo focused on application code.

**Alternatives considered:**

- Single RAG container, separate from Ollama — clean separation, independent iteration; chosen
- Add RAG to homelab compose — all in one place but couples infrastructure with application; ruled out
- No container — simpler but marker-pdf has complex dependencies; ruled out
- Microservices (separate ingest, query, vector DB) — flexible but overkill for personal project; ruled out

---

### D8: Where to run

**Decision:** Homelab only. Develop on laptop, deploy to homelab.

**Context:** Homelab has NVIDIA GPU. Ollama already runs there.

**Alternatives considered:**

- Homelab only — GPU, all compute in one place; chosen
- Laptop only — no deployment but weaker hardware, Ollama is remote anyway; ruled out
- Both — unnecessary complexity; ruled out

---

### D9: Data storage

**Decision:** External path at `/srv/shadowrun-rag/` on the homelab host, mounted into the container as volumes.

**Context:** PDFs are copyright material and too large for git. ChromaDB data needs to persist across container restarts.

**Alternatives considered:**

- External path `/srv/shadowrun-rag/` — clean, outside repo, easy to backup; chosen
- In repo — large files, copyright concerns, bloats git; ruled out
- Named Docker volumes — container-native but harder to inspect and backup; ruled out

---

### D10: Deployment workflow

**Decision:** Build Docker image locally, push to homelab registry (`HOMELAB_HOST:5000`), deploy via `personal-homelab` repo.

**Context:** Originally used a `deploy.sh` SSH script. Moved to registry-based workflow when `compose.yaml` was moved to `personal-homelab` repo (2026-04-21).

**Alternatives considered:**

- Build locally, push to registry — production-like, decouples build from deploy; chosen
- Git push + SSH deploy script — simple but tightly coupled; superseded
- GitHub Actions auto-deploy — overkill, needs homelab exposed to GitHub; ruled out

---

### D11: Repo separation

**Decision:** Keep RAG code in a separate repo from `personal-homelab`.

**Context:** `personal-homelab` manages infrastructure and shared services (Ollama, filebrowser). This repo is a standalone application that consumes those services.

**Alternatives considered:**

- Separate repo — clean separation, independent iteration; chosen
- In homelab repo — everything in one place but mixes infrastructure with application; ruled out
