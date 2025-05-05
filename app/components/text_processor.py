"""Module providing text processing functionality.

Functions to process, summarize, and convert research paper text to podcast format.
"""

from typing import List

from app.models.openai_model import OpenAIModel

# Removed transformers import (not used)
# from transformers import Pipeline, pipeline


class TextProcessor:
    """Class that processes research paper text and converts it to podcast text."""

    def __init__(self) -> None:
        """Initialize TextProcessor."""
        # Removed transformers summarization model related code
        self.openai_model = OpenAIModel()
        self.use_openai = False

    def set_openai_api_key(self, api_key: str) -> bool:
        """
        Set the OpenAI API key.

        Args:
            api_key (str): OpenAI API key

        Returns:
            bool: Whether the API key was successfully set
        """
        success = self.openai_model.set_api_key(api_key)
        if success:
            self.use_openai = True
        return success

    def set_model_name(self, model_name: str) -> bool:
        """
        Set the OpenAI model name.

        Args:
            model_name (str): Model name to use

        Returns:
            bool: Whether the model name was successfully set
        """
        return self.openai_model.set_model_name(model_name)

    def get_model_name(self) -> str:
        """
        Get the current OpenAI model name.

        Returns:
            str: Current model name
        """
        return self.openai_model.model_name

    def set_prompt_template(self, prompt_template: str) -> bool:
        """
        Set the custom prompt template for podcast generation.

        Args:
            prompt_template (str): Custom prompt template

        Returns:
            bool: Whether the template was successfully set
        """
        return self.openai_model.set_prompt_template(prompt_template)

    def get_prompt_template(self) -> str:
        """
        Get the current prompt template.

        Returns:
            str: The current prompt template
        """
        return self.openai_model.get_current_prompt_template()

    def set_podcast_mode(self, mode: str) -> bool:
        """
        ポッドキャスト生成モードを設定します。

        Args:
            mode (str): 'standard' または 'section_by_section'

        Returns:
            bool: モードが正常に設定されたかどうか
        """
        return self.openai_model.set_podcast_mode(mode)

    def get_podcast_mode(self) -> str:
        """
        現在のポッドキャスト生成モードを取得します。

        Returns:
            str: 現在のモード ('standard' または 'section_by_section')
        """
        return self.openai_model.get_podcast_mode()

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
                podcast_text = self.openai_model.generate_podcast_conversation(
                    cleaned_text
                )
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

    def get_token_usage(self) -> dict:
        """
        最後のAPI呼び出しで使用されたトークン情報を取得します。

        Returns:
            dict: トークン使用状況を含む辞書
        """
        return self.openai_model.get_last_token_usage()
