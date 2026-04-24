# TODO

## In Progress

- [x] Commit pending changes (docs restructure, Dockerfile user setup, mise tasks, compose.yaml removal)

## Up Next

- [ ] PDF organisation — audit for duplicates, establish clean naming/structure before re-running extraction
- [ ] Invocation — add mise tasks for convert, embed, query instead of raw `docker exec ... uv run python ...`
- [ ] Table handling — implement D4 (table-aware chunking) and D5 (row-as-sentence conversion)
- [ ] Markdown quality — fine-tune marker-pdf extraction after PDFs are clean

## Future

- [ ] D6: DuckDB parallel store + query router for comparative queries (implement after D4/D5 validated)
