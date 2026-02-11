# Shadowrun Lore RAG

A RAG system for querying Shadowrun RPG rulebooks using natural language. Runs on a homelab with Ollama.

## Architecture

```
PDFs → marker-pdf → markdown → chunks → embeddings → ChromaDB
                                                         ↓
                           query → retrieve → Ollama LLM → answer
```

| Component      | Choice                                          |
| -------------- | ----------------------------------------------- |
| PDF extraction | marker-pdf                                      |
| Chunking       | langchain text splitters (markdown-aware)       |
| Embeddings     | Ollama `nomic-embed-text`                       |
| Vector store   | ChromaDB (file-based)                           |
| LLM            | Ollama (user's choice: llama3.2, mistral, etc.) |
| Orchestration  | langchain + langchain-ollama                    |

## Infrastructure

- **This repo:** Application code only
- **Homelab repo:** `~/projects/github-GabrielDCelery/personal-homelab` manages Ollama and other services
- **Ollama:** Runs separately in Docker on homelab (GPU-enabled), exposed on port 11434
- **Data path:** `/srv/shadowrun-rag/` on homelab (not in repo)
  - `pdfs/` - source PDFs (read-only)
  - `extracted/` - markdown output from marker-pdf
  - `chroma_db/` - vector database

## Development Workflow

1. Edit code locally on laptop
2. `git push`
3. `./deploy.sh` - SSHs to homelab, pulls, builds, restarts container
4. Query via: `ssh homelab docker exec -it shadowrun-rag python src/query.py "your question"`

## Key Files

| File            | Purpose                                           |
| --------------- | ------------------------------------------------- |
| `src/ingest.py` | Process PDFs, chunk, embed, store in ChromaDB     |
| `src/query.py`  | CLI interface to ask questions                    |
| `src/config.py` | Settings (paths, Ollama host)                     |
| `compose.yaml`  | Container config, mounts data, connects to Ollama |
| `deploy.sh`     | One-command deployment to homelab                 |

## Environment Variables

| Variable      | Description        | Default                             |
| ------------- | ------------------ | ----------------------------------- |
| `OLLAMA_HOST` | Ollama API URL     | `http://host.docker.internal:11434` |
| `DATA_PATH`   | Base path for data | `/srv/shadowrun-rag`                |

## Decisions

See `.claude/docs/decisions.md` for architecture decisions and rationale.

## Status

- [x] Architecture decisions made
- [x] AI context files created
- [ ] Ingest pipeline (`src/ingest.py`)
- [ ] Query CLI (`src/query.py`)
- [ ] Dockerfile and compose.yaml
- [ ] deploy.sh script
- [ ] Test with actual PDFs
