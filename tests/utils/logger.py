"""Utility module providing logging functionality for tests.

Provides logging configuration and setup for test modules.
"""

import logging
import os
from datetime import datetime


def setup_logger(name="yomitalk_test", level=logging.INFO):
    """
    Set up a logger for test modules.

    Args:
        name (str): Logger name
        level: Log level

    Returns:
        logging.Logger: Configured logger instance
    """
    # Ensure log directory exists
    log_dir = "data/logs/tests"
    os.makedirs(log_dir, exist_ok=True)

    # Generate log filename with current date
    log_file = os.path.join(
        log_dir, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    # Get logger instance
    logger = logging.getLogger(name)

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(level)

    # Set up handlers (file and console output)
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Create default test logger
test_logger = setup_logger()
