"""Test for GeminiModel class."""

from unittest.mock import MagicMock, patch

from yomitalk.models.gemini_model import GeminiModel


class TestGeminiModel:
    """Tests for the GeminiModel class."""

    def test_initialization(self):
        """Test that model initializes with default values."""
        model = GeminiModel()
        assert model.model_name == GeminiModel.DEFAULT_MODEL
        assert model.max_tokens == GeminiModel.DEFAULT_MAX_TOKENS
        assert model.last_token_usage == {}

    def test_set_api_key(self):
        """Test setting the API key."""
        model = GeminiModel()
        # Valid key
        assert model.set_api_key("valid_key") is True
        assert model.api_key == "valid_key"
        assert model.has_api_key() is True
        # Empty key
        assert model.set_api_key("") is False
        assert model.api_key == "valid_key"  # Should not change
        # Whitespace key
        assert model.set_api_key("   ") is False
        assert model.api_key == "valid_key"  # Should not change

    def test_set_max_tokens(self):
        """Test setting the max tokens."""
        model = GeminiModel()
        # Valid value
        assert model.set_max_tokens(1000) is True
        assert model.max_tokens == 1000
        # Too small
        assert model.set_max_tokens(50) is False
        assert model.max_tokens == 1000  # Should not change
        # Too large
        assert model.set_max_tokens(70000) is False
        assert model.max_tokens == 1000  # Should not change
        # Invalid type
        assert model.set_max_tokens(int("0")) is False  # 0は無効な値なのでFalseが返るはず
        assert model.max_tokens == 1000  # Should not change

    def test_set_model_name(self):
        """Test setting the model name."""
        model = GeminiModel()
        # Valid model name
        assert model.set_model_name("gemini-2.5-flash") is True
        assert model.model_name == "gemini-2.5-flash"
        # Non-existent model
        assert model.set_model_name("nonexistent-model") is False
        assert model.model_name == "gemini-2.5-flash"  # Should not change
        # Empty model name
        assert model.set_model_name("") is False
        assert model.model_name == "gemini-2.5-flash"  # Should not change

    @patch("google.genai.Client")
    def test_generate_text_success(self, mock_client):
        """Test successful text generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "Generated text"
        mock_response.candidates = [MagicMock()]
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 20
        mock_response.usage_metadata.total_token_count = 30

        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Test
        model = GeminiModel()
        model.api_key = "test_api_key"
        result = model.generate_text("Test prompt")

        # Assertions
        assert result == "Generated text"
        assert model.last_token_usage == {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }
        mock_client.assert_called_once_with(api_key="test_api_key")

    @patch("google.genai.Client")
    def test_generate_text_no_api_key(self, mock_client):
        """Test text generation with no API key."""
        model = GeminiModel()
        model.api_key = None
        result = model.generate_text("Test prompt")
        assert result == "API key error: Google Gemini API key is not set."
        mock_client.assert_not_called()

    @patch("google.genai.Client")
    def test_generate_text_no_candidates(self, mock_client):
        """Test text generation with no candidates in response."""
        # Mock response with no candidates
        mock_response = MagicMock()
        mock_response.candidates = []

        # Set up mock client
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Test
        model = GeminiModel()
        model.api_key = "test_api_key"
        result = model.generate_text("Test prompt")

        # Assertions
        assert result == "Error: No text was generated"

    @patch("google.genai.Client")
    def test_generate_text_blocked_prompt(self, mock_client):
        """Test handling of blocked prompt exception."""

        # Create an exception object with a class that has "BlockedPrompt" in its name
        class BlockedPromptException(Exception):
            pass

        # Set up mock client to raise exception
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.side_effect = BlockedPromptException()
        mock_client.return_value = mock_client_instance

        # Test
        model = GeminiModel()
        model.api_key = "test_api_key"
        result = model.generate_text("Test prompt")

        # Assertions
        assert result == "Error: Your request contains content that is flagged as inappropriate or against usage policies."

    @patch("google.genai.Client")
    def test_generate_text_stop_candidate(self, mock_client):
        """Test handling of stop candidate exception."""

        # Create an exception object with a class that has "StopCandidate" in its name
        class StopCandidateException(Exception):
            pass

        # Set up mock client to raise exception
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.side_effect = StopCandidateException()
        mock_client.return_value = mock_client_instance

        # Test
        model = GeminiModel()
        model.api_key = "test_api_key"
        result = model.generate_text("Test prompt")

        # Assertions
        assert result == "Error: The generation was stopped as the potential response may contain inappropriate content."

    @patch("google.genai.Client")
    def test_generate_text_generic_exception(self, mock_client):
        """Test handling of generic exception."""
        # Set up mock client to raise exception
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.side_effect = Exception("Generic error")
        mock_client.return_value = mock_client_instance

        # Test
        model = GeminiModel()
        model.api_key = "test_api_key"
        result = model.generate_text("Test prompt")

        # Assertions
        assert result == "Error generating text: Generic error"
