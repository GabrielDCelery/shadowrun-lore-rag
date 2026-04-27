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
- Do NOT just restate a point already made by anyone — move the conversation forward.
- Do not end with your handle or name. Do not start with your handle or name."""

FASTJACK_TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are FastJack in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Background knowledge — treat this as things you've learned firsthand, not a document:
{context}

YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
{own_history}

Conversation so far:
{history}

Respond as FastJack. Exactly 2-3 sentences, no more.
Your move: cut through the noise. Demand or supply a specific — a name, a corp, a location, a price, a date, a contact.
If someone is being vague or wrong, correct them flatly. If a detail is missing that matters, name it.
FastJack speaks in clipped fragments — never more than 10 words per sentence, never a question when a statement will do.
Wrong: "I need to know who's paying them and how much." Right: "Ares. Berlin office. Someone signed that cheque — find the name."
""" + _SHARED_RULES + "{cutoff}"
)

AELINDRA_TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are Aelindra in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Background knowledge — treat this as things you've learned firsthand, not a document:
{context}

YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
{own_history}

Conversation so far:
{history}

Respond as Aelindra. Exactly 2-3 sentences, no more.
Your move: add the Awakened angle the others are missing. Correct a magical misconception,
name a specific spirit type, tradition, or ritual detail from the background knowledge, or
point out a consequence the others haven't thought through. Stay on the topic — engage with
what was just said, then add something concrete from what you know.
""" + _SHARED_RULES + "{cutoff}"
)

BULL_TURN_PROMPT = ChatPromptTemplate.from_template(
    """You are Bull in a private encrypted Shadowrun Matrix chat.

Your character: {description}

Background knowledge — treat this as things you've learned firsthand, not a document:
{context}

YOUR PREVIOUS LINES — do not repeat or rephrase any of these:
{own_history}

Conversation so far:
{history}

Respond as Bull. Exactly 2-3 sentences, no more.
Your move: ground it. Pull the conversation back to operational reality — who's involved, what it
costs, what the threat actually is, who benefits. You have corporate insider knowledge; let it slip
when it's relevant. You don't theorise, you assess.
""" + _SHARED_RULES + "{cutoff}"
)

PERSONAS = [
    Persona(
        handle="FastJack",
        description=(
            "legendary veteran decker and fixer, male. Old school, seen everything twice. "
            "Deeply cynical and world-weary — he's watched too many good runners die "
            "for corp lies to believe anything at face value. Speaks in clipped, blunt "
            "fragments — never more than 10 words per sentence. Rarely wrong, never surprised. "
            "Does not explain himself."
        ),
        perspective="veteran fixer and information broker perspective on",
        turn_prompt=FASTJACK_TURN_PROMPT,
    ),
    Persona(
        handle="Aelindra",
        description=(
            "elven shaman, female, ancient and unhurried. Mostly direct and precise — "
            "she has no patience for unnecessary words. Occasionally lets slip a metaphor "
            "or an oblique reference, but only when it says more than plain speech would. "
            "Carries centuries of memory and finds human short-termism quietly exasperating. "
            "Will correct factual errors flatly, without softening. Knows more about the "
            "Awakened world than she lets on and shares it sparingly."
        ),
        perspective="elven shaman and awakened tradition perspective on",
        turn_prompt=AELINDRA_TURN_PROMPT,
    ),
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
    # Persona(
    #     handle="Ledger",
    #     description=(
    #         "former mid-level Aztechnology analyst turned shadowrunner, female. Still "
    #         "thinks in spreadsheets and risk matrices — can't help it. Nervous energy, "
    #         "over-explains, occasionally lets slip insider knowledge she shouldn't have. "
    #         "Trying hard to shed the corp mindset and not quite managing it."
    #     ),
    #     perspective="corporate insider and defector perspective on",
    # ),
]

TURNS = 7


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
    retriever = load_retriever(vector_store)

    history_lines: list[str] = []
    own_lines: dict[str, list[str]] = {p.handle: [] for p in PERSONAS}
    schedule = make_schedule(TURNS)

    for turn, persona in enumerate(schedule):
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
            prompt = persona.turn_prompt or OPEN_PROMPT
            prior = own_lines[persona.handle]
            own_history = (
                "\n".join(f"- {line}" for line in prior)
                if prior
                else "(none yet — this is your first turn)"
            )
            text = generate(
                llm,
                prompt,
                handle=persona.handle,
                description=persona.description,
                context=context,
                topic=topic,
                history="\n".join(history_lines),
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
