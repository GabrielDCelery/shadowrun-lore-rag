# TODO

## Done

- [x] Commit pending changes (docs restructure, Dockerfile user setup, mise tasks, compose.yaml removal)
- [x] PDF organisation — normalise filenames via `normalise_pdf_filenames.py` (slugify, no pattern matching)
- [x] Invocation — added mise tasks (`run:normalise`, `run:convert`, `run:embed`, `run:query`) with `image:` prefix for build tasks
- [x] Dockerfile — create app user before dependency install, no chown needed
- [x] Pipeline directories — `pdfs_raw/`, `pdfs_normalised/`, `markdown_extracted/`, `markdown/`, `chroma_db/`
- [x] marker-pdf quality — enabled `drop_repeated_text` and `disable_ocr_math`

## Up Next

- [ ] Markdown post-processing — strip image references, navigation headers, page markers, malformed table rows (reads from `markdown_extracted/`, writes to `markdown/`)
- [ ] Table handling — implement D4 (table-aware chunking) and D5 (row-as-sentence conversion)

## Future

- [ ] D6: DuckDB parallel store + query router for comparative queries (implement after D4/D5 validated)
- [ ] Claude Code session sync — sync `~/.claude/projects/` across machines to preserve conversation history
