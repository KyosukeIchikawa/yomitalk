import logging
import pytest
from yomitalk.user_session import UserSession
from yomitalk.common import APIType


class TestSecurity:
    """Security regression tests to ensure API keys are handled correctly."""

    @pytest.fixture
    def user_session(self):
        """Create a user session for testing."""
        return UserSession("test_security_session")

    def test_api_keys_not_in_logs(self, user_session, caplog):
        """Test that API keys are not written to logs."""
        # Set log level to DEBUG to capture all logs
        caplog.set_level(logging.DEBUG)

        fake_openai_key = "sk-test-openai-key-12345"
        fake_gemini_key = "AIza-test-gemini-key-67890"

        # Set API keys
        user_session.text_processor.set_openai_api_key(fake_openai_key)
        user_session.text_processor.set_gemini_api_key(fake_gemini_key)

        # Perform some actions that might trigger logging
        user_session.text_processor.set_api_type(APIType.OPENAI)
        user_session.text_processor.set_api_type(APIType.GEMINI)

        # Check logs
        log_text = caplog.text

        assert fake_openai_key not in log_text, "OpenAI API key found in logs!"
        assert fake_gemini_key not in log_text, "Gemini API key found in logs!"

    def test_api_keys_not_in_serialization(self, user_session):
        """Test that API keys are not saved in UserSession serialization."""
        fake_openai_key = "sk-test-openai-key-serialization"
        fake_gemini_key = "AIza-test-gemini-key-serialization"

        # Set API keys
        user_session.text_processor.set_openai_api_key(fake_openai_key)
        user_session.text_processor.set_gemini_api_key(fake_gemini_key)

        # Serialize session
        session_dict = user_session.to_dict()

        # Convert dict to string to check for key presence anywhere
        session_str = str(session_dict)

        assert fake_openai_key not in session_str, "OpenAI API key found in serialized session!"
        assert fake_gemini_key not in session_str, "Gemini API key found in serialized session!"

        # Also check specific fields if they exist (double check)
        text_processor_state = session_dict.get("text_processor_state", {})
        assert text_processor_state.get("openai_api_key_set") is True
        assert text_processor_state.get("gemini_api_key_set") is True
        # Ensure the keys themselves are not keys in the dict
        assert "openai_api_key" not in text_processor_state
        assert "gemini_api_key" not in text_processor_state

    def test_api_keys_not_in_browser_state(self, user_session):
        """Test that API keys are not synced to BrowserState."""
        fake_openai_key = "sk-test-openai-key-browser"
        fake_gemini_key = "AIza-test-gemini-key-browser"

        # Set API keys
        user_session.text_processor.set_openai_api_key(fake_openai_key)
        user_session.text_processor.set_gemini_api_key(fake_gemini_key)

        # Create a dummy browser state
        browser_state: dict = {"user_settings": {}}

        # Sync settings to browser state
        updated_state = user_session.sync_settings_to_browser_state(browser_state)

        # Convert to string to check for key presence anywhere
        state_str = str(updated_state)

        assert fake_openai_key not in state_str, "OpenAI API key found in browser state!"
        assert fake_gemini_key not in state_str, "Gemini API key found in browser state!"
