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
    turn_prompt: ChatPromptTemplate | None = field(default=None, repr=False)


OPEN_PROMPT = ChatPromptTemplate.from_template(
    """You are {handle} in a private encrypted Shadowrun Matrix chat with other shadowrunners.

Your character: {description}

Lore pulled from the shadows — use specific details from this, don't summarise it:
{context}

Topic: {topic}

Open the conversation. Exactly 2-3 sentences, no more.
- Your specifics must come from the lore above — do not invent locations, corps, or events not mentioned there
- Speak from your own angle — something you saw, ran, or heard. Not "the corps do X" but name the specific corp, division, or location from the lore
- Drop at least one specific proper noun from the lore: a corp, city, person, weapon, spell, or gang name
- Do not start with your handle or name
- Do not wrap up or conclude anything"""
)

_SHARED_RULES = """Hard rules — violating any of these is a failure:
- NEVER cite a source ("according to X", "the book says", "SRII states") — you speak from lived experience, not documents
- NEVER invent a specific location or character name that does not appear in the background knowledge above. If you need a place, use a vague descriptor ("an Aztechnology compound", "a Barrens factory", "downtown Seattle") not an invented proper noun.
- Do NOT repeat or rephrase anything listed under YOUR PREVIOUS LINES above — those are banned, say something new.
- Do NOT claim an experience another character already claimed — you were not on their run, you did not see what they saw.
- Do NOT acknowledge, repeat, or rephrase what was just said — you heard it, skip the acknowledgment, say what you know.
- Do not end with your handle or name. Do not start with your handle or name."""

FASTJACK_TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are FastJack in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Background knowledge — treat this as things you've learned firsthand, not a document:
{context}

YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
{own_history}

Last said (context only — you heard it, do not restate it):
{reply_to}

Respond as FastJack. Exactly 2-3 sentences, no more.
You heard that. Drop what you know in plain speech — don't acknowledge what they said, just add it.
If you have a name, a corp, or a number that fits, say it and move on. You do not ask others for
information; you already have it or you don't care.
FastJack speaks in clipped fragments — never more than 10 words per sentence, never a question when a statement will do.
Never use headers, labels, or colons to introduce a point. Speak, don't report.
""" + _SHARED_RULES + "{cutoff}"
)

# AELINDRA_TURN_PROMPT = ChatPromptTemplate.from_template(
#     """You are Aelindra in a private encrypted Shadowrun Matrix chat.
#
#     Your character: {description}
#
#     Background knowledge — treat this as things you've learned firsthand, not a document:
#     {context}
#
#     YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
#     {own_history}
#
#     Conversation so far:
#     {history}
#
#     Respond as Aelindra. Exactly 2-3 sentences, no more.
#     Your move: add the Awakened angle the others are missing. Correct a magical misconception,
#     name a specific spirit type, tradition, or ritual detail from the background knowledge, or
#     point out a consequence the others haven't thought through. Stay on the topic — engage with
#     what was just said, then add something concrete from what you know.
#     """ + _SHARED_RULES + "{cutoff}"
# )

BULL_TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are Bull in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Background knowledge — treat this as things you've learned firsthand, not a document:
{context}

YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
{own_history}

Last said (context only — you heard it, do not restate it):
{reply_to}

Respond as Bull. Exactly 2-3 sentences, no more.
You heard that. Say what you actually know about who's running this, what it's costing, and who
gets hurt — don't acknowledge what they said, just add your read. If you've seen this play before,
name the outcome. Never a question, never speculation — you assess, you don't wonder.
Never use headers, labels, or colons to introduce a point. Speak, don't report.
""" + _SHARED_RULES + "{cutoff}"
)

COYOTE_TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are Coyote in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Background knowledge — treat this as things you've learned firsthand, not a document:
{context}

YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
{own_history}

Last said (context only — you heard it, do not restate it):
{reply_to}

Respond as Coyote. Exactly 2-3 sentences, no more.
You heard that. Say what the astral situation actually looks like — don't acknowledge what they
said, just add what you know. Background count, spirit type, whether a ritual is still running —
say it the way a mechanic talks about an engine. Never more than 12 words per sentence. No philosophy, no metaphor.
Never use headers, labels, or colons to introduce a point. Speak, don't report.
""" + _SHARED_RULES + "{cutoff}"
)

LEDGER_TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are Ledger in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Background knowledge — treat this as things you've learned firsthand, not a document:
{context}

YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
{own_history}

Last said (context only — you heard it, do not restate it):
{reply_to}

Respond as Ledger. Exactly 2-3 sentences, no more.
You heard that. Say what the financial or legal exposure actually looks like — don't acknowledge
what they said, just add the numbers. Who's on the hook, how much, and why it matters to the run.
Never more than 12 words per sentence. No small talk. Never a question.
Never use headers, labels, or colons to introduce a point. Speak, don't report.
""" + _SHARED_RULES + "{cutoff}"
)

PERSONAS = [
    Persona(
        handle="FastJack",
        description=(
            "legendary veteran decker and fixer, male. Old school — been in the shadows longer "
            "than most runners have been alive. Deeply cynical, world-weary, rarely surprised. "
            "Knows corps, contacts, and the Matrix better than anyone. Speaks in clipped, blunt "
            "fragments — never more than 10 words per sentence. When he has Matrix intel he drops "
            "it plainly; when he has street intel he drops that instead. Does not explain himself."
        ),
        perspective="veteran decker and fixer perspective on",
        turn_prompt=FASTJACK_TURN_PROMPT,
    ),
    # Persona(
    #     handle="Aelindra",
    #     description=(
    #         "elven shaman, female, ancient and unhurried. Mostly direct and precise — "
    #         "she has no patience for unnecessary words. Occasionally lets slip a metaphor "
    #         "or an oblique reference, but only when it says more than plain speech would. "
    #         "Carries centuries of memory and finds human short-termism quietly exasperating. "
    #         "Will correct factual errors flatly, without softening. Knows more about the "
    #         "Awakened world than she lets on and shares it sparingly."
    #     ),
    #     perspective="elven shaman and awakened tradition perspective on",
    #     turn_prompt=AELINDRA_TURN_PROMPT,
    # ),
    Persona(
        handle="Bull",
        description=(
            "troll ex-corporate security turned street samurai, male. Blunt and pragmatic — "
            "cuts through idealism and paranoia alike to ask who's paying and where "
            "the exits are. Has more corporate insider knowledge than he lets on. "
            "Thinks in terms of threats, angles, and practical outcomes."
        ),
        perspective="street samurai and corporate security perspective on",
        turn_prompt=BULL_TURN_PROMPT,
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
        turn_prompt=COYOTE_TURN_PROMPT,
    ),
    Persona(
        handle="Ledger",
        description=(
            "former mid-level Aztechnology financial analyst turned shadowrunner, female. "
            "Paranoid about exposure — always half-watching the door. Still thinks in risk "
            "matrices, audit trails, and quarterly projections; can't turn it off. Knows "
            "exactly how corps hide money, bury liability, and structure deniable ops. "
            "Speaks in clipped corporate shorthand. Never uses a metaphor when a number will do."
        ),
        perspective="corporate financial analyst and insider perspective on",
        turn_prompt=LEDGER_TURN_PROMPT,
    ),
]

TURNS = 8  # 2 full rounds for 4 personas


def retrieve(vector_store: Chroma, query: str, exclude_ids: set[str]) -> tuple[str, set[str]]:
    search_kwargs: dict = {"k": settings.top_k}
    if exclude_ids:
        search_kwargs["filter"] = {"chunk_id": {"$nin": list(exclude_ids)}}
    docs = vector_store.similarity_search(query, **search_kwargs)
    new_ids = {doc.metadata["chunk_id"] for doc in docs if "chunk_id" in doc.metadata}
    return "\n\n".join(doc.page_content for doc in docs), new_ids


def generate(llm: ChatOllama, prompt: ChatPromptTemplate, **kwargs) -> str:
    chain = prompt | llm | StrOutputParser()
    raw = chain.invoke(kwargs).strip()
    return " ".join(raw.split())


def format_line(handle: str, text: str) -> str:
    return f">>>{handle.upper()}: {text}<<<"


def format_history_line(handle: str, text: str) -> str:
    return f"[{handle}]: {text}"


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
    own_lines: dict[str, list[str]] = {p.handle: [] for p in PERSONAS}
    used_ids: dict[str, set[str]] = {p.handle: set() for p in PERSONAS}
    schedule = make_schedule(TURNS)

    for turn, persona in enumerate(schedule):
        is_last = turn == TURNS - 1

        prior = own_lines[persona.handle]
        query = f"{topic} {persona.perspective}"
        context, new_ids = retrieve(vector_store, query, used_ids[persona.handle])
        used_ids[persona.handle].update(new_ids)

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
            prompt = persona.turn_prompt or OPEN_PROMPT
            own_history = (
                "\n".join(f"- {line}" for line in prior)
                if prior
                else "(none yet — this is your first turn)"
            )
            other_lines = [l for l in history_lines if not l.startswith(f"[{persona.handle}]")]
            reply_to = "\n".join(other_lines[-2:]) if other_lines else "(you are first to speak)"
            text = generate(
                llm,
                prompt,
                handle=persona.handle,
                description=persona.description,
                context=context,
                topic=topic,
                reply_to=reply_to,
                own_history=own_history,
                cutoff=cutoff,
            )

        line = format_line(persona.handle, text)
        history_lines.append(format_history_line(persona.handle, text))
        own_lines[persona.handle].append(text)
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
