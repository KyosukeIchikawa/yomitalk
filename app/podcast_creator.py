"""Podcast text generation module using OpenAI API.

This module provides functionality to generate podcast scripts using OpenAI's GPT models.
It includes the PodcastCreator class which handles API interactions and text generation.
"""

import textwrap
from typing import Dict, Union

from openai import OpenAI


class PodcastCreator:
    """Class for creating podcast scripts using OpenAI API.

    This class handles the interaction with OpenAI's API to generate
    podcast scripts based on input text.
    """

    def __init__(self):
        """Initialize the PodcastCreator class.

        Sets up the OpenAI client with the API key if provided.
        """
        self.client = None
        self.api_key = None

    def set_api_key(self, api_key: str) -> str:
        """Set the OpenAI API key and initialize the client.

        Args:
            api_key: The OpenAI API key

        Returns:
            Message indicating successful API key setting
        """
        try:
            self.api_key = api_key
            self.client = OpenAI(api_key=api_key)
            # Test API key
            self.client.models.list()
            return "API key successfully set."
        except Exception as e:
            self.api_key = None
            self.client = None
            return f"Error setting API key: {str(e)}"

    def create_podcast_text(
        self, input_text: str, model: str = "gpt-3.5-turbo"
    ) -> Union[str, Dict]:
        """Generate podcast script from input text.

        Args:
            input_text: Text extracted from PDF to base the podcast on
            model: OpenAI model to use for generation

        Returns:
            Generated podcast script or error message
        """
        if not self.client:
            return "Please set your OpenAI API key first."

        if not input_text or input_text.strip() == "":
            return "No input text provided. Please upload a PDF and extract text first."

        try:
            # Define the prompt with instructions for the podcast script
            system_prompt = (
                "You are a professional podcast creator that specializes in "
                "academic content. Create an engaging podcast script based on "
                "the academic paper provided. Make it engaging, clear, and "
                "aimed at an audience with basic familiarity with the field."
            )

            user_prompt = (
                "Create a podcast script based on the following text extracted "
                "from an academic paper. Include an introduction, discussion of "
                "key points, and conclusion. Make the content engaging while "
                "maintaining academic integrity.\n\n"
                f"Paper text: {input_text[:6000]}"  # Limit input to avoid token limits
            )

            # Make the API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            # Extract the generated text from the response
            podcast_text = response.choices[0].message.content

            # Format the text for better readability
            formatted_text = self._format_podcast_text(podcast_text)

            return formatted_text

        except Exception as e:
            return f"Error generating podcast text: {str(e)}"

    def _format_podcast_text(self, text: str) -> str:
        """Format the podcast text for better readability.

        Args:
            text: Raw podcast text from API

        Returns:
            Formatted podcast text
        """
        # Split into paragraphs
        paragraphs = text.split("\n\n")

        # Format each paragraph with proper line wrapping
        formatted_paragraphs = []
        for para in paragraphs:
            if para.strip():
                # Preserve paragraph structure but wrap text
                formatted = "\n".join(
                    textwrap.fill(line, width=80) for line in para.split("\n")
                )
                formatted_paragraphs.append(formatted)

        # Join paragraphs with double newlines
        return "\n\n".join(formatted_paragraphs)
