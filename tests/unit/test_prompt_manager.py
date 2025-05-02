"""
PromptManagerのユニットテスト
"""

import pytest

from app.prompt_manager import PromptManager


class TestPromptManager:
    """PromptManagerクラスのテスト"""

    def test_init(self):
        """初期化のテスト"""
        pm = PromptManager()
        assert pm is not None
        assert pm.templates_dir is not None
        assert pm.env is not None
        assert pm.current_template_name == "default.j2"
        assert pm.custom_template_str is None

    def test_get_available_templates(self):
        """利用可能なテンプレート一覧を取得するテスト"""
        pm = PromptManager()
        templates = pm.get_available_template_names()
        assert isinstance(templates, list)
        assert "default.j2" in templates
        assert "technical.j2" in templates
        assert "simple.j2" in templates

    def test_generate_podcast_conversation(self):
        """ポッドキャスト会話を生成するテスト"""
        pm = PromptManager()
        pm.set_template_by_name("default.j2")
        text = pm.generate_podcast_conversation("これはテスト用のペーパーテキストです。")
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Character1" in text or "Character2" in text

    def test_custom_template(self):
        """カスタムテンプレートを設定するテスト"""
        pm = PromptManager()
        template = "カスタムテンプレート: {{ paper_text }}"
        success = pm.set_prompt_template(template)
        assert success is True
        result = pm.generate_podcast_conversation("テストテキスト")
        assert "カスタムテンプレート: テストテキスト" == result

    def test_set_character_mapping(self):
        """キャラクターマッピングを設定するテスト"""
        pm = PromptManager()
        assert pm.set_character_mapping("ずんだもん", "四国めたん") is True
        assert pm.get_character_mapping()["Character1"] == "ずんだもん"
        assert pm.get_character_mapping()["Character2"] == "四国めたん"

        # 無効なキャラクター名の場合はFalseを返す
        assert pm.set_character_mapping("無効な名前", "四国めたん") is False

    def test_default_prompt_template(self):
        """Test getting default prompt template."""
        pm = PromptManager()
        template = pm.get_current_prompt_template()
        assert template is not None
        assert "{{ paper_text }}" in template

    def test_set_custom_prompt_template(self):
        """Test setting custom prompt template."""
        pm = PromptManager()
        custom_template = "カスタムテンプレート {{ paper_text }}"
        result = pm.set_prompt_template(custom_template)

        assert result is True
        assert custom_template == pm.get_current_prompt_template()

    def test_set_empty_prompt_template(self):
        """Test setting an empty prompt template."""
        pm = PromptManager()
        result = pm.set_prompt_template("")

        assert result is False
        assert pm.custom_template_str is None

    def test_set_and_get_character_mapping(self):
        """Test setting and getting character mapping."""
        pm = PromptManager()
        # デフォルトのマッピングを確認
        default_mapping = pm.get_character_mapping()
        assert "ずんだもん" == default_mapping["Character1"]
        assert "四国めたん" == default_mapping["Character2"]

        # マッピングを変更
        result = pm.set_character_mapping("四国めたん", "九州そら")
        assert result is True

        # 変更後のマッピングを確認
        updated_mapping = pm.get_character_mapping()
        assert "四国めたん" == updated_mapping["Character1"]
        assert "九州そら" == updated_mapping["Character2"]

    def test_get_valid_characters(self):
        """Test getting list of valid characters."""
        pm = PromptManager()
        characters = pm.get_valid_characters()
        assert "ずんだもん" in characters
        assert "四国めたん" in characters
        assert "九州そら" in characters

    def test_character_name_conversion(self):
        """Test converting abstract character names to real character names."""
        pm = PromptManager()
        text = "Character1: こんにちは\nCharacter2: はじめまして"
        converted = pm.convert_abstract_to_real_characters(text)

        assert "ずんだもん: こんにちは\n四国めたん: はじめまして" == converted

        # 全角コロンの変換もテスト
        text_with_fullwidth = "Character1： こんにちは\nCharacter2： はじめまして"
        converted_fullwidth = pm.convert_abstract_to_real_characters(
            text_with_fullwidth
        )

        assert "ずんだもん： こんにちは\n四国めたん： はじめまして" == converted_fullwidth


if __name__ == "__main__":
    pytest.main()
