"""Configuration for Shadowrun Lore RAG system."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama connection
    ollama_host: str = "http://ollama-rag:11434"

    # Ollama models
    embedding_model: str = "mxbai-embed-large"
    llm_model: str = "llama3.1:8b"

    # Data paths
    data_path: Path = Path("/srv/shadowrun-rag")

    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Retrieval settings
    top_k: int = 5

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def pdf_path(self) -> Path:
        return self.data_path / "pdfs"

    @property
    def extracted_path(self) -> Path:
        return self.data_path / "extracted"

    @property
    def chroma_path(self) -> Path:
        return self.data_path / "chroma_db"


settings = Settings()
