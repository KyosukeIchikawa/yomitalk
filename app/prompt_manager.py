"""Prompt management module.

This module provides functionality to manage prompt templates.
It includes the PromptManager class which handles Jinja2 templates and generation.
"""

from pathlib import Path
from typing import Dict, List, Optional

import jinja2

from app.utils.logger import logger


class PromptManager:
    """プロンプトテンプレートを管理するクラス。

    このクラスは、ポッドキャスト生成用のプロンプトテンプレートを管理します。
    Jinja2ライブラリを使用して、テンプレートの管理と変数の置換を行います。
    """

    def __init__(self) -> None:
        """Initialize the PromptManager class."""
        # テンプレートディレクトリのパス
        self.template_dir = Path("app/templates")

        # Jinja2環境の設定
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # デフォルトテンプレートのパス
        self.default_template_path = "paper_to_podcast.j2"

        # カスタムテンプレートをメモリに保持
        self.custom_template: Optional[str] = None

        # 現在使用中のテンプレート
        self.use_custom_template = False

        # キャラクターマッピング
        self.character_mapping = {"Character1": "四国めたん", "Character2": "ずんだもん"}

        # 有効なキャラクターのリスト
        self.valid_characters = ["ずんだもん", "四国めたん", "九州そら"]

    def set_prompt_template(self, prompt_template: str) -> bool:
        """カスタムプロンプトテンプレートを設定します。

        Args:
            prompt_template (str): カスタムプロンプトテンプレート

        Returns:
            bool: テンプレートが正常に設定されたかどうか
        """
        if not prompt_template or prompt_template.strip() == "":
            # カスタムテンプレートをクリア
            self.custom_template = None
            self.use_custom_template = False
            return True

        try:
            # テンプレート文字列の検証
            template_str = prompt_template.strip()
            try:
                # Jinja2テンプレートとして構文チェック
                jinja2.Template(template_str)
                # 問題なければメモリに保存
                self.custom_template = template_str
                self.use_custom_template = True
                return True
            except Exception as e:
                logger.error(f"Custom template syntax error: {e}")
                # エラーの場合はクリア
                self.custom_template = None
                self.use_custom_template = False
                return False

        except Exception as e:
            logger.error(f"Error setting prompt template: {e}")
            return False

    def get_current_prompt_template(self) -> str:
        """現在のプロンプトテンプレートを取得します。

        Returns:
            str: 現在のプロンプトテンプレート（カスタムが設定されている場合はカスタム、そうでなければデフォルト）
        """
        if self.use_custom_template and self.custom_template:
            return self.custom_template

        try:
            with open(
                self.template_dir / self.default_template_path, "r", encoding="utf-8"
            ) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading template file: {e}")
            # デフォルトテンプレートが読めない場合は緊急措置として空の文字列を返す
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
            character1 = self.character_mapping["Character1"]
            character2 = self.character_mapping["Character2"]

            if self.use_custom_template and self.custom_template:
                # カスタムテンプレートがある場合はメモリから使用
                template = jinja2.Template(self.custom_template)
            else:
                # デフォルトテンプレートをファイルから使用
                template = self.jinja_env.get_template(self.default_template_path)

            prompt: str = template.render(
                paper_text=paper_text, character1=character1, character2=character2
            )
            return prompt
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            error_message: str = f"Error generating podcast conversation: {e}"
            return error_message
