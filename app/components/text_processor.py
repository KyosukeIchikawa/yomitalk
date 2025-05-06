"""Module providing text processing functionality.

Functions to process, summarize, and convert research paper text to podcast format.
"""

from typing import Dict, List

from app.models.openai_model import OpenAIModel
from app.prompt_manager import PromptManager

# Removed transformers import (not used)
# from transformers import Pipeline, pipeline


class TextProcessor:
    """Class that processes research paper text and converts it to podcast text."""

    def __init__(self) -> None:
        """Initialize TextProcessor."""
        # PromptManagerのインスタンスを作成
        self.prompt_manager = PromptManager()
        # OpenAIModelを初期化
        self.openai_model = OpenAIModel()
        self.use_openai = False

    def set_openai_api_key(self, api_key: str) -> bool:
        """
        Set the OpenAI API key and returns the result.

        Args:
            api_key (str): OpenAI API key

        Returns:
            bool: Whether the configuration was successful
        """
        success = self.openai_model.set_api_key(api_key)
        if success:
            self.use_openai = True
        return success

    def get_template_content(self) -> str:
        """
        Get the current prompt template.

        Returns:
            str: Current prompt template
        """
        return self.prompt_manager.get_template_content()

    def set_podcast_mode(self, mode: str) -> bool:
        """
        ポッドキャスト生成モードを設定します。

        Args:
            mode (str): 'standard' または 'section_by_section'

        Returns:
            bool: モードが正常に設定されたかどうか
        """
        return self.prompt_manager.set_podcast_mode(mode)

    def get_podcast_mode(self) -> str:
        """
        現在のポッドキャスト生成モードを取得します。

        Returns:
            str: 現在のモード ('standard' または 'section_by_section')
        """
        return self.prompt_manager.get_podcast_mode()

    def set_character_mapping(self, character1: str, character2: str) -> bool:
        """
        キャラクターマッピングを設定します。

        Args:
            character1 (str): Character1に割り当てるキャラクターの名前
            character2 (str): Character2に割り当てるキャラクターの名前

        Returns:
            bool: 設定が成功したかどうか
        """
        return self.prompt_manager.set_character_mapping(character1, character2)

    def get_character_mapping(self) -> dict:
        """
        現在のキャラクターマッピングを取得します。

        Returns:
            dict: 現在のキャラクターマッピング
        """
        return self.prompt_manager.get_character_mapping()

    def get_valid_characters(self) -> list:
        """
        有効なキャラクターのリストを取得します。

        Returns:
            list: 有効なキャラクター名のリスト
        """
        return self.prompt_manager.get_valid_characters()

    def generate_podcast_conversation(self, paper_text: str) -> str:
        """
        論文テキストからポッドキャスト形式の会話テキストを生成します。

        Args:
            paper_text (str): 論文テキスト

        Returns:
            str: 会話形式のポッドキャストテキスト
        """
        if not paper_text.strip():
            return "Error: No paper text provided."

        # プロンプトマネージャーを使用してプロンプトを生成
        prompt = self.prompt_manager.generate_podcast_conversation(paper_text)

        # OpenAIモデルでテキスト生成
        result = self.openai_model.generate_text(prompt)

        # 抽象キャラクター名を実際のキャラクター名に変換
        if not result.startswith("Error"):
            result = self.convert_abstract_to_real_characters(result)

        return result

    def convert_abstract_to_real_characters(self, text: str) -> str:
        """
        抽象的なキャラクター名（Character1, Character2）を実際のキャラクター名に変換します。

        Args:
            text (str): 変換するテキスト

        Returns:
            str: 変換後のテキスト
        """
        return self.prompt_manager.convert_abstract_to_real_characters(text)

    def process_text(self, text: str) -> str:
        """
        Process research paper text and convert it to podcast text.

        Args:
            text (str): Research paper text to process

        Returns:
            str: Podcast text
        """
        if not text or text.strip() == "":
            return "No text has been input for processing."

        try:
            # Text preprocessing
            cleaned_text = self._preprocess_text(text)

            # Convert to conversation format if OpenAI model is available
            if self.use_openai:
                podcast_text = self.generate_podcast_conversation(cleaned_text)
            else:
                # If OpenAI is not set up
                podcast_text = "OpenAI API key is not set. Please enter your API key."

            return podcast_text

        except Exception as e:
            return f"An error occurred during text processing: {e}"

    def _preprocess_text(self, text: str) -> str:
        """
        Perform text preprocessing.

        Args:
            text (str): Research paper text to preprocess

        Returns:
            str: Preprocessed text
        """
        # Organize page splits
        lines = text.split("\n")
        cleaned_lines: List[str] = []

        for line in lines:
            # Remove page numbers and empty lines
            if line.startswith("## Page") or line.strip() == "":
                continue

            cleaned_lines.append(line)

        # Join the text
        cleaned_text = " ".join(cleaned_lines)

        return cleaned_text

    def get_token_usage(self) -> Dict[str, int]:
        """
        最後のAPI呼び出しで使用されたトークン情報を取得します。

        Returns:
            dict: トークン使用状況を含む辞書
        """
        return self.openai_model.get_last_token_usage()
