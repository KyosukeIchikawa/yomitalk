"""Tests for BrowserState-based session management."""

from unittest.mock import Mock

from yomitalk.app import PaperPodcastApp
from yomitalk.user_session import UserSession


class TestBrowserStateManagement:
    """Test BrowserState-based session management functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        self.app = PaperPodcastApp()
        self.mock_request = Mock()
        self.mock_request.session_hash = "gradio-session-hash"

    def test_new_session_creates_uuid_based_id(self):
        """Test that new sessions get UUID-based IDs independent of Gradio session hash."""
        empty_browser_state = {"app_session_id": "", "audio_generation_state": {}, "user_settings": {}, "ui_state": {}}

        user_session, updated_browser_state = self.app.create_user_session_with_browser_state(self.mock_request, empty_browser_state)

        # Should generate new UUID-based session ID
        assert user_session.session_id != ""
        assert user_session.session_id != self.mock_request.session_hash
        assert len(user_session.session_id) == 36  # UUID format
        assert "-" in user_session.session_id  # UUID contains hyphens

        # Browser state should be updated with new session ID
        assert updated_browser_state["app_session_id"] == user_session.session_id

    def test_existing_session_restoration(self):
        """Test that existing sessions are restored using app_session_id."""
        existing_session_id = "550e8400-e29b-41d4-a716-446655440000"
        browser_state_with_session = {
            "app_session_id": existing_session_id,
            "audio_generation_state": {"is_generating": False, "status": "idle"},
            "user_settings": {"current_api_type": "openai", "character1": "Kyushu Sora"},
            "ui_state": {"podcast_text": "Previous session content", "terms_agreed": True},
        }

        user_session, updated_browser_state = self.app.create_user_session_with_browser_state(self.mock_request, browser_state_with_session)

        # Should use existing session ID, not create new one
        assert user_session.session_id == existing_session_id
        assert updated_browser_state["app_session_id"] == existing_session_id

        # Browser state should remain unchanged
        assert updated_browser_state == browser_state_with_session

    def test_session_independence_from_gradio_hash(self):
        """Test that app session ID remains stable even when Gradio session hash changes."""
        app_session_id = "550e8400-e29b-41d4-a716-446655440000"
        browser_state = {"app_session_id": app_session_id, "audio_generation_state": {}, "user_settings": {}, "ui_state": {}}

        # First request with one Gradio session hash
        request1 = Mock()
        request1.session_hash = "gradio-hash-1"

        user_session1, _ = self.app.create_user_session_with_browser_state(request1, browser_state)

        # Second request with different Gradio session hash but same browser state
        request2 = Mock()
        request2.session_hash = "gradio-hash-2"

        user_session2, _ = self.app.create_user_session_with_browser_state(request2, browser_state)

        # Both should use the same app session ID
        assert user_session1.session_id == app_session_id
        assert user_session2.session_id == app_session_id
        assert user_session1.session_id == user_session2.session_id

    def test_browser_state_structure_validation(self):
        """Test that the new BrowserState structure is properly initialized."""
        empty_browser_state = {"app_session_id": "", "audio_generation_state": {}, "user_settings": {}, "ui_state": {}}

        user_session, updated_browser_state = self.app.create_user_session_with_browser_state(self.mock_request, empty_browser_state)

        # Verify complete BrowserState structure
        assert "app_session_id" in updated_browser_state
        assert "audio_generation_state" in updated_browser_state
        assert "user_settings" in updated_browser_state
        assert "ui_state" in updated_browser_state

        # Verify user_settings are properly populated
        user_settings = updated_browser_state["user_settings"]
        assert "current_api_type" in user_settings
        assert "document_type" in user_settings
        assert "podcast_mode" in user_settings
        assert "character1" in user_settings
        assert "character2" in user_settings

    def test_settings_sync_to_browser_state(self):
        """Test that session settings are properly synced to BrowserState."""
        from yomitalk.common import APIType
        from yomitalk.prompt_manager import DocumentType

        user_session = UserSession()

        # Configure some settings
        user_session.text_processor.openai_model.set_api_key("test-openai-key")  # Set API key first
        user_session.text_processor.set_api_type(APIType.OPENAI)
        user_session.text_processor.set_document_type(DocumentType.PAPER)
        user_session.text_processor.prompt_manager.char_mapping = {"Character1": "Kyushu Sora", "Character2": "Chugoku Usagi"}

        browser_state = {"app_session_id": user_session.session_id, "audio_generation_state": {}, "user_settings": {}, "ui_state": {}}

        updated_browser_state = user_session.sync_settings_to_browser_state(browser_state)

        # Verify settings are synced
        user_settings = updated_browser_state["user_settings"]
        assert user_settings["current_api_type"] == "openai"
        assert user_settings["document_type"] == "paper"  # Enum value
        assert user_settings["character1"] == "Kyushu Sora"
        assert user_settings["character2"] == "Chugoku Usagi"

    def test_settings_restore_from_browser_state(self):
        """Test that session settings are properly restored from BrowserState."""
        user_session = UserSession()

        browser_state = {
            "app_session_id": user_session.session_id,
            "audio_generation_state": {},
            "user_settings": {
                "current_api_type": "gemini",
                "document_type": "paper",
                "podcast_mode": "standard",
                "character1": "Zundamon",
                "character2": "Shikoku Metan",
                "openai_max_tokens": 3000,
                "gemini_max_tokens": 7000,
            },
            "ui_state": {},
        }

        user_session.update_settings_from_browser_state(browser_state)

        # Verify settings are restored
        if user_session.text_processor.current_api_type:
            assert user_session.text_processor.current_api_type.value == "gemini"
        assert user_session.text_processor.prompt_manager.current_document_type.value == "paper"
        assert user_session.text_processor.prompt_manager.current_mode.value == "standard"
        assert user_session.text_processor.prompt_manager.char_mapping["Character1"] == "Zundamon"
        assert user_session.text_processor.prompt_manager.char_mapping["Character2"] == "Shikoku Metan"
        assert user_session.text_processor.openai_model.get_max_tokens() == 3000
        assert user_session.text_processor.gemini_model.get_max_tokens() == 7000


class TestBrowserStateUIContent:
    """Test BrowserState UI content management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = PaperPodcastApp()

    def test_update_browser_state_ui_content_new_structure(self):
        """Test updating UI content in the new BrowserState structure."""
        browser_state = {"app_session_id": "test-uuid", "audio_generation_state": {}, "user_settings": {}, "ui_state": {}}

        updated_state = self.app.update_browser_state_ui_content(browser_state, podcast_text="Generated podcast script", terms_agreed=True)

        # Verify ui_state section is properly updated
        ui_state = updated_state["ui_state"]
        assert ui_state["podcast_text"] == "Generated podcast script"
        assert ui_state["terms_agreed"] is True
        # extracted_text is not saved to browser_state anymore
        assert "extracted_text" not in ui_state

    def test_update_browser_state_creates_ui_state_if_missing(self):
        """Test that ui_state section is created if missing."""
        browser_state = {
            "app_session_id": "test-uuid",
            "audio_generation_state": {},
            "user_settings": {},
            # ui_state is missing
        }

        updated_state = self.app.update_browser_state_ui_content(browser_state, podcast_text="Test content", terms_agreed=False)

        # Should create ui_state section
        assert "ui_state" in updated_state
        assert updated_state["ui_state"]["podcast_text"] == "Test content"
        assert updated_state["ui_state"]["terms_agreed"] is False
        # extracted_text is not saved to browser_state anymore
        assert "extracted_text" not in updated_state["ui_state"]

    def test_update_browser_state_handles_empty_values(self):
        """Test handling of empty/None values in UI content update."""
        browser_state = {"app_session_id": "test-uuid", "audio_generation_state": {}, "user_settings": {}, "ui_state": {}}

        updated_state = self.app.update_browser_state_ui_content(browser_state, podcast_text="", terms_agreed=False)

        ui_state = updated_state["ui_state"]
        assert ui_state["podcast_text"] == ""  # Empty string should remain empty
        assert ui_state["terms_agreed"] is False
        # extracted_text is not saved to browser_state anymore
        assert "extracted_text" not in ui_state
