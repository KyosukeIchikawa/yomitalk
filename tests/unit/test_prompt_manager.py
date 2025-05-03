"""Test for prompt management.

This module tests the prompt management functionality using Jinja2.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import jinja2

from app.prompt_manager import PromptManager


class TestPromptManager(unittest.TestCase):
    """Test cases for PromptManager."""

    def setUp(self):
        """Set up test cases."""
        # テスト用のテンプレートディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir) / "templates"
        self.template_dir.mkdir(exist_ok=True)

        # オリジナルのテンプレートディレクトリをバックアップ
        self.original_template_dir = Path("app/templates")

        # デフォルトのプロンプトテンプレートをテスト用ディレクトリにコピー
        if (self.original_template_dir / "paper_to_podcast.j2").exists():
            shutil.copy(
                self.original_template_dir / "paper_to_podcast.j2",
                self.template_dir / "paper_to_podcast.j2",
            )
        else:
            # デフォルトのテンプレートが存在しない場合は作成
            with open(
                self.template_dir / "paper_to_podcast.j2", "w", encoding="utf-8"
            ) as f:
                f.write(
                    "Test template for {{ character1 }} and {{ character2 }}: {{ paper_text }}"
                )

        # テスト用のPromptManagerインスタンスを作成
        self.prompt_manager = PromptManager()

        # template_dirを一時的に変更
        self._original_template_dir = self.prompt_manager.template_dir
        self.prompt_manager.template_dir = self.template_dir

        # Jinja2環境を再初期化
        self.prompt_manager.jinja_env = self.prompt_manager.jinja_env.overlay(
            loader=jinja2.FileSystemLoader(self.template_dir)
        )

    def tearDown(self):
        """Clean up after tests."""
        # 元のパスに戻す
        self.prompt_manager.template_dir = self._original_template_dir
        # テンポラリディレクトリを削除
        shutil.rmtree(self.temp_dir)

    def test_default_prompt_template(self):
        """Test getting default prompt template."""
        template = self.prompt_manager.get_current_prompt_template()
        self.assertIsNotNone(template)
        # テンプレートにJinja2の変数構文が含まれているか確認
        self.assertIn("{{ paper_text }}", template)

    def test_set_custom_prompt_template(self):
        """Test setting custom prompt template."""
        custom_template = (
            "カスタムテンプレート {{ paper_text }} for {{ character1 }} and {{ character2 }}"
        )
        result = self.prompt_manager.set_prompt_template(custom_template)

        self.assertTrue(result)
        self.assertEqual(
            custom_template, self.prompt_manager.get_current_prompt_template()
        )
        self.assertTrue(self.prompt_manager.use_custom_template)
        self.assertEqual(custom_template, self.prompt_manager.custom_template)

    def test_set_empty_prompt_template(self):
        """Test setting an empty prompt template."""
        # まずカスタムテンプレートを設定
        custom_template = "カスタムテンプレート {{ paper_text }}"
        self.prompt_manager.set_prompt_template(custom_template)
        self.assertTrue(self.prompt_manager.use_custom_template)

        # 空のテンプレートを設定
        result = self.prompt_manager.set_prompt_template("")
        self.assertTrue(result)
        self.assertFalse(self.prompt_manager.use_custom_template)
        self.assertIsNone(self.prompt_manager.custom_template)

    def test_generate_podcast_conversation(self):
        """Test generating podcast conversation from paper text."""
        paper_text = "これはテスト用の論文テキストです。"
        prompt = self.prompt_manager.generate_podcast_conversation(paper_text)

        self.assertIn(paper_text, prompt)
        # キャラクター名が変数に置き換えられているか確認
        self.assertIn("四国めたん", prompt)
        self.assertIn("ずんだもん", prompt)

        # カスタムテンプレートを設定した場合
        custom_template = (
            "Custom: {{ character1 }} and {{ character2 }} discussing {{ paper_text }}"
        )
        self.prompt_manager.set_prompt_template(custom_template)

        custom_prompt = self.prompt_manager.generate_podcast_conversation(paper_text)
        self.assertIn("Custom:", custom_prompt)
        self.assertIn("四国めたん", custom_prompt)
        self.assertIn(paper_text, custom_prompt)

    def test_set_and_get_character_mapping(self):
        """Test setting and getting character mapping."""
        # デフォルトのマッピングを確認
        default_mapping = self.prompt_manager.get_character_mapping()
        self.assertEqual("四国めたん", default_mapping["Character1"])
        self.assertEqual("ずんだもん", default_mapping["Character2"])

        # マッピングを変更
        result = self.prompt_manager.set_character_mapping("ずんだもん", "九州そら")
        self.assertTrue(result)

        # 変更後のマッピングを確認
        updated_mapping = self.prompt_manager.get_character_mapping()
        self.assertEqual("ずんだもん", updated_mapping["Character1"])
        self.assertEqual("九州そら", updated_mapping["Character2"])

    def test_set_invalid_character_mapping(self):
        """Test setting invalid character mapping."""
        # 無効なキャラクター名での設定
        result = self.prompt_manager.set_character_mapping("存在しないキャラクター", "九州そら")
        self.assertFalse(result)

        # マッピングが変更されていないことを確認
        mapping = self.prompt_manager.get_character_mapping()
        self.assertEqual("四国めたん", mapping["Character1"])

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

        self.assertEqual("四国めたん: こんにちは\nずんだもん: はじめまして", converted)

        # 全角コロンの変換もテスト
        text_with_fullwidth = "Character1： こんにちは\nCharacter2： はじめまして"
        converted_fullwidth = self.prompt_manager.convert_abstract_to_real_characters(
            text_with_fullwidth
        )

        self.assertEqual("四国めたん： こんにちは\nずんだもん： はじめまして", converted_fullwidth)


if __name__ == "__main__":
    unittest.main()
