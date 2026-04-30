"""Generate Shadowrun-style shadowtalk conversations.

Multi-turn conversation between fixed character personas. Each character queries
the shared ChromaDB with their own perspective to get distinct lore context,
producing different takes on the same topic. Turn order is randomised with no
consecutive repeats.

Usage:
    uv run python src/shadowtalk.py "Tell me about Aztlan corporate security"
    uv run python src/shadowtalk.py --debug "Tell me about Aztlan corporate security" > out.json
"""

import json
import random
import sys
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import settings
from logs import logger, setup_logging


@dataclass
class Persona:
    handle: str
    description: str
    perspective: str


_SHARED_RULES = """Output rules — these override everything else:
- Plain text only — no ">", ">>", brackets, timestamps, or signatures
- No narration, no "I say", no "my avatar" — write the message itself
- No verbal acknowledgments — forbidden phrases include: "good point", "agreed", "NAME is right", "that's interesting", "I think NAME is onto something", "This X makes me think"
"""

OPEN_PROMPT = ChatPromptTemplate.from_template(
    """You are {handle} ({description}) in a private Shadowrun Matrix chat with other shadowrunners.

""" + _SHARED_RULES + """

Background knowledge:
{context}

Topic: {topic}

Open the conversation in 2-3 sentences. Use a specific detail from the background above.
Do not invent names or places not mentioned in the background."""
)

TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are {handle} ({description}) in a private Shadowrun Matrix chat with other shadowrunners.

""" + _SHARED_RULES + """

Background knowledge:
{context}

Last said:
{reply_to}

Respond in 2-3 sentences. React to what was just said — push further on it, contradict it, or name what it implies.
Use what you know from the background above. Do not invent names or places not in the background.{cutoff}"""
)

PERSONAS = [
    Persona(
        handle="FastJack",
        description="cuts to motive — who set it up, why now, who walks away clean",
        perspective="veteran decker and fixer perspective on",
    ),
    Persona(
        handle="Bull",
        description="reads the op structure — what the team composition tells you about the real objective",
        perspective="street samurai and corporate security perspective on",
    ),
    Persona(
        handle="Coyote",
        description="speaks from what she personally ran into — a spirit, a zone, something that cost her",
        perspective="street shaman and urban awakened perspective on",
    ),
    Persona(
        handle="Ledger",
        description="watches for when corps go quiet, when assets move, who takes the fall",
        perspective="corporate financial analyst and insider perspective on",
    ),
]

TURNS = 8  # 2 full rounds for 4 personas


def retrieve(
    vector_store: Chroma, query: str, exclude_ids: set[str], handle: str
) -> tuple[str, set[str], list[Document]]:
    search_kwargs: dict = {"k": settings.top_k}
    if exclude_ids:
        search_kwargs["filter"] = {"chunk_id": {"$nin": list(exclude_ids)}}
    search_kwargs["where_document"] = {"$not_contains": handle}
    docs = vector_store.similarity_search(query, **search_kwargs)
    new_ids = {doc.metadata["chunk_id"] for doc in docs if "chunk_id" in doc.metadata}
    context = "\n\n".join(doc.page_content for doc in docs)
    return context, new_ids, docs


def generate(llm: ChatOllama, prompt: ChatPromptTemplate, **kwargs) -> str:
    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke(kwargs).strip()
    return " ".join(raw.split())


def format_line(handle: str, text: str) -> str:
    return f">>>{handle.upper()}: {text}<<<"


def make_schedule(turns: int) -> list[Persona]:
    """Build a turn schedule: shuffled rounds of all personas, truncated to turns.

    Ensures no character speaks twice in a row across round boundaries by
    swapping if the last persona of one round matches the first of the next.
    """
    schedule: list[Persona] = []
    while len(schedule) < turns:
        round_ = PERSONAS[:]
        random.shuffle(round_)
        if schedule and schedule[-1] is round_[0]:
            round_[0], round_[1] = round_[1], round_[0]
        schedule.extend(round_)
    return schedule[:turns]


def run(topic: str, debug: bool = False) -> None:
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
    history_lines: list[str] = []
    used_ids: set[str] = set()
    schedule = make_schedule(TURNS)
    debug_turns: list[dict] = []

    for turn, persona in enumerate(schedule):
        is_last = turn == TURNS - 1

        query = f"{topic} {persona.perspective}"
        context, new_ids, docs = retrieve(
            vector_store, query, used_ids, persona.handle
        )
        used_ids.update(new_ids)

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
            reply_to = (
                history_lines[-1] if history_lines else "(you are first to speak)"
            )
            text = generate(
                llm,
                TURN_PROMPT,
                handle=persona.handle,
                description=persona.description,
                context=context,
                reply_to=reply_to,
                cutoff=cutoff,
            )

        history_lines.append(f"[{persona.handle}]: {text}")

        if debug:
            debug_turns.append({
                "turn": turn,
                "handle": persona.handle,
                "query": query,
                "chunks": [
                    {
                        "chunk_id": doc.metadata.get("chunk_id", ""),
                        "source": doc.metadata.get("source", ""),
                        "content": doc.page_content,
                    }
                    for doc in docs
                ],
                "text": text,
            })
        else:
            print(format_line(persona.handle, text))
            print()

    if debug:
        print(json.dumps({"topic": topic, "turns": debug_turns}, indent=2))
    else:
        print(">>> [SIGNAL LOST] <<<")


def main() -> None:
    setup_logging(settings.log_level)

    args = sys.argv[1:]
    debug = "--debug" in args
    args = [a for a in args if a != "--debug"]

    if not args:
        print("Usage: python shadowtalk.py [--debug] <topic>")
        print('Example: python shadowtalk.py "Tell me about Aztlan corporate security"')
        sys.exit(1)

    topic = " ".join(args)
    run(topic, debug=debug)


if __name__ == "__main__":
    main()
