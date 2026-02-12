"""Ingest PDFs into the RAG system."""

import sys

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import MarkdownTextSplitter
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

from config import settings


def convert_pdfs_to_markdown():
    """Convert PDFs to markdown using marker-pdf."""
    print(f"Looking for PDFs in {settings.pdf_path}")

    if not settings.pdf_path.exists():
        print(f"Error: PDF path {settings.pdf_path} does not exist")
        sys.exit(1)

    pdf_files = list(settings.pdf_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {settings.pdf_path}")
        return

    print(f"Found {len(pdf_files)} PDF files")
    settings.extracted_path.mkdir(parents=True, exist_ok=True)

    # Initialize marker-pdf models
    print("Loading marker-pdf models...")
    model_dict = create_model_dict()
    converter = PdfConverter(artifact_dict=model_dict)

    for pdf_file in pdf_files:
        output_file = settings.extracted_path / f"{pdf_file.stem}.md"

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
    print(f"\nLoading documents from {settings.extracted_path}")

    if not settings.extracted_path.exists() or not list(
        settings.extracted_path.glob("*.md")
    ):
        print(f"No markdown files found in {settings.extracted_path}")
        print("Run PDF conversion first")
        return []

    loader = DirectoryLoader(
        str(settings.extracted_path),
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()
    print(f"Loaded {len(documents)} documents")

    print(f"Chunking with size={settings.chunk_size}, overlap={settings.chunk_overlap}")
    text_splitter = MarkdownTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    return chunks


def create_vector_store(chunks):
    """Create embeddings and store in ChromaDB."""
    if not chunks:
        print("No chunks to process")
        return

    print(f"\nConnecting to Ollama at {settings.ollama_host}")
    print(f"Using embedding model: {settings.embedding_model}")

    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_host,
    )

    print(f"Creating vector store at {settings.chroma_path}")
    settings.chroma_path.mkdir(parents=True, exist_ok=True)

    # Clear existing vector store contents (can't delete mount point)
    if (settings.chroma_path / "chroma.sqlite3").exists():
        print("Clearing existing vector store")
        import shutil

        for item in settings.chroma_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    print("Generating embeddings and storing in ChromaDB...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(settings.chroma_path),
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
