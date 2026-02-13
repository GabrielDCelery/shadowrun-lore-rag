import logging

from config import settings

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO"):
    """Configure logging format and level"""
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
