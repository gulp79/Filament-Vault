"""Logging configuration for Filament Vault.

Sets up structured console and file logging.
"""

from __future__ import annotations
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(log_dir: Optional[Path] = None, debug: bool = False) -> logging.Logger:
    """Configure root logger with formatting and optional log file."""
    logger = logging.getLogger("filament_vault")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Avoid duplicate handlers if re-called
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] [%(name)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_dir:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "filament_vault.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not initialize file log: {e}")

    return logger


def get_logger(name: str = "filament_vault") -> logging.Logger:
    """Get a named logger child."""
    return logging.getLogger(name)
