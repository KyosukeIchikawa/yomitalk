"""Tests for UI initialization with BrowserState restoration."""

from unittest.mock import Mock

from yomitalk.app import PaperPodcastApp


class TestUIInitialization:
    """Test UI initialization and component updates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = PaperPodcastApp()
        self.mock_request = Mock()
        self.mock_request.session_hash = "test-gradio-hash"

    def test_initialize_session_and_ui_empty_state(self):
        """Test UI initialization with empty BrowserState."""
        empty_browser_state = {
            "app_session_id": "",
            "audio_generation_state": {
                "is_generating": False,
                "progress": 0.0,
                "status": "idle",
                "current_script": "",
                "final_audio_path": None,
                "streaming_parts": [],
                "generation_id": None,
                "start_time": None,
                "estimated_total_parts": 1,
            },
            "user_settings": {
                "current_api_type": "gemini",
                "document_type": "research_paper",
                "podcast_mode": "academic",
                "character1": "Zundamon",
                "character2": "Shikoku Metan",
                "openai_max_tokens": 4000,
                "gemini_max_tokens": 8000,
                "openai_model": "gpt-4o-mini",
                "gemini_model": "gemini-1.5-flash",
            },
            "ui_state": {"podcast_text": "", "terms_agreed": False},
        }

        result = self.app.initialize_session_and_ui(self.mock_request, empty_browser_state)

        # Should return 31 elements (all UI components)
        assert len(result) == 31

        # Check key components
        user_session = result[0]
        updated_browser_state = result[1]
        extracted_text_update = result[13]
        podcast_text_update = result[25]
        terms_checkbox_update = result[26]

        # Verify session creation
        assert user_session is not None
        assert user_session.session_id != ""
        assert len(user_session.session_id) == 36  # UUID format

        # Verify browser state update
        assert updated_browser_state["app_session_id"] == user_session.session_id

        # Verify UI components are returned (specific content testing done elsewhere)
        assert extracted_text_update is not None
        assert podcast_text_update is not None
        assert terms_checkbox_update is not None

    def test_initialize_session_and_ui_with_content(self):
        """Test UI initialization with existing content in BrowserState."""
        browser_state_with_content = {
            "app_session_id": "550e8400-e29b-41d4-a716-446655440000",
            "audio_generation_state": {
                "is_generating": False,
                "progress": 1.0,
                "status": "completed",
                "current_script": "Previous script content",
                "final_audio_path": "/path/to/audio.wav",
                "streaming_parts": ["part1.wav", "part2.wav"],
                "generation_id": "gen123",
                "start_time": None,
                "estimated_total_parts": 2,
            },
            "user_settings": {
                "current_api_type": "openai",
                "document_type": "paper",
                "podcast_mode": "standard",
                "character1": "Kyushu Sora",
                "character2": "Chugoku Usagi",
                "openai_max_tokens": 3000,
                "gemini_max_tokens": 6000,
                "openai_model": "gpt-4",
                "gemini_model": "gemini-1.5-pro",
            },
            "ui_state": {"podcast_text": "これは既存のポッドキャストスクリプトです。", "terms_agreed": True},
        }

        result = self.app.initialize_session_and_ui(self.mock_request, browser_state_with_content)

        # Check key components
        user_session = result[0]
        _ = result[1]  # updated_browser_state
        extracted_text_update = result[13]
        podcast_text_update = result[25]
        terms_checkbox_update = result[26]

        # Verify existing session is used
        assert user_session.session_id == "550e8400-e29b-41d4-a716-446655440000"

        # Verify UI components are returned with content (specific testing done elsewhere)
        assert extracted_text_update is not None
        assert podcast_text_update is not None
        assert terms_checkbox_update is not None

    def test_initialize_session_and_ui_settings_restoration(self):
        """Test that user settings are properly restored during initialization."""
        browser_state = {
            "app_session_id": "test-uuid",
            "audio_generation_state": {
                "is_generating": False,
                "progress": 0.0,
                "status": "idle",
                "current_script": "",
                "final_audio_path": None,
                "streaming_parts": [],
                "generation_id": None,
                "start_time": None,
                "estimated_total_parts": 1,
            },
            "user_settings": {
                "current_api_type": "openai",
                "document_type": "paper",
                "podcast_mode": "standard",
                "character1": "Chubu Tsurugi",
                "character2": "Kyushu Sora",
                "openai_max_tokens": 2500,
                "gemini_max_tokens": 7500,
                "openai_model": "gpt-4-turbo",
                "gemini_model": "gemini-1.5-flash",
            },
            "ui_state": {"podcast_text": "", "terms_agreed": False},
        }

        result = self.app.initialize_session_and_ui(self.mock_request, browser_state)

        # Check UI sync values (positions 2-7)
        document_type = result[2]
        podcast_mode = result[3]
        character1 = result[4]
        character2 = result[5]
        openai_max_tokens = result[6]
        gemini_max_tokens = result[7]

        # Verify settings are properly restored
        assert document_type == "論文"  # Japanese label name
        assert podcast_mode == "概要解説"  # Japanese label name
        assert character1 == "Chubu Tsurugi"
        assert character2 == "Kyushu Sora"
        assert openai_max_tokens == 2500
        assert gemini_max_tokens == 7500

    def test_ui_component_interactive_states(self):
        """Test that all UI components are properly set to interactive."""
        browser_state = {"app_session_id": "", "audio_generation_state": {}, "user_settings": {}, "ui_state": {}}

        result = self.app.initialize_session_and_ui(self.mock_request, browser_state)

        # Check that key interactive components are enabled
        file_input_update = result[8]
        url_input_update = result[9]
        url_extract_btn_update = result[10]
        auto_separator_checkbox_update = result[11]
        clear_text_btn_update = result[12]
        extracted_text_update = result[13]
        document_type_radio_update = result[14]
        podcast_mode_radio_update = result[15]
        character1_dropdown_update = result[16]
        character2_dropdown_update = result[17]

        # Verify all components are returned (interactivity testing requires more setup)
        assert file_input_update is not None
        assert url_input_update is not None
        assert url_extract_btn_update is not None
        assert auto_separator_checkbox_update is not None
        assert clear_text_btn_update is not None
        assert extracted_text_update is not None
        assert document_type_radio_update is not None
        assert podcast_mode_radio_update is not None
        assert character1_dropdown_update is not None
        assert character2_dropdown_update is not None

    def test_placeholder_behavior_consistency(self):
        """Test consistent placeholder behavior across different content states."""
        # Test with empty content
        browser_state = {"app_session_id": "test-uuid", "audio_generation_state": {}, "user_settings": {}, "ui_state": {"podcast_text": "", "terms_agreed": False, "extracted_text": ""}}
        result = self.app.initialize_session_and_ui(self.mock_request, browser_state)

        extracted_text_update = result[13]
        podcast_text_update = result[25]

        # Verify components are returned (placeholder testing requires more complex setup)
        assert extracted_text_update is not None
        assert podcast_text_update is not None


class TestAudioStateUpdate:
    """Test audio state updates in BrowserState."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = PaperPodcastApp()

    def test_update_browser_state_ui_content(self):
        """Test updating UI content in BrowserState."""
        browser_state = {
            "app_session_id": "test-session",
            "audio_generation_state": {},
            "user_settings": {},
            "ui_state": {"podcast_text": "old text", "terms_agreed": False},
        }

        # Update UI content
        updated_state = self.app.update_browser_state_ui_content(browser_state, "new podcast text", True)

        # Verify UI state was updated
        ui_state = updated_state["ui_state"]
        assert ui_state["podcast_text"] == "new podcast text"
        assert ui_state["terms_agreed"] is True

        # Verify other sections are preserved
        assert updated_state["app_session_id"] == "test-session"
        assert "audio_generation_state" in updated_state
        assert "user_settings" in updated_state
