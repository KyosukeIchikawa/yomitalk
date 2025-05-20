"""Test module for the content extractor."""

from unittest.mock import MagicMock, patch

from yomitalk.components.content_extractor import ContentExtractor


class TestContentExtractor:
    """Test class for the ContentExtractor."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.uploader = ContentExtractor()

    def test_init(self):
        """Test FileUploader initialization."""
        assert hasattr(self.uploader, "markdown_converter")
        assert hasattr(self.uploader, "supported_extensions")

    def test_supported_extensions(self):
        """Test that the supported extensions are correct."""
        extensions = self.uploader.get_supported_extensions()
        assert ".txt" in extensions
        assert ".md" in extensions
        assert ".pdf" in extensions
        assert len(extensions) >= 4  # At least 4 extensions should be supported

    def test_extract_from_bytes_with_pdf(self):
        """Test extract_from_bytes with PDF content."""
        # DocumentConverterResultをシミュレートするモックを作成
        mock_result = MagicMock()
        mock_result.text_content = (
            "# Sample PDF Content\n\nThis is some sample content."
        )

        # モックPDFコンテンツ
        mock_pdf_content = b"%PDF-1.4\n..."  # PDFのバイナリデータ

        # MarkItDownのconvertメソッドをモック
        with patch("markitdown.MarkItDown.convert", return_value=mock_result):
            # テスト実行
            result = self.uploader.extract_from_bytes(mock_pdf_content, ".pdf")

            # 結果の検証
            assert "# Sample PDF Content" in result
            assert "This is some sample content." in result

    def test_extract_from_bytes_with_text(self):
        """Test extract_from_bytes with text content."""
        # UTF-8テキストのテスト
        text_content = "This is a test content.".encode("utf-8")
        result = self.uploader.extract_from_bytes(text_content, ".txt")
        assert result == "This is a test content."

        # Shift-JISテキストのテスト
        jp_text_content = "これはテストです。".encode("shift_jis")
        result = self.uploader.extract_from_bytes(jp_text_content, ".txt")
        assert result == "これはテストです。"

    def test_extract_text_with_pdf(self):
        """Test extract_text with PDF file object."""
        # DocumentConverterResultをシミュレートするモックを作成
        mock_result = MagicMock()
        mock_result.text_content = (
            "# Sample PDF Content\n\nThis is some sample content."
        )

        # モックファイルオブジェクトの作成
        mock_file = MagicMock()
        mock_file.name = "test.pdf"
        mock_file.read = MagicMock(return_value=b"%PDF-1.4\n...")

        # MarkItDownのconvertメソッドをモック
        with patch("markitdown.MarkItDown.convert", return_value=mock_result):
            # テスト実行
            result = self.uploader.extract_text(mock_file)

            # 結果の検証
            assert "# Sample PDF Content" in result
            assert "This is some sample content." in result

    def test_extract_file_content(self):
        """Test extract_file_content function."""
        # モックファイルオブジェクトの作成
        mock_file = MagicMock()
        mock_file.name = "test.pdf"
        mock_file.read = MagicMock(return_value=b"test content")
        mock_file.tell = MagicMock(return_value=0)
        mock_file.seek = MagicMock()

        # テスト実行
        ext, content = self.uploader.extract_file_content(mock_file)

        # 結果の検証
        assert ext == ".pdf"
        assert content == b"test content"
        mock_file.read.assert_called_once()
        mock_file.tell.assert_called_once()
        mock_file.seek.assert_called_once_with(0)
