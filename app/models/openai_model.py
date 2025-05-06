"""Module providing text generation functionality using the OpenAI API.

Uses OpenAI's LLM to generate podcast-style conversation text from research papers.
"""

import os
from typing import Dict, List, Optional

import httpx
from openai import OpenAI

from app.prompt_manager import PromptManager
from app.utils.logger import logger


class OpenAIModel:
    """Class that generates conversational text using the OpenAI API."""

    def __init__(self) -> None:
        """Initialize OpenAIModel."""
        # Try to get API key from environment
        self.api_key: Optional[str] = os.environ.get("OPENAI_API_KEY")

        # デフォルトモデル
        self.model_name: str = "gpt-4.1-mini"

        # 利用可能なモデルのリスト
        self._available_models = [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "o4-mini",
        ]

        # プロンプトマネージャーを初期化
        self.prompt_manager = PromptManager()

        # デフォルトの最大トークン数
        self.max_tokens: int = 32768

        # トークン使用状況の初期化
        self.last_token_usage: Dict[str, int] = {}

    def set_api_key(self, api_key: str) -> bool:
        """
        Set the OpenAI API key and returns the result.

        Args:
            api_key (str): OpenAI API key

        Returns:
            bool: Whether the configuration was successful
        """
        if not api_key or api_key.strip() == "":
            return False

        self.api_key = api_key.strip()
        os.environ["OPENAI_API_KEY"] = self.api_key
        return True

    def set_max_tokens(self, max_tokens: int) -> bool:
        """
        最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数

        Returns:
            bool: 設定が成功したかどうか
        """
        try:
            max_tokens_int = int(max_tokens)
            if max_tokens_int < 100:
                return False
            if max_tokens_int > 32768:
                return False

            self.max_tokens = max_tokens_int
            return True
        except (ValueError, TypeError):
            return False

    def get_max_tokens(self) -> int:
        """
        現在設定されている最大トークン数を取得します。

        Returns:
            int: 現在の最大トークン数
        """
        return self.max_tokens

    def get_available_models(self) -> List[str]:
        """
        Get available OpenAI models.

        Returns:
            List[str]: List of available model names
        """
        return self._available_models

    def set_model_name(self, model_name: str) -> bool:
        """
        Set the OpenAI model name.

        Args:
            model_name (str): Model name to use

        Returns:
            bool: Whether the model name was successfully set
        """
        if not model_name or model_name.strip() == "":
            return False

        model_name = model_name.strip()
        if model_name not in self._available_models:
            return False

        self.model_name = model_name
        return True

    def set_prompt_template(self, prompt_template: str) -> bool:
        """
        Set a custom prompt template for podcast generation.

        Args:
            prompt_template (str): Custom prompt template

        Returns:
            bool: Whether the template was successfully set
        """
        return self.prompt_manager.set_prompt_template(prompt_template)

    def get_current_prompt_template(self) -> str:
        """
        Get the current prompt template.

        Returns:
            str: The current prompt template (custom if set, otherwise default)
        """
        return self.prompt_manager.get_current_prompt_template()

    def generate_text(self, prompt: str) -> str:
        """
        Generate text using OpenAI API based on the provided prompt.

        Args:
            prompt (str): The prompt text to send to the API

        Returns:
            str: Generated text response
        """
        if not self.api_key:
            return "API key error: OpenAI API key is not set."

        try:
            logger.info(f"Making OpenAI API request with model: {self.model_name}")

            # Create client with default http client to avoid proxies issue
            http_client = httpx.Client()
            client = OpenAI(api_key=self.api_key, http_client=http_client)

            # API request
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=self.max_tokens,
            )

            # Get response content
            generated_text = str(response.choices[0].message.content)

            # トークン使用状況の保存
            self.last_token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            # Debug output
            logger.info(f"Generated text sample: {generated_text[:200]}...")
            logger.info(f"Token usage: {self.last_token_usage}")

            return generated_text

        except ImportError:
            return "Error: Install the openai library with: pip install openai"
        except Exception as e:
            logger.error(f"Error during OpenAI API request: {e}")
            return f"Error generating text: {e}"

    def get_last_token_usage(self) -> dict:
        """
        最後のAPI呼び出しで使用されたトークン情報を取得します。

        Returns:
            dict: トークン使用状況（prompt_tokens, completion_tokens, total_tokens）
            またはAPIがまだ呼び出されていない場合は空の辞書
        """
        if hasattr(self, "last_token_usage"):
            return self.last_token_usage
        return {}

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

    def convert_abstract_to_real_characters(self, text: str) -> str:
        """
        抽象的なキャラクター名（Character1, Character2）を実際のキャラクター名に変換します。

        Args:
            text (str): 変換するテキスト

        Returns:
            str: 変換後のテキスト
        """
        return self.prompt_manager.convert_abstract_to_real_characters(text)

    def generate_podcast_conversation(self, paper_summary: str) -> str:
        """
        Generate podcast-style conversation text from a paper summary.

        Args:
            paper_summary (str): Paper summary text

        Returns:
            str: Conversation-style podcast text
        """
        if not paper_summary.strip():
            return "Error: No paper summary provided."

        # プロンプトマネージャーを使用してプロンプトを生成
        prompt = self.prompt_manager.generate_podcast_conversation(paper_summary)

        logger.info("Sending podcast generation prompt to OpenAI")

        # Use the general text generation method
        result = self.generate_text(prompt)

        # 抽象キャラクター名を実際のキャラクター名に変換
        if not result.startswith("Error"):
            result = self.convert_abstract_to_real_characters(result)

        # Debug: Log conversation lines
        if not result.startswith("Error"):
            lines = result.split("\n")
            speaker_lines = [
                line
                for line in lines
                if line.startswith(
                    f"{self.prompt_manager.character_mapping['Character1']}:"
                )
                or line.startswith(
                    f"{self.prompt_manager.character_mapping['Character2']}:"
                )
                or line.startswith(
                    f"{self.prompt_manager.character_mapping['Character1']}："
                )
                or line.startswith(
                    f"{self.prompt_manager.character_mapping['Character2']}："
                )
            ]
            logger.info(f"Generated {len(speaker_lines)} conversation lines")
            if speaker_lines:
                logger.debug(f"First few lines: {speaker_lines[:3]}")
            else:
                logger.warning("No lines with correct speaker format found")
                logger.warning(f"First few output lines: {lines[:3]}")
                # Try to reformat the result if format is incorrect
                real_char1 = self.prompt_manager.character_mapping["Character1"]
                real_char2 = self.prompt_manager.character_mapping["Character2"]
                if real_char1 in result and real_char2 in result:
                    logger.info("Attempting to fix formatting...")
                    import re

                    # Add colons after character names if missing
                    fixed_result = re.sub(
                        f"({real_char1})\\s+",
                        "\\1: ",
                        result,
                    )
                    fixed_result = re.sub(
                        f"({real_char2})\\s+",
                        "\\1: ",
                        fixed_result,
                    )
                    result = fixed_result

        return result

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
