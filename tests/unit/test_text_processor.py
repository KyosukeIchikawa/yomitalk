"""Unit tests for TextProcessor class."""

import unittest
from unittest.mock import patch

from app.components.text_processor import TextProcessor


class TestTextProcessor(unittest.TestCase):
    """Test case for TextProcessor class."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.text_processor = TextProcessor()

    def test_init(self):
        """Test initialization of TextProcessor."""
        self.assertIsNotNone(self.text_processor)
        self.assertFalse(self.text_processor.use_openai)
        self.assertIsNotNone(self.text_processor.openai_model)

    def test_preprocess_text(self):
        """Test text preprocessing functionality."""
        # Test with page markers and empty lines
        input_text = "--- Page 1 ---\nLine 1\n\nLine 2\n--- Page 2 ---\nLine 3"
        expected = "Line 1 Line 2 Line 3"
        result = self.text_processor._preprocess_text(input_text)
        self.assertEqual(result, expected)

        # Test with empty input
        self.assertEqual(self.text_processor._preprocess_text(""), "")

    @patch("app.models.openai_model.OpenAIModel.set_api_key")
    def test_set_openai_api_key(self, mock_set_api_key):
        """Test setting the OpenAI API key."""
        # Test with valid API key
        mock_set_api_key.return_value = True
        result = self.text_processor.set_openai_api_key("valid-api-key")
        self.assertTrue(result)
        self.assertTrue(self.text_processor.use_openai)
        mock_set_api_key.assert_called_with("valid-api-key")

        # Test with invalid API key
        mock_set_api_key.return_value = False
        result = self.text_processor.set_openai_api_key("invalid-api-key")
        self.assertFalse(result)
        mock_set_api_key.assert_called_with("invalid-api-key")

    @patch("app.models.openai_model.OpenAIModel.generate_podcast_conversation")
    def test_process_text_with_openai(self, mock_generate):
        """Test text processing with OpenAI API."""
        mock_generate.return_value = "ずんだもん: こんにちは"
        self.text_processor.use_openai = True

        result = self.text_processor.process_text("Test text")
        self.assertEqual(result, "ずんだもん: こんにちは")
        mock_generate.assert_called_once()

    def test_process_text_no_openai(self):
        """Test text processing without OpenAI API configured."""
        self.text_processor.use_openai = False
        result = self.text_processor.process_text("Test text")
        self.assertIn("OpenAI API key is not set", result)

    def test_process_text_empty(self):
        """Test text processing with empty input."""
        result = self.text_processor.process_text("")
        self.assertEqual(result, "No text has been input for processing.")

    @patch("app.models.openai_model.OpenAIModel.set_prompt_template")
    def test_set_prompt_template(self, mock_set_prompt):
        """Test setting custom prompt template."""
        # テンプレート設定が成功する場合
        mock_set_prompt.return_value = True
        result = self.text_processor.set_prompt_template("カスタムテンプレート")
        self.assertTrue(result)
        mock_set_prompt.assert_called_with("カスタムテンプレート")

        # テンプレート設定が失敗する場合
        mock_set_prompt.return_value = False
        result = self.text_processor.set_prompt_template("")
        self.assertFalse(result)
        mock_set_prompt.assert_called_with("")

    @patch("app.models.openai_model.OpenAIModel.get_current_prompt_template")
    def test_get_prompt_template(self, mock_get_prompt):
        """Test getting current prompt template."""
        mock_get_prompt.return_value = "テストテンプレート"
        result = self.text_processor.get_prompt_template()
        self.assertEqual(result, "テストテンプレート")
        mock_get_prompt.assert_called_once()

    @patch("app.models.openai_model.OpenAIModel.set_prompt_template")
    @patch("app.models.openai_model.OpenAIModel.generate_podcast_conversation")
    def test_process_text_with_custom_prompt(self, mock_generate, mock_set_prompt):
        """Test processing text with custom prompt template."""
        # カスタムプロンプトを設定
        mock_set_prompt.return_value = True
        self.text_processor.set_prompt_template("カスタムテンプレート{paper_summary}")

        # OpenAI利用フラグを有効に
        self.text_processor.use_openai = True

        # 会話生成結果をモック
        mock_generate.return_value = "ずんだもん: カスタムプロンプトでの会話"

        # テキスト処理を実行
        result = self.text_processor.process_text("テスト論文")

        # 結果を検証
        self.assertEqual(result, "ずんだもん: カスタムプロンプトでの会話")
        mock_generate.assert_called_once_with("テスト論文")
