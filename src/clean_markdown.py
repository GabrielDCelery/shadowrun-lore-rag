"""Clean extracted markdown files before embedding.

Reads from markdown_extracted/, writes cleaned files to markdown_clean/.

Cleans:
- Image reference lines (![](...))
- Navigation bar lines (lines containing sidebar nav artifacts with page markers)
- Malformed table rows (cells containing only punctuation/whitespace)
- OCR hallucinations (a phrase repeated 5+ times on a single line)
- Consecutive blank lines (collapsed to single blank line)
- OCR-split table headers: empty cells and continuation fragments (/word, :word,
  'and/or/of word') in header rows are merged into the previous cell so that
  row-as-sentence conversion produces labelled sentences instead of ': value'
- Currency symbol expansion: ¥ → nuyen (¥), £ → Irish punts (£) so that queries
  using either the symbol or the word form match the same chunks
- Markdown normalisation via mdformat (collapses excessive table cell whitespace
  that marker-pdf inserts to match PDF column widths)

Usage:
    uv run python src/clean_markdown.py
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

# Matches a markdown separator row: cells containing only dashes, colons, spaces
SEPARATOR_ROW_RE = re.compile(r"^\|[\s\-:|]+\|$")

# Continuation fragments that should be merged into the previous header cell
_CONTINUATION_STARTS = ("/", ":")
_CONTINUATION_WORDS = ("and ", "or ", "of ")

# Currency symbol expansion — embed both symbol and word form so queries using
# either "nuyen" or "¥" / "Irish punts" or "£" match the same chunks.
# Two patterns per symbol: one for when preceded by a word char (digit/letter)
# needing a space inserted, and one for other contexts (inside parens, etc.).
# Lookbehind guards prevent double-expansion when the word form is already present.
_YEN_WORD_RE = re.compile(r"(\w)(?<!nuyen \()¥")
_YEN_NONWORD_RE = re.compile(r"(?<!\w)(?<!nuyen \()¥")
_POUND_WORD_RE = re.compile(r"(\w)(?<!punts \()£")
_POUND_NONWORD_RE = re.compile(r"(?<!\w)(?<!punts \()£")


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


def _repair_header_row(line: str) -> str:
    """Merge empty and continuation-fragment cells into the previous header cell.

    OCR frequently splits a single multi-word column header across two adjacent
    cells, e.g. 'Offense and Fine' + '/Imprisonment'.  Empty cells in the header
    row leave the row-as-sentence converter with no label, producing output like
    ': 22,000¥/1 yr' instead of 'Possession: 22,000¥/1 yr'.

    Rules applied left-to-right:
    - Empty cell          → copy the previous cell's text (propagate label)
    - Cell starting with /  :  'and ' 'or ' 'of '
                          → prepend previous cell text (merge continuation)
    """
    parts = line.split("|")
    # parts[0] and parts[-1] are the text outside the outer pipes (empty for
    # well-formed rows); parts[1:-1] are the actual cells.
    cells = parts[1:-1]
    repaired: list[str] = []
    last_meaningful = ""

    for cell in cells:
        stripped = cell.strip()
        if not stripped:
            repaired.append(f" {last_meaningful} " if last_meaningful else cell)
        elif stripped.startswith(_CONTINUATION_STARTS) or stripped.lower().startswith(
            _CONTINUATION_WORDS
        ):
            merged = last_meaningful + stripped
            repaired.append(f" {merged} ")
            last_meaningful = merged
        else:
            last_meaningful = stripped
            repaired.append(cell)

    return "|" + "|".join(repaired) + "|"


def repair_table_headers(content: str) -> str:
    """Repair OCR-split header cells across all tables in the content."""
    lines = content.splitlines()
    result = []
    for i, line in enumerate(lines):
        if (
            TABLE_ROW_RE.match(line)
            and i + 1 < len(lines)
            and SEPARATOR_ROW_RE.match(lines[i + 1])
            and "--" in lines[i + 1]
        ):
            line = _repair_header_row(line)
        result.append(line)
    return "\n".join(result)


def expand_currency_symbols(content: str) -> str:
    """Expand currency symbols to include the word form.

    Table column headers use ¥ and £ but queries use "nuyen" and "Irish punts".
    Embedding "nuyen (¥)" makes both query forms match the same chunk.
    The lookbehind guards prevent double-expansion if the text already contains
    the expanded form (e.g. "nuyen (¥)" → unchanged on a second pass).
    """
    content = _YEN_WORD_RE.sub(r"\1 nuyen (¥)", content)
    content = _YEN_NONWORD_RE.sub("nuyen (¥)", content)
    content = _POUND_WORD_RE.sub(r"\1 Irish punts (£)", content)
    content = _POUND_NONWORD_RE.sub("Irish punts (£)", content)
    return content


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
    result = repair_table_headers(result)
    result = expand_currency_symbols(result)
    result = mdformat.text(
        result, extensions={"gfm"}, options={"wrap": "no", "compact_tables": True}
    )
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
