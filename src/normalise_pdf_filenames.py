"""Copy PDFs from pdfs_raw/ to pdfs_normalised/ with slugified filenames.

Normalises any filename to lowercase, hyphen-separated, filesystem-safe.

Usage:
    uv run python src/normalise_pdf_filenames.py
"""

import re
import shutil

from config import settings
from logs import logger, setup_logging


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s_]+", "-", text).strip("-")


def main() -> None:
    setup_logging(settings.log_level)

    if not settings.pdfs_raw_path.exists():
        logger.error(f"raw pdf path {settings.pdfs_raw_path} does not exist")
        return

    settings.pdfs_normalised_path.mkdir(parents=True, exist_ok=True)

    for pdf in sorted(settings.pdfs_raw_path.glob("*.pdf")):
        dest = settings.pdfs_normalised_path / f"{slugify(pdf.stem)}.pdf"

        if dest.exists():
            logger.warning(
                f"skipping duplicate: {pdf.name} → {dest.name} already exists"
            )
            continue

        logger.info(f"{pdf.name} → {dest.name}")
        shutil.copy2(pdf, dest)


if __name__ == "__main__":
    main()
