"""Query the Shadowrun Lore RAG system."""

import sys

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import settings
from logs import logger


def load_vector_store():
    """Load the existing ChromaDB vector store."""
    if not settings.chroma_path.exists():
        logger.error(f"error: vector store not found at {settings.chroma_path}")
        sys.exit(1)

    logger.info(f"loading vector store from {settings.chroma_path}")
    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_host,
    )

    vector_store = Chroma(
        persist_directory=str(settings.chroma_path),
        embedding_function=embeddings,
    )

    return vector_store


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)


def create_rag_chain(vector_store):
    """Create a RAG chain with the vector store using LCEL."""
    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_host,
        temperature=0,
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": settings.top_k})

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
    logger.info(f"using model: {settings.llm_model}")
    logger.info(f"retrieving top {settings.top_k} relevant chunks\n")

    vector_store = load_vector_store()
    rag_chain, retriever = create_rag_chain(vector_store)

    logger.debug(f"question: {question}\n")
    logger.debug("generating answer...\n")

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
