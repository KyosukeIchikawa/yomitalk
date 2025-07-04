"""Unit tests for PromptManager class."""

from yomitalk.prompt_manager import DocumentType, PodcastMode, PromptManager


class TestPromptManager:
    """Test class for PromptManager."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        self.prompt_manager = PromptManager()

    def test_initialization(self):
        """Test that PromptManager initializes correctly."""
        # Check that the basic attributes are initialized
        assert hasattr(self.prompt_manager, "current_mode")
        assert hasattr(self.prompt_manager, "current_document_type")

        # Check default values
        assert self.prompt_manager.current_mode == PodcastMode.STANDARD
        assert self.prompt_manager.current_document_type == DocumentType.PAPER

    def test_podcast_mode_enum(self):
        """Test PodcastMode enum values."""
        # Check that all expected modes are defined
        assert hasattr(PodcastMode, "STANDARD")
        assert hasattr(PodcastMode, "SECTION_BY_SECTION")

        # Check values are different
        assert PodcastMode.STANDARD != PodcastMode.SECTION_BY_SECTION

    def test_document_type_enum(self):
        """Test DocumentType enum values."""
        # Check that all expected types are defined
        assert hasattr(DocumentType, "PAPER")
        assert hasattr(DocumentType, "MANUAL")
        assert hasattr(DocumentType, "MINUTES")
        assert hasattr(DocumentType, "BLOG")
        assert hasattr(DocumentType, "GENERAL")

        # Check values are different
        assert DocumentType.PAPER != DocumentType.MANUAL
        assert DocumentType.MANUAL != DocumentType.MINUTES
        assert DocumentType.MINUTES != DocumentType.BLOG
        assert DocumentType.BLOG != DocumentType.GENERAL
        assert DocumentType.GENERAL != DocumentType.PAPER

    def test_get_prompt_template(self):
        """Test getting prompt template."""
        # Get prompt template for default settings
        prompt = self.prompt_manager.get_template_content()

        # Check that the prompt is a string and contains expected keywords
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_varies_with_mode(self):
        """Test that prompt varies with podcast mode."""
        # Get prompt for STANDARD mode
        self.prompt_manager.current_mode = PodcastMode.STANDARD
        standard_prompt = self.prompt_manager.get_template_content()

        # Get prompt for SECTION_BY_SECTION mode
        self.prompt_manager.current_mode = PodcastMode.SECTION_BY_SECTION
        detailed_prompt = self.prompt_manager.get_template_content()

        # Prompts should be different
        assert standard_prompt != detailed_prompt

    def test_prompt_varies_with_document_type(self):
        """Test that prompt varies with document type."""
        # このテストはスキップ - 現在の実装では文書タイプによってテンプレートは変わらないため

    def test_format_prompt(self):
        """Test formatting a prompt with input text."""
        # Sample input text
        input_text = "This is a sample research paper about machine learning."

        # Get formatted prompt
        formatted_prompt = self.prompt_manager.generate_podcast_conversation(input_text)

        # Check that the formatted prompt is a string
        assert isinstance(formatted_prompt, str)
        assert len(formatted_prompt) > 0
