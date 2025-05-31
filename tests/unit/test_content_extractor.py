"""Unit tests for ContentExtractor class."""
from unittest.mock import MagicMock

from yomitalk.components.content_extractor import ContentExtractor


class TestContentExtractor:
    """Test class for ContentExtractor."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        # No need to create instance since all methods are now classmethods

    def test_initialization(self):
        """Test that ContentExtractor initializes correctly."""
        # Check that supported extensions are properly defined
        assert isinstance(ContentExtractor.SUPPORTED_TEXT_EXTENSIONS, list)
        assert isinstance(ContentExtractor.SUPPORTED_PDF_EXTENSIONS, list)
        assert isinstance(ContentExtractor.SUPPORTED_EXTENSIONS, list)

        # Check that text and PDF extensions are included in supported extensions
        for ext in ContentExtractor.SUPPORTED_TEXT_EXTENSIONS:
            assert ext in ContentExtractor.SUPPORTED_EXTENSIONS
        for ext in ContentExtractor.SUPPORTED_PDF_EXTENSIONS:
            assert ext in ContentExtractor.SUPPORTED_EXTENSIONS

    def test_supported_extensions(self):
        """Test the supported extensions."""
        # Test that common extensions are included
        assert ".txt" in ContentExtractor.SUPPORTED_TEXT_EXTENSIONS
        assert ".md" in ContentExtractor.SUPPORTED_TEXT_EXTENSIONS
        assert ".pdf" in ContentExtractor.SUPPORTED_PDF_EXTENSIONS

        # Check the combined list
        all_extensions = (
            ContentExtractor.SUPPORTED_TEXT_EXTENSIONS
            + ContentExtractor.SUPPORTED_PDF_EXTENSIONS
        )
        for ext in all_extensions:
            assert ext in ContentExtractor.SUPPORTED_EXTENSIONS

    def test_extract_file_content(self):
        """Test extracting content from a file object."""
        # Mock a file object
        mock_file = MagicMock()
        mock_file.name = "test.txt"
        mock_file.read.return_value = b"This is test content."
        mock_file.tell.return_value = 0

        # Test with the mock file
        extension, content = ContentExtractor.extract_file_content(mock_file)

        # Verify results
        assert extension == ".txt"
        assert content == b"This is test content."

    def test_extract_text(self):
        """Test the extract_text method."""
        # Test with None input
        assert ContentExtractor.extract_text(None) == "Please upload a file."

        # Mock a valid file object for later implementation
        # of more comprehensive tests as needed
