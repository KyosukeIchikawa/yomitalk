"""Text processor module for podcast generation.

This module provides text preprocessing and API integrations.
"""

from typing import Dict, List

from app.models.gemini_model import GeminiModel
from app.models.openai_model import OpenAIModel
from app.prompt_manager import DocumentType, PodcastMode, PromptManager
from app.utils.logger import logger


class TextProcessor:
    """Class that processes research paper text and converts it to podcast text."""

    def __init__(self) -> None:
        """Initialize TextProcessor."""
        # PromptManagerのインスタンスを作成
        self.prompt_manager = PromptManager()

        # モデルの初期化
        self.openai_model = OpenAIModel()
        self.gemini_model = GeminiModel()

        # APIの使用状態
        self.use_openai = False
        self.use_gemini = False

        # 現在選択されているAPIタイプ（デフォルトはOpenAI）
        self.current_api_type = "openai"

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
            # APIキーが設定されたら、このAPIタイプを現在の選択に
            self.current_api_type = "openai"
        return success

    def set_gemini_api_key(self, api_key: str) -> bool:
        """
        Set the Google Gemini API key and returns the result.

        Args:
            api_key (str): Google API key

        Returns:
            bool: Whether the configuration was successful
        """
        success = self.gemini_model.set_api_key(api_key)
        if success:
            self.use_gemini = True
            # APIキーが設定されたら、このAPIタイプを現在の選択に
            self.current_api_type = "gemini"
        return success

    def set_api_type(self, api_type: str) -> bool:
        """
        使用するAPIタイプを設定します。

        Args:
            api_type (str): "openai" または "gemini"

        Returns:
            bool: 設定が成功したかどうか
        """
        if api_type not in ["openai", "gemini"]:
            return False

        # APIキーが設定されているか確認
        if api_type == "openai" and not self.use_openai:
            return False
        if api_type == "gemini" and not self.use_gemini:
            return False

        self.current_api_type = api_type
        return True

    def get_current_api_type(self) -> str:
        """
        現在選択されているAPIタイプを取得します。

        Returns:
            str: "openai" または "gemini"
        """
        return self.current_api_type

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
            mode (str): 設定するモード名の文字列、"standard"または"section_by_section"

        Returns:
            bool: モードが正常に設定されたかどうか
        """
        try:
            # 文字列からEnumへの変換
            enum_mode = None
            for podcast_mode in PodcastMode:
                if podcast_mode.value == mode:
                    enum_mode = podcast_mode
                    break

            if enum_mode is None:
                logger.warning(f"無効なポッドキャストモード: {mode}")
                return False

            return self.prompt_manager.set_podcast_mode(enum_mode)
        except TypeError as e:
            logger.warning(f"ポッドキャストモード設定エラー: {e}")
            return False

    def get_podcast_mode(self) -> PodcastMode:
        """
        現在のポッドキャスト生成モードを取得します。

        Returns:
            PodcastMode: 現在のモード
        """
        return self.prompt_manager.get_podcast_mode()

    def set_character_mapping(self, character1: str, character2: str) -> bool:
        """
        キャラクターマッピングを設定します。

        Args:
            character1 (str): 1人目のキャラクター名
            character2 (str): 2人目のキャラクター名

        Returns:
            bool: 設定が成功したかどうか
        """
        # 明示的に戻り値の型を指定
        success: bool = self.prompt_manager.set_character_mapping(
            character1, character2
        )
        return success

    def get_character_mapping(self) -> Dict[str, str]:
        """
        現在のキャラクターマッピングを取得します。

        Returns:
            dict: 現在のキャラクターマッピング
        """
        # 明示的に戻り値の型を指定
        char_map: Dict[str, str] = self.prompt_manager.get_character_mapping()
        return char_map

    def get_valid_characters(self) -> List[str]:
        """
        有効なキャラクターのリストを取得します。

        Returns:
            list: 有効なキャラクター名のリスト
        """
        # 明示的に戻り値の型を指定
        chars: List[str] = self.prompt_manager.get_valid_characters()
        return chars

    def set_document_type(self, doc_type: DocumentType) -> bool:
        """
        ドキュメントタイプを設定します。

        Args:
            doc_type (str): 設定するドキュメントタイプの文字列
                           "paper", "blog", "minutes", "manual", "general"のいずれか

        Returns:
            bool: 設定が成功したかどうか
        """
        # 明示的に戻り値の型を指定
        success: bool = self.prompt_manager.set_document_type(doc_type)
        return success

    def get_document_type(self) -> DocumentType:
        """
        現在のドキュメントタイプを取得します。

        Returns:
            DocumentType: 現在のドキュメントタイプ
        """
        return self.prompt_manager.get_document_type()

    def get_document_type_name(self) -> str:
        """
        現在のドキュメントタイプの日本語名を取得します。

        Returns:
            str: ドキュメントタイプの日本語名
        """
        return self.prompt_manager.get_document_type_name()

    def generate_podcast_conversation(self, paper_text: str) -> str:
        """
        テキストからポッドキャスト形式の会話テキストを生成します。

        Args:
            paper_text (str): ドキュメントのテキスト

        Returns:
            str: 会話形式のポッドキャストテキスト
        """
        if not paper_text.strip():
            return "Error: No text provided."

        # プロンプトマネージャーを使用してプロンプトを生成
        prompt = self.prompt_manager.generate_podcast_conversation(paper_text)

        # プロンプトの先頭何文字かをログに記録
        logger.info(f"生成されたプロンプト: {prompt[:100]}")

        # 現在選択されているAPIに基づいてテキスト生成
        if self.current_api_type == "openai" and self.use_openai:
            result = self.openai_model.generate_text(prompt)
        elif self.current_api_type == "gemini" and self.use_gemini:
            result = self.gemini_model.generate_text(prompt)
        else:
            return "Error: No API key is set or valid API type is not selected."

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

            # 現在のポッドキャストモードをログに記録
            current_mode = self.prompt_manager.get_podcast_mode()
            logger.info(f"現在のポッドキャストモード: {current_mode.name}")

            # 現在のAPIタイプに基づいて適切なAPIが設定されているか確認
            if self.current_api_type == "openai" and self.use_openai:
                podcast_text = self.generate_podcast_conversation(cleaned_text)
            elif self.current_api_type == "gemini" and self.use_gemini:
                podcast_text = self.generate_podcast_conversation(cleaned_text)
            else:
                api_name = (
                    "OpenAI" if self.current_api_type == "openai" else "Google Gemini"
                )
                podcast_text = (
                    f"{api_name} API key is not set. Please enter your API key."
                )

            return podcast_text

        except Exception as e:
            logger.error(f"テキスト処理エラー: {e}")
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
        if self.current_api_type == "openai":
            return self.openai_model.get_last_token_usage()
        else:
            return self.gemini_model.get_last_token_usage()

    def set_model_name(self, model_name: str) -> bool:
        """
        現在選択されているAPIタイプに基づいてモデル名を設定します。

        Args:
            model_name (str): 設定するモデル名

        Returns:
            bool: 設定が成功したかどうか
        """
        if self.current_api_type == "openai":
            return self.openai_model.set_model_name(model_name)
        else:
            return self.gemini_model.set_model_name(model_name)

    def get_current_model(self) -> str:
        """
        現在選択されているAPIタイプのモデル名を取得します。

        Returns:
            str: 現在のモデル名
        """
        if self.current_api_type == "openai":
            return self.openai_model.model_name
        else:
            return self.gemini_model.model_name

    def get_available_models(self) -> List[str]:
        """
        現在選択されているAPIタイプで利用可能なモデルのリストを取得します。

        Returns:
            List[str]: 利用可能なモデル名のリスト
        """
        if self.current_api_type == "openai":
            return self.openai_model.get_available_models()
        else:
            return self.gemini_model.get_available_models()

    def set_max_tokens(self, max_tokens: int) -> bool:
        """
        現在選択されているAPIタイプの最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数

        Returns:
            bool: 設定が成功したかどうか
        """
        if self.current_api_type == "openai":
            return self.openai_model.set_max_tokens(max_tokens)
        else:
            return self.gemini_model.set_max_tokens(max_tokens)

    def get_max_tokens(self) -> int:
        """
        現在選択されているAPIタイプの最大トークン数を取得します。

        Returns:
            int: 現在の最大トークン数
        """
        if self.current_api_type == "openai":
            return self.openai_model.get_max_tokens()
        else:
            return self.gemini_model.get_max_tokens()
