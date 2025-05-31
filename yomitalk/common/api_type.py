"""API type enumeration for different language model providers."""

from enum import Enum, auto


class APIType(Enum):
    """Enumeration for supported API types."""

    OPENAI = auto()
    GEMINI = auto()

    @property
    def display_name(self) -> str:
        """Get the display name for the API type."""
        if self is APIType.OPENAI:
            return "OpenAI"
        elif self is APIType.GEMINI:
            return "Google Gemini"
        else:
            return self.value
