"""Query the Shadowrun Lore RAG system."""

import sys

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
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


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_chain(vector_store):
    """Create a RAG chain with the vector store using LCEL."""
    llm = ChatOllama(
        model=LLM_MODEL,
        base_url=OLLAMA_HOST,
        temperature=0,
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})

    prompt = ChatPromptTemplate.from_template(
        """You are an expert on the Shadowrun RPG system. Use the following pieces of context from the Shadowrun rulebooks to answer the question. If you don't know the answer based on the context, say so - don't make up information.

Context:
{context}

Question: {question}

Answer:"""
    )

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain, retriever


def query(question: str, show_sources: bool = False):
    """Query the RAG system."""
    print(f"Using model: {LLM_MODEL}")
    print(f"Retrieving top {TOP_K} relevant chunks\n")

    vector_store = load_vector_store()
    rag_chain, retriever = create_rag_chain(vector_store)

    print(f"Question: {question}\n")
    print("Generating answer...\n")

    answer = rag_chain.invoke(question)

    print("Answer:")
    print(answer)

    if show_sources:
        docs = retriever.invoke(question)
        print("\n" + "=" * 80)
        print("Sources:")
        for i, doc in enumerate(docs, 1):
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
