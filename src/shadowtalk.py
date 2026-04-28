"""Generate Shadowrun-style shadowtalk conversations.

Multi-turn conversation between fixed character personas. Each character queries
the shared ChromaDB with their own perspective to get distinct lore context,
producing different takes on the same topic. Turn order is randomised with no
consecutive repeats.

Usage:
    uv run python src/shadowtalk.py "Tell me about Aztlan corporate security"
"""

import random
import sys
from dataclasses import dataclass, field

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
    perspective: str


OPEN_PROMPT = ChatPromptTemplate.from_template(
    """You are {handle} in a private Shadowrun Matrix chat with other shadowrunners.

Background knowledge:
{context}

Topic: {topic}

Open the conversation in 2-3 sentences. Use a specific detail from the background above.
Do not invent names or places not mentioned in the background."""
)

TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are {handle} in a private Shadowrun Matrix chat with other shadowrunners.

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
        description=(
            "legendary veteran decker and fixer, male. Been in the shadows long enough to stop "
            "caring about what and start asking why. Deeply cynical — assumes everything is a "
            "play and someone is benefiting. When everyone else is tracking the threat, he's "
            "tracking the motive: who set this up, why now, who walks away clean. Speaks in "
            "clipped fragments — never more than 10 words per sentence. Drops a fact only when "
            "it points at something bigger. States conclusions, never speculates out loud."
        ),
        perspective="veteran decker and fixer perspective on",
    ),
    Persona(
        handle="Bull",
        description=(
            "troll ex-corporate security turned street samurai, male. Ran corporate security "
            "long enough to know that the contract never says what the job actually is. Reads "
            "ops by their structure: what kind of team they hired, who's running point, whether "
            "it's official or deniable. That tells him more than anything in the briefing. "
            "Blunt and specific — never trades in general cynicism when he can name the play. "
            "Speaks from what he's run or seen run, not from what he thinks corps are like."
        ),
        perspective="street samurai and corporate security perspective on",
    ),
    Persona(
        handle="Coyote",
        description=(
            "human street shaman, female, Coyote totem. Grew up in the Barrens, learned magic "
            "the hard way. Treats spirits as dangerous tools — respects them, doesn't romanticise "
            "them. Knows urban astral terrain: background counts, toxic zones, spirit territories, "
            "what kills what. Speaks plainly and fast. No mysticism, no philosophy — just "
            "what she's seen and what it costs."
        ),
        perspective="street shaman and urban awakened perspective on",
    ),
    Persona(
        handle="Ledger",
        description=(
            "former mid-level Aztechnology financial analyst turned shadowrunner, female. "
            "Left Aztec because she saw how it ends for people who know too much — and she "
            "knows too much. Paranoid in a specific way: she recognises corp plays the way "
            "you recognise a con you've been run before. Watches for when corps go quiet, "
            "when assets move, when executives disappear from public agendas. Speaks in short "
            "tight bursts — not because she's efficient but because she's always listening for "
            "the door. Never invents a number. Expresses risk as behaviour: which corp moves, "
            "which exec goes silent, who starts restructuring."
        ),
        perspective="corporate financial analyst and insider perspective on",
    ),
]

TURNS = 8  # 2 full rounds for 4 personas


def retrieve(
    vector_store: Chroma, query: str, exclude_ids: set[str], handle: str
) -> tuple[str, set[str]]:
    search_kwargs: dict = {"k": settings.top_k}
    if exclude_ids:
        search_kwargs["filter"] = {"chunk_id": {"$nin": list(exclude_ids)}}
    search_kwargs["where_document"] = {"$not_contains": handle}
    docs = vector_store.similarity_search(query, **search_kwargs)
    new_ids = {doc.metadata["chunk_id"] for doc in docs if "chunk_id" in doc.metadata}
    return "\n\n".join(doc.page_content for doc in docs), new_ids


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
    history_lines: list[str] = []
    used_ids: dict[str, set[str]] = {p.handle: set() for p in PERSONAS}
    schedule = make_schedule(TURNS)

    for turn, persona in enumerate(schedule):
        is_last = turn == TURNS - 1

        query = f"{topic} {persona.perspective}"
        context, new_ids = retrieve(
            vector_store, query, used_ids[persona.handle], persona.handle
        )
        used_ids[persona.handle].update(new_ids)

        if turn == 0:
            text = generate(
                llm,
                OPEN_PROMPT,
                handle=persona.handle,
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
                context=context,
                reply_to=reply_to,
                cutoff=cutoff,
            )

        history_lines.append(f"[{persona.handle}]: {text}")
        print(format_line(persona.handle, text))
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
