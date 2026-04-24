"""Post-process extracted markdown files before embedding.

Reads from markdown_extracted/, writes cleaned files to markdown/.

Cleans:
- Image reference lines (![](...))
- Navigation bar lines (lines containing sidebar nav artifacts with page markers)
- Malformed table rows (cells containing only punctuation/whitespace)
- Consecutive blank lines (collapsed to single blank line)

Usage:
    uv run python src/postprocess_markdown.py
"""

import re

from config import settings
from logs import logger, setup_logging

# Matches standalone image reference lines
IMAGE_RE = re.compile(r'^!\[.*?\]\(.*?\)\s*$')

# Matches navigation bar emoji used in Tir Tairngire and similar books
NAV_EMOJI_RE = re.compile(r'[🗆🔲]')

# Navigation bar pattern: 2+ all-caps words followed by "Page N"
NAV_BAR_RE = re.compile(r'(?:[A-Z]{3,}\s+){2,}Page\s+\d+.*')

# Malformed table row: all cells contain only punctuation/whitespace
MALFORMED_TABLE_RE = re.compile(r'^\|[\s,\.;:!\?|]+\|$')


def is_image_line(line: str) -> bool:
    return bool(IMAGE_RE.match(line))


def clean_nav_bar(line: str) -> str:
    """Strip navigation bar from a line, keeping any real content before it."""
    if not NAV_EMOJI_RE.search(line):
        return line
    # Strip the nav bar pattern and everything up to and including the emoji
    cleaned = NAV_BAR_RE.sub('', line)
    cleaned = NAV_EMOJI_RE.sub('', cleaned).strip()
    return cleaned


def is_malformed_table_row(line: str) -> bool:
    return bool(MALFORMED_TABLE_RE.match(line))


def postprocess(content: str) -> str:
    lines = content.splitlines()
    output = []
    prev_blank = False

    for line in lines:
        if is_image_line(line):
            continue

        if is_malformed_table_row(line):
            continue

        line = clean_nav_bar(line)

        # Collapse consecutive blank lines
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue

        output.append(line)
        prev_blank = is_blank

    return '\n'.join(output)


def main() -> None:
    setup_logging(settings.log_level)

    if not settings.markdown_extracted_path.exists():
        logger.error(f"markdown extracted path {settings.markdown_extracted_path} does not exist")
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
        logger.info(f"  {original_lines} → {cleaned_lines} lines ({original_lines - cleaned_lines} removed)")


if __name__ == "__main__":
    main()
