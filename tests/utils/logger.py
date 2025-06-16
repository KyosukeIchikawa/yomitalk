"""Utility module providing logging functionality for tests.

Provides logging configuration and setup for test modules.
"""

import logging


def setup_logger(name="yomitalk_test", level=logging.INFO):
    """
    Set up a logger for test modules.

    Args:
        name (str): Logger name
        level: Log level

    Returns:
        logging.Logger: Configured logger instance
    """
    # Get logger instance
    logger = logging.getLogger(name)

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(level)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    return logger


# Create default test logger
test_logger = setup_logger()
