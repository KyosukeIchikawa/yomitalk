"""Module providing text generation functionality using the OpenAI API.

Uses OpenAI's LLM to generate podcast-style conversation text from research papers.
"""

import os
from typing import Dict, List, Optional, Tuple

import httpx
from openai import OpenAI

from yomitalk.utils.logger import logger


class OpenAIModel:
    """Class that generates conversational text using the OpenAI API."""

    # Class-level constants for model configuration
    DEFAULT_MODELS = [
        "gpt-4.1-nano",
        "gpt-4.1-mini",
        "gpt-4.1",
        "o4-mini",
    ]
    DEFAULT_MODEL = "gpt-4.1-mini"
    DEFAULT_MAX_TOKENS = 32768

    def __init__(self) -> None:
        """Initialize OpenAIModel."""
        # Try to get API key from environment
        self.api_key: Optional[str] = os.environ.get("OPENAI_API_KEY")

        # デフォルトモデル
        self.model_name: str = self.DEFAULT_MODEL

        # 利用可能なモデルのリスト
        self._available_models = self.DEFAULT_MODELS.copy()

        # デフォルトの最大トークン数
        self.max_tokens: int = self.DEFAULT_MAX_TOKENS

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

            # デバッグ出力（セキュリティのため生成テキストの内容は出力しない）
            # logger.info(f"Generated text sample: {generated_text[:200]}...")
            logger.info(
                f"Text generation completed. Length: {len(generated_text)} characters"
            )
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

    @classmethod
    def get_default_models_info(cls) -> Tuple[List[str], str, int]:
        """
        Get default OpenAI models information without creating instance.

        Returns:
            Tuple[List[str], str, int]: (available_models, default_model, default_max_tokens)
        """
        return cls.DEFAULT_MODELS.copy(), cls.DEFAULT_MODEL, cls.DEFAULT_MAX_TOKENS
