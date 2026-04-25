"""Post-process extracted markdown files before embedding.

Reads from markdown_extracted/, writes cleaned files to markdown/.

Cleans:
- Image reference lines (![](...))
- Navigation bar lines (lines containing sidebar nav artifacts with page markers)
- Malformed table rows (cells containing only punctuation/whitespace)
- OCR hallucinations (a phrase repeated 5+ times on a single line)
- Consecutive blank lines (collapsed to single blank line)
- Markdown normalisation via mdformat (collapses excessive table cell whitespace
  that marker-pdf inserts to match PDF column widths)

Usage:
    uv run python src/postprocess_markdown.py
"""

import re

import mdformat

from config import settings
from logs import logger, setup_logging

# Matches standalone image reference lines
IMAGE_RE = re.compile(r"^!\[.*?\]\(.*?\)\s*$")

# Matches navigation bar emoji used in Tir Tairngire and similar books
NAV_EMOJI_RE = re.compile(r"[🗆🔲]")

# Navigation bar pattern: 2+ all-caps words followed by "Page N"
NAV_BAR_RE = re.compile(r"(?:[A-Z]{3,}\s+){2,}Page\s+\d+.*")

# Malformed table row: all cells contain only punctuation/whitespace
MALFORMED_TABLE_RE = re.compile(r"^\|[\s,\.;:!\?|]+\|$")

# Matches a table row (starts and ends with |)
TABLE_ROW_RE = re.compile(r"^\|.*\|$")

# Matches runs of 2+ spaces within a table cell
CELL_WHITESPACE_RE = re.compile(r"  +")

# OCR hallucination: a non-whitespace phrase of 10+ chars repeated 5+ times on a single line
REPEATED_PHRASE_RE = re.compile(r"(\S.{9,})\1{5,}")


def is_image_line(line: str) -> bool:
    return bool(IMAGE_RE.match(line))


def clean_nav_bar(line: str) -> str:
    """Strip navigation bar from a line, keeping any real content before it."""
    if not NAV_EMOJI_RE.search(line):
        return line
    # Strip the nav bar pattern and everything up to and including the emoji
    cleaned = NAV_BAR_RE.sub("", line)
    cleaned = NAV_EMOJI_RE.sub("", cleaned).strip()
    return cleaned


def is_malformed_table_row(line: str) -> bool:
    return bool(MALFORMED_TABLE_RE.match(line))


def collapse_table_cell_whitespace(line: str) -> str:
    """Collapse runs of spaces within table cells to a single space.

    Must run before mdformat — extremely wide cells (marker-pdf pads to PDF
    column widths) cause mdformat to misparse the table and merge all rows
    into one line. Separator rows (|---|---|) also need collapsing for the
    same reason; their exact dash count is irrelevant to markdown rendering.
    """
    if not TABLE_ROW_RE.match(line):
        return line
    return CELL_WHITESPACE_RE.sub(" ", line)


def postprocess(content: str) -> str:
    lines = content.splitlines()
    output = []
    prev_blank = False

    for line in lines:
        if is_image_line(line):
            continue

        if is_malformed_table_row(line):
            continue

        # if not line.strip().startswith("|"):
        #     line = REPEATED_PHRASE_RE.sub(r"\1", line).strip()
        #     if not line:
        #         continue

        line = collapse_table_cell_whitespace(line)
        line = clean_nav_bar(line)

        # Collapse consecutive blank lines
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue

        output.append(line)
        prev_blank = is_blank

    result = "\n".join(output)
    result = mdformat.text(result, extensions={"gfm"}, options={"wrap": "no", "compact_tables": True})
    return result


def main() -> None:
    setup_logging(settings.log_level)

    if not settings.markdown_extracted_path.exists():
        logger.error(
            f"markdown extracted path {settings.markdown_extracted_path} does not exist"
        )
        return

    settings.markdown_path.mkdir(parents=True, exist_ok=True)

    for md_file in sorted(settings.markdown_extracted_path.glob("*.md")):
        dest = settings.markdown_path / md_file.name
        logger.info(f"processing {md_file.name}")

        content = md_file.read_text(encoding="utf-8")
        cleaned = postprocess(content)
        dest.write_text(cleaned, encoding="utf-8")

        original_lines = len(content.splitlines())
        cleaned_lines = len(cleaned.splitlines())
        logger.info(
            f"  {original_lines} → {cleaned_lines} lines ({original_lines - cleaned_lines} removed)"
        )


if __name__ == "__main__":
    main()
