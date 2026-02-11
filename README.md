# Shadowrun Lore RAG

A RAG system for querying Shadowrun RPG rulebooks using natural language. Runs on a homelab with Ollama.

## Quick Start

```sh
git clone <repo>
cd shadowrun-lore-rag
uv sync
./deploy.sh
```

## Architecture

- **Language/Framework**: Python 3.12
- **Database**: ChromaDB (file-based vector store)
- **Hosting**: Homelab (Docker)
- **Messaging**: None
- **Storage**: Local filesystem (`/srv/shadowrun-rag/`)
- **Provisioning**: None
- **External APIs**: Ollama (LLM and embeddings)

```
PDFs → marker-pdf → markdown → chunks → embeddings → ChromaDB
                                                         ↓
                           query → retrieve → Ollama LLM → answer
```

| Component      | Choice                                    |
| -------------- | ----------------------------------------- |
| PDF extraction | marker-pdf                                |
| Chunking       | langchain text splitters (markdown-aware) |
| Embeddings     | Ollama `nomic-embed-text`                 |
| Vector store   | ChromaDB                                  |
| LLM            | Ollama (configurable: llama3.2, mistral)  |

## Configuration

| Variable      | Description              | Required | Default                             |
| ------------- | ------------------------ | -------- | ----------------------------------- |
| `OLLAMA_HOST` | Ollama API URL           | No       | `http://host.docker.internal:11434` |
| `DATA_PATH`   | Base path for data files | No       | `/srv/shadowrun-rag`                |
| `LLM_MODEL`   | Ollama model for answers | No       | `llama3.2`                          |

Secrets are stored in: None

### Data Directory Structure

```
/srv/shadowrun-rag/
├── pdfs/        # Source PDFs (read-only)
├── extracted/   # Markdown output from marker-pdf
└── chroma_db/   # Vector database
```

## Development

```sh
uv sync
uv run python src/ingest.py
uv run python src/query.py "What is essence?"
```

## Deployment

- **Provisioning**: None
- **Infrastructure**: Homelab (Docker)
- **CI/CD**: Manual (`./deploy.sh`)
- **Environments**: prod only

### Deploy to Homelab

```sh
git push
./deploy.sh
```

### Run Commands on Homelab

```sh
# Ingest PDFs
ssh homelab docker exec -it shadowrun-rag uv run python src/ingest.py

# Query
ssh homelab docker exec -it shadowrun-rag uv run python src/query.py "your question"

# Query with sources
ssh homelab docker exec -it shadowrun-rag uv run python src/query.py "your question" --sources
```
