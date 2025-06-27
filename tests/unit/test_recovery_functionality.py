"""Tests for session recovery functionality."""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from yomitalk.app import PaperPodcastApp
from yomitalk.user_session import UserSession


class TestRecoveryFunctionality:
    """Test class for recovery functionality."""

    @pytest.fixture
    def app(self):
        """Create PaperPodcastApp instance for testing."""
        return PaperPodcastApp()

    @pytest.fixture
    def mock_request(self):
        """Create mock Gradio request."""
        request = Mock()
        request.session_hash = "test_session_123"
        return request

    @pytest.fixture
    def browser_state(self):
        """Create test browser state."""
        return {
            "session_id": "test_session_123",
            "audio_generation_active": False,
            "has_generated_audio": False,
            "podcast_text": "Test podcast content",
            "terms_agreed": True,
            "extracted_text": "Test extracted content",
        }

    def test_update_browser_state_ui_content(self, app):
        """Test browser state UI content update."""
        browser_state = {"session_id": "test"}

        result = app.update_browser_state_ui_content(browser_state, "test podcast", True, "test extracted")

        assert result["podcast_text"] == "test podcast"
        assert result["terms_agreed"] is True
        assert result["extracted_text"] == "test extracted"
        assert result["session_id"] == "test"

    def test_update_browser_state_audio_status(self, app):
        """Test browser state audio status update."""
        user_session = UserSession("test_session")
        user_session.update_audio_generation_state(is_generating=True, status="generating", progress=0.5, streaming_parts=["part1.wav", "part2.wav"], estimated_total_parts=4)

        browser_state = {"session_id": "test"}

        result = app.update_browser_state_audio_status(user_session, browser_state)

        assert result["session_id"] == "test_session"
        assert result["audio_generation_active"] is True
        assert result["audio_status"] == "generating"
        assert result["audio_progress"] == 0.5
        assert result["streaming_parts_count"] == 2
        assert result["estimated_total_parts"] == 4

    def test_update_browser_state_audio_status_none_session(self, app):
        """Test browser state audio status update with None session."""
        browser_state = {"session_id": "test"}

        result = app.update_browser_state_audio_status(None, browser_state)

        assert result == browser_state

    def test_update_audio_button_state_with_resume_check(self, app):
        """Test audio button state update with resume check."""
        user_session = UserSession("test_session")
        podcast_text = "Test podcast content"

        # Set up audio generation state with same script
        user_session.update_audio_generation_state(current_script=podcast_text, final_audio_path="/test/audio.wav", status="completed")

        # Mock file existence for has_generated_audio check
        with patch("os.path.exists", return_value=True):
            result = app.update_audio_button_state_with_resume_check(True, podcast_text, user_session)

        assert "音声生成を再開" in result["value"]
        assert result["interactive"] is True
        assert result["variant"] == "primary"

    def test_update_audio_button_state_with_resume_check_different_script(self, app):
        """Test audio button state when script has changed."""
        user_session = UserSession("test_session")
        old_script = "Old podcast content"
        new_script = "New podcast content"

        # Set up audio generation state with different script
        user_session.update_audio_generation_state(current_script=old_script, final_audio_path="/test/audio.wav", status="completed")

        with patch("os.path.exists", return_value=True):
            result = app.update_audio_button_state_with_resume_check(True, new_script, user_session)

        assert "音声を生成" in result["value"]
        assert "再開" not in result["value"]

    def test_extract_file_text_auto_with_browser_state(self, app):
        """Test file text extraction with browser state update."""
        user_session = UserSession("test_session")
        browser_state = {"session_id": "test"}

        # Mock file object
        mock_file = Mock()
        mock_file.name = "test.txt"

        with (
            patch("yomitalk.components.content_extractor.ContentExtractor.extract_text", return_value="Extracted text"),
            patch("yomitalk.components.content_extractor.ContentExtractor.get_source_name_from_file", return_value="test.txt"),
            patch("yomitalk.components.content_extractor.ContentExtractor.append_text_with_source", return_value="Combined text"),
        ):
            result = app.extract_file_text_auto_with_browser_state(mock_file, "existing text", True, user_session, browser_state)

        combined_text, updated_session, updated_browser_state = result

        assert combined_text == "Combined text"
        assert updated_browser_state["extracted_text"] == "Combined text"
        assert updated_browser_state["podcast_text"] == ""
        assert updated_browser_state["terms_agreed"] is False

    def test_generate_podcast_text_with_browser_state(self, app):
        """Test podcast text generation with browser state update."""
        user_session = UserSession("test_session")
        browser_state = {"session_id": "test", "terms_agreed": False}

        # Set up API key for testing
        user_session.text_processor.gemini_model.api_key = "test_key"

        with patch.object(user_session.text_processor, "process_text", return_value="Generated podcast"):
            result = app.generate_podcast_text_with_browser_state("Input text", user_session, browser_state)

        podcast_text, updated_session, updated_browser_state = result

        assert podcast_text == "Generated podcast"
        assert updated_browser_state["podcast_text"] == "Generated podcast"
        assert updated_browser_state["extracted_text"] == "Input text"

    def test_audio_button_state_with_browser_state(self, app):
        """Test audio button state update with browser state."""
        browser_state = {"session_id": "test"}

        result = app.update_audio_button_state_with_browser_state(True, "Test podcast", browser_state)

        button_update, updated_browser_state = result

        assert button_update["interactive"] is True
        assert button_update["variant"] == "primary"
        assert updated_browser_state["podcast_text"] == "Test podcast"
        assert updated_browser_state["terms_agreed"] is True

    def test_browser_state_extracted_text_update(self, app):
        """Test browser state update when extracted text changes."""
        browser_state = {"session_id": "test", "podcast_text": "existing podcast", "terms_agreed": True}

        result = app.update_browser_state_extracted_text("New extracted text", browser_state)

        assert result["extracted_text"] == "New extracted text"
        assert result["podcast_text"] == "existing podcast"
        assert result["terms_agreed"] is True
        assert result["session_id"] == "test"

    def test_browser_state_podcast_text_update(self, app):
        """Test browser state update when podcast text changes."""
        browser_state = {"session_id": "test", "extracted_text": "existing extracted", "terms_agreed": False}

        updated_browser_state = app.update_browser_state_podcast_text("New podcast script", browser_state)

        assert updated_browser_state["podcast_text"] == "New podcast script"
        assert updated_browser_state["extracted_text"] == "existing extracted"  # Should preserve existing
        assert updated_browser_state["terms_agreed"] is False  # Should preserve existing
        assert updated_browser_state["session_id"] == "test"

    def test_browser_state_podcast_text_update_empty_state(self, app):
        """Test browser state update when podcast text changes from empty state."""
        browser_state: Dict[str, Any] = {}

        updated_browser_state = app.update_browser_state_podcast_text("First podcast script", browser_state)

        assert updated_browser_state["podcast_text"] == "First podcast script"
        assert updated_browser_state["extracted_text"] == ""  # Should default to empty
        assert updated_browser_state["terms_agreed"] is False  # Should default to False
