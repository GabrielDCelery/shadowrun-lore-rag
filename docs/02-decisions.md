# Design Decisions

Decisions inferred from the codebase and prior decision log. Code tells you what was chosen, not always why — verify reasoning with the team.

## Summary

**RAG Pipeline**

| #   | Question                    | Decision                                         |
| --- | --------------------------- | ------------------------------------------------ |
| D1  | RAG stack                   | LangChain + ChromaDB                             |
| D2  | Embedding model             | mxbai-embed-large via Ollama                     |
| D3  | PDF extraction tool         | marker-pdf (surya OCR)                           |
| D4  | Table chunking              | Table-aware chunking                             |
| D5  | Table embedding format      | Row-as-sentence natural language conversion      |
| D6  | Comparative queries         | DuckDB parallel store (planned, not implemented) |
| D12 | Pipeline stages             | Separate directory per stage, no in-place edits  |
| D13 | Markdown post-processing    | Strip OCR noise, normalise with mdformat         |
| D14 | ToC/credits/index stripping | Detect and remove front/back matter              |
| D15 | Evaluation approach         | Two-pass: generate answers, then judge separately |

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

**Decision:** marker-pdf with GPU acceleration. `drop_repeated_text` and `disable_ocr_math` are enabled. Image extraction must NOT be disabled.

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

---

### D13: Markdown post-processing (`clean_markdown.py`)

**Decision:** After marker-pdf extraction, run a cleaning pass that strips image references, navigation bar lines, malformed table rows, and collapses consecutive blank lines. Then normalise table whitespace with `mdformat`.

**Context:** marker-pdf consistently produces the same noise patterns across Shadowrun sourcebooks: `![]()` image lines, emoji-based nav bars, table rows with only punctuation, and table cells padded to PDF column widths with runs of spaces. `mdformat` with GFM extension normalises the result.

**Alternatives considered:**

- Dedicated cleaning script + mdformat — catches all known noise patterns; chosen
- Skip cleaning, rely on chunker to ignore noise — noise ends up embedded, hurts retrieval; ruled out
- Manual review per book — not scalable; ruled out

**Why:** Consistent noise patterns across the corpus make rule-based cleaning effective. mdformat table normalisation is necessary because marker-pdf pads cells to PDF column widths, which causes mdformat to misparse extremely wide tables if not pre-collapsed.

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

| Q | Category | v1 correctness | v2 correctness | v3 correctness | v3 groundedness | Root cause |
| --- | --- | --- | --- | --- | --- | --- |
| Q1 — population & racial composition | factual | 3 | 0 | 0 | 3 | Retrieval miss — demographic stats chunk not in top 7 |
| Q2 — Rite of Progression | factual | 4 | 4 | 4 | 5 | Missing results/appeal timing detail (not in retrieved chunks) |
| Q3 — automatic weapon penalties | factual | 3 | 4 | 4 | 5 | Garbled table row conversion — column headers split mid-word by OCR |
| Q4 — Portland economy decline | inference | 5 | 4 | 4 | 5 | "Council decision is the cause" implied not explicitly stated |
| Q5 — Ehran/Bright Water identity | inference | 4 | 4 | 4 | 5 | Missing Bright Water terminal cancer detail (not in retrieved chunks) |
| **Avg** | | **3.8** | **3.2** | **3.2** | **4.6** | |

**Findings:**
- Scores stabilised at v2/v3 — fact-count rubric produces consistent results across runs
- Q1 groundedness dropped to 3 in v3: model guessed "elves are probably dominant" which isn't in the retrieved chunks; stricter "must be explicitly stated" rule penalised this correctly
- Q1 is a pure retrieval miss; the demographic stats chunk was not in the top 7 retrieved. Increasing `top_k` may help but is unconfirmed
- Q3 correct chunk was retrieved (ranked 4th) but OCR splits column headers mid-word in weapon penalty tables, producing garbled row-as-sentence output the model cannot parse. Data quality issue, not a retrieval problem
- Inference questions perform on par with factual ones under the stricter rubric (both averaging 4) — the gap closes because "implied not stated" deductions hit inference questions too
- Groundedness averaging 4.6 (5.0 excluding Q1) — model is working from retrieved chunks, not training data

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
