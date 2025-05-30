"""Session Manager Module.

This module provides functionality for managing Hugging Face Space sessions.
"""

import shutil
import time
import uuid
from pathlib import Path

from yomitalk.utils.logger import logger


class SessionManager:
    """Class for managing session data across Hugging Face Space sessions."""

    def __init__(self):
        """Initialize SessionManager."""
        self.session_id = self._generate_session_id()
        self.base_temp_dir = Path("data/temp")
        self.base_output_dir = Path("data/output")
        logger.info(f"Session initialized with ID: {self.session_id}")

    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID.

        Creates a unique ID based on timestamp and UUID to ensure uniqueness
        across all environments.

        Returns:
            str: A unique session ID
        """
        # Always use UUID-based session ID
        timestamp = int(time.time())
        random_id = uuid.uuid4().hex[:8]
        return f"session_{timestamp}_{random_id}"

    def get_session_id(self) -> str:
        """
        Get the current session ID.

        Returns:
            str: The current session ID
        """
        return self.session_id

    def get_temp_dir(self) -> Path:
        """
        Get the temporary directory for the current session.

        Returns:
            Path: Path to the session's temporary directory
        """
        session_temp_dir = self.base_temp_dir / self.session_id
        session_temp_dir.mkdir(parents=True, exist_ok=True)
        return session_temp_dir

    def get_output_dir(self) -> Path:
        """
        Get the output directory for the current session.

        Returns:
            Path: Path to the session's output directory
        """
        session_output_dir = self.base_output_dir / self.session_id
        session_output_dir.mkdir(parents=True, exist_ok=True)
        return session_output_dir

    def get_talk_temp_dir(self) -> Path:
        """
        Get the talks temporary directory for the current session.

        Returns:
            Path: Path to the session's talks temporary directory
        """
        talk_temp_dir = self.get_temp_dir() / "talks"
        talk_temp_dir.mkdir(parents=True, exist_ok=True)
        return talk_temp_dir

    def cleanup_session_data(self) -> bool:
        """
        Clean up all session data when the session ends.

        Removes the session's temporary and output directories.

        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        success = True
        try:
            # セッション用テンポラリディレクトリの削除
            temp_dir = self.get_temp_dir()
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Removed session temp directory: {temp_dir}")

            # セッション用出力ディレクトリの削除
            output_dir = self.get_output_dir()
            if output_dir.exists():
                shutil.rmtree(output_dir, ignore_errors=True)
                logger.info(f"Removed session output directory: {output_dir}")

            return success
        except Exception as e:
            logger.error(f"Failed to clean up session data: {str(e)}")
            return False
