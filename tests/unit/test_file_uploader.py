"""Test module for the file uploader."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from app.components.file_uploader import FileUploader


class TestFileUploader:
    """Test class for the FileUploader."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.uploader = FileUploader()

    def test_supported_extensions(self):
        """Test that the supported extensions are correct."""
        extensions = self.uploader.get_supported_extensions()
        assert ".txt" in extensions
        assert ".md" in extensions
        assert ".pdf" in extensions
        assert len(extensions) >= 4  # At least 4 extensions should be supported

    def test_extract_from_text_file(self):
        """Test text extraction from a text file."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w"
        ) as temp_file:
            temp_file.write("This is a test content.\nLine 2 of test content.")
            temp_file_path = temp_file.name

        try:
            # Extract text
            result = self.uploader._extract_from_text_file(temp_file_path)

            # Check the result
            assert "This is a test content." in result
            assert "Line 2 of test content." in result
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_extract_from_markdown_file(self):
        """Test text extraction from a Markdown file."""
        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(
            suffix=".md", delete=False, mode="w"
        ) as temp_file:
            temp_file.write(
                "# Test Header\n\nThis is markdown content.\n\n- Item 1\n- Item 2"
            )
            temp_file_path = temp_file.name

        try:
            # Extract text
            result = self.uploader._extract_from_text_file(temp_file_path)

            # Check the result
            assert "# Test Header" in result
            assert "This is markdown content." in result
            assert "- Item 1" in result
            assert "- Item 2" in result
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    @patch("app.components.file_uploader.PdfReader")
    def test_extract_from_pdf(self, mock_pdf_reader):
        """Test successful text extraction from a PDF file."""
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

            # Mock open function
            with patch("builtins.open", MagicMock()), patch.object(
                self.uploader,
                "_extract_with_pypdf",
                return_value="--- Page 1 ---\nTest content page 1\n\n--- Page 2 ---\nTest content page 2\n\n",
            ):
                # Call the method being tested
                result = self.uploader._extract_from_pdf(temp_file_path)

                # Verify the results
                expected_parts = [
                    "--- Page 1 ---",
                    "Test content page 1",
                    "--- Page 2 ---",
                    "Test content page 2",
                ]
                for part in expected_parts:
                    assert part in result

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_extract_text_from_path_with_text_file(self):
        """Test extract_text_from_path with a text file."""
        # Create a temporary text file
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False, mode="w"
        ) as temp_file:
            temp_file.write("This is a simple text file.")
            temp_file_path = temp_file.name

        try:
            # Mock the _extract_from_text_file method
            with patch.object(
                self.uploader,
                "_extract_from_text_file",
                return_value="This is a simple text file.",
            ):
                result = self.uploader.extract_text_from_path(temp_file_path)
                assert "This is a simple text file." in result
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_extract_text_from_path_with_pdf_file(self):
        """Test extract_text_from_path with a PDF file."""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Mock the _extract_from_pdf method
            with patch.object(
                self.uploader,
                "_extract_from_pdf",
                return_value="--- Page 1 ---\nPDF content\n\n",
            ):
                result = self.uploader.extract_text_from_path(temp_file_path)
                assert "PDF content" in result
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_extract_text_from_path_with_unsupported_file(self):
        """Test extract_text_from_path with an unsupported file type."""
        # Create a temporary unsupported file
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            result = self.uploader.extract_text_from_path(temp_file_path)
            assert "Unsupported file type" in result
            assert ".xyz" in result
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_extract_text_from_path_file_not_found(self):
        """Test extract_text_from_path with a non-existent file."""
        result = self.uploader.extract_text_from_path("non_existent_file.txt")
        assert "File not found" in result
