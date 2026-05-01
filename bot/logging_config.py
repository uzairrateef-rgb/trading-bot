"""
logging_config.py

Sets up logging for the whole application. Two destinations:
  - A daily log file in logs/ that captures everything (DEBUG and above)
  - The terminal, which only shows INFO and above to stay readable

The goal is to have enough information in the log file to reconstruct
exactly what happened during a run — including raw API payloads — without
making the terminal noisy during normal use.
"""

import logging
import os
from datetime import datetime


def setup_logging() -> logging.Logger:
    """
    Configures and returns the 'trading_bot' logger.

    The log directory is created automatically if it doesn't exist yet.
    Log files rotate daily (one file per date), which keeps them manageable
    without needing to set up a RotatingFileHandler.

    Call this once at startup (in cli.py), then use:
        logger = logging.getLogger("trading_bot")
    anywhere else in the codebase.
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(log_dir, f"trading_{today}.log")

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler — captures DEBUG and above (raw payloads, full responses)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    # Console handler — only INFO and above (clean, human-readable messages)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if setup_logging() gets called more than once
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    logger.info(f"Logging initialised — writing to {log_path}")
    return logger