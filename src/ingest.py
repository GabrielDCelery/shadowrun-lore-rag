"""Ingest PDFs into the RAG system."""

import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import MarkdownTextSplitter
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

from config import (
    CHROMA_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    EXTRACTED_PATH,
    OLLAMA_HOST,
    PDF_PATH,
)


def convert_pdfs_to_markdown():
    """Convert PDFs to markdown using marker-pdf."""
    print(f"Looking for PDFs in {PDF_PATH}")

    if not PDF_PATH.exists():
        print(f"Error: PDF path {PDF_PATH} does not exist")
        sys.exit(1)

    pdf_files = list(PDF_PATH.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {PDF_PATH}")
        return

    print(f"Found {len(pdf_files)} PDF files")
    EXTRACTED_PATH.mkdir(parents=True, exist_ok=True)

    # Initialize marker-pdf models
    print("Loading marker-pdf models...")
    model_dict = create_model_dict()
    converter = PdfConverter(artifact_dict=model_dict)

    for pdf_file in pdf_files:
        output_file = EXTRACTED_PATH / f"{pdf_file.stem}.md"

        if output_file.exists():
            print(f"Skipping {pdf_file.name} (already extracted)")
            continue

        print(f"Converting {pdf_file.name}...")
        try:
            rendered = converter(str(pdf_file))

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rendered.markdown)

            print(f"  Saved to {output_file.name}")
        except Exception as e:
            print(f"  Error converting {pdf_file.name}: {e}")


def load_and_chunk_documents():
    """Load markdown files and chunk them."""
    print(f"\nLoading documents from {EXTRACTED_PATH}")

    if not EXTRACTED_PATH.exists() or not list(EXTRACTED_PATH.glob("*.md")):
        print(f"No markdown files found in {EXTRACTED_PATH}")
        print("Run PDF conversion first")
        return []

    loader = DirectoryLoader(
        str(EXTRACTED_PATH),
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()
    print(f"Loaded {len(documents)} documents")

    print(f"Chunking with size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    text_splitter = MarkdownTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    return chunks


def create_vector_store(chunks):
    """Create embeddings and store in ChromaDB."""
    if not chunks:
        print("No chunks to process")
        return

    print(f"\nConnecting to Ollama at {OLLAMA_HOST}")
    print(f"Using embedding model: {EMBEDDING_MODEL}")

    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_HOST,
    )

    print(f"Creating vector store at {CHROMA_PATH}")
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    # Delete existing vector store
    if (CHROMA_PATH / "chroma.sqlite3").exists():
        print("Removing existing vector store")
        import shutil

        shutil.rmtree(CHROMA_PATH)
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)

    print("Generating embeddings and storing in ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_PATH),
    )

    print(f"Successfully created vector store with {len(chunks)} chunks")


def main():
    """Run the full ingestion pipeline."""
    print("=== Shadowrun Lore RAG Ingestion ===\n")

    # Step 1: Convert PDFs to markdown
    convert_pdfs_to_markdown()

    # Step 2: Load and chunk documents
    chunks = load_and_chunk_documents()

    # Step 3: Create vector store
    create_vector_store(chunks)

    print("\n=== Ingestion complete ===")


if __name__ == "__main__":
    main()
