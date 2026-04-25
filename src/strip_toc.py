"""Strip table of contents, credits, and index sections from cleaned markdown.

Reads from markdown_clean/, writes stripped files to markdown_stripped/.

Removes:
- Table of contents sections (identified by headings matching "TABLE OF CONTENTS"
  or "CREDITS/CONTENTS")
- Publisher credits that follow the ToC (production staff tables, copyright notices)
- Index sections at the end (identified by a standalone "INDEX" heading in the
  last 30% of the document)

Real content start is detected as the first heading (after the ToC block) that is
followed within 20 lines by a non-table prose line of 80+ characters.

Usage:
    uv run python src/strip_toc.py
"""

import re

from config import settings
from logs import logger, setup_logging

# Headings that mark the start of a ToC/credits block
TOC_HEADING_RE = re.compile(
    r"^#+\s+.*\bTABLE\s+OF\s+CONTENTS\b.*$|^#+\s+CREDITS(/CONTENTS)?\s*$",
    re.IGNORECASE,
)

# Standalone index heading (must be only the word INDEX)
INDEX_HEADING_RE = re.compile(r"^#+\s+INDEX\s*$", re.IGNORECASE)

# Markdown heading
HEADING_RE = re.compile(r"^#+\s+")

# Markdown table row
TABLE_ROW_RE = re.compile(r"^\|")


def find_toc_start(lines: list[str]) -> int | None:
    """Return the line index of the first ToC/credits heading, or None."""
    for i, line in enumerate(lines):
        if TOC_HEADING_RE.match(line.rstrip()):
            return i
    return None


def find_content_start(lines: list[str], from_line: int) -> int | None:
    """Return the line index of the first real-content heading after the ToC block.

    Scans forward from `from_line` looking for a heading that is followed
    within 20 lines by a non-table, non-heading line of 80+ characters.
    Returns None if no such heading is found (safety valve — don't strip).
    """
    i = from_line
    while i < len(lines):
        if HEADING_RE.match(lines[i]):
            for j in range(i + 1, min(i + 21, len(lines))):
                candidate = lines[j].strip()
                if (
                    candidate
                    and not TABLE_ROW_RE.match(candidate)
                    and not HEADING_RE.match(candidate)
                    and len(candidate) >= 80
                ):
                    return i
        i += 1
    return None


def find_index_start(lines: list[str]) -> int | None:
    """Return the line index of the INDEX heading if found in the last 30% of the doc."""
    min_line = int(len(lines) * 0.70)
    for i in range(len(lines) - 1, min_line, -1):
        if INDEX_HEADING_RE.match(lines[i].rstrip()):
            return i
    return None


def strip_front_matter(lines: list[str], filename: str) -> list[str]:
    toc_start = find_toc_start(lines)
    if toc_start is None:
        logger.info("  no ToC heading found — skipping front matter strip")
        return lines

    content_start = find_content_start(lines, toc_start + 1)
    if content_start is None:
        logger.warning(
            "  ToC found but could not detect content start — skipping front matter strip"
        )
        return lines

    removed = content_start - toc_start
    logger.info(
        f"  front matter: lines {toc_start + 1}–{content_start} stripped ({removed} lines)"
    )
    return lines[:toc_start] + lines[content_start:]


def strip_back_matter(lines: list[str]) -> list[str]:
    index_start = find_index_start(lines)
    if index_start is None:
        return lines

    removed = len(lines) - index_start
    logger.info(
        f"  back matter: lines {index_start + 1}–{len(lines)} stripped ({removed} lines)"
    )
    return lines[:index_start]


def process(content: str, filename: str) -> str:
    lines = content.splitlines()
    lines = strip_front_matter(lines, filename)
    lines = strip_back_matter(lines)
    return "\n".join(lines)


def main() -> None:
    setup_logging(settings.log_level)

    if not settings.markdown_path.exists():
        logger.error(f"markdown clean path {settings.markdown_path} does not exist")
        return

    settings.markdown_stripped_path.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(settings.markdown_path.glob("*.md")):
        dest = settings.markdown_stripped_path / md_file.name
        logger.info(f"processing {md_file.name}")

        content = md_file.read_text(encoding="utf-8")
        stripped = process(content, md_file.name)
        dest.write_text(stripped, encoding="utf-8")

        original_lines = len(content.splitlines())
        stripped_lines = len(stripped.splitlines())
        logger.info(
            f"  {original_lines} → {stripped_lines} lines ({original_lines - stripped_lines} removed)"
        )


if __name__ == "__main__":
    main()
