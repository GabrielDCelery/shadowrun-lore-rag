"""Ingest PDFs into the RAG system."""

import math

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from chunk_documents import chunk_markdown
from config import settings
from logs import logger, setup_logging


def load_and_chunk_documents():
    """Load markdown files and chunk them using two-pass table-aware chunker."""
    logger.info(f"loading documents from {settings.markdown_path}")

    md_files = list(settings.markdown_path.glob("*.md"))
    if not settings.markdown_path.exists() or not md_files:
        logger.info(f"no markdown files found in {settings.markdown_path}")
        return []

    logger.info(f"found {len(md_files)} markdown files")
    logger.info(
        f"chunking with size={settings.chunk_size}, overlap={settings.chunk_overlap}"
    )

    chunks: list[Document] = []
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        file_chunks = chunk_markdown(
            content=content,
            source=md_file.name,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        logger.info(f"  {md_file.name} → {len(file_chunks)} chunks")
        chunks.extend(file_chunks)

    logger.info(f"created {len(chunks)} chunks total")
    return chunks


def create_vector_store(chunks: list[Document]):
    """Create embeddings and store in ChromaDB."""
    if not chunks:
        logger.info("no chunks to process")
        return

    logger.info(f"connecting to Ollama at {settings.ollama_host}")
    logger.info(f"using embedding model: {settings.embedding_model}")

    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_host,
    )

    logger.info(f"creating vector store at {settings.chroma_path}")
    settings.chroma_path.mkdir(parents=True, exist_ok=True)

    # Clear existing vector store contents (can't delete mount point)
    if (settings.chroma_path / "chroma.sqlite3").exists():
        logger.info("clearing existing vector store")
        import shutil

        for item in settings.chroma_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    logger.info("generating embeddings and storing in ChromaDB")

    batch_size = settings.embedding_batch_size
    vector_store = None

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        curr_batch = math.floor(i / batch_size) + 1
        total_batch_count = math.ceil(len(chunks) / batch_size)
        logger.info(f"processing batch {curr_batch}/{total_batch_count}")

        if vector_store is None:
            vector_store = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=str(settings.chroma_path),
            )
        else:
            try:
                vector_store.add_documents(batch)
            except Exception as e:
                logger.warning(f"batch {curr_batch} failed: {e}, trying individually")
                for idx, document in enumerate(batch):
                    try:
                        vector_store.add_documents([document])
                    except Exception:
                        logger.error(f"skipping chunk {i+idx}")

    logger.info(f"successfully created vector store with {len(chunks)} chunks")


def main():
    """Run the full ingestion pipeline."""
    setup_logging(settings.log_level)

    logger.info("shadowrun lore RAG ingestion started")

    # Step 2: Load and chunk documents
    chunks = load_and_chunk_documents()

    # Step 3: Create vector store
    create_vector_store(chunks)

    logger.info("shadowrun lore RAG ingestion complete")


if __name__ == "__main__":
    main()
