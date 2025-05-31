"""Module providing text generation functionality using the Google Gemini API.

Uses Google's Gemini LLM to generate podcast-style conversation text from research papers.
"""
import os
from typing import Dict, Optional

from google import genai
from google.genai.types import GenerateContentConfig

from yomitalk.utils.logger import logger


class GeminiModel:
    """Class that generates conversational text using the Google Gemini API."""

    # Class-level constants for model configuration
    AVAILABLE_MODELS = [
        "gemini-2.5-flash-preview-05-20",
        "gemini-2.5-pro-preview-05-06",
    ]
    DEFAULT_MODEL = "gemini-2.5-flash-preview-05-20"
    DEFAULT_MAX_TOKENS = 65536

    def __init__(self) -> None:
        """Initialize GeminiModel."""
        # APIキーの取得試行
        self.api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY")

        self.model_name: str = self.DEFAULT_MODEL
        self.max_tokens: int = self.DEFAULT_MAX_TOKENS
        self.last_token_usage: Dict[str, int] = {}

    def set_api_key(self, api_key: str) -> bool:
        """
        Set the Google API key and returns the result.

        Args:
            api_key (str): Google API key

        Returns:
            bool: Whether the configuration was successful
        """
        if api_key_ := api_key.strip():
            self.api_key = api_key_
            return True
        return False

    def has_api_key(self) -> bool:
        """
        Check if API key is set.

        Returns:
            bool: Whether API key is set
        """
        return self.api_key is not None and self.api_key.strip() != ""

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
            if max_tokens_int > 65536:  # Geminiの最大値
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

    def set_model_name(self, model_name: str) -> bool:
        """
        Set the Gemini model name.

        Args:
            model_name (str): Model name to use

        Returns:
            bool: Whether the model name was successfully set
        """
        if not model_name or model_name.strip() == "":
            return False

        model_name = model_name.strip()
        if model_name not in self.AVAILABLE_MODELS:
            return False

        self.model_name = model_name
        return True

    def generate_text(self, prompt: str) -> str:
        """
        Generate text using Gemini API based on the provided prompt.

        Args:
            prompt (str): The prompt text to send to the API

        Returns:
            str: Generated text response
        """
        if not self.api_key:
            return "API key error: Google Gemini API key is not set."

        try:
            logger.info(f"Making Gemini API request with model: {self.model_name}")

            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=GenerateContentConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=0.7,
                ),
            )

            if not response.candidates:
                return "Error: No text was generated"

            # トークン使用量の取得（Gemini APIでは必ず取得できる）
            usage_metadata = response.usage_metadata
            self.last_token_usage = {
                "prompt_tokens": usage_metadata.prompt_token_count,
                "completion_tokens": usage_metadata.candidates_token_count,
                "total_tokens": usage_metadata.total_token_count,
            }

            generated_text: str = response.text
            logger.info(
                f"Text generation completed. Length: {len(generated_text)} characters"
            )
            logger.info(f"Token usage: {self.last_token_usage}")

            return generated_text

        except ImportError:
            return "Error: Install the Google Generative AI library with: pip install google-generativeai"
        except Exception as e:
            error_class = str(e.__class__.__name__)

            if "BlockedPrompt" in error_class:
                logger.error("Prompt was blocked: Contains prohibited content")
                return "Error: Your request contains content that is flagged as inappropriate or against usage policies."
            elif "StopCandidate" in error_class:
                logger.error(
                    "Generation stopped: Output may contain prohibited content"
                )
                return "Error: The generation was stopped as the potential response may contain inappropriate content."
            else:
                logger.error(f"Error during Gemini API request: {error_class} - {e}")
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
