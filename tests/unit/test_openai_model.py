"""Unit tests for OpenAIModel class."""

import os
import unittest
from unittest.mock import MagicMock, patch

from app.models.openai_model import OpenAIModel


class TestOpenAIModel(unittest.TestCase):
    """Test case for OpenAIModel class."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.model = OpenAIModel()

    def test_init(self):
        """Test initialization of OpenAIModel."""
        self.assertIsNotNone(self.model)
        self.assertIsNone(self.model.api_key)
        self.assertIsNotNone(self.model.default_prompt_template)
        self.assertIsNone(self.model.custom_prompt_template)

    @patch("app.models.openai_model.OpenAI")
    def test_generate_text_success(self, mock_openai):
        """Test text processing with successful API response."""
        # Set up the mock
        mock_completion = MagicMock()
        mock_message = type(
            "obj",
            (object,),
            {
                "message": type(
                    "msg", (object,), {"content": "Generated text from OpenAI"}
                )()
            },
        )()
        mock_completion.choices = [mock_message]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        # Set API key
        self.model.api_key = "fake-key"

        # Call the method to test
        prompt = "Generate a podcast script"
        response = self.model.generate_text(prompt)

        # Check the results
        self.assertEqual(response, "Generated text from OpenAI")
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.models.openai_model.OpenAI")
    def test_generate_text_with_no_api_key(self, mock_openai):
        """Test behavior when API key is not set."""
        # Ensure API key is None
        self.model.api_key = None

        response = self.model.generate_text("Test prompt")
        self.assertEqual(response, "API key error: OpenAI API key is not set.")
        # The client should not be created if API key is missing
        mock_openai.assert_not_called()

    @patch("app.models.openai_model.OpenAI")
    def test_generate_text_exception(self, mock_openai):
        """Test error handling when API raises exception."""
        # Set up the mock to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_openai.return_value = mock_client

        # Set API key
        self.model.api_key = "fake-key"

        # Call the method and check error handling
        response = self.model.generate_text("Test prompt")
        self.assertTrue(response.startswith("Error generating text:"))
        self.assertIn("API error", response)

    def test_set_api_key_valid(self):
        """Test setting a valid API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = self.model.set_api_key("valid-api-key")
            self.assertTrue(result)
            self.assertEqual(self.model.api_key, "valid-api-key")
            self.assertEqual(os.environ.get("OPENAI_API_KEY"), "valid-api-key")

    def test_set_api_key_invalid(self):
        """Test setting an invalid API key."""
        original_key = self.model.api_key

        # Empty key
        result = self.model.set_api_key("")
        self.assertFalse(result)
        self.assertEqual(self.model.api_key, original_key)

        # Whitespace only key
        result = self.model.set_api_key("   ")
        self.assertFalse(result)
        self.assertEqual(self.model.api_key, original_key)

    def test_set_prompt_template(self):
        """Test setting a custom prompt template."""
        # デフォルトプロンプトを取得
        default_prompt = self.model.get_current_prompt_template()
        self.assertEqual(default_prompt, self.model.default_prompt_template)

        # カスタムプロンプトを設定
        custom_prompt = "これはカスタムプロンプトです。\n{paper_summary}"
        result = self.model.set_prompt_template(custom_prompt)
        self.assertTrue(result)
        self.assertEqual(self.model.custom_prompt_template, custom_prompt)

        # 現在のプロンプトがカスタムプロンプトになっていることを確認
        current_prompt = self.model.get_current_prompt_template()
        self.assertEqual(current_prompt, custom_prompt)

        # 空のプロンプトを設定するとカスタムプロンプトがクリアされ、デフォルトに戻ることを確認
        result = self.model.set_prompt_template("")
        self.assertFalse(result)
        self.assertIsNone(self.model.custom_prompt_template)
        self.assertEqual(
            self.model.get_current_prompt_template(), self.model.default_prompt_template
        )

    @patch("app.models.openai_model.OpenAI")
    def test_generate_podcast_conversation_with_custom_prompt(self, mock_openai):
        """Test generating podcast conversation with custom prompt."""
        # Set up the mock
        mock_completion = MagicMock()
        mock_message = type(
            "obj",
            (object,),
            {
                "message": type(
                    "msg", (object,), {"content": "ずんだもん: こんにちは\n四国めたん: こんにちは"}
                )()
            },
        )()
        mock_completion.choices = [mock_message]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        # Set API key
        self.model.api_key = "fake-key"

        # Set custom prompt
        custom_prompt = "カスタムプロンプト\n{paper_summary}"
        self.model.set_prompt_template(custom_prompt)

        # Call method
        result = self.model.generate_podcast_conversation("テスト論文")

        # Verify the result and that the custom prompt was used
        self.assertEqual(result, "ずんだもん: こんにちは\n四国めたん: こんにちは")
        mock_client.chat.completions.create.assert_called_once()
        # Verify the prompt sent to the API contains our custom template
        call_args = mock_client.chat.completions.create.call_args
        sent_prompt = call_args[1]["messages"][0]["content"]
        self.assertEqual(sent_prompt, "カスタムプロンプト\nテスト論文")

    @patch("app.models.openai_model.OpenAI")
    def test_generate_podcast_conversation_success(self, mock_openai):
        """Test generating podcast conversation with valid input."""
        # Set up the mock
        mock_completion = MagicMock()
        mock_message = type(
            "obj",
            (object,),
            {
                "message": type(
                    "msg", (object,), {"content": "ホスト: こんにちは\nゲスト: よろしくお願いします"}
                )()
            },
        )()
        mock_completion.choices = [mock_message]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_client

        # Set API key
        self.model.api_key = "fake-key"

        # Call the method to test
        paper_summary = "This is a summary of a research paper."
        response = self.model.generate_podcast_conversation(paper_summary)

        # Check the results
        self.assertEqual(response, "ホスト: こんにちは\nゲスト: よろしくお願いします")
        mock_client.chat.completions.create.assert_called_once()

    def test_generate_podcast_conversation_empty_summary(self):
        """Test generating podcast conversation with empty summary."""
        response = self.model.generate_podcast_conversation("")
        self.assertEqual(response, "Error: No paper summary provided.")

        response = self.model.generate_podcast_conversation("   ")
        self.assertEqual(response, "Error: No paper summary provided.")


if __name__ == "__main__":
    unittest.main()
