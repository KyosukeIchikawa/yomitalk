"""Test for prompt management.

This module tests the prompt management functionality using Jinja2.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import jinja2

from app.prompt_manager import PodcastMode, PromptManager


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

        # 共通ユーティリティテンプレートを作成
        with open(
            self.template_dir / "common_podcast_utils.j2", "w", encoding="utf-8"
        ) as f:
            f.write(
                """
{% macro get_character_speech_pattern(character_name) %}
{% set speech_patterns = {
    "ずんだもん": {
        "first_person": "ぼく",
        "sentence_end": ["のだ", "なのだ"]
    },
    "四国めたん": {
        "first_person": "わたし",
        "sentence_end": ["です", "ます"]
    },
    "九州そら": {
        "first_person": "わたし",
        "sentence_end": ["ですね", "ですよ"]
    }
} %}
{% if speech_patterns[character_name] %}
  - 一人称: {{ speech_patterns[character_name].first_person }}
  - 語尾の特徴: {{ speech_patterns[character_name].sentence_end|join('、') }}
{% endif %}
{% endmacro %}

{% macro podcast_common_macro(character1, character2) %}
Character speech patterns:
- {{ character1 }}:
{% if character1 %}
{{ get_character_speech_pattern(character1) }}
{% endif %}
- {{ character2 }}:
{% if character2 %}
{{ get_character_speech_pattern(character2) }}
{% endif %}
{% endmacro %}
            """
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
        template = self.prompt_manager.get_template_content()
        self.assertIsNotNone(template)
        # テンプレートにJinja2の変数構文が含まれているか確認
        self.assertIn("{{ paper_text }}", template)

    def test_generate_podcast_conversation(self):
        """Test generating podcast conversation from paper text."""
        paper_text = "これはテスト用の論文テキストです。"
        prompt = self.prompt_manager.generate_podcast_conversation(paper_text)

        self.assertIn(paper_text, prompt)
        # キャラクター名が変数に置き換えられているか確認
        self.assertIn("四国めたん", prompt)
        self.assertIn("ずんだもん", prompt)

        # モードを変更して再テスト
        self.prompt_manager.set_podcast_mode(PodcastMode.SECTION_BY_SECTION)
        # section_by_sectionモードのテンプレートが存在する場合はそれを使用
        if (
            self.template_dir / self.prompt_manager.section_by_section_template_path
        ).exists():
            updated_prompt = self.prompt_manager.generate_podcast_conversation(
                paper_text
            )
            self.assertIn(paper_text, updated_prompt)

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

    def test_character_speech_patterns(self):
        """Test character speech patterns are available through the common utils file."""
        # 共通ユーティリティのパスが設定されていることを確認
        self.assertIsNotNone(self.prompt_manager.common_utils_path)
        self.assertEqual(
            "common_podcast_utils.j2", self.prompt_manager.common_utils_path
        )

        # ファイルの存在を確認
        common_utils_path = self.template_dir / "common_podcast_utils.j2"
        self.assertTrue(common_utils_path.exists(), "共通ユーティリティファイルが存在しません")

    def test_speech_patterns_in_prompt(self):
        """Test if speech patterns are included in the generated prompt."""
        # テスト用のペーパートゥポッドキャストテンプレートを更新
        with open(
            self.template_dir / "paper_to_podcast.j2", "w", encoding="utf-8"
        ) as f:
            f.write(
                """
{% import 'common_podcast_utils.j2' as utils %}
Paper text: {{ paper_text }}
{{ utils.podcast_common_macro(character1, character2) }}
            """
            )

        paper_text = "これはテスト用の論文テキストです。"

        # デフォルトキャラクター設定での生成
        prompt = self.prompt_manager.generate_podcast_conversation(paper_text)

        # 各キャラクターの口調情報が含まれていることを確認
        self.assertIn("一人称: わたし", prompt)  # 四国めたん
        self.assertIn("一人称: ぼく", prompt)  # ずんだもん
        self.assertIn("語尾の特徴", prompt)

        # キャラクター設定を変更して再テスト
        self.prompt_manager.set_character_mapping("ずんだもん", "九州そら")
        updated_prompt = self.prompt_manager.generate_podcast_conversation(paper_text)

        # 更新後の口調情報が含まれていることを確認
        self.assertIn("一人称: ぼく", updated_prompt)  # ずんだもん
        self.assertIn("一人称: わたし", updated_prompt)  # 九州そら

    def test_set_and_get_podcast_mode(self):
        """Test setting and getting podcast mode using Enum."""
        # デフォルトモードの確認
        self.assertEqual(PodcastMode.STANDARD, self.prompt_manager.get_podcast_mode())

        # モードをSECTION_BY_SECTIONに変更
        result = self.prompt_manager.set_podcast_mode(PodcastMode.SECTION_BY_SECTION)
        self.assertTrue(result)
        self.assertEqual(
            PodcastMode.SECTION_BY_SECTION, self.prompt_manager.get_podcast_mode()
        )

        # モードをSTANDARDに戻す
        result = self.prompt_manager.set_podcast_mode(PodcastMode.STANDARD)
        self.assertTrue(result)
        self.assertEqual(PodcastMode.STANDARD, self.prompt_manager.get_podcast_mode())

        # 無効な値を渡した場合
        with self.assertRaises(TypeError):
            # Enumでない値を渡すとTypeErrorが発生するはず
            self.prompt_manager.set_podcast_mode("invalid_value")  # type: ignore


if __name__ == "__main__":
    unittest.main()
