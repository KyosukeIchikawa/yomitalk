"""User session management module.

This module contains the UserSession class for managing per-user session data.
"""

import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Tuple

from yomitalk.common import APIType
from yomitalk.components.audio_generator import AudioGenerator
from yomitalk.components.text_processor import TextProcessor
from yomitalk.utils.logger import logger

# Global base directories for all users
BASE_TEMP_DIR = Path("data/temp")
BASE_OUTPUT_DIR = Path("data/output")


class UserSession:
    """Class for managing per-user session data."""

    def __init__(self, session_id: str):
        """Initialize user session with unique session ID."""
        self.session_id = session_id

        # Initialize per-user components
        self.text_processor = TextProcessor()
        self.audio_generator = AudioGenerator(
            session_output_dir=self.get_output_dir(),
            session_temp_dir=self.get_talk_temp_dir(),
        )

        # Audio generation state management
        self.audio_generation_state: Dict[str, Any] = {
            "is_generating": False,
            "progress": 0.0,
            "status": "idle",  # idle, generating, completed, failed
            "current_script": "",
            "generated_parts": [],
            "final_audio_path": None,
            "streaming_parts": [],
            "generation_id": None,
            "start_time": None,
            "last_update": None,
        }

        # Default API type is Gemini
        self.text_processor.set_api_type(APIType.GEMINI)

        logger.info(f"User session initialized: {session_id}")

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

    def _is_session_directory(self, directory_name: str) -> bool:
        """
        Check if directory name matches session directory pattern.

        Session directories are typically random alphanumeric strings
        generated by Gradio (like '09wzhr6n07u5', '1aelhpzyzz5').

        Args:
            directory_name (str): Name of the directory

        Returns:
            bool: True if the directory name looks like a session directory
        """

        # セッションディレクトリは通常：
        # - 8文字以上の英数字
        # - 小文字のみ、またはランダムな文字列パターン
        # - 'session_'で始まるテスト用セッション名も含む
        if directory_name.startswith("session_"):
            return True

        # Gradioが生成する典型的なセッションIDパターン（8文字以上の英数字）
        if re.match(r"^[a-z0-9]{8,}$", directory_name):
            return True

        return False

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
            if BASE_TEMP_DIR.exists():
                logger.debug(f"Scanning temp directory: {BASE_TEMP_DIR}")
                removed_count += self._cleanup_directory(
                    BASE_TEMP_DIR, current_time, max_age_seconds
                )
            else:
                logger.debug(f"Temp directory does not exist: {BASE_TEMP_DIR}")

            # Clean up output directory
            if BASE_OUTPUT_DIR.exists():
                logger.debug(f"Scanning output directory: {BASE_OUTPUT_DIR}")
                removed_count += self._cleanup_directory(
                    BASE_OUTPUT_DIR, current_time, max_age_seconds
                )
            else:
                logger.debug(f"Output directory does not exist: {BASE_OUTPUT_DIR}")

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

                # セッションディレクトリかどうかをチェック（セッションIDは通常12文字以上の英数字）
                if not self._is_session_directory(item.name):
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

    def get_temp_dir(self) -> Path:
        """
        Get the temporary directory for the current session.

        Returns:
            Path: Path to the session's temporary directory
        """
        session_temp_dir = BASE_TEMP_DIR / self.session_id
        session_temp_dir.mkdir(parents=True, exist_ok=True)
        return session_temp_dir

    def get_output_dir(self) -> Path:
        """
        Get the output directory for the current session.

        Returns:
            Path: Path to the session's output directory
        """
        session_output_dir = BASE_OUTPUT_DIR / self.session_id
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

    @property
    def current_document_type(self) -> str:
        """Get current document type label name.

        Returns:
            str: Current document type label name
        """
        return self.text_processor.prompt_manager.current_document_type.label_name

    @property
    def current_podcast_mode(self) -> str:
        """Get current podcast mode label name.

        Returns:
            str: Current podcast mode label name
        """
        return self.text_processor.prompt_manager.current_mode.label_name

    @property
    def current_character_mapping(self) -> Tuple[str, str]:
        """Get current character mapping.

        Returns:
            Tuple[str, str]: (character1, character2)
        """
        char_mapping = self.text_processor.prompt_manager.char_mapping
        return char_mapping["Character1"], char_mapping["Character2"]

    @property
    def openai_max_tokens(self) -> int:
        """Get current OpenAI max tokens.

        Returns:
            int: Current OpenAI max tokens
        """
        return self.text_processor.openai_model.get_max_tokens()

    @property
    def gemini_max_tokens(self) -> int:
        """Get current Gemini max tokens.

        Returns:
            int: Current Gemini max tokens
        """
        return self.text_processor.gemini_model.get_max_tokens()

    def get_ui_sync_values(self) -> Tuple[str, str, str, str, int, int]:
        """Get values for syncing UI components with session state.

        Returns:
            Tuple[str, str, str, str, int, int]: (document_type, podcast_mode, character1, character2, openai_max_tokens, gemini_max_tokens)
        """
        character1, character2 = self.current_character_mapping
        return (
            self.current_document_type,
            self.current_podcast_mode,
            character1,
            character2,
            self.openai_max_tokens,
            self.gemini_max_tokens,
        )

    def cleanup(self):
        """Clean up session resources."""
        logger.info(f"Cleaning up user session: {self.session_id}")
        self.cleanup_session_data()

    def update_audio_generation_state(self, **kwargs) -> None:
        """Update audio generation state.

        Args:
            **kwargs: State fields to update
        """
        for key, value in kwargs.items():
            if key in self.audio_generation_state:
                self.audio_generation_state[key] = value
                logger.debug(f"Audio state updated - {key}: {value}")

        # Update last update time
        self.audio_generation_state["last_update"] = time.time()

    def reset_audio_generation_state(self) -> None:
        """Reset audio generation state to initial values."""
        self.audio_generation_state = {
            "is_generating": False,
            "progress": 0.0,
            "status": "idle",
            "current_script": "",
            "generated_parts": [],
            "final_audio_path": None,
            "streaming_parts": [],
            "generation_id": None,
            "start_time": None,
            "last_update": None,
        }
        logger.debug("Audio generation state reset")

    def is_audio_generation_active(self) -> bool:
        """Check if audio generation is currently active.

        Returns:
            bool: True if audio generation is active
        """
        return (
            bool(self.audio_generation_state["is_generating"])
            and self.audio_generation_state["status"] == "generating"
        )

    def get_audio_generation_status(self) -> Dict[str, Any]:
        """Get current audio generation status.

        Returns:
            Dict[str, Any]: Current audio generation state
        """
        return self.audio_generation_state.copy()

    def has_generated_audio(self) -> bool:
        """Check if there is generated audio available.

        Returns:
            bool: True if audio has been generated
        """
        return (
            self.audio_generation_state["final_audio_path"] is not None
            or len(list(self.audio_generation_state["streaming_parts"])) > 0
        )
