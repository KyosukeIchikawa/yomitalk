"""
テスト用テンプレートを使用したPromptManagerのテスト
"""

import os

from jinja2 import Environment, FileSystemLoader

from app.prompt_manager import PromptManager


class TestPromptManagerWithTestTemplates:
    """テスト用テンプレートを使ったPromptManagerのテスト"""

    def test_load_test_templates(self, test_templates_dir):
        """テスト用テンプレートをロードするテスト"""
        # テスト用のEnvironmentを作成
        templates_dir = os.path.join(test_templates_dir, "prompts")
        env = Environment(
            loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
        )

        # テンプレートが存在することを確認
        template_names = ["test_default.j2", "test_simple.j2", "test_technical.j2"]
        for name in template_names:
            template = env.get_template(name)
            assert template is not None
            source = template.render(paper_text="テスト用ペーパー")
            assert isinstance(source, str)
            assert len(source) > 0

    def test_custom_environment_with_test_templates(self, test_templates_dir):
        """カスタム環境でテスト用テンプレートを使用するテスト"""
        templates_dir = os.path.join(test_templates_dir, "prompts")
        # カスタムディレクトリを指定してPromptManagerを初期化
        pm = PromptManager(custom_templates_dir=templates_dir)

        # 利用可能なテンプレートを確認
        templates = pm.get_available_template_names()
        assert "test_default.j2" in templates
        assert "test_simple.j2" in templates
        assert "test_technical.j2" in templates

        # テンプレートを設定して使用
        assert pm.set_template_by_name("test_default.j2")
        result = pm.generate_podcast_conversation("テストテキスト")
        assert "これはテスト用のデフォルトプロンプトです。" in result
