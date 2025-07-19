"""User session management module.

This module contains the UserSession class for managing per-user session data.
"""

import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from yomitalk.common import APIType
from yomitalk.components.audio_generator import AudioGenerator
from yomitalk.components.text_processor import TextProcessor
from yomitalk.prompt_manager import DocumentType, PodcastMode
from yomitalk.utils.logger import logger

# Global base directories for all users
BASE_TEMP_DIR = Path("data/temp")
BASE_OUTPUT_DIR = Path("data/output")


class UserSession:
    """Class for managing per-user session data."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize user session with unique session ID."""
        # Use provided session_id or generate new UUID-based ID
        self.session_id = session_id or str(uuid.uuid4())

        # Initialize per-user components
        self.text_processor = TextProcessor()
        self.audio_generator = AudioGenerator(
            session_output_dir=self.get_output_dir(),
            session_temp_dir=self.get_talk_temp_dir(),
        )

        # Default API type is Gemini
        self.text_processor.set_api_type(APIType.GEMINI)

    def cleanup_old_sessions(self, max_age_days: float = 1.0) -> int:
        """
        Clean up sessions older than specified days.
        Simplified version that only removes the current session's directories.
        """
        import shutil

        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 86400

            removed_count = 0

            # Clean up current session's directories if they're old enough
            for directory in [self.get_temp_dir(), self.get_output_dir()]:
                if directory.exists():
                    mod_time = directory.stat().st_mtime
                    if current_time - mod_time > max_age_seconds:
                        shutil.rmtree(directory, ignore_errors=True)
                        removed_count += 1
                        logger.info(f"Removed old session directory: {directory}")

            return removed_count
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
            return 0

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

    def get_audio_generation_status(self, browser_state: Optional[dict] = None) -> Dict[str, Any]:
        """Get current audio generation status.

        Args:
            browser_state: Current BrowserState dictionary (optional for backward compatibility)

        Returns:
            Dict[str, Any]: Current audio generation state
        """
        # Backward compatibility: if no browser_state provided, return legacy format
        if browser_state is None:
            return self.audio_generation_state.copy()

        return dict(browser_state.get("audio_generation_state", {}))

    def has_generated_audio(self, browser_state: Optional[dict] = None) -> bool:
        """Check if there is generated audio available.

        Args:
            browser_state: Current BrowserState dictionary (optional for backward compatibility)

        Returns:
            bool: True if audio has been generated
        """
        # Backward compatibility: if no browser_state provided, return False
        if browser_state is None:
            return False

        audio_state = browser_state.get("audio_generation_state", {})
        return audio_state.get("final_audio_path") is not None or len(audio_state.get("streaming_parts", [])) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session state to dictionary for persistence.

        Returns:
            Dict[str, Any]: Serializable session state
        """
        return {
            "session_id": self.session_id,
            "audio_generation_state": self.audio_generation_state.copy(),
            "text_processor_state": {
                "current_api_type": (self.text_processor.current_api_type.value if self.text_processor.current_api_type else None),
                "openai_api_key_set": bool(self.text_processor.openai_model.api_key),
                "gemini_api_key_set": bool(self.text_processor.gemini_model.api_key),
                "openai_max_tokens": self.text_processor.openai_model.get_max_tokens(),
                "gemini_max_tokens": self.text_processor.gemini_model.get_max_tokens(),
                "openai_model_name": self.text_processor.openai_model.model_name,
                "gemini_model_name": self.text_processor.gemini_model.model_name,
                "prompt_manager_state": {
                    "current_document_type": self.text_processor.prompt_manager.current_document_type.value,
                    "current_mode": self.text_processor.prompt_manager.current_mode.value,
                    "char_mapping": self.text_processor.prompt_manager.char_mapping.copy(),
                },
            },
            "last_save_time": time.time(),
        }

    def update_settings_from_browser_state(self, browser_state: dict) -> None:
        """Update session settings from BrowserState.

        Args:
            browser_state: Current BrowserState dictionary
        """
        settings = browser_state.get("user_settings", {})

        # Update API type
        api_type_str = settings.get("current_api_type", "gemini")
        for api_type in APIType:
            if api_type.name.lower() == api_type_str:
                # Only set if we have the necessary API key
                if (api_type == APIType.OPENAI and self.text_processor.openai_model.has_api_key()) or (api_type == APIType.GEMINI and self.text_processor.gemini_model.has_api_key()):
                    self.text_processor.set_api_type(api_type)
                break

        # Update model settings
        if "openai_max_tokens" in settings:
            self.text_processor.openai_model.set_max_tokens(settings["openai_max_tokens"])
        if "gemini_max_tokens" in settings:
            self.text_processor.gemini_model.set_max_tokens(settings["gemini_max_tokens"])
        if "openai_model" in settings:
            self.text_processor.openai_model.set_model_name(settings["openai_model"])
        if "gemini_model" in settings:
            self.text_processor.gemini_model.set_model_name(settings["gemini_model"])

        # Update prompt manager settings
        if "document_type" in settings:
            for doc_type in DocumentType:
                if doc_type.value == settings["document_type"]:
                    self.text_processor.prompt_manager.set_document_type(doc_type)
                    break
        if "podcast_mode" in settings:
            for mode in PodcastMode:
                if mode.value == settings["podcast_mode"]:
                    self.text_processor.prompt_manager.set_podcast_mode(mode)
                    break
        if "character1" in settings and "character2" in settings:
            self.text_processor.prompt_manager.char_mapping = {"Character1": settings["character1"], "Character2": settings["character2"]}

    def sync_settings_to_browser_state(self, browser_state: dict) -> dict:
        """Sync current session settings to BrowserState.

        Args:
            browser_state: Current BrowserState dictionary

        Returns:
            dict: Updated BrowserState
        """
        browser_state["user_settings"].update(
            {
                "current_api_type": self.text_processor.current_api_type.name.lower() if self.text_processor.current_api_type else "gemini",
                "openai_max_tokens": self.text_processor.openai_model.get_max_tokens(),
                "gemini_max_tokens": self.text_processor.gemini_model.get_max_tokens(),
                "openai_model": self.text_processor.openai_model.model_name,
                "gemini_model": self.text_processor.gemini_model.model_name,
                "document_type": self.text_processor.prompt_manager.current_document_type.value,
                "podcast_mode": self.text_processor.prompt_manager.current_mode.value,
                "character1": self.text_processor.prompt_manager.char_mapping.get("Character1", "Zundamon"),
                "character2": self.text_processor.prompt_manager.char_mapping.get("Character2", "Shikoku Metan"),
            }
        )

        return browser_state

    # Temporary compatibility methods for tests - will be removed
    @property
    def audio_generation_state(self) -> Dict[str, Any]:
        """Temporary compatibility property for tests."""
        return {
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
            "estimated_total_parts": 1,
        }
