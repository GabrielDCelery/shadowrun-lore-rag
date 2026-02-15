"""Ingest PDFs into the RAG system."""

import math

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import MarkdownTextSplitter

from config import settings
from logs import logger, setup_logging


def load_and_chunk_documents():
    """Load markdown files and chunk them."""
    logger.info(f"loading documents from {settings.extracted_path}")

    if not settings.extracted_path.exists() or not list(
        settings.extracted_path.glob("*.md")
    ):
        logger.info(f"no markdown files found in {settings.extracted_path}")
        return []

    loader = DirectoryLoader(
        str(settings.extracted_path),
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()
    logger.info(f"loaded {len(documents)} documents")

    logger.info(
        f"chunking with size={settings.chunk_size}, overlap={settings.chunk_overlap}"
    )
    text_splitter = MarkdownTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(f"created {len(chunks)} chunks")

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
