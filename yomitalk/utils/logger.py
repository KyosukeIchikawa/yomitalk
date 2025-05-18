"""Utility module providing logging functionality.

Provides logging-related features such as logger setup and logging decorators
for use throughout the application.
"""

import logging


# Logger configuration
def setup_logger(name="yomitalk", level=logging.INFO):
    """
    Set up a logger.

    Args:
        name (str): Logger name
        level: Log level

    Returns:
        logging.Logger: Configured logger instance
    """
    # Get logger instance
    logger = logging.getLogger(name)

    # Clear any existing handlers to prevent duplicate handlers
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(level)

    # Set up handlers
    # Console handler only by default
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)

    # Add console handler to logger
    logger.addHandler(console_handler)

    return logger


# Create default logger
logger = setup_logger()
