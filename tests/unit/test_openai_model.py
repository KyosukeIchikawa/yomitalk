"""Test for OpenAI text generation.

This module tests the OpenAI text generation functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from app.models.openai_model import OpenAIModel


class TestOpenAIModel(unittest.TestCase):
    """Test cases for OpenAIModel."""

    @patch("app.prompt_manager.PromptManager")
    def setUp(self, mock_prompt_manager_class):
        """Set up test cases."""
        # Mock PromptManager instance
        self.mock_prompt_manager = MagicMock()
        mock_prompt_manager_class.return_value = self.mock_prompt_manager

        # Mock prompt manager methods
        self.mock_set_prompt_template = MagicMock(return_value=True)
        self.mock_get_prompt_template = MagicMock(return_value="テストテンプレート")
        self.mock_generate_podcast = MagicMock(return_value="テストプロンプト")
        self.mock_convert_chars = MagicMock(return_value="ずんだもん: こんにちは\n四国めたん: はじめまして")

        # Assign mocks to the prompt manager methods
        self.mock_prompt_manager.set_prompt_template = self.mock_set_prompt_template
        self.mock_prompt_manager.get_current_prompt_template = (
            self.mock_get_prompt_template
        )
        self.mock_prompt_manager.generate_podcast_conversation = (
            self.mock_generate_podcast
        )
        self.mock_prompt_manager.convert_abstract_to_real_characters = (
            self.mock_convert_chars
        )
        self.mock_prompt_manager.character_mapping = {
            "Character1": "ずんだもん",
            "Character2": "四国めたん",
        }

        # Create the model
        self.model = OpenAIModel()
        # Replace the prompt manager with our mock
        self.model.prompt_manager = self.mock_prompt_manager

    def test_initialization(self):
        """Test model initialization."""
        self.assertIsNotNone(self.model)
        self.assertIsNotNone(self.model.prompt_manager)

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

    @patch("app.models.openai_model.OpenAI")
    def test_generate_text(self, mock_openai):
        """Test generating text with OpenAI API."""
        # モックの設定
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text response"
        mock_client.chat.completions.create.return_value = mock_response

        # APIキー設定
        self.model.set_api_key("sk-test123456789")

        # テキスト生成
        response = self.model.generate_text("Test prompt")

        # 検証
        self.assertEqual("Generated text response", response)
        mock_client.chat.completions.create.assert_called_once()

    def test_set_prompt_template(self):
        """Test setting a custom prompt template."""
        # カスタムプロンプトを設定
        custom_prompt = "これはカスタムプロンプトです。\n${paper_summary}"
        result = self.model.set_prompt_template(custom_prompt)

        # 検証
        self.assertTrue(result)
        self.mock_set_prompt_template.assert_called_with(custom_prompt)

    def test_get_current_prompt_template(self):
        """Test getting the current prompt template."""
        # 現在のプロンプトテンプレートを取得
        template = self.model.get_current_prompt_template()

        # 検証
        self.assertEqual("テストテンプレート", template)
        self.mock_get_prompt_template.assert_called_once()

    @patch("app.models.openai_model.OpenAI")
    def test_generate_podcast_conversation(self, mock_openai):
        """Test generating podcast conversation with custom prompt."""
        # モックの設定
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = "Character1: こんにちは\nCharacter2: はじめまして"
        mock_client.chat.completions.create.return_value = mock_response

        # APIキー設定
        self.model.set_api_key("sk-test123456789")

        # ポッドキャスト会話生成
        result = self.model.generate_podcast_conversation("テスト論文")

        # 検証
        self.assertEqual("ずんだもん: こんにちは\n四国めたん: はじめまして", result)
        self.mock_generate_podcast.assert_called_with("テスト論文")
        mock_client.chat.completions.create.assert_called_once()


if __name__ == "__main__":
    unittest.main()
