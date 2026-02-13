# What is this project?

Shadowrun is a Role-playing game from the 90s that I grew up with and got very fond memories of. This is a project idea that I have been toying with for a while but when I saw this article [Guide to RAG embeddings](https://medium.com/@sharanharsoor/the-complete-guide-to-embeddings-and-rag-from-theory-to-production-758a16d747ac) I decided to put things into action.

Here we are, a RAG system for querying Shadowrun RPG rulebooks using natural language. Runs on a homelab with Ollama.

![Screenshot Shadowrun 03](./assets/screenshot-shadowrun-03.jpg)
![Screenshot Shadowrun 01](./assets/screenshot-shadowrun-01.jpg)
![Screenshot Shadowrun 02](./assets/screenshot-shadowrun-02.jpg)

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

| Component      | Choice                                      |
| -------------- | ------------------------------------------- |
| PDF extraction | marker-pdf                                  |
| Chunking       | langchain text splitters (markdown-aware)   |
| Embeddings     | Ollama `mxbai-embed-large`                  |
| Vector store   | ChromaDB                                    |
| LLM            | Ollama (configurable: llama3.1:8b, mistral) |

## Configuration

| Variable      | Description              | Required | Default                             |
| ------------- | ------------------------ | -------- | ----------------------------------- |
| `OLLAMA_HOST` | Ollama API URL           | No       | `http://host.docker.internal:11434` |
| `DATA_PATH`   | Base path for data files | No       | `/srv/shadowrun-rag`                |
| `LLM_MODEL`   | Ollama model for answers | No       | `llama3.2`                          |

Secrets are stored in: None

## Deployment

1. Set up necessary dir structure on the machine you want to run the containers on

```sh
/srv/ollama/        # mount point for ollama
/srv/shadowrun-rag/ # mount point for shadowrun-rag
├── pdfs/           # Source PDFs (read-only)
├── extracted/      # Markdown output from marker-pdf
└── chroma_db/      # Vector database
```

```sh
# On the remote machine
sudo mkdir -p /srv/ollama
sudo chown -R $USER:$USER /srv/ollama
sudo mkdir -p /srv/shadowrun-rag/{pdfs,extracted,chroma_db,model_cache}
sudo chown -R $USER:$USER /srv/shadowrun-rag
# place the pdfs into /srv/shadowrun-rag/pdfs
```

3. Set up `.env` file on the development machine
4. Run from the development machine (`./deploy.sh`)
5. Run the following scripts from the development machine

```sh
ssh $HOMELAB_HOST docker exec shadowrun-rag uv run python src/ingest.py
# This will:
# - Convert PDFs to markdown using marker-pdf
# - Chunk the markdown into ~1000 char pieces
# - Generate embeddings and store in ChromaDB

# Also while it is running worth verifying if the GPU is being used
ssh $HOMELAB_HOST nvidia-smi
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.126.09             Driver Version: 580.126.09     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 3060        Off |   00000000:01:00.0 Off |                  N/A |
|  0%   40C    P2             36W /  170W |    3453MiB /  12288MiB |      0%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A           17892      C   /app/.venv/bin/python3                 3444MiB |
+-----------------------------------------------------------------------------------------+
```

6. Once the PDFs have been analyzed have fun

```sh
docker exec -it shadowrun-rag uv run python src/query.py "What is Tír Tairngire"
docker exec -it shadowrun-rag uv run python src/query.py "How does magic work?" --sources
```
