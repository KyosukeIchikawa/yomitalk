"""Prompt management module.

This module provides functionality to manage prompt templates.
It includes the PromptManager class which handles Jinja2 templates and generation.
"""

from pathlib import Path
from typing import Dict, List

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
        # 論文の詳細解説用テンプレートのパス
        self.section_by_section_template_path = "section_by_section.j2"
        # 共通ユーティリティのパス
        self.common_utils_path = "common_podcast_utils.j2"

        # 現在のモード（標準またはセクション解説）
        self.current_mode = "standard"

        # キャラクターマッピング
        self.character_mapping = {"Character1": "四国めたん", "Character2": "ずんだもん"}

        # 有効なキャラクターのリスト
        self.valid_characters = ["ずんだもん", "四国めたん", "九州そら", "中国うさぎ", "中部つるぎ"]

        # 初期化時にテンプレートファイルの存在を確認
        self._check_template_files()

    def _check_template_files(self) -> None:
        """
        テンプレートファイルの存在を確認します。
        初期化時に呼び出され、警告ログを出力します。
        """
        # デフォルトテンプレートの確認
        default_path = self.template_dir / self.default_template_path
        if not default_path.exists():
            logger.warning(f"デフォルトテンプレートファイルが見つかりません: {default_path}")
        else:
            logger.info(f"デフォルトテンプレートファイル確認: {default_path}")

        # 論文の詳細解説用テンプレートの確認
        section_path = self.template_dir / self.section_by_section_template_path
        if not section_path.exists():
            logger.warning(f"論文の詳細解説用テンプレートファイルが見つかりません: {section_path}")
        else:
            logger.info(f"論文の詳細解説用テンプレートファイル確認: {section_path}")

        # 共通ユーティリティテンプレートの確認
        common_path = self.template_dir / self.common_utils_path
        if not common_path.exists():
            logger.warning(f"共通ユーティリティテンプレートファイルが見つかりません: {common_path}")
        else:
            logger.info(f"共通ユーティリティテンプレートファイル確認: {common_path}")

    def set_podcast_mode(self, mode: str) -> bool:
        """ポッドキャスト生成モードを設定します。

        Args:
            mode (str): 'standard' または 'section_by_section'

        Returns:
            bool: モードが正常に設定されたかどうか
        """
        if mode not in ["standard", "section_by_section"]:
            return False

        self.current_mode = mode
        return True

    def get_podcast_mode(self) -> str:
        """現在のポッドキャスト生成モードを取得します。

        Returns:
            str: 現在のモード ('standard' または 'section_by_section')
        """
        return self.current_mode

    def get_template_content(self) -> str:
        """現在のプロンプトテンプレートを取得します。

        Returns:
            str: 現在のプロンプトテンプレート（モードに応じたデフォルト）
        """
        try:
            # モードに応じたテンプレートファイルを選択
            template_path = (
                self.section_by_section_template_path
                if self.current_mode == "section_by_section"
                else self.default_template_path
            )

            # ファイルの存在を確認
            full_path = self.template_dir / template_path
            logger.info(f"テンプレートファイルパス: {full_path}")

            if not full_path.exists():
                logger.error(f"テンプレートファイルが見つかりません: {full_path}")
                # 論文の詳細解説でファイルが見つからない場合は論文の概要解説のテンプレートを使用
                if (
                    self.current_mode == "section_by_section"
                    and (self.template_dir / self.default_template_path).exists()
                ):
                    logger.warning("代わりに論文の概要解説のテンプレートを使用します")
                    full_path = self.template_dir / self.default_template_path
                else:
                    return "エラー: テンプレートファイルが見つかりません。"

            # ファイルを読み込み
            with open(full_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # 内容を確認
            if not template_content or template_content.strip() == "":
                logger.error(f"テンプレートファイルが空です: {full_path}")
                return "エラー: テンプレートファイルが空です。"

            return template_content

        except Exception as e:
            logger.error(f"テンプレートファイル読み込みエラー: {e}")
            # デフォルトテンプレートが読めない場合は緊急措置としてエラーメッセージを返す
            return f"エラー: テンプレートファイルの読み込みに失敗しました: {e}"

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

            try:
                # モードに応じたテンプレートを使用
                template_path = (
                    self.section_by_section_template_path
                    if self.current_mode == "section_by_section"
                    else self.default_template_path
                )
                logger.info(
                    f"モード '{self.current_mode}' のテンプレート '{template_path}' を使用します"
                )

                # ファイルの存在を確認
                if not (self.template_dir / template_path).exists():
                    logger.error(f"テンプレートファイルが見つかりません: {template_path}")
                    if (
                        self.current_mode == "section_by_section"
                        and (self.template_dir / self.default_template_path).exists()
                    ):
                        # 論文の詳細解説でファイルが見つからない場合は論文の概要解説のテンプレートを使用
                        logger.warning("代わりに論文の概要解説のテンプレートを使用します")
                        template_path = self.default_template_path
                    else:
                        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")

                # テンプレートを取得
                template = self.jinja_env.get_template(template_path)
            except Exception as template_error:
                logger.error(f"テンプレート取得エラー: {template_error}")
                return f"Error: テンプレートの取得に失敗しました: {template_error}"

            # テンプレートをレンダリング
            try:
                prompt: str = template.render(
                    paper_text=paper_text,
                    character1=character1,
                    character2=character2,
                )
                return prompt
            except Exception as render_error:
                logger.error(f"テンプレートレンダリングエラー: {render_error}")
                return f"Error: テンプレートのレンダリングに失敗しました: {render_error}"

        except Exception as e:
            logger.error(f"ポッドキャスト会話生成エラー: {e}")
            error_message: str = f"Error generating podcast conversation: {e}"
            return error_message
