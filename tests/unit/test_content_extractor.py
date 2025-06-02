"""Unit tests for ContentExtractor class."""

from unittest.mock import MagicMock, patch

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

    def test_is_url_valid_urls(self):
        """Test is_url method with valid URLs."""
        valid_urls = [
            "https://www.example.com",
            "http://example.com",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://en.wikipedia.org/wiki/Test",
            "https://feeds.feedburner.com/example",
            "https://www.bing.com/search?q=test",
        ]

        for url in valid_urls:
            assert ContentExtractor.is_url(url) is True

    def test_is_url_invalid_urls(self):
        """Test is_url method with invalid URLs."""
        invalid_urls = [
            "",
            "not a url",
            "example.com",  # Missing scheme
            "file://local/path",  # Local file path
            "ftp://example.com",  # Non-HTTP scheme
            "https://",  # Missing netloc
            "://example.com",  # Missing scheme
        ]

        for url in invalid_urls:
            assert ContentExtractor.is_url(url) is False

    def test_is_url_edge_cases(self):
        """Test is_url method with edge cases."""
        # Test with whitespace
        assert ContentExtractor.is_url("  https://example.com  ") is True

        # Test with None input
        assert ContentExtractor.is_url(None) is False

    @patch("yomitalk.components.content_extractor._markdown_converter")
    def test_extract_from_url_success(self, mock_converter):
        """Test successful URL text extraction."""
        # Mock the converter response
        mock_result = MagicMock()
        mock_result.text_content = "Extracted content from URL"
        mock_converter.convert.return_value = mock_result

        url = "https://example.com/article"
        result = ContentExtractor.extract_from_url(url)

        assert result == "Extracted content from URL"
        mock_converter.convert.assert_called_once_with(url)

    @patch("yomitalk.components.content_extractor._markdown_converter")
    def test_extract_from_url_empty_content(self, mock_converter):
        """Test URL extraction with empty content."""
        # Mock the converter response with empty content
        mock_result = MagicMock()
        mock_result.text_content = None
        mock_converter.convert.return_value = mock_result

        url = "https://example.com/empty"
        result = ContentExtractor.extract_from_url(url)

        assert result == ""
        mock_converter.convert.assert_called_once_with(url)

    @patch("yomitalk.components.content_extractor._markdown_converter")
    def test_extract_from_url_conversion_error(self, mock_converter):
        """Test URL extraction with conversion error."""
        # Mock the converter to raise an exception
        mock_converter.convert.side_effect = Exception("Connection error")

        url = "https://example.com/error"
        result = ContentExtractor.extract_from_url(url)

        assert "URL conversion error: Connection error" in result
        mock_converter.convert.assert_called_once_with(url)

    def test_extract_from_url_invalid_url(self):
        """Test URL extraction with invalid URL."""
        invalid_url = "not a url"
        result = ContentExtractor.extract_from_url(invalid_url)

        assert result == "Invalid URL format."

    @patch("yomitalk.components.content_extractor._markdown_converter")
    def test_extract_from_url_youtube(self, mock_converter):
        """Test URL extraction from YouTube."""
        # Mock the converter response for YouTube
        mock_result = MagicMock()
        mock_result.text_content = "YouTube video transcript: How to code"
        mock_converter.convert.return_value = mock_result

        youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = ContentExtractor.extract_from_url(youtube_url)

        assert result == "YouTube video transcript: How to code"
        mock_converter.convert.assert_called_once_with(youtube_url)

    @patch("yomitalk.components.content_extractor._markdown_converter")
    def test_extract_from_url_wikipedia(self, mock_converter):
        """Test URL extraction from Wikipedia."""
        # Mock the converter response for Wikipedia
        mock_result = MagicMock()
        mock_result.text_content = "Wikipedia article about machine learning..."
        mock_converter.convert.return_value = mock_result

        wikipedia_url = "https://en.wikipedia.org/wiki/Machine_learning"
        result = ContentExtractor.extract_from_url(wikipedia_url)

        assert result == "Wikipedia article about machine learning..."
        mock_converter.convert.assert_called_once_with(wikipedia_url)

    @patch("yomitalk.components.content_extractor._markdown_converter")
    def test_extract_from_url_rss_feed(self, mock_converter):
        """Test URL extraction from RSS feed."""
        # Mock the converter response for RSS feed
        mock_result = MagicMock()
        mock_result.text_content = "RSS feed content: Latest news articles..."
        mock_converter.convert.return_value = mock_result

        rss_url = "https://feeds.feedburner.com/example"
        result = ContentExtractor.extract_from_url(rss_url)

        assert result == "RSS feed content: Latest news articles..."
        mock_converter.convert.assert_called_once_with(rss_url)

    def test_append_text_with_source_no_separator(self):
        """Test appending text without separator."""
        existing_text = "Existing content"
        new_text = "New content"
        source_name = "test.txt"

        result = ContentExtractor.append_text_with_source(
            existing_text, new_text, source_name, add_separator=False
        )

        expected = "Existing content\n\nNew content"
        assert result == expected

    def test_append_text_with_source_with_separator(self):
        """Test appending text with separator."""
        existing_text = "Existing content"
        new_text = "New content"
        source_name = "test.txt"

        result = ContentExtractor.append_text_with_source(
            existing_text, new_text, source_name, add_separator=True
        )

        expected = "Existing content\n\n---\n**Source: test.txt**\n\nNew content"
        assert result == expected

    def test_append_text_with_source_empty_existing(self):
        """Test appending to empty existing text."""
        existing_text = ""
        new_text = "New content"
        source_name = "test.txt"

        result = ContentExtractor.append_text_with_source(
            existing_text, new_text, source_name, add_separator=True
        )

        expected = "**Source: test.txt**\n\nNew content"
        assert result == expected

    def test_append_text_with_source_empty_new_text(self):
        """Test appending empty new text."""
        existing_text = "Existing content"
        new_text = ""
        source_name = "test.txt"

        result = ContentExtractor.append_text_with_source(
            existing_text, new_text, source_name, add_separator=True
        )

        # Should return existing text unchanged when new text is empty
        assert result == existing_text

    def test_get_source_name_from_file(self):
        """Test extracting source name from file object."""
        # Mock file object with name attribute
        mock_file = MagicMock()
        mock_file.name = "/path/to/document.pdf"

        result = ContentExtractor.get_source_name_from_file(mock_file)
        assert result == "document.pdf"

    def test_get_source_name_from_file_none(self):
        """Test extracting source name from None file object."""
        result = ContentExtractor.get_source_name_from_file(None)
        assert result == "Unknown File"

    def test_get_source_name_from_file_no_name(self):
        """Test extracting source name from file object without name."""
        mock_file = MagicMock()
        del mock_file.name  # Remove name attribute

        result = ContentExtractor.get_source_name_from_file(mock_file)
        assert result == "Uploaded File"
