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
- [ ] Generate test set — use Claude Code to read cleaned markdowns and produce `tests/rag_queries.md` with questions + expected answers covering rules, characters, lore, and in-character content
- [ ] Build evaluation script `src/evaluate.py` — runs test set through RAG, scores each answer via LLM-as-judge (Ollama locally, swappable to Claude Haiku via config)
- [ ] Add `debug:evaluate` mise task

## Known Markdown Extraction Issues (potential future fixes)

- [ ] Split headings — OCR breaks decorative capital letters into separate single-char headings (e.g. `# F` + `#### IRST IMPRESSIONS`). Hard to fix automatically.
- [ ] Short line fragments — ~52 very short lines in Tir Tairngire, likely OCR fragments. Spot-check to assess impact.

## Future

- [ ] D6: DuckDB parallel store + query router for comparative queries (implement after D4/D5 validated)
- [ ] Claude Code session sync — sync `~/.claude/projects/` across machines to preserve conversation history
