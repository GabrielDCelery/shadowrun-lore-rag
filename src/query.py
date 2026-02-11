"""Query the Shadowrun Lore RAG system."""

import sys

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import CHROMA_PATH, EMBEDDING_MODEL, LLM_MODEL, OLLAMA_HOST, TOP_K


def load_vector_store():
    """Load the existing ChromaDB vector store."""
    if not CHROMA_PATH.exists():
        print(f"Error: Vector store not found at {CHROMA_PATH}")
        print("Run ingest.py first to create the vector store")
        sys.exit(1)

    print(f"Loading vector store from {CHROMA_PATH}")
    embeddings = OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_HOST,
    )

    vector_store = Chroma(
        persist_directory=str(CHROMA_PATH),
        embedding_function=embeddings,
    )

    return vector_store


def create_qa_chain(vector_store):
    """Create a QA chain with the vector store."""
    llm = ChatOllama(
        model=LLM_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0,
    )

    prompt_template = """You are an expert on the Shadowrun RPG system. Use the following pieces of context from the Shadowrun rulebooks to answer the question. If you don't know the answer based on the context, say so - don't make up information.

Context:
{context}

Question: {question}

Answer:"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": TOP_K}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True,
    )

    return qa_chain


def query(question: str, show_sources: bool = False):
    """Query the RAG system."""
    print(f"Using model: {LLM_MODEL}")
    print(f"Retrieving top {TOP_K} relevant chunks\n")

    vector_store = load_vector_store()
    qa_chain = create_qa_chain(vector_store)

    print(f"Question: {question}\n")
    print("Generating answer...\n")

    result = qa_chain.invoke({"query": question})

    print("Answer:")
    print(result["result"])

    if show_sources:
        print("\n" + "=" * 80)
        print("Sources:")
        for i, doc in enumerate(result["source_documents"], 1):
            source = doc.metadata.get("source", "Unknown")
            print(f"\n[{i}] {source}")
            print(doc.page_content[:200] + "...")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python query.py <question> [--sources]")
        print('\nExample: python query.py "What is essence in Shadowrun?"')
        print('         python query.py "How does magic work?" --sources')
        sys.exit(1)

    # Check for --sources flag
    show_sources = "--sources" in sys.argv
    if show_sources:
        sys.argv.remove("--sources")

    question = " ".join(sys.argv[1:])

    print("=== Shadowrun Lore RAG Query ===\n")
    query(question, show_sources=show_sources)


if __name__ == "__main__":
    main()
