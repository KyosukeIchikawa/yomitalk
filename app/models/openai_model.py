"""Module providing text generation functionality using the OpenAI API.

Uses OpenAI's LLM to generate podcast-style conversation text from research papers.
"""

import os
from typing import Optional

import httpx
from openai import OpenAI


class OpenAIModel:
    """Class that generates conversational text using the OpenAI API."""

    def __init__(self) -> None:
        """Initialize OpenAIModel."""
        # Try to get API key from environment
        self.api_key: Optional[str] = os.environ.get("OPENAI_API_KEY")

        # Default prompt template
        self.default_prompt_template = """
Please generate a Japanese conversation-style podcast text between "ずんだもん" (Zundamon) and "四国めたん" (Shikoku Metan)
based on the following paper summary.

Character roles:
- ずんだもん: A beginner in the paper's field with basic knowledge but sometimes makes common mistakes.
  Asks curious and sometimes naive questions. Slightly ditzy but eager to learn.
- 四国めたん: An expert on the paper's subject who explains concepts clearly and corrects Zundamon's misunderstandings.
  Makes complex topics understandable through metaphors and examples.

Format (STRICTLY FOLLOW THIS FORMAT):
ずんだもん: [Zundamon's speech in Japanese]
四国めたん: [Shikoku Metan's speech in Japanese]
ずんだもん: [Zundamon's next line]
四国めたん: [Shikoku Metan's next line]
...

IMPORTANT FORMATTING RULES:
1. ALWAYS start each new speaker's line with their name followed by a colon ("ずんだもん:" or "四国めたん:").
2. ALWAYS put each speaker's line on a new line.
3. NEVER combine multiple speakers' lines into a single line.
4. ALWAYS use the exact names "ずんだもん" and "四国めたん" (not variations or translations).
5. NEVER add any other text, headings, or explanations outside the conversation format.

Guidelines for content:
1. Create an engaging, fun podcast that explains the paper to beginners while also providing value to experts
2. Include examples and metaphors to help listeners understand difficult concepts
3. Have Zundamon make some common beginner mistakes that Shikoku Metan corrects politely
4. Cover the paper's key findings, methodology, and implications
5. Keep the conversation natural, friendly and entertaining
6. Make sure the podcast has a clear beginning, middle, and conclusion

Paper summary:
{paper_summary}
"""
        self.custom_prompt_template: Optional[str] = None

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

    def set_prompt_template(self, prompt_template: str) -> bool:
        """
        Set a custom prompt template for podcast generation.

        Args:
            prompt_template (str): Custom prompt template

        Returns:
            bool: Whether the template was successfully set
        """
        if not prompt_template or prompt_template.strip() == "":
            self.custom_prompt_template = None
            return False

        self.custom_prompt_template = prompt_template.strip()
        return True

    def get_current_prompt_template(self) -> str:
        """
        Get the current prompt template.

        Returns:
            str: The current prompt template (custom if set, otherwise default)
        """
        return self.custom_prompt_template or self.default_prompt_template

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
            print("Making OpenAI API request with model: gpt-4o-mini")

            # Create client with default http client to avoid proxies issue
            http_client = httpx.Client()
            client = OpenAI(api_key=self.api_key, http_client=http_client)

            # API request
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # or 'gpt-3.5-turbo'
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )

            # Get response content
            generated_text = str(response.choices[0].message.content)

            # Debug output
            print(f"Generated text sample: {generated_text[:200]}...")

            return generated_text

        except ImportError:
            return "Error: Install the openai library with: pip install openai"
        except Exception as e:
            print(f"Error during OpenAI API request: {e}")
            return f"Error generating text: {e}"

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

        # Get current prompt template (custom or default)
        prompt_template = self.get_current_prompt_template()

        # Create prompt for podcast conversation using the template
        prompt = prompt_template.format(paper_summary=paper_summary)

        print("Sending podcast generation prompt to OpenAI")

        # Use the general text generation method
        result = self.generate_text(prompt)

        # Debug: Log conversation lines
        if not result.startswith("Error"):
            lines = result.split("\n")
            speaker_lines = [
                line
                for line in lines
                if line.startswith("ずんだもん:")
                or line.startswith("四国めたん:")
                or line.startswith("ずんだもん：")
                or line.startswith("四国めたん：")
            ]
            print(f"Generated {len(speaker_lines)} conversation lines")
            if speaker_lines:
                print(f"First few lines: {speaker_lines[:3]}")
            else:
                print("Warning: No lines with correct speaker format found")
                print(f"First few output lines: {lines[:3]}")
                # Try to reformat the result if format is incorrect
                if "ずんだもん" in result and "四国めたん" in result:
                    print("Attempting to fix formatting...")
                    import re

                    # Add colons after character names if missing
                    fixed_result = re.sub(
                        r"(^|\n)(ずんだもん)(\s+)(?=[^\s:])", r"\1\2:\3", result
                    )
                    fixed_result = re.sub(
                        r"(^|\n)(四国めたん)(\s+)(?=[^\s:])", r"\1\2:\3", fixed_result
                    )

                    # Check if fix worked
                    fixed_lines = fixed_result.split("\n")
                    fixed_speaker_lines = [
                        line
                        for line in fixed_lines
                        if line.startswith("ずんだもん:")
                        or line.startswith("四国めたん:")
                        or line.startswith("ずんだもん：")
                        or line.startswith("四国めたん：")
                    ]
                    if fixed_speaker_lines:
                        print(
                            f"Fixed formatting. Now have {len(fixed_speaker_lines)} proper lines"
                        )
                        print(f"First few fixed lines: {fixed_speaker_lines[:3]}")
                        result = fixed_result

        return result
