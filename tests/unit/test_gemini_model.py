"""Test for Google Gemini text generation.

This module tests the Google Gemini text generation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from yomitalk.models.gemini_model import GeminiModel


class TestGeminiModel(unittest.TestCase):
    """Test cases for GeminiModel."""

    def setUp(self):
        """Set up test cases."""
        # モデルを作成
        self.model = GeminiModel()

    def test_initialization(self):
        """Test model initialization."""
        self.assertIsNotNone(self.model)
        self.assertEqual(self.model.model_name, "gemini-2.5-flash-preview-04-17")
        self.assertEqual(self.model.max_tokens, 8192)
        self.assertDictEqual(self.model.last_token_usage, {})

    def test_set_api_key(self):
        """Test setting the API key."""
        # APIの初期化をモック
        with patch.object(self.model, "_initialize_api") as mock_init:
            # 有効なAPIキーを設定
            result = self.model.set_api_key("AIzaTest123456789")
            self.assertTrue(result)
            self.assertEqual("AIzaTest123456789", self.model.api_key)
            mock_init.assert_called_once()

            # 空のAPIキーを設定
            result = self.model.set_api_key("")
            self.assertFalse(result)

    def test_get_available_models(self):
        """Test getting available models."""
        models = self.model.get_available_models()
        self.assertIsInstance(models, list)
        self.assertIn("gemini-2.0-flash", models)
        self.assertIn("gemini-2.5-flash-preview-04-17", models)
        self.assertIn("gemini-2.5-pro-preview-05-06", models)

    def test_set_model_name(self):
        """Test setting a model name."""
        # 有効なモデル名を設定
        result = self.model.set_model_name("gemini-2.5-pro-preview-05-06")
        self.assertTrue(result)
        self.assertEqual("gemini-2.5-pro-preview-05-06", self.model.model_name)

        # 無効なモデル名を設定
        result = self.model.set_model_name("invalid-model")
        self.assertFalse(result)
        self.assertEqual(
            "gemini-2.5-pro-preview-05-06", self.model.model_name
        )  # 変更されない

        # 空のモデル名を設定
        result = self.model.set_model_name("")
        self.assertFalse(result)
        self.assertEqual(
            "gemini-2.5-pro-preview-05-06", self.model.model_name
        )  # 変更されない

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

    @patch("google.generativeai.GenerativeModel")
    def test_generate_text(self, mock_generative_model_class):
        """Test generating text with Gemini API."""
        # モックの設定
        mock_model = MagicMock()
        mock_generative_model_class.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = "Generated text response"
        mock_model.generate_content.return_value = mock_response

        # APIキー設定
        with patch.object(self.model, "_initialize_api"):
            self.model.set_api_key("AIzaTest123456789")

        # テキスト生成
        response = self.model.generate_text("Test prompt")

        # 検証
        self.assertEqual("Generated text response", response)
        mock_model.generate_content.assert_called_once()

        # トークン使用状況の検証（Geminiでは概算値）
        self.assertIn("prompt_tokens", self.model.last_token_usage)
        self.assertIn("completion_tokens", self.model.last_token_usage)
        self.assertIn("total_tokens", self.model.last_token_usage)

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
