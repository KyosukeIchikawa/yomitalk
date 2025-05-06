"""Test for OpenAI text generation.

This module tests the OpenAI text generation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from app.models.openai_model import OpenAIModel


class TestOpenAIModel(unittest.TestCase):
    """Test cases for OpenAIModel."""

    def setUp(self):
        """Set up test cases."""
        # Create the model
        self.model = OpenAIModel()

    def test_initialization(self):
        """Test model initialization."""
        self.assertIsNotNone(self.model)
        self.assertEqual(self.model.model_name, "gpt-4.1-mini")
        self.assertEqual(self.model.max_tokens, 32768)
        self.assertDictEqual(self.model.last_token_usage, {})

    def test_set_api_key(self):
        """Test setting the API key."""
        # 有効なAPIキーを設定
        result = self.model.set_api_key("sk-test123456789")
        self.assertTrue(result)
        self.assertEqual("sk-test123456789", self.model.api_key)

        # 空のAPIキーを設定
        result = self.model.set_api_key("")
        self.assertFalse(result)

    def test_get_available_models(self):
        """Test getting available models."""
        models = self.model.get_available_models()
        self.assertIsInstance(models, list)
        self.assertIn("gpt-4o", models)
        self.assertIn("gpt-4.1-mini", models)

    def test_set_model_name(self):
        """Test setting a model name."""
        # 有効なモデル名を設定
        result = self.model.set_model_name("gpt-4o")
        self.assertTrue(result)
        self.assertEqual("gpt-4o", self.model.model_name)

        # 無効なモデル名を設定
        result = self.model.set_model_name("invalid-model")
        self.assertFalse(result)
        self.assertEqual("gpt-4o", self.model.model_name)  # 変更されない

        # 空のモデル名を設定
        result = self.model.set_model_name("")
        self.assertFalse(result)
        self.assertEqual("gpt-4o", self.model.model_name)  # 変更されない

    def test_set_max_tokens(self):
        """Test setting max tokens."""
        # 有効なトークン数を設定
        result = self.model.set_max_tokens(1000)
        self.assertTrue(result)
        self.assertEqual(1000, self.model.max_tokens)

        # 範囲外のトークン数を設定
        result = self.model.set_max_tokens(50)
        self.assertFalse(result)
        self.assertEqual(1000, self.model.max_tokens)  # 変更されない

        result = self.model.set_max_tokens(40000)
        self.assertFalse(result)
        self.assertEqual(1000, self.model.max_tokens)  # 変更されない

    def test_get_max_tokens(self):
        """Test getting max tokens."""
        self.model.max_tokens = 2000
        self.assertEqual(2000, self.model.get_max_tokens())

    @patch("app.models.openai_model.OpenAI")
    def test_generate_text(self, mock_openai):
        """Test generating text with OpenAI API."""
        # モックの設定
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text response"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        # APIキー設定
        self.model.set_api_key("sk-test123456789")

        # テキスト生成
        response = self.model.generate_text("Test prompt")

        # 検証
        self.assertEqual("Generated text response", response)
        mock_client.chat.completions.create.assert_called_once()

        # トークン使用状況の検証
        self.assertEqual(100, self.model.last_token_usage.get("prompt_tokens"))
        self.assertEqual(50, self.model.last_token_usage.get("completion_tokens"))
        self.assertEqual(150, self.model.last_token_usage.get("total_tokens"))

    def test_get_last_token_usage(self):
        """Test getting token usage information."""
        # 初期状態
        self.assertEqual({}, self.model.get_last_token_usage())

        # 設定後
        self.model.last_token_usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }
        usage = self.model.get_last_token_usage()
        self.assertEqual(100, usage.get("prompt_tokens"))
        self.assertEqual(50, usage.get("completion_tokens"))
        self.assertEqual(150, usage.get("total_tokens"))


if __name__ == "__main__":
    unittest.main()
