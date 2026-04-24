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

## Up Next

- [ ] Test queries — verify retrieval quality for prose, table, and comparative questions after embedding

## Known Markdown Extraction Issues (potential future fixes)

- [ ] Split headings — OCR breaks decorative capital letters into separate single-char headings (e.g. `# F` + `#### IRST IMPRESSIONS`). Hard to fix automatically.
- [ ] Short line fragments — ~52 very short lines in Tir Tairngire, likely OCR fragments. Spot-check to assess impact.

## Future

- [ ] D6: DuckDB parallel store + query router for comparative queries (implement after D4/D5 validated)
- [ ] Claude Code session sync — sync `~/.claude/projects/` across machines to preserve conversation history
