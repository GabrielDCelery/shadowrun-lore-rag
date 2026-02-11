"""Configuration for Shadowrun Lore RAG system."""

import os
from pathlib import Path

# Ollama connection
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")

# Ollama models
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")

# Data paths
DATA_PATH = Path(os.getenv("DATA_PATH", "/srv/shadowrun-rag"))
PDF_PATH = DATA_PATH / "pdfs"
EXTRACTED_PATH = DATA_PATH / "extracted"
CHROMA_PATH = DATA_PATH / "chroma_db"

# Chunking settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval settings
TOP_K = 5
