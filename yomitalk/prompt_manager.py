"""Prompt manager module for podcast generator.

This module provides templates and utilities for generating podcast conversations.
"""

import os
import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import Dict, List

import jinja2

from yomitalk.common.character import DISPLAY_NAMES, Character
from yomitalk.utils.logger import logger


class DocumentType(Enum):
    """ドキュメントタイプのEnum"""

    PAPER = ("paper", "論文")
    MANUAL = ("manual", "マニュアル")
    MINUTES = ("minutes", "議事録")
    BLOG = ("blog", "ブログ記事")
    GENERAL = ("general", "一般ドキュメント")

    def __init__(self, value, label_name):
        self._value_ = value
        self.label_name: str = label_name

    @classmethod
    def from_label_name(cls, label_name: str):
        """ラベル名からEnumを取得"""
        for doc_type in cls:
            if doc_type.label_name == label_name:
                return doc_type
        raise ValueError(
            f"ラベル名 '{label_name}' に該当するドキュメントタイプが見つかりません。"
        )

    @classmethod
    def get_all_label_names(cls) -> List[str]:
        """全てのラベル名を取得"""
        return [doc_type.label_name for doc_type in cls]


class PodcastMode(Enum):
    """ポッドキャスト生成モードのEnum"""

    STANDARD = ("standard", "概要解説")
    SECTION_BY_SECTION = ("section_by_section", "詳細解説")

    def __init__(self, value, label_name):
        self._value_ = value
        self.label_name: str = label_name

    @classmethod
    def from_label_name(cls, label_name: str):
        """ラベル名からEnumを取得"""
        for mode in cls:
            if mode.label_name == label_name:
                return mode
        raise ValueError(
            f"ラベル名 '{label_name}' に該当するポッドキャストモードが見つかりません。"
        )

    @classmethod
    def get_all_label_names(cls) -> List[str]:
        """全てのラベル名を取得"""
        return [mode.label_name for mode in cls]


class PromptManager:
    """Manages templates and prompt generation for podcast conversations."""

    TEMPLATE_DIR = Path("yomitalk/templates")
    TEMPLATE_MAPPING = {
        PodcastMode.STANDARD: "paper_to_podcast.j2",
        PodcastMode.SECTION_BY_SECTION: "section_by_section.j2",
    }
    DEFAULT_DOCUMENT_TYPE = DocumentType.PAPER
    DEFAULT_MODE = PodcastMode.STANDARD
    DEFAULT_CHARACTER1 = Character.SHIKOKU_METAN
    DEFAULT_CHARACTER2 = Character.ZUNDAMON

    def __init__(self):
        """Initialize the PromptManager."""
        self.current_document_type = self.DEFAULT_DOCUMENT_TYPE
        self.current_mode = self.DEFAULT_MODE

        # デフォルトのキャラクターマッピング
        self.char_mapping = {
            "Character1": self.DEFAULT_CHARACTER1.display_name,
            "Character2": self.DEFAULT_CHARACTER2.display_name,
        }

    @classmethod
    def check_template_files(cls):
        """Check if template files exist."""
        # 各モードのテンプレートファイルの存在を確認
        for mode, template_file in cls.TEMPLATE_MAPPING.items():
            template_path = cls.TEMPLATE_DIR / template_file
            if not template_path.exists():
                logger.warning(
                    f"テンプレートファイルが見つかりません: {template_path} (モード: {mode.value})"
                )
        else:
            logger.info(
                f"テンプレートファイル確認: {template_path} (モード: {mode.value})"
            )

        # 共通ユーティリティテンプレートの存在を確認
        utils_template = cls.TEMPLATE_DIR / "common_podcast_utils.j2"
        if not utils_template.exists():
            logger.warning(
                f"共通ユーティリティテンプレートファイルが見つかりません: {utils_template}"
            )
        else:
            logger.info(f"共通ユーティリティテンプレートファイル確認: {utils_template}")

    def set_character_mapping(self, char1: str, char2: str):
        """Set character mapping.

        Args:
            char1 (str): Character1 name.
            char2 (str): Character2 name.

        Returns:
            bool: True if successful, False otherwise.
        """
        if char1 not in DISPLAY_NAMES or char2 not in DISPLAY_NAMES:
            logger.warning(
                f"無効なキャラクター名: char1={char1}, char2={char2}、有効なキャラクター: {DISPLAY_NAMES}"
            )
            return False

        self.char_mapping = {"Character1": char1, "Character2": char2}
        return True

    def generate_podcast_conversation(self, paper_text: str) -> str:
        """Generate podcast conversation from paper text.

        Args:
            paper_text (str): The paper text to process.

        Returns:
            str: Generated conversation in podcast format.
        """
        try:
            template_content = self.get_template_content()
            return self._render_template(
                template_content, paper_text=paper_text, char_mapping=self.char_mapping
            )
        except Exception as e:
            logger.error(f"会話生成エラー: {e}")
            return f"エラー: 会話の生成に失敗しました: {e}"

    def get_template_content(self) -> str:
        """Get template content based on the current mode.

        Returns:
            str: Template content as string.
        """
        # 現在のモードに基づいてテンプレートファイルを選択
        template_file = self.TEMPLATE_MAPPING.get(self.current_mode)

        if not template_file:
            logger.warning(
                f"モード '{self.current_mode.value}' に対応するテンプレートが見つかりません。デフォルトを使用します。"
            )
            template_file = self.TEMPLATE_MAPPING[PodcastMode.STANDARD]

        logger.info(f"テンプレートファイルパス: {self.TEMPLATE_DIR / template_file}")
        logger.info(
            f"使用するドキュメントタイプ: {self.current_document_type.name}, "
            f"モード: {self.current_mode.name}, "
            f"テンプレート: {template_file}"
        )

        try:
            with open(self.TEMPLATE_DIR / template_file, "r", encoding="utf-8") as f:
                template_content = f.read()
                logger.info(f"テンプレート長: {len(template_content)} 文字")
                return template_content
        except FileNotFoundError:
            logger.error(f"テンプレートファイルが見つかりません: {template_file}")
            # 最低限の情報を含むフォールバックテンプレート
            return (
                "Character1: こんにちは、今日は{{document_type}}の解説をします。\n"
                "Character2: よろしくお願いします。\n"
                "Character1: では始めましょう。"
            )

    def _render_template(
        self, template_content: str, paper_text: str, char_mapping: Dict[str, str]
    ) -> str:
        """Render template with jinja2.

        Args:
            template_content (str): Template content.
            paper_text (str): Paper text.
            char_mapping (Dict[str, str]): Character mapping.

        Returns:
            str: Rendered template.

        Raises:
            jinja2.exceptions.TemplateError: On template rendering error.
        """
        # 一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp()
        try:
            # 一時ディレクトリに templates サブディレクトリを作成
            temp_templates_dir = os.path.join(temp_dir, "templates")
            os.makedirs(temp_templates_dir, exist_ok=True)

            # プロジェクトのテンプレートディレクトリから共通テンプレートをコピー
            common_utils_src = self.TEMPLATE_DIR / "common_podcast_utils.j2"
            if common_utils_src.exists():
                common_utils_dest = os.path.join(
                    temp_templates_dir, "common_podcast_utils.j2"
                )
                shutil.copy(common_utils_src, common_utils_dest)

            # テンプレートコンテンツをファイルとして保存
            with open(
                os.path.join(temp_templates_dir, "template.j2"), "w", encoding="utf-8"
            ) as f:
                f.write(template_content)

            # Jinja2環境をセットアップ
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(temp_templates_dir))

            # テンプレートをロード
            template = env.get_template("template.j2")

            # レンダリングパラメータを準備
            render_params = {
                "paper_text": paper_text,
                "character1": char_mapping["Character1"],
                "character2": char_mapping["Character2"],
                "document_type": self.get_document_type_name(),
            }

            # テンプレートをレンダリング
            rendered_text: str = template.render(**render_params)
            return rendered_text
        finally:
            # 一時ディレクトリを削除
            shutil.rmtree(temp_dir)

    def convert_abstract_to_real_characters(self, text: str) -> str:
        """Convert abstract character names to real character names.

        Args:
            text (str): Text with abstract character names.

        Returns:
            str: Text with real character names.
        """
        result = text

        # 半角コロンの置換
        result = result.replace("Character1:", f"{self.char_mapping['Character1']}:")
        result = result.replace("Character2:", f"{self.char_mapping['Character2']}:")

        # 全角コロンの置換
        result = result.replace("Character1：", f"{self.char_mapping['Character1']}：")
        result = result.replace("Character2：", f"{self.char_mapping['Character2']}：")

        return result

    def set_document_type(self, document_type: DocumentType) -> bool:
        """Set document type.

        Args:
            document_type (DocumentType): Document type to set.

        Returns:
            bool: True if successful, False otherwise.

        Raises:
            TypeError: If document_type is not a DocumentType instance.
        """
        self.current_document_type = document_type
        return True

    def get_document_type_name(self) -> str:
        """現在のドキュメントタイプの日本語名を取得します。

        Returns:
            str: ドキュメントタイプの日本語名
        """
        return self.current_document_type.label_name

    def set_podcast_mode(self, mode: PodcastMode) -> bool:
        """Set podcast mode.

        Args:
            mode (PodcastMode): Podcast mode to set.

        Returns:
            bool: True if successful, False otherwise.

        Raises:
            TypeError: If mode is not a PodcastMode instance.
        """
        if not isinstance(mode, PodcastMode):
            raise TypeError(
                f"mode must be an instance of PodcastMode, not {type(mode)}"
            )

        self.current_mode = mode
        return True

    def get_podcast_mode(self) -> PodcastMode:
        """Get current podcast mode.

        Returns:
            PodcastMode: Current podcast mode.
        """
        return self.current_mode

    def get_character_mapping(self) -> Dict[str, str]:
        """Get character mapping.

        Returns:
            Dict[str, str]: Current character mapping.
        """
        return self.char_mapping


# Check if template files exist
PromptManager.check_template_files()
