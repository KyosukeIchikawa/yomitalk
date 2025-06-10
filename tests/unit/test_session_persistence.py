"""Test session persistence functionality."""

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from yomitalk.common import APIType
from yomitalk.prompt_manager import DocumentType, PodcastMode
from yomitalk.user_session import UserSession


class TestSessionPersistence:
    """Test session persistence functionality."""

    @pytest.fixture
    def temp_session_dir(self):
        """Create a temporary directory for session testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    def test_session_serialization_to_dict(self):
        """Test session serialization to dictionary."""
        session = UserSession("test_serialization")

        # Configure some settings - set API key first to enable API type setting
        session.text_processor.set_openai_api_key("test_key")
        session.text_processor.set_api_type(APIType.OPENAI)
        session.text_processor.set_document_type(DocumentType.PAPER)
        session.text_processor.set_podcast_mode("section_by_section")
        session.text_processor.openai_model.set_max_tokens(2000)
        session.text_processor.openai_model.set_model_name("gpt-4.1-mini")

        # Serialize to dict
        session_dict = session.to_dict()

        # Verify basic structure
        assert "session_id" in session_dict
        assert "audio_generation_state" in session_dict
        assert "text_processor_state" in session_dict
        assert "last_save_time" in session_dict

        # Verify session ID
        assert session_dict["session_id"] == "test_serialization"

        # Verify text processor state
        text_state = session_dict["text_processor_state"]
        assert text_state["current_api_type"] == APIType.OPENAI.value
        assert text_state["openai_max_tokens"] == 2000
        assert text_state["openai_model_name"] == "gpt-4.1-mini"

        # Verify prompt manager state
        pm_state = text_state["prompt_manager_state"]
        assert pm_state["current_document_type"] == DocumentType.PAPER.value
        assert pm_state["current_mode"] == PodcastMode.SECTION_BY_SECTION.value

    def test_session_deserialization_from_dict(self):
        """Test session restoration from dictionary."""
        # Create original session
        original_session = UserSession("test_deserialization")
        original_session.text_processor.set_gemini_api_key("test_key")
        original_session.text_processor.set_api_type(APIType.GEMINI)
        original_session.text_processor.set_document_type(DocumentType.MANUAL)
        original_session.text_processor.set_podcast_mode("standard")
        original_session.text_processor.gemini_model.set_max_tokens(1500)
        original_session.text_processor.gemini_model.set_model_name(
            "gemini-2.5-pro-preview-05-06"
        )

        # Serialize to dict
        session_dict = original_session.to_dict()

        # Restore from dict
        restored_session = UserSession.from_dict(session_dict)

        # Verify session was restored correctly
        assert restored_session.session_id == "test_deserialization"
        assert restored_session.text_processor.current_api_type == APIType.GEMINI
        assert (
            restored_session.text_processor.prompt_manager.current_document_type
            == DocumentType.MANUAL
        )
        assert (
            restored_session.text_processor.prompt_manager.current_mode
            == PodcastMode.STANDARD
        )
        assert restored_session.text_processor.gemini_model.get_max_tokens() == 1500
        assert (
            restored_session.text_processor.gemini_model.model_name
            == "gemini-2.5-pro-preview-05-06"
        )

    def test_session_file_save_and_load(self, temp_session_dir):
        """Test session save/load to/from file."""
        # Patch the base directories to use temp directory
        with patch("yomitalk.user_session.BASE_TEMP_DIR", temp_session_dir):
            # Create and configure session
            session = UserSession("test_file_persistence")
            session.text_processor.set_openai_api_key("test_key")
            session.text_processor.set_api_type(APIType.OPENAI)
            session.text_processor.set_document_type(DocumentType.BLOG)
            session.text_processor.openai_model.set_max_tokens(3000)

            # Update audio state
            session.update_audio_generation_state(
                status="generating", progress=0.5, current_script="Test script content"
            )

            # Save to file
            success = session.save_to_file()
            assert success is True

            # Verify file was created
            session_file = (
                temp_session_dir / "test_file_persistence" / "session_state.json"
            )
            assert session_file.exists()

            # Verify file content is valid JSON
            with open(session_file, "r") as f:
                saved_data = json.load(f)
            assert saved_data["session_id"] == "test_file_persistence"

            # Load session from file
            loaded_session = UserSession.load_from_file("test_file_persistence")
            assert loaded_session is not None
            assert loaded_session.session_id == "test_file_persistence"
            assert loaded_session.text_processor.current_api_type == APIType.OPENAI
            assert (
                loaded_session.text_processor.prompt_manager.current_document_type
                == DocumentType.BLOG
            )
            assert loaded_session.text_processor.openai_model.get_max_tokens() == 3000

            # Verify audio state was restored
            audio_state = loaded_session.get_audio_generation_status()
            assert audio_state["status"] == "generating"
            assert audio_state["progress"] == 0.5
            assert audio_state["current_script"] == "Test script content"

    def test_session_load_nonexistent_file(self, temp_session_dir):
        """Test loading a session that doesn't exist."""
        with patch("yomitalk.user_session.BASE_TEMP_DIR", temp_session_dir):
            loaded_session = UserSession.load_from_file("nonexistent_session")
            assert loaded_session is None

    def test_session_auto_save(self, temp_session_dir):
        """Test automatic session saving."""
        with patch("yomitalk.user_session.BASE_TEMP_DIR", temp_session_dir):
            session = UserSession("test_auto_save")

            # Auto-save should be triggered when creating new session
            session_file = temp_session_dir / "test_auto_save" / "session_state.json"
            # Note: auto_save is called in the creation process

            # Trigger auto-save by updating state
            session.update_audio_generation_state(status="completed")

            # File should exist after auto-save
            assert session_file.exists()

            # Verify content was saved
            with open(session_file, "r") as f:
                saved_data = json.load(f)
            assert saved_data["audio_generation_state"]["status"] == "completed"

    def test_session_restoration_info(self):
        """Test session restoration information."""
        # Clear any environment API keys for this test
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False
        ):
            session = UserSession("test_restoration_info")

            # Get restoration info
            info = session.get_session_restoration_info()

            # Verify structure
            assert "session_id" in info
            assert "missing_api_keys" in info
            assert "current_api_type" in info
            assert "has_generated_audio" in info
            assert "last_save_time" in info

            # Verify values (initially no API keys or audio)
            assert info["session_id"] == "test_restoration_info"
            assert info["missing_api_keys"]["openai"] is True  # No API key set
            assert info["missing_api_keys"]["gemini"] is True  # No API key set
            assert info["has_generated_audio"] is False  # No audio generated

            # Set an API key and check that it's no longer missing
            session.text_processor.set_openai_api_key("test_key")
            session.text_processor.set_api_type(APIType.OPENAI)
            info = session.get_session_restoration_info()
            assert info["current_api_type"] == APIType.OPENAI.value
            assert info["missing_api_keys"]["openai"] is False  # Now has key
            assert info["missing_api_keys"]["gemini"] is True  # Still missing

    def test_session_needs_api_key_restoration(self):
        """Test API key restoration detection."""
        # Clear any environment API keys for this test
        with patch.dict(
            os.environ, {"OPENAI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False
        ):
            session = UserSession("test_api_key_restoration")

            # Initially both API keys should be missing
            missing_keys = session.needs_api_key_restoration()
            assert missing_keys["openai"] is True
            assert missing_keys["gemini"] is True

            # Set OpenAI API key
            session.text_processor.set_openai_api_key("test_openai_key")
            missing_keys = session.needs_api_key_restoration()
            assert missing_keys["openai"] is False  # Now has key
            assert missing_keys["gemini"] is True  # Still missing

            # Set Gemini API key
            session.text_processor.set_gemini_api_key("test_gemini_key")
            missing_keys = session.needs_api_key_restoration()
            assert missing_keys["openai"] is False  # Has key
            assert missing_keys["gemini"] is False  # Now has key

    def test_session_character_mapping_persistence(self, temp_session_dir):
        """Test character mapping persistence."""
        with patch("yomitalk.user_session.BASE_TEMP_DIR", temp_session_dir):
            # Create session and set character mapping
            session = UserSession("test_character_mapping")
            session.text_processor.set_character_mapping("ずんだもん", "四国めたん")

            # Save and reload
            session.save_to_file()
            loaded_session = UserSession.load_from_file("test_character_mapping")

            # Verify character mapping was preserved
            assert loaded_session is not None
            char1, char2 = loaded_session.current_character_mapping
            assert char1 == "ずんだもん"
            assert char2 == "四国めたん"

    def test_session_roundtrip_persistence(self, temp_session_dir):
        """Test complete roundtrip session persistence."""
        with patch("yomitalk.user_session.BASE_TEMP_DIR", temp_session_dir):
            # Create session with comprehensive settings
            original_session = UserSession("test_roundtrip")

            # Configure all major settings
            original_session.text_processor.set_gemini_api_key("test_key")
            original_session.text_processor.set_api_type(APIType.GEMINI)
            original_session.text_processor.set_document_type(DocumentType.MINUTES)
            original_session.text_processor.set_podcast_mode("section_by_section")
            original_session.text_processor.set_character_mapping(
                "九州そら", "中国うさぎ"
            )
            original_session.text_processor.openai_model.set_max_tokens(4000)
            original_session.text_processor.openai_model.set_model_name("gpt-4.1")
            original_session.text_processor.gemini_model.set_max_tokens(2500)
            original_session.text_processor.gemini_model.set_model_name(
                "gemini-2.5-pro-preview-05-06"
            )

            # Update audio generation state
            original_session.update_audio_generation_state(
                status="completed",
                progress=1.0,
                current_script="完全なスクリプト内容",
                final_audio_path="/path/to/final/audio.wav",
            )

            # Save session
            save_success = original_session.save_to_file()
            assert save_success is True

            # Load session
            loaded_session = UserSession.load_from_file("test_roundtrip")
            assert loaded_session is not None

            # Verify all settings were preserved
            assert loaded_session.text_processor.current_api_type == APIType.GEMINI
            assert (
                loaded_session.text_processor.prompt_manager.current_document_type
                == DocumentType.MINUTES
            )
            assert (
                loaded_session.text_processor.prompt_manager.current_mode
                == PodcastMode.SECTION_BY_SECTION
            )

            char1, char2 = loaded_session.current_character_mapping
            assert char1 == "九州そら"
            assert char2 == "中国うさぎ"

            assert loaded_session.text_processor.openai_model.get_max_tokens() == 4000
            assert loaded_session.text_processor.openai_model.model_name == "gpt-4.1"
            assert loaded_session.text_processor.gemini_model.get_max_tokens() == 2500
            assert (
                loaded_session.text_processor.gemini_model.model_name
                == "gemini-2.5-pro-preview-05-06"
            )

            # Verify audio state was preserved
            audio_state = loaded_session.get_audio_generation_status()
            assert audio_state["status"] == "completed"
            assert audio_state["progress"] == 1.0
            assert audio_state["current_script"] == "完全なスクリプト内容"
            assert audio_state["final_audio_path"] == "/path/to/final/audio.wav"

            # Verify restoration info shows correct state
            restoration_info = loaded_session.get_session_restoration_info()
            assert restoration_info["current_api_type"] == APIType.GEMINI.value
            assert restoration_info["has_generated_audio"] is True
            # Note: API keys are not persisted for security, but the test environment might have them
            # So we don't assert their absence in this comprehensive test
