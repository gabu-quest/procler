"""Logging configuration using loguru."""

import sys
import os
from pathlib import Path

from loguru import logger

# Remove default handler
logger.remove()

# Determine log level from environment
LOG_LEVEL = os.environ.get("PROCLER_LOG_LEVEL", "INFO").upper()
LOG_FILE = os.environ.get("PROCLER_LOG_FILE", "")

# Console handler with color
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    colorize=True,
)

# File handler if specified
if LOG_FILE:
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        LOG_FILE,
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="gz",
    )

# Export configured logger
__all__ = ["logger"]
