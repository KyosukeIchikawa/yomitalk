"""Module providing text generation functionality using the Google Gemini API.

Uses Google's Gemini LLM to generate podcast-style conversation text from research papers.
"""

import os
from typing import Dict, List, Optional

import google.generativeai as genai

from yomitalk.utils.logger import logger


class GeminiModel:
    """Class that generates conversational text using the Google Gemini API."""

    def __init__(self) -> None:
        """Initialize GeminiModel."""
        # APIキーの取得試行
        self.api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY")

        # デフォルトモデル
        self.model_name: str = "gemini-2.5-flash-preview-04-17"

        # 利用可能なモデルのリスト
        self._available_models = [
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.5-pro-preview-05-06",
        ]

        # デフォルトの最大トークン数
        self.max_tokens: int = 65536

        # トークン使用状況の初期化
        self.last_token_usage: Dict[str, int] = {}

        # APIが設定されていれば初期化
        if self.api_key:
            self._initialize_api()

    def _initialize_api(self) -> None:
        """Initialize the Gemini API with the current API key."""
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def set_api_key(self, api_key: str) -> bool:
        """
        Set the Google API key and returns the result.

        Args:
            api_key (str): Google API key

        Returns:
            bool: Whether the configuration was successful
        """
        if not api_key or api_key.strip() == "":
            return False

        self.api_key = api_key.strip()
        os.environ["GOOGLE_API_KEY"] = self.api_key

        try:
            self._initialize_api()
            return True
        except Exception as e:
            logger.error(f"Error initializing Gemini API: {e}")
            return False

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

    def get_available_models(self) -> List[str]:
        """
        Get available Gemini models.

        Returns:
            List[str]: List of available model names
        """
        return self._available_models

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
        if model_name not in self._available_models:
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

            # モデルを設定
            model = genai.GenerativeModel(self.model_name)

            # APIリクエスト
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": self.max_tokens,
                },
            )

            # レスポンスの取得
            generated_text = str(response.text)

            # トークン使用状況を推定（Gemini APIは正確なトークン使用量を返さないため）
            # 実際のAPIでは利用可能かもしれないが、現在のSDKでは直接提供されていない
            approx_prompt_tokens = len(prompt.split()) * 2  # 大まかな推定
            approx_completion_tokens = len(generated_text.split()) * 2  # 大まかな推定

            self.last_token_usage = {
                "prompt_tokens": approx_prompt_tokens,
                "completion_tokens": approx_completion_tokens,
                "total_tokens": approx_prompt_tokens + approx_completion_tokens,
            }

            # デバッグ出力（セキュリティのため生成テキストの内容は出力しない）
            # logger.info(f"Generated text sample: {generated_text[:200]}...")
            logger.info(
                f"Text generation completed. Length: {len(generated_text)} characters"
            )
            logger.info(f"Approximate token usage: {self.last_token_usage}")

            return generated_text

        except ImportError:
            return "Error: Install the Google Generative AI library with: pip install google-generativeai"
        except Exception as e:
            logger.error(f"Error during Gemini API request: {e}")
            return f"Error generating text: {e}"

    def get_last_token_usage(self) -> dict:
        """
        最後のAPI呼び出しで使用されたトークン情報の概算を取得します。

        Returns:
            dict: トークン使用状況の概算（prompt_tokens, completion_tokens, total_tokens）
            またはAPIがまだ呼び出されていない場合は空の辞書
        """
        if hasattr(self, "last_token_usage"):
            return self.last_token_usage
        return {}
