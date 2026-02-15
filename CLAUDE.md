# Shadowrun Lore RAG

A RAG system for querying Shadowrun RPG rulebooks using natural language. Runs on a homelab with Ollama.

## Architecture

```
PDFs → marker-pdf → markdown → chunks → embeddings → ChromaDB
                                                         ↓
                           query → retrieve → Ollama LLM → answer
```

| Component      | Choice                                    |
| -------------- | ----------------------------------------- |
| PDF extraction | marker-pdf                                |
| Chunking       | langchain text splitters (markdown-aware) |
| Embeddings     | Ollama `mxbai-embed-large`                |
| Vector store   | ChromaDB (file-based)                     |
| LLM            | Ollama `llama3.1:8b` (configurable)       |
| Orchestration  | langchain + langchain-ollama              |

## Infrastructure

- **This repo:** Application code + compose.yaml (runs both RAG app and Ollama)
- **Ollama:** Runs in Docker container (`ollama-rag`) with GPU access
- **Data path:** `/srv/shadowrun-rag/` on homelab (mounted into container as `/data`)
  - `pdfs/` - source PDFs (read-only)
  - `extracted/` - markdown output from marker-pdf
  - `chroma_db/` - vector database
  - `model_cache/` - marker-pdf model cache

## Development Workflow

1. Edit code locally on laptop
2. Create docker context for remote: `docker context create shadowrun-rag --docker "host=ssh://user@host"`
3. `docker context use shadowrun-rag`
4. `docker compose build && docker compose up -d`
5. Convert PDFs: `docker exec shadowrun-rag uv run python src/convert_pdfs_to_markdown.py`
6. Create embeddings: `docker exec shadowrun-rag uv run python src/create_embeddings.py`
7. Query: `docker exec -it shadowrun-rag uv run python src/query.py "your question"`

## Key Files

| File                              | Purpose                                        |
| --------------------------------- | ---------------------------------------------- |
| `src/convert_pdfs_to_markdown.py` | Convert PDFs to markdown using marker-pdf      |
| `src/create_embeddings.py`        | Chunk markdown, create embeddings, store in DB |
| `src/query.py`                    | CLI interface to ask questions                 |
| `src/config.py`                   | Pydantic settings (paths, models, tuning)      |
| `src/logs.py`                     | Logging configuration                          |
| `compose.yaml`                    | Container config for RAG app + Ollama          |
| `Dockerfile`                      | Python 3.12 + uv + marker-pdf dependencies     |

## Environment Variables

| Variable                | Description                       | Default                   |
| ----------------------- | --------------------------------- | ------------------------- |
| `OLLAMA_HOST`           | Ollama API URL                    | `http://ollama-rag:11434` |
| `EMBEDDING_MODEL`       | Ollama model for embeddings       | `mxbai-embed-large`       |
| `LLM_MODEL`             | Ollama model for answers          | `llama3.1:8b`             |
| `DATA_PATH`             | Base path for data files          | `/srv/shadowrun-rag`      |
| `CHUNK_SIZE`            | Text chunk size (characters)      | `1000`                    |
| `CHUNK_OVERLAP`         | Overlap between chunks            | `200`                     |
| `TOP_K`                 | Number of chunks to retrieve      | `5`                       |
| `EMBEDDING_BATCH_SIZE`  | Batch size for embedding creation | `10`                      |
| `LOG_LEVEL`             | Logging level                     | `INFO`                    |

## Decisions

See `.claude/docs/decisions.md` for architecture decisions and rationale.
