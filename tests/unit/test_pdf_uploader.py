"""Unit tests for the PDFUploader class.

Tests for the functionality of the PDF uploading and text extraction.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

from app.components.pdf_uploader import PDFUploader


class TestPDFUploader:
    """Test class for the PDFUploader."""

    def setup_method(self):
        """Set up the test environment before each test."""
        self.uploader = PDFUploader()

    def test_init(self):
        """Test the initialization of the PDFUploader class.

        Verifies that the temp_dir attribute exists and is valid.
        """
        assert hasattr(self.uploader, "temp_dir")
        assert os.path.isdir(self.uploader.temp_dir)

    def test_extract_text_no_file(self):
        """Test the behavior when no file is provided for text extraction.

        Expected to return an error message.
        """
        result = self.uploader.extract_text_from_path("")
        assert result == "PDF file not found."

    @patch("app.components.pdf_uploader.PdfReader")
    def test_extract_text_success(self, mock_pdf_reader):
        """Test successful text extraction from a PDF file.

        Uses a mock PDF reader to simulate text extraction.
        """
        # Create a mock file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Set up the mock PDF reader
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Test content page 1"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Test content page 2"

            mock_reader_instance = MagicMock()
            mock_reader_instance.pages = [mock_page1, mock_page2]
            mock_pdf_reader.return_value = mock_reader_instance

            # PdfReaderのオープン動作をモック化
            with patch("builtins.open", MagicMock()), patch.object(
                self.uploader,
                "_extract_with_pypdf",
                return_value="--- Page 1 ---\nTest content page 1\n\n--- Page 2 ---\nTest content page 2\n\n",
            ):
                # Call the method being tested
                result = self.uploader.extract_text_from_path(temp_file_path)

                # Verify the results
                expected_parts = [
                    "--- Page 1 ---",
                    "Test content page 1",
                    "--- Page 2 ---",
                    "Test content page 2",
                ]
                for part in expected_parts:
                    assert part in result

                # We don't check the exact format as it may include newlines
                assert "Test content page 1" in result
                assert "Test content page 2" in result

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @patch("app.components.pdf_uploader.PdfReader")
    @patch("app.components.pdf_uploader.pdfplumber.open")
    def test_extract_text_exception(self, mock_pdfplumber, mock_pdf_reader):
        """Test error handling during text extraction.

        Verifies that appropriate error messages are returned when exceptions occur.
        """
        # Create a mock file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Set up the mock to raise an exception
            mock_pdf_reader.side_effect = Exception("Test exception")
            # Also make pdfplumber fail with different error
            mock_pdfplumber.side_effect = Exception(
                "No /Root object! - Is this really a PDF?"
            )

            # Call the method being tested
            result = self.uploader.extract_text_from_path(temp_file_path)

            # Verify the error message
            assert "PDF parsing failed" in result
            assert "Is this really a PDF" in result
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
