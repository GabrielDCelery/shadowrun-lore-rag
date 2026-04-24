"""Two-pass markdown chunker.

Pass 1: splits markdown into prose and table sections.
Pass 2: chunks prose with MarkdownTextSplitter, converts table rows to
        natural language sentences (one document per row).

Tables with clear headers and > MIN_TABLE_ROWS rows get row-as-sentence
conversion. Small or headerless tables are kept as a single atomic chunk.
"""

import re
from typing import Generator

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter

MIN_TABLE_ROWS = 5  # tables below this threshold are kept as atomic chunks

_SEPARATOR_RE = re.compile(r"^\|[-:\s|]+\|$")


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def _is_separator(line: str) -> bool:
    return bool(_SEPARATOR_RE.match(line.strip()))


def _parse_table(table_lines: list[str]) -> tuple[list[str] | None, list[list[str]]]:
    """Extract headers and data rows from a block of table lines."""
    headers = None
    data_rows = []

    for i, line in enumerate(table_lines):
        if _is_separator(line):
            if i > 0:
                headers = [c.strip() for c in table_lines[i - 1].split("|")[1:-1]]
            continue

        cells = [c.strip() for c in line.split("|")[1:-1]]

        # Skip the header row itself (already captured above)
        if headers and cells == headers:
            continue

        data_rows.append(cells)

    # If first data row duplicates headers (edge case), drop it
    if headers and data_rows and data_rows[0] == headers:
        data_rows = data_rows[1:]

    return headers, data_rows


def _row_to_sentence(heading: str, headers: list[str], row: list[str]) -> str:
    parts = [f"{h}: {v}" for h, v in zip(headers, row) if v.strip()]
    prefix = f"{heading} — " if heading else ""
    return prefix + ", ".join(parts)


def _split_sections(
    content: str,
) -> Generator[tuple[str, str, list[str] | str], None, None]:
    """Yield (type, heading_context, content) tuples — type is 'prose' or 'table'."""
    lines = content.splitlines()
    current_heading = ""
    prose_buf: list[str] = []
    table_buf: list[str] = []
    in_table = False

    def flush_prose():
        if prose_buf:
            yield ("prose", current_heading, "\n".join(prose_buf))
            prose_buf.clear()

    def flush_table():
        if table_buf:
            yield ("table", current_heading, list(table_buf))
            table_buf.clear()

    for line in lines:
        if _is_table_line(line):
            if not in_table:
                yield from flush_prose()
                in_table = True
            table_buf.append(line)
        else:
            if in_table:
                yield from flush_table()
                in_table = False
            if line.startswith("#"):
                current_heading = line.lstrip("#").strip()
            prose_buf.append(line)

    yield from flush_table()
    yield from flush_prose()


def chunk_markdown(
    content: str,
    source: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Chunk a markdown document into a list of LangChain Documents."""
    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documents: list[Document] = []

    for section_type, heading, section_content in _split_sections(content):
        if section_type == "prose":
            chunks = splitter.create_documents(
                [section_content],
                metadatas=[{"source": source, "type": "prose", "heading": heading}],
            )
            documents.extend(chunks)

        elif section_type == "table":
            table_lines = section_content
            headers, data_rows = _parse_table(table_lines)

            use_row_conversion = (
                headers is not None and len(data_rows) >= MIN_TABLE_ROWS
            )

            if use_row_conversion:
                for row in data_rows:
                    sentence = _row_to_sentence(heading, headers, row)
                    if sentence.strip():
                        documents.append(
                            Document(
                                page_content=sentence,
                                metadata={
                                    "source": source,
                                    "type": "table_row",
                                    "heading": heading,
                                },
                            )
                        )
            else:
                # Keep small or headerless tables as a single atomic chunk
                atomic = "\n".join(table_lines)
                if heading:
                    atomic = f"{heading}\n\n{atomic}"
                documents.append(
                    Document(
                        page_content=atomic,
                        metadata={
                            "source": source,
                            "type": "table",
                            "heading": heading,
                        },
                    )
                )

    return documents
