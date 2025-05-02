"""Prompt management module.

This module provides functionality to manage prompt templates.
It includes the PromptManager class which handles prompt templates and generation.
"""

import os
from typing import Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template, exceptions

from app.utils.logger import logger


class PromptManager:
    """プロンプトテンプレートを管理するクラス。

    このクラスは、ポッドキャスト生成用のシステムプロンプトとユーザープロンプトを管理します。
    Jinja2テンプレートエンジンを使用して、テンプレートの管理と変数の置換を行います。
    """

    def __init__(self, custom_templates_dir=None) -> None:
        """Initialize the PromptManager class.

        Args:
            custom_templates_dir: Optional custom templates directory path
        """
        # テンプレートディレクトリとEnvironmentの設定
        # プロジェクトルートからの相対パスでテンプレートディレクトリを指定
        current_dir = os.getcwd()  # 現在の作業ディレクトリ（プロジェクトルート）

        if custom_templates_dir:
            self.templates_dir = custom_templates_dir
        else:
            self.templates_dir = os.path.join(
                current_dir, "app", "templates", "prompts"
            )

        logger.info(f"Loading templates from: {self.templates_dir}")

        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 現在使用中のテンプレート名
        self.current_template_name = "default.j2"

        # カスタムテンプレート文字列（直接指定された場合はこちらを優先）
        self.custom_template_str: Optional[str] = None

        # キャラクターマッピング
        self.character_mapping = {"Character1": "ずんだもん", "Character2": "四国めたん"}

        # 有効なキャラクターのリスト
        self.valid_characters = ["ずんだもん", "四国めたん", "九州そら"]

        # 利用可能なテンプレートのリスト
        self.available_templates = self._get_available_templates()

    def _get_available_templates(self) -> List[str]:
        """利用可能なテンプレートファイルのリストを取得します。

        Returns:
            List[str]: テンプレートファイル名のリスト
        """
        try:
            # 古いテンプレートフォルダの確認（ルートディレクトリのtemplates/prompts）
            current_dir = os.getcwd()
            old_templates_dir = os.path.join(current_dir, "templates", "prompts")
            if os.path.exists(old_templates_dir):
                logger.warning(
                    f"古いテンプレートディレクトリが存在しています: {old_templates_dir}\n"
                    "これは使用されません。app/templates/prompts を使用してください。"
                )

            return [f for f in os.listdir(self.templates_dir) if f.endswith(".j2")]
        except Exception as e:
            logger.error(f"Error listing template files: {e}")
            return ["default.j2"]

    def get_available_template_names(self) -> List[str]:
        """利用可能なテンプレート名のリストを取得します。

        Returns:
            List[str]: テンプレート名のリスト
        """
        return self.available_templates

    def set_template_by_name(self, template_name: str) -> bool:
        """テンプレート名を指定してテンプレートを設定します。

        Args:
            template_name (str): テンプレートファイル名

        Returns:
            bool: 設定が成功したかどうか
        """
        if not template_name or template_name not in self.available_templates:
            logger.error(f"Template '{template_name}' not found")
            return False

        self.current_template_name = template_name
        self.custom_template_str = None  # カスタムテンプレート文字列をクリア
        return True

    def set_prompt_template(self, prompt_template: str) -> bool:
        """カスタムプロンプトテンプレートを設定します。

        Args:
            prompt_template (str): カスタムプロンプトテンプレート

        Returns:
            bool: テンプレートが正常に設定されたかどうか
        """
        if not prompt_template or prompt_template.strip() == "":
            self.custom_template_str = None
            return False

        try:
            # Jinja2テンプレートとして解析できるか確認
            env = Environment()
            env.parse(prompt_template.strip())

            # 問題なければテンプレートをセット
            self.custom_template_str = prompt_template.strip()
            return True
        except exceptions.TemplateSyntaxError as e:
            logger.error(f"Jinja2 syntax error in template: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting prompt template: {e}")
            return False

    def get_current_prompt_template(self) -> str:
        """現在のプロンプトテンプレートを取得します。

        Returns:
            str: 現在のプロンプトテンプレート（カスタムが設定されている場合はカスタム、そうでなければファイルから）
        """
        if self.custom_template_str:
            return self.custom_template_str

        try:
            # テンプレートローダーからテンプレートソースを取得
            if self.env.loader is None:
                logger.error("Template loader is not initialized")
                return ""

            template_source: str = self.env.loader.get_source(
                self.env, self.current_template_name
            )[0]
            return template_source
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            # エラーが発生した場合は空の文字列を返す
            return ""

    def set_character_mapping(self, character1: str, character2: str) -> bool:
        """
        キャラクターマッピングを設定します。

        Args:
            character1 (str): Character1に割り当てるキャラクターの名前
            character2 (str): Character2に割り当てるキャラクターの名前

        Returns:
            bool: 設定が成功したかどうか
        """
        if (
            character1 not in self.valid_characters
            or character2 not in self.valid_characters
        ):
            return False

        self.character_mapping["Character1"] = character1
        self.character_mapping["Character2"] = character2
        return True

    def get_character_mapping(self) -> Dict[str, str]:
        """
        現在のキャラクターマッピングを取得します。

        Returns:
            dict: 現在のキャラクターマッピング
        """
        return self.character_mapping

    def get_valid_characters(self) -> List[str]:
        """
        有効なキャラクターのリストを取得します。

        Returns:
            list: 有効なキャラクター名のリスト
        """
        return self.valid_characters

    def convert_abstract_to_real_characters(self, text: str) -> str:
        """
        抽象的なキャラクター名（Character1, Character2）を実際のキャラクター名に変換します。

        Args:
            text (str): 変換するテキスト

        Returns:
            str: 変換後のテキスト
        """
        result = text
        for abstract, real in self.character_mapping.items():
            result = result.replace(f"{abstract}:", f"{real}:")
            result = result.replace(f"{abstract}：", f"{real}：")  # 全角コロンも対応
        return result

    def generate_podcast_conversation(self, paper_text: str) -> str:
        """
        論文テキストからポッドキャスト形式の会話テキストを生成します。

        Args:
            paper_text (str): 論文テキスト（全文または一部）

        Returns:
            str: 会話形式のポッドキャストテキスト
        """
        if not paper_text.strip():
            return "Error: No paper text provided."

        try:
            # カスタムテンプレート文字列があればそれを使用、なければファイルからロード
            prompt: str
            if self.custom_template_str:
                template = Template(self.custom_template_str)
                prompt = template.render(paper_text=paper_text)
            else:
                template = self.env.get_template(self.current_template_name)
                prompt = template.render(paper_text=paper_text)

            return prompt
        except exceptions.TemplateSyntaxError as e:
            logger.error(f"Jinja2 syntax error when rendering template: {e}")
            error_message = f"Error generating podcast conversation (syntax error): {e}"
            return error_message
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            error_message = f"Error generating podcast conversation: {e}"
            return error_message
