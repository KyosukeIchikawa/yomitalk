"""Test for prompt management.

This module tests the prompt management functionality using prompt-template.
"""

import unittest

from app.prompt_manager import PromptManager


class TestPromptManager(unittest.TestCase):
    """Test cases for PromptManager."""

    def setUp(self):
        """Set up test cases."""
        self.prompt_manager = PromptManager()

    def test_default_prompt_template(self):
        """Test getting default prompt template."""
        template = self.prompt_manager.get_current_prompt_template()
        self.assertIsNotNone(template)
        self.assertIn("${paper_text}", template)

    def test_set_custom_prompt_template(self):
        """Test setting custom prompt template."""
        custom_template = "カスタムテンプレート ${paper_text}"
        result = self.prompt_manager.set_prompt_template(custom_template)

        self.assertTrue(result)
        self.assertEqual(
            custom_template, self.prompt_manager.get_current_prompt_template()
        )

    def test_set_empty_prompt_template(self):
        """Test setting an empty prompt template."""
        result = self.prompt_manager.set_prompt_template("")

        self.assertFalse(result)
        self.assertIsNone(self.prompt_manager.custom_template)

    def test_generate_podcast_conversation(self):
        """Test generating podcast conversation from paper text."""
        paper_text = "これはテスト用の論文テキストです。"
        prompt = self.prompt_manager.generate_podcast_conversation(paper_text)

        self.assertIn(paper_text, prompt)

    def test_set_and_get_character_mapping(self):
        """Test setting and getting character mapping."""
        # デフォルトのマッピングを確認
        default_mapping = self.prompt_manager.get_character_mapping()
        self.assertEqual("ずんだもん", default_mapping["Character1"])
        self.assertEqual("四国めたん", default_mapping["Character2"])

        # マッピングを変更
        result = self.prompt_manager.set_character_mapping("四国めたん", "九州そら")
        self.assertTrue(result)

        # 変更後のマッピングを確認
        updated_mapping = self.prompt_manager.get_character_mapping()
        self.assertEqual("四国めたん", updated_mapping["Character1"])
        self.assertEqual("九州そら", updated_mapping["Character2"])

    def test_set_invalid_character_mapping(self):
        """Test setting invalid character mapping."""
        # 無効なキャラクター名での設定
        result = self.prompt_manager.set_character_mapping("存在しないキャラクター", "九州そら")
        self.assertFalse(result)

        # マッピングが変更されていないことを確認
        mapping = self.prompt_manager.get_character_mapping()
        self.assertEqual("ずんだもん", mapping["Character1"])

    def test_get_valid_characters(self):
        """Test getting list of valid characters."""
        characters = self.prompt_manager.get_valid_characters()
        self.assertIn("ずんだもん", characters)
        self.assertIn("四国めたん", characters)
        self.assertIn("九州そら", characters)

    def test_character_name_conversion(self):
        """Test converting abstract character names to real character names."""
        text = "Character1: こんにちは\nCharacter2: はじめまして"
        converted = self.prompt_manager.convert_abstract_to_real_characters(text)

        self.assertEqual("ずんだもん: こんにちは\n四国めたん: はじめまして", converted)

        # 全角コロンの変換もテスト
        text_with_fullwidth = "Character1： こんにちは\nCharacter2： はじめまして"
        converted_fullwidth = self.prompt_manager.convert_abstract_to_real_characters(
            text_with_fullwidth
        )

        self.assertEqual("ずんだもん： こんにちは\n四国めたん： はじめまして", converted_fullwidth)


if __name__ == "__main__":
    unittest.main()
