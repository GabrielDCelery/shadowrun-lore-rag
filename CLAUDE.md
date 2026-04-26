# Shadowrun Lore RAG

A RAG system for querying Shadowrun RPG rulebooks using natural language. Runs on a homelab with Ollama.

## Architecture

```
pdfs_raw/ → normalise → pdfs_normalised/ → marker-pdf → markdown_extracted/ → clean → markdown_clean/ → strip_toc → markdown_stripped/ → chunks → embeddings → ChromaDB
                                                                                              ↓
                                                          query → retrieve → Ollama LLM → answer
```

## Key Files

| File                                  | Purpose                                          |
| ------------------------------------- | ------------------------------------------------ |
| `src/normalise_pdf_filenames.py`      | Copy PDFs from pdfs_raw/ to pdfs_normalised/ with normalised names |
| `src/convert_pdfs_to_markdown.py`     | Convert PDFs to markdown using marker-pdf; `--use-llm --book <name>` for LLM-assisted table fixing on specific books |
| `src/clean_markdown.py`              | Fix OCR artifacts, expand currency symbols (¥→nuyen, £→Irish punts), normalise table whitespace |
| `src/strip_toc.py`                   | Remove ToC/Credits/Index sections                |
| `src/create_embeddings.py`            | Chunk markdown (table-aware), create embeddings, store in ChromaDB |
| `src/evaluate.py`                     | Two-pass evaluation: pass1 generates answers, pass2 judges with separate LLM |
| `src/query.py`                        | CLI interface to ask questions                   |
| `src/config.py`                       | Pydantic settings (paths, models, tuning)        |
| `src/logs.py`                         | Logging configuration                            |
| `Dockerfile`                          | Python 3.12 + uv + marker-pdf dependencies       |
| `tests/rag_queries.md`                | 41 test questions with expected answers across all books |

## Development Workflow

1. Edit code locally on laptop
2. Push changes — `personal-homelab` repo handles building the image and deploying
3. Run pipeline steps via mise tasks (see `mise.toml`)

## Decisions

See `docs/02-decisions.md` for architecture decisions and rationale.
