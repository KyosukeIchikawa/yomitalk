"""File operation utility module.

Provides useful functions for file operations such as creating temporary files,
ensuring directories exist, and saving uploaded files.
"""

import os
import uuid
from pathlib import Path


def ensure_dir(directory):
    """
    Ensure directory exists, create it if it doesn't.

    Args:
        directory (str): Path of the directory to create

    Returns:
        str: Path of the created directory
    """
    os.makedirs(directory, exist_ok=True)
    return directory


def get_temp_filepath(ext=".tmp"):
    """
    Generate a temporary file path.

    Args:
        ext (str): File extension

    Returns:
        str: Path to the temporary file
    """
    temp_dir = ensure_dir("data/temp")
    return os.path.join(temp_dir, f"{uuid.uuid4()}{ext}")


def get_output_filepath(prefix="output", ext=".wav"):
    """
    Generate an output file path.

    Args:
        prefix (str): Prefix for the file name
        ext (str): File extension

    Returns:
        str: Path to the output file
    """
    output_dir = ensure_dir("data/output")
    return os.path.join(output_dir, f"{prefix}_{uuid.uuid4()}{ext}")


def save_uploaded_file(uploaded_file, destination=None):
    """
    Save an uploaded file.

    Args:
        uploaded_file: Uploaded file object
        destination (str, optional): Destination path. If None, generates a temp path

    Returns:
        str: Path to the saved file
    """
    if destination is None:
        _, ext = os.path.splitext(uploaded_file.name)
        destination = get_temp_filepath(ext)

    with open(destination, "wb") as f:
        f.write(uploaded_file.read())

    return destination


def clean_temp_files(days=1):
    """
    Delete old temporary files.

    Args:
        days (int): Delete files older than this number of days

    Returns:
        int: Number of deleted files
    """
    import time

    temp_dir = Path("data/temp")
    if not temp_dir.exists():
        return 0

    now = time.time()
    count = 0

    for file_path in temp_dir.glob("*"):
        if file_path.is_file():
            # Get file's last modification time
            mtime = file_path.stat().st_mtime
            age_days = (now - mtime) / (24 * 3600)

            # Delete if older than specified days
            if age_days >= days:
                try:
                    file_path.unlink()
                    count += 1
                except BaseException:
                    pass

    return count
