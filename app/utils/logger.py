"""Utility module providing logging functionality.

Provides logging-related features such as logger setup and logging decorators
for use throughout the application.
"""

import logging
import os
from datetime import datetime


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
    # Ensure log directory exists
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)

    # Generate log filename with current date
    log_file = os.path.join(
        log_dir, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    # Get logger instance
    logger = logging.getLogger(name)
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


# Create default logger
logger = setup_logger()


def log_process(process_name):
    """
    Log process start and end.

    Args:
        process_name (str): Name of the process

    Returns:
        function: Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"{process_name} started")
            try:
                result = func(*args, **kwargs)
                logger.info(f"{process_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{process_name} error occurred: {str(e)}", exc_info=True)
                raise

        return wrapper

    return decorator
