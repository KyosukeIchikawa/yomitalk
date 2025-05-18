"""Test module for the PDF Extractor."""

from unittest.mock import MagicMock, patch

from yomitalk.utils.pdf_extractor import PDFExtractor


class TestPDFExtractor:
    """Test class for the PDFExtractor."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.extractor = PDFExtractor()

    def test_init(self):
        """Test PDFExtractor initialization."""
        assert hasattr(self.extractor, "markdown_converter")

    def test_extract_from_pdf(self):
        """Test extract_from_pdf method."""
        # DocumentConverterResultをシミュレートするモックを作成
        mock_result = MagicMock()
        mock_result.text_content = (
            "# Sample PDF Content\n\nThis is some sample content."
        )

        # Mock the convert method directly on the instance
        self.extractor.markdown_converter = MagicMock()
        self.extractor.markdown_converter.convert.return_value = mock_result

        # Call the method with a test path
        test_path = "/path/to/test.pdf"
        result = self.extractor.extract_from_pdf(test_path)

        # Verify that convert was called with the file path
        self.extractor.markdown_converter.convert.assert_called_once_with(test_path)

        # Verify the result
        assert "# Sample PDF Content" in result
        assert "This is some sample content." in result

    def test_extract_from_pdf_with_error(self):
        """Test extract_from_pdf method when an error occurs."""
        # Mock the convert method directly on the instance
        self.extractor.markdown_converter = MagicMock()
        self.extractor.markdown_converter.convert.side_effect = Exception("Test error")

        # Call the method with a test path
        test_path = "/path/to/test.pdf"

        # Call the method being tested and expect it to raise an exception
        with patch("yomitalk.utils.pdf_extractor.logger") as mock_logger:
            try:
                self.extractor.extract_from_pdf(test_path)
                assert False, "Expected an exception to be raised"
            except Exception as e:
                assert str(e) == "Test error"
                # Verify that the error was logged
                mock_logger.error.assert_called_once()
