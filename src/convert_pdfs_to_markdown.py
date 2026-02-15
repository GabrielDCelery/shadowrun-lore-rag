"""Ingest PDFs into the RAG system."""

import gc
import sys

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

from config import settings
from logs import logger, setup_logging


def convert_pdfs_to_markdown():
    """Convert PDFs to markdown using marker-pdf."""
    logger.info(f"looking for PDFs in {settings.pdf_path}")

    if not settings.pdf_path.exists():
        logger.error(f"pdf path {settings.pdf_path} does not exist")
        sys.exit(1)

    pdf_files = list(settings.pdf_path.glob("*.pdf"))
    if not pdf_files:
        logger.info(f"no PDF files found in {settings.pdf_path}")
        return

    logger.info(f"found {len(pdf_files)} PDF files for extraction")

    settings.extracted_path.mkdir(parents=True, exist_ok=True)

    for pdf_file in pdf_files:

        output_file = settings.extracted_path / f"{pdf_file.stem}.md"

        if output_file.exists():
            logger.info(f"skipping {pdf_file.name} (already extracted)")
            continue

        # Initialize marker-pdf models
        logger.info(f"loading marker-pdf models...")
        model_dict = create_model_dict()
        converter = PdfConverter(artifact_dict=model_dict)

        logger.info(f"converting {pdf_file.name}")

        try:
            rendered = converter(str(pdf_file))

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rendered.markdown)

            logger.info(f"saved to {output_file.name}")
        except Exception as e:
            logger.error(f"error converting {pdf_file.name}: {e}")
        finally:
            logger.info(f"tear down marker-pdf models")
            del converter
            del model_dict
            gc.collect()


def main():
    """Run the full ingestion pipeline."""
    setup_logging(settings.log_level)

    # Step 1: Convert PDFs to markdown
    convert_pdfs_to_markdown()


if __name__ == "__main__":
    main()
