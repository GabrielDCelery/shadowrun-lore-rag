"""Ingest PDFs into the RAG system."""

import argparse
import gc
import sys

import torch
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict

from config import settings
from logs import logger, setup_logging


def build_converter(model_dict, use_llm: bool = False) -> PdfConverter:
    """Build a PdfConverter, optionally with LLM-assisted table fixing via Ollama."""
    config = {
        "drop_repeated_text": True,
        "disable_ocr_math": True,
    }

    if use_llm:
        from marker.config.parser import ConfigParser

        config.update(
            {
                "use_llm": True,
                "output_format": "markdown",
                "llm_service": "marker.services.ollama.OllamaService",
                "ollama_base_url": settings.ollama_host,
                "ollama_model": settings.marker_llm_model,
            }
        )
        config_parser = ConfigParser(config)
        return PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=model_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )

    return PdfConverter(artifact_dict=model_dict, config=config)


def convert_pdfs_to_markdown(
    book: str | None = None, force: bool = False, use_llm: bool = False
) -> None:
    """Convert PDFs to markdown using marker-pdf."""
    logger.info(f"looking for PDFs in {settings.pdfs_normalised_path}")

    if not settings.pdfs_normalised_path.exists():
        logger.error(f"pdf path {settings.pdfs_normalised_path} does not exist")
        sys.exit(1)

    pdf_files = list(settings.pdfs_normalised_path.glob("*.pdf"))
    if not pdf_files:
        logger.info(f"no PDF files found in {settings.pdfs_normalised_path}")
        return

    if book:
        pdf_files = [f for f in pdf_files if book in f.stem]
        if not pdf_files:
            logger.error(f"no PDF found matching '{book}'")
            sys.exit(1)

    logger.info(f"found {len(pdf_files)} PDF files for extraction")

    settings.markdown_extracted_path.mkdir(parents=True, exist_ok=True)

    for pdf_file in pdf_files:
        output_file = settings.markdown_extracted_path / f"{pdf_file.stem}.md"

        if output_file.exists() and not force:
            logger.info(f"skipping {pdf_file.name} (already extracted)")
            continue

        logger.info(f"loading marker-pdf models...")
        model_dict = create_model_dict()
        converter = None
        try:
            converter = build_converter(model_dict, use_llm=use_llm)
            label = " [LLM-assisted]" if use_llm else ""
            logger.info(f"converting {pdf_file.name}{label}")
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
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()


def main() -> None:
    setup_logging(settings.log_level)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--book",
        help="Only convert this book (filename stem, e.g. 7204---germany-sourcebook)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-convert even if output already exists",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help=f"LLM-assisted table fixing via Ollama ({settings.marker_llm_model})",
    )
    args = parser.parse_args()

    convert_pdfs_to_markdown(book=args.book, force=args.force, use_llm=args.use_llm)


if __name__ == "__main__":
    main()
