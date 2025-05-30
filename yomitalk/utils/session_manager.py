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

        # Initialize directories
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

        # Cleanup old sessions on startup
        self.cleanup_old_sessions()

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

    def _get_folder_modification_time(self, folder_path: Path) -> float:
        """
        Get the modification time of a folder.

        Args:
            folder_path (Path): Path to the folder

        Returns:
            float: Modification time as seconds since the epoch
        """
        try:
            return folder_path.stat().st_mtime
        except Exception as e:
            logger.error(f"Error getting modification time for {folder_path}: {str(e)}")
            return 0

    def cleanup_old_sessions(self, max_age_days: float = 1.0) -> int:
        """
        Clean up sessions older than specified days.

        Args:
            max_age_days (float): Maximum age of sessions in days

        Returns:
            int: Number of removed sessions
        """
        removed_count = 0
        current_time = time.time()
        max_age_seconds = max_age_days * 86400  # Convert days to seconds

        logger.debug(
            f"Starting cleanup of sessions older than {max_age_days} days ({max_age_seconds} seconds)"
        )
        logger.debug(f"Current time: {time.ctime(current_time)}")

        try:
            # Clean up temp directory
            if self.base_temp_dir.exists():
                logger.debug(f"Scanning temp directory: {self.base_temp_dir}")
                removed_count += self._cleanup_directory(
                    self.base_temp_dir, current_time, max_age_seconds
                )
            else:
                logger.debug(f"Temp directory does not exist: {self.base_temp_dir}")

            # Clean up output directory
            if self.base_output_dir.exists():
                logger.debug(f"Scanning output directory: {self.base_output_dir}")
                removed_count += self._cleanup_directory(
                    self.base_output_dir, current_time, max_age_seconds
                )
            else:
                logger.debug(f"Output directory does not exist: {self.base_output_dir}")

            if removed_count > 0:
                logger.info(
                    f"Removed {removed_count} old session folders older than {max_age_days} days"
                )
            else:
                logger.debug("No old sessions found to remove")

            return removed_count
        except Exception as e:
            logger.error(f"Error during old session cleanup: {str(e)}")
            return 0

    def _cleanup_directory(
        self, base_dir: Path, current_time: float, max_age_seconds: float
    ) -> int:
        """
        Clean up old session folders in a directory.

        Args:
            base_dir (Path): Base directory containing session folders
            current_time (float): Current timestamp
            max_age_seconds (float): Maximum age in seconds

        Returns:
            int: Number of removed session folders
        """
        removed_count = 0

        try:
            logger.debug(f"Scanning directory for old sessions: {base_dir}")

            for item in base_dir.iterdir():
                if not item.is_dir():
                    logger.debug(f"Skipping non-directory: {item}")
                    continue

                # セッションフォルダのみを処理（session_で始まるフォルダ名）
                if not item.name.startswith("session_"):
                    logger.debug(f"Skipping non-session directory: {item}")
                    continue

                # フォルダの更新日時を取得
                mod_time = self._get_folder_modification_time(item)
                if mod_time == 0:
                    logger.debug(f"Could not get modification time for: {item}")
                    continue

                # 現在時刻との差分を計算
                age_seconds = current_time - mod_time
                age_days = age_seconds / 86400

                logger.debug(
                    f"Directory: {item}, Last modified: {time.ctime(mod_time)}, Age: {age_days:.1f} days"
                )

                # max_age_seconds（デフォルト1日）より古い場合は削除
                if age_seconds > max_age_seconds:
                    try:
                        logger.info(
                            f"Removing old session directory: {item} (age: {age_days:.1f} days)"
                        )
                        shutil.rmtree(item, ignore_errors=True)
                        removed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to remove old session directory {item}: {str(e)}"
                        )
                else:
                    logger.debug(f"Keeping directory (not old enough): {item}")
        except Exception as e:
            logger.error(f"Error scanning directory {base_dir}: {str(e)}")

        return removed_count

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
