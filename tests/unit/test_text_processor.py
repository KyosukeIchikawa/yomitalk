"""Unit tests for TextProcessor class."""

import unittest
from unittest.mock import MagicMock, patch

from app.components.text_processor import TextProcessor


class TestTextProcessor(unittest.TestCase):
    """Test case for TextProcessor class."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # TextProcessorをパッチして作成
        with patch("app.prompt_manager.PromptManager") as mock_prompt_manager_class:
            # PromptManagerのモックを設定
            self.mock_prompt_manager = MagicMock()
            mock_prompt_manager_class.return_value = self.mock_prompt_manager

            # OpenAIModelのモックを設定
            with patch(
                "app.models.openai_model.OpenAIModel"
            ) as mock_openai_model_class:
                self.mock_openai_model = MagicMock()
                mock_openai_model_class.return_value = self.mock_openai_model

                # TextProcessorを作成
                self.text_processor = TextProcessor()

                # モックを直接適用
                self.text_processor.prompt_manager = self.mock_prompt_manager
                self.text_processor.openai_model = self.mock_openai_model

    def test_init(self):
        """Test initialization of TextProcessor."""
        self.assertIsNotNone(self.text_processor)
        self.assertFalse(self.text_processor.use_openai)
        self.assertIsNotNone(self.text_processor.openai_model)
        self.assertIsNotNone(self.text_processor.prompt_manager)

    def test_preprocess_text(self):
        """Test text preprocessing functionality."""
        # Test with page markers and empty lines
        input_text = "## Page 1\nLine 1\n\nLine 2\n## Page 2\nLine 3"
        expected = "Line 1 Line 2 Line 3"
        result = self.text_processor._preprocess_text(input_text)
        self.assertEqual(result, expected)

        # Test with empty input
        self.assertEqual(self.text_processor._preprocess_text(""), "")

    def test_set_openai_api_key(self):
        """Test setting the OpenAI API key."""
        # Test with valid API key
        self.mock_openai_model.set_api_key.return_value = True
        result = self.text_processor.set_openai_api_key("valid-api-key")
        self.assertTrue(result)
        self.assertTrue(self.text_processor.use_openai)
        self.mock_openai_model.set_api_key.assert_called_with("valid-api-key")

        # Test with invalid API key
        self.mock_openai_model.set_api_key.return_value = False
        result = self.text_processor.set_openai_api_key("invalid-api-key")
        self.assertFalse(result)
        self.mock_openai_model.set_api_key.assert_called_with("invalid-api-key")

    def test_get_template_content(self):
        """Test getting prompt template content."""
        self.mock_prompt_manager.get_template_content.return_value = "テストテンプレート"
        result = self.text_processor.get_template_content()
        self.assertEqual(result, "テストテンプレート")
        self.mock_prompt_manager.get_template_content.assert_called_once()

    def test_set_podcast_mode(self):
        """Test setting podcast mode."""
        self.mock_prompt_manager.set_podcast_mode.return_value = True
        result = self.text_processor.set_podcast_mode("section_by_section")
        self.assertTrue(result)
        self.mock_prompt_manager.set_podcast_mode.assert_called_with(
            "section_by_section"
        )

    def test_get_podcast_mode(self):
        """Test getting podcast mode."""
        self.mock_prompt_manager.get_podcast_mode.return_value = "standard"
        result = self.text_processor.get_podcast_mode()
        self.assertEqual(result, "standard")
        self.mock_prompt_manager.get_podcast_mode.assert_called_once()

    def test_generate_podcast_conversation(self):
        """Test generating podcast conversation."""
        # モックの設定
        self.mock_prompt_manager.generate_podcast_conversation.return_value = "テストプロンプト"
        self.mock_openai_model.generate_text.return_value = (
            "Character1: こんにちは\nCharacter2: はじめまして"
        )
        self.mock_prompt_manager.convert_abstract_to_real_characters.return_value = (
            "ずんだもん: こんにちは\n四国めたん: はじめまして"
        )

        # メソッド実行
        result = self.text_processor.generate_podcast_conversation("テスト論文")

        # 検証
        self.assertEqual("ずんだもん: こんにちは\n四国めたん: はじめまして", result)
        self.mock_prompt_manager.generate_podcast_conversation.assert_called_with(
            "テスト論文"
        )
        self.mock_openai_model.generate_text.assert_called_with("テストプロンプト")
        self.mock_prompt_manager.convert_abstract_to_real_characters.assert_called_with(
            "Character1: こんにちは\nCharacter2: はじめまして"
        )

    def test_convert_abstract_to_real_characters(self):
        """Test converting abstract characters to real characters."""
        self.mock_prompt_manager.convert_abstract_to_real_characters.return_value = (
            "ずんだもん: こんにちは"
        )
        result = self.text_processor.convert_abstract_to_real_characters(
            "Character1: こんにちは"
        )
        self.assertEqual(result, "ずんだもん: こんにちは")
        self.mock_prompt_manager.convert_abstract_to_real_characters.assert_called_with(
            "Character1: こんにちは"
        )

    def test_process_text_with_openai(self):
        """Test text processing with OpenAI API."""
        # モックの設定
        self.text_processor.use_openai = True
        with patch.object(
            self.text_processor,
            "generate_podcast_conversation",
            return_value="ずんだもん: こんにちは",
        ) as mock_gen:
            result = self.text_processor.process_text("Test text")
            self.assertEqual(result, "ずんだもん: こんにちは")
            mock_gen.assert_called_once_with("Test text")

    def test_process_text_no_openai(self):
        """Test text processing without OpenAI API configured."""
        self.text_processor.use_openai = False
        result = self.text_processor.process_text("Test text")
        self.assertIn("OpenAI API key is not set", result)

    def test_process_text_empty(self):
        """Test text processing with empty input."""
        result = self.text_processor.process_text("")
        self.assertEqual(result, "No text has been input for processing.")

    def test_get_token_usage(self):
        """Test getting token usage information."""
        self.mock_openai_model.get_last_token_usage.return_value = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

        usage = self.text_processor.get_token_usage()
        self.assertEqual(100, usage.get("prompt_tokens"))
        self.assertEqual(50, usage.get("completion_tokens"))
        self.assertEqual(150, usage.get("total_tokens"))
        self.mock_openai_model.get_last_token_usage.assert_called_once()

    def test_set_character_mapping(self):
        """Test setting character mapping."""
        self.mock_prompt_manager.set_character_mapping.return_value = True
        result = self.text_processor.set_character_mapping("ずんだもん", "四国めたん")
        self.assertTrue(result)
        self.mock_prompt_manager.set_character_mapping.assert_called_with(
            "ずんだもん", "四国めたん"
        )

    def test_get_character_mapping(self):
        """Test getting character mapping."""
        self.mock_prompt_manager.get_character_mapping.return_value = {
            "Character1": "ずんだもん",
            "Character2": "四国めたん",
        }
        mapping = self.text_processor.get_character_mapping()
        self.assertEqual("ずんだもん", mapping["Character1"])
        self.assertEqual("四国めたん", mapping["Character2"])
        self.mock_prompt_manager.get_character_mapping.assert_called_once()

    def test_get_valid_characters(self):
        """Test getting valid characters list."""
        self.mock_prompt_manager.get_valid_characters.return_value = [
            "ずんだもん",
            "四国めたん",
            "九州そら",
            "中国うさぎ",
            "中部つるぎ",
        ]
        characters = self.text_processor.get_valid_characters()
        self.assertIn("ずんだもん", characters)
        self.assertIn("四国めたん", characters)
        self.assertEqual(5, len(characters))
        self.mock_prompt_manager.get_valid_characters.assert_called_once()
