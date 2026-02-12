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

1. Make sure ollama is deployed via the homelab repo `https://github.com/GabrielDCelery/personal-homelab`
2. Set up necessary dir structure on the homelab

```sh
# On the remote machine
sudo mkdir -p /srv/shadowrun-rag/{pdfs,extracted,chroma_db,model_cache}
sudo chown -R $USER:$USER /srv/shadowrun-rag
# place the pdfs into /srv/shadowrun-rag/pdfs
```

3. Set up `.env` file on the development machine
4. Run from the development machine (`./deploy.sh`)
5. Run the fillowing scripts from the development machine

```sh
ssh $HOMELAB_HOST docker exec shadowrun-rag uv run python src/ingest.py
# This will:
# - Convert PDFs to markdown using marker-pdf
# - Chunk the markdown into ~1000 char pieces
# - Generate embeddings and store in ChromaDB

docker exec -it shadowrun-rag uv run python src/query.py "What is essence in Shadowrun?"
docker exec -it shadowrun-rag uv run python src/query.py "How does magic work?" --sources
```
