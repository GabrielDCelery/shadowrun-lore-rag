"""Generate Shadowrun-style shadowtalk conversations.

Multi-turn conversation between fixed character personas. Each character queries
the shared ChromaDB with their own perspective to get distinct lore context,
producing different takes on the same topic.

Usage:
    uv run python src/shadowtalk.py "Tell me about Aztlan corporate security"
"""

import sys
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import settings
from logs import logger, setup_logging


@dataclass
class Persona:
    handle: str
    description: str
    perspective: str  # prepended to retrieval query to shape what lore they pull


PERSONAS = [
    Persona(
        handle="FastJack",
        description=(
            "legendary veteran decker and fixer. Old school, seen everything twice. "
            "Speaks in short sharp sentences. Deeply cynical but rarely wrong. "
            "Knows where the bodies are buried — literally."
        ),
        perspective="veteran fixer and information broker perspective on",
    ),
    Persona(
        handle="Haze",
        description=(
            "young ork street shaman from Seattle. Passionate about awakened rights "
            "and parazoology. Tends to ramble when excited. Asks questions others "
            "find uncomfortable. Sees patterns others miss."
        ),
        perspective="street shaman and awakened community perspective on",
    ),
    Persona(
        handle="Bull",
        description=(
            "troll ex-corporate security turned street samurai. Thinks in terms of "
            "threats, angles, and exits. Blunt and direct. Has more corporate insider "
            "knowledge than he lets on."
        ),
        perspective="street samurai and corporate security perspective on",
    ),
]

TURNS = 6

OPEN_PROMPT = ChatPromptTemplate.from_template(
    """You are {handle} in a private encrypted Shadowrun Matrix chat with other shadowrunners.

Your character: {description}

Relevant lore from the Shadowrun world — react to this:
{context}

Topic: {topic}

Open the conversation with a reaction. 2-3 sentences. Do not start with your name or handle.
Do not conclude or wrap anything up. Stay in character."""
)

TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are {handle} in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Relevant lore — use this to ground your response:
{context}

Topic: {topic}

Conversation so far:
{history}

Respond as {handle}. 2-4 sentences. Do not start with your name or handle.
React to what was said, add something new from the lore, challenge a point, or shift the angle.
Stay in character. Do not conclude the conversation.{cutoff}"""
)


def load_retriever(vector_store: Chroma):
    return vector_store.as_retriever(search_kwargs={"k": settings.top_k})


def retrieve(retriever, query: str) -> str:
    docs = retriever.invoke(query)
    return "\n\n".join(doc.page_content for doc in docs)


def generate(llm: ChatOllama, prompt: ChatPromptTemplate, **kwargs) -> str:
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(kwargs).strip()


def format_line(handle: str, text: str) -> str:
    return f">>>{handle.upper()}: {text}<<<"


def run(topic: str) -> None:
    if not settings.chroma_path.exists():
        logger.error(f"vector store not found at {settings.chroma_path}")
        sys.exit(1)

    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_host,
        temperature=0.8,
    )
    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_host,
    )
    vector_store = Chroma(
        persist_directory=str(settings.chroma_path),
        embedding_function=embeddings,
    )
    retriever = load_retriever(vector_store)

    history_lines: list[str] = []

    for turn in range(TURNS):
        persona = PERSONAS[turn % len(PERSONAS)]
        is_last = turn == TURNS - 1

        context = retrieve(retriever, f"{persona.perspective} {topic}")

        if turn == 0:
            text = generate(
                llm,
                OPEN_PROMPT,
                handle=persona.handle,
                description=persona.description,
                context=context,
                topic=topic,
            )
        else:
            cutoff = (
                "\nIMPORTANT: End your response mid-sentence as if the signal dropped."
                if is_last
                else ""
            )
            text = generate(
                llm,
                TURN_PROMPT,
                handle=persona.handle,
                description=persona.description,
                context=context,
                topic=topic,
                history="\n".join(history_lines),
                cutoff=cutoff,
            )

        line = format_line(persona.handle, text)
        history_lines.append(line)
        print(line)
        print()

    print(">>> [SIGNAL LOST] <<<")


def main() -> None:
    setup_logging(settings.log_level)

    if len(sys.argv) < 2:
        print("Usage: python shadowtalk.py <topic>")
        print('Example: python shadowtalk.py "Tell me about Aztlan corporate security"')
        sys.exit(1)

    topic = " ".join(sys.argv[1:])
    run(topic)


if __name__ == "__main__":
    main()
