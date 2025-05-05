"""Test module for the file uploader."""

import os
import tempfile
from unittest.mock import mock_open, patch

from app.components.file_uploader import FileUploader
from app.utils.pdf_extractor import PDFExtractor


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
            # Mock the PDFExtractor.extract_from_pdf method
            with patch.object(
                self.uploader.pdf_extractor,
                "extract_from_pdf",
                return_value="## Page 1 ---\nPDF content\n\n",
            ):
                result = self.uploader.extract_text_from_path(temp_file_path)
                assert "## Page 1" in result
                assert "PDF content" in result
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_extract_text_from_path_with_unsupported_file(self):
        """Test extract_text_from_path with an unsupported file type."""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(
            suffix=".unsupported", delete=False
        ) as temp_file:
            temp_file_path = temp_file.name

        try:
            result = self.uploader.extract_text_from_path(temp_file_path)
            assert "Unsupported file type" in result
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_extract_text_from_path_file_not_found(self):
        """Test extract_text_from_path with a file that doesn't exist."""
        result = self.uploader.extract_text_from_path("nonexistent_file.txt")
        assert "File not found" in result


def test_init():
    """Test initialization of FileUploader."""
    uploader = FileUploader()
    assert uploader.temp_dir.exists()
    assert hasattr(uploader, "supported_extensions")
    assert hasattr(uploader, "pdf_extractor")
    assert isinstance(uploader.pdf_extractor, PDFExtractor)


def test_extract_text_no_file():
    """Test extract_text with no file."""
    uploader = FileUploader()
    result = uploader.extract_text(None)
    assert "Please upload a file" in result


def test_extract_text_from_path_not_found():
    """Test extract_text_from_path with non-existent file."""
    uploader = FileUploader()
    result = uploader.extract_text_from_path("non_existent_file.txt")
    assert "File not found" in result


def test_extract_text_from_path_unsupported_extension():
    """Test extract_text_from_path with unsupported file extension."""
    # Create a temporary file with unsupported extension
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
        temp_file_path = temp_file.name

    try:
        uploader = FileUploader()
        result = uploader.extract_text_from_path(temp_file_path)
        assert "Unsupported file type" in result
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@patch("builtins.open", new_callable=mock_open, read_data="Text content")
@patch("os.path.exists", return_value=True)
def test_extract_from_text_file(mock_exists, mock_file):
    """Test _extract_from_text_file."""
    uploader = FileUploader()
    result = uploader._extract_from_text_file("test.txt")
    assert result == "Text content"
    mock_file.assert_called_once_with("test.txt", "r", encoding="utf-8")


@patch(
    "builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "test error")
)
@patch("os.path.exists", return_value=True)
def test_extract_from_text_file_unicode_error(mock_exists, mock_file):
    """Test _extract_from_text_file with unicode error."""
    # モック: shift_jisで開いた場合は成功
    shift_jis_mock = mock_open(read_data="日本語テキスト")
    with patch("builtins.open", shift_jis_mock):
        uploader = FileUploader()
        result = uploader._extract_from_text_file("test.txt")
        assert "日本語テキスト" in result
