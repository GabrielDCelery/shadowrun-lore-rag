"""Configuration for Shadowrun Lore RAG system."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ollama connection
    ollama_host: str = "http://ollama:11434"

    # Ollama models
    embedding_model: str = "mxbai-embed-large"
    llm_model: str = "llama3.1:8b"

    # Data paths
    data_path: Path = Path("/data")

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval settings
    top_k: int = 5

    # Embedding config
    embedding_batch_size: int = 10

    # Logging
    log_level: str = "INFO"

    @property
    def pdfs_raw_path(self) -> Path:
        return self.data_path / "pdfs_raw"

    @property
    def pdfs_normalised_path(self) -> Path:
        return self.data_path / "pdfs_normalised"

    @property
    def markdown_extracted_path(self) -> Path:
        return self.data_path / "markdown_extracted"

    @property
    def markdown_path(self) -> Path:
        return self.data_path / "markdown_clean"

    @property
    def chroma_path(self) -> Path:
        return self.data_path / "chroma_db"


settings = Settings()
