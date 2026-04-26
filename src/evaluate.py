"""Evaluate the RAG system against a set of test queries.

Two-pass evaluation:

  Pass 1 (--pass1): Run each query through the RAG pipeline and save answers
  to results/answers_<timestamp>.json. Inspect answers manually before judging.

  Pass 2 (--pass2 <answers_file>): Run a judge LLM against the saved answers
  and score each on correctness and groundedness. Saves scores to
  results/scores_<timestamp>.json referencing the original answers file.

Usage:
    uv run python src/evaluate.py --pass1 tests/rag_queries.md
    uv run python src/evaluate.py --pass2 /data/results/answers_20260425_193000.json
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama, OllamaEmbeddings

from config import settings
from logs import logger, setup_logging


# ---------------------------------------------------------------------------
# Query parsing
# ---------------------------------------------------------------------------

def parse_queries(path: Path) -> list[dict]:
    """Parse tests/rag_queries.md into a list of query dicts."""
    text = path.read_text(encoding="utf-8")

    # Match book sections: ## Book Name (`file-slug`)
    book_re = re.compile(r"^## .+\(`([^`]+)`\)", re.MULTILINE)
    # Match question blocks: ### Q<n> or XQ<n> — <category>
    question_re = re.compile(r"^### (X?Q\d+) — ([\w-]+)", re.MULTILINE)

    # Split into book sections
    book_positions = [(m.start(), m.group(1)) for m in book_re.finditer(text)]

    queries = []

    for i, (book_start, book_slug) in enumerate(book_positions):
        book_end = book_positions[i + 1][0] if i + 1 < len(book_positions) else len(text)
        book_text = text[book_start:book_end]

        # Find all question blocks within this book section
        q_positions = [(m.start(), m.group(1), m.group(2)) for m in question_re.finditer(book_text)]

        for j, (q_start, q_id, category) in enumerate(q_positions):
            q_end = q_positions[j + 1][0] if j + 1 < len(q_positions) else len(book_text)
            block = book_text[q_start:q_end]

            question = _extract_field(block, r"\*\*Q:\*\* (.+)")
            source = _extract_field(block, r"\*\*Sources?:\*\* (.+)")
            expected = _extract_list(block)

            if not question:
                continue

            queries.append({
                "id": f"{book_slug}-{q_id}",
                "book": book_slug,
                "category": category,
                "question": question.strip(),
                "source": source.strip() if source else "",
                "expected": expected,
            })

    return queries


def _extract_field(text: str, pattern: str) -> str:
    m = re.search(pattern, text)
    return m.group(1) if m else ""


def _extract_list(text: str) -> list[str]:
    """Extract bullet points from the Expected section."""
    m = re.search(r"\*\*Expected:\*\*\n((?:- .+\n?)+)", text)
    if not m:
        return []
    return [line.lstrip("- ").strip() for line in m.group(1).splitlines() if line.strip().startswith("-")]


# ---------------------------------------------------------------------------
# RAG helpers
# ---------------------------------------------------------------------------

def load_vector_store() -> Chroma:
    if not settings.chroma_path.exists():
        logger.error(f"vector store not found at {settings.chroma_path}")
        sys.exit(1)

    embeddings = OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_host,
    )
    return Chroma(
        persist_directory=str(settings.chroma_path),
        embedding_function=embeddings,
    )


ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """You are an expert on the Shadowrun RPG system. Use the following context from the Shadowrun sourcebooks to answer the question. If the answer is not in the context, say so — do not make up information.

Context:
{context}

Question: {question}

Answer:"""
)


def run_query(question: str, retriever, llm) -> tuple[str, list[dict]]:
    """Run a single query. Returns (answer, retrieved_chunks)."""
    docs = retriever.invoke(question)

    context = "\n\n".join(doc.page_content for doc in docs)

    chain = (
        ANSWER_PROMPT
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke({"context": context, "question": question})

    chunks = [
        {
            "source": doc.metadata.get("source", "unknown"),
            "content": doc.page_content,
        }
        for doc in docs
    ]

    return answer.strip(), chunks


# ---------------------------------------------------------------------------
# Pass 1 — generate answers
# ---------------------------------------------------------------------------

def pass1(queries_path: Path) -> None:
    logger.info(f"pass 1 — generating answers from {queries_path}")

    queries = parse_queries(queries_path)
    if not queries:
        logger.error("no queries parsed from file")
        sys.exit(1)

    logger.info(f"loaded {len(queries)} queries")

    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": settings.top_k})

    llm = ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_host,
        temperature=0,
    )

    results = []

    for i, q in enumerate(queries, 1):
        logger.info(f"  [{i}/{len(queries)}] {q['id']} — {q['question'][:60]}...")
        answer, chunks = run_query(q["question"], retriever, llm)
        results.append({**q, "answer": answer, "retrieved_chunks": chunks})
        logger.info(f"    answer: {answer[:80]}...")

    settings.evals_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = settings.evals_path / f"{timestamp}_answers.json"
    output = {
        "metadata": {
            "timestamp": timestamp,
            "queries_file": str(queries_path),
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "top_k": settings.top_k,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
        },
        "results": results,
    }
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info(f"answers saved to {output_path}")
    print(output_path.name)


# ---------------------------------------------------------------------------
# Pass 2 — judge answers
# ---------------------------------------------------------------------------

JUDGE_PROMPT = ChatPromptTemplate.from_template(
    """You are evaluating a RAG (retrieval-augmented generation) system for Shadowrun RPG lore.

Question asked:
{question}

Expected key facts a correct answer should contain:
{expected}

Retrieved context chunks provided to the model:
{chunks}

Answer produced by the model:
{answer}

Score the answer on two dimensions (1-5 each):

1. CORRECTNESS: How many of the expected key facts appear in the answer?
   Count the expected facts. Each missing fact is a deduction. Be strict — a fact must be explicitly stated, not merely implied.
   5 = all expected facts present and accurate
   4 = one fact missing or slightly inaccurate
   3 = roughly half the facts present
   2 = only one or two facts present, most missing
   1 = answer is wrong or contradicts the expected facts
   0 = none of the expected facts present and no useful information provided

2. GROUNDEDNESS: Is the answer based on the retrieved chunks, or does it appear to draw on outside knowledge not present in the chunks?
   5 = everything in the answer can be traced to the retrieved chunks
   3 = mostly grounded but some claims not supported by chunks
   1 = answer ignores chunks and relies on outside knowledge

Respond with JSON only, no explanation outside the JSON:
{{
  "correctness": <1-5>,
  "groundedness": <1-5>,
  "reasoning": "<one or two sentences explaining both scores>"
}}"""
)


def pass2(answers_path: Path) -> None:
    logger.info(f"pass 2 — judging answers from {answers_path}")

    raw = json.loads(answers_path.read_text(encoding="utf-8"))
    # Support both old format (flat list) and new format ({metadata, results})
    if isinstance(raw, list):
        answers_metadata = {}
        answers = raw
    else:
        answers_metadata = raw.get("metadata", {})
        answers = raw.get("results", [])
    logger.info(f"loaded {len(answers)} answers")

    judge_llm = ChatOllama(
        model=settings.judge_model,
        base_url=settings.ollama_host,
        temperature=0,
    )

    scores = []

    for i, entry in enumerate(answers, 1):
        logger.info(f"  [{i}/{len(answers)}] judging {entry['id']}...")

        expected_text = "\n".join(f"- {f}" for f in entry.get("expected", []))
        chunks_text = "\n\n".join(
            f"[{c['source']}]\n{c['content']}" for c in entry.get("retrieved_chunks", [])
        )

        chain = JUDGE_PROMPT | judge_llm | StrOutputParser()
        raw = chain.invoke({
            "question": entry["question"],
            "expected": expected_text,
            "chunks": chunks_text,
            "answer": entry["answer"],
        })

        try:
            # Extract JSON even if model adds surrounding text
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            score = json.loads(json_match.group()) if json_match else {"error": raw}
        except Exception:
            score = {"error": raw}

        scores.append({
            "id": entry["id"],
            "category": entry.get("category"),
            "book": entry.get("book"),
            "question": entry["question"],
            **score,
            "answer_file": answers_path.name,
        })

        if "correctness" in score:
            logger.info(f"    correctness={score['correctness']} groundedness={score['groundedness']}")
        else:
            logger.warning(f"    judge returned unexpected format: {raw[:100]}")

    # Summary
    valid = [s for s in scores if "correctness" in s]
    if valid:
        avg_c = sum(s["correctness"] for s in valid) / len(valid)
        avg_g = sum(s["groundedness"] for s in valid) / len(valid)
        logger.info(f"summary: {len(valid)}/{len(scores)} scored | avg correctness={avg_c:.1f} avg groundedness={avg_g:.1f}")

    settings.evals_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = settings.evals_path / f"{timestamp}_scores.json"
    output = {
        "metadata": {
            "timestamp": timestamp,
            "judge_model": settings.judge_model,
            "answers": {
                "file": answers_path.name,
                **answers_metadata,
            },
        },
        "results": scores,
    }
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info(f"scores saved to {output_path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    setup_logging(settings.log_level)

    parser = argparse.ArgumentParser(description="Evaluate the RAG system")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pass1", metavar="QUERIES_FILE", help="Generate answers from a queries markdown file")
    group.add_argument("--pass2", metavar="ANSWERS_FILE", help="Judge answers from a pass 1 output file")

    args = parser.parse_args()

    if args.pass1:
        pass1(Path(args.pass1))
    elif args.pass2:
        pass2(Path(args.pass2))


if __name__ == "__main__":
    main()
