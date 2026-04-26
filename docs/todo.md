# TODO

## Done

- [x] Commit pending changes (docs restructure, Dockerfile user setup, mise tasks, compose.yaml removal)
- [x] PDF organisation — normalise filenames via `normalise_pdf_filenames.py` (slugify, no pattern matching)
- [x] Invocation — added mise tasks (`run:normalise`, `run:convert`, `run:embed`, `run:query`) with `image:` prefix for build tasks
- [x] Dockerfile — create app user before dependency install, no chown needed
- [x] Pipeline directories — `pdfs_raw/`, `pdfs_normalised/`, `markdown_extracted/`, `markdown_clean/`, `chroma_db/`
- [x] marker-pdf quality — enabled `drop_repeated_text` and `disable_ocr_math`
- [x] Markdown post-processing script — strips image references, navigation headers, malformed table rows
- [x] Table handling — D4 (table-aware chunking) and D5 (row-as-sentence conversion) implemented in `chunk_documents.py`
- [x] Initial test queries run — identified retrieval issues (ToC noise, garbled headings, semantic gap between query phrasing and source terminology)

## Up Next

- [x] Implement `strip_toc.py` — detect and remove ToC/Credits/Index sections from `markdown_clean/` → `markdown_stripped/`
- [x] Update `create_embeddings.py` to read from `markdown_stripped/` instead of `markdown_clean/`
- [x] Add `markdown_stripped/` path to `config.py`
- [x] Add `pipeline:4-strip-toc` debug pull to `debug:pull-markdown` mise task
- [x] Re-embed clean corpus after ToC removal
- [x] Run baseline evaluation score after clean corpus is embedded — same results as pre-ToC-strip baseline
- [x] Generate test set — `tests/rag_queries.md` with 41 questions across all books (factual, inference, cross-book)
- [x] Build evaluation script `src/evaluate.py` — two-pass: pass1 generates answers, pass2 judges with separate LLM
- [x] Add `debug:evaluate` mise task
- [x] Add metadata to eval output files (model, top_k, chunk settings in answers; judge model + answers ref in scores)
- [x] OCR split table header repair — heuristic fix in `clean_markdown.py`; Q3 improved, persistent failures identified
- [x] top_k tuning — tested k=5,7,9,12; settled on k=7 (k=5 marginal gain, k=9+ degrades)
- [x] Model comparison — confirmed self-scoring bias (0.58pt inflation); mistral and llama3.1:8b equivalent under fair judge

## Up Next

- [x] Q6 — currency symbol expansion implemented and evaluated; retrieval now works but LLM fails on "the Tír" vs "Tir na nÓg" terminology gap; accepted as LLM limitation (larger model would handle it)
- [x] Q9 — resolved by currency expansion; score unchanged at 4 (was already fixed in prior run)
- [x] Q8, Q25 — resolved in prior runs; stable at 4 and 5 respectively
- [x] Q18 — judge error, not a pipeline failure; LLM answer was correct, judge misread it
- [x] Q19 — root cause identified: airfare table landed under `### BY TRAIN` heading in extracted markdown due to PDF page boundary; `pipeline:2-convert-llm` added to re-convert with `qwen2.5vl:3b` via Ollama
- [x] Q19 — LLM-assisted re-conversion attempted; fails with VRAM OOM (surya models hold 7GB, no headroom for vision LLM); accepted as known limitation alongside Q6
- [ ] Q31 — vocabulary collision (space travel section outranks Sprawl Survival Guide); requires D6 or query expansion
- [ ] Q33 — structural failure (10 corp entries); requires D6
- [ ] D6: DuckDB parallel store + query router for comparative/aggregation queries (Q31, Q33)

## Known Markdown Extraction Issues (potential future fixes)

- [ ] Split headings — OCR breaks decorative capital letters into separate single-char headings (e.g. `# F` + `#### IRST IMPRESSIONS`). Hard to fix automatically.
- [ ] Short line fragments — ~52 very short lines in Tir Tairngire, likely OCR fragments. Spot-check to assess impact.
- [ ] marker-pdf `--use_llm` re-conversion — `pipeline:2-convert-llm` now supports this via `qwen2.5vl:3b`; Germany is the priority candidate; other affected books: Tir Tairngire, Tir na nÓg, Sprawl Survival Guide, Core Rules

## Future

- [ ] Expose query as a FastAPI endpoint in `shadowrun-rag` (wraps current `query.py` logic)
- [ ] Chainlit chat UI as a separate container in `personal-homelab` repo — calls the RAG API
- [ ] Claude Code session sync — sync `~/.claude/projects/` across machines to preserve conversation history
