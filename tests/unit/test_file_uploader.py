"""Test module for the file uploader."""

import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

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

    @patch("app.components.file_uploader.fitz.open")
    def test_extract_from_pdf(self, mock_fitz_open):
        """Test successful text extraction from a PDF file using PyMuPDF."""
        # Create a mock file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Set up the mock fitz document
            mock_page1 = MagicMock()
            mock_page1.get_text.return_value = "Test content page 1"
            mock_page2 = MagicMock()
            mock_page2.get_text.return_value = "Test content page 2"

            mock_doc = MagicMock()
            mock_doc.__iter__.return_value = iter([mock_page1, mock_page2])
            mock_doc.__len__.return_value = 2
            mock_fitz_open.return_value = mock_doc

            # Mock the column detection method to use the standard method instead
            with patch.object(
                self.uploader,
                "_extract_with_column_detection",
                side_effect=Exception("Simulated column detection failure"),
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

    @patch("app.components.file_uploader.fitz.open")
    def test_extract_with_column_detection(self, mock_fitz_open):
        """Test column detection for PDF extraction."""
        # Create a mock file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Mock page with text blocks
            mock_page = MagicMock()
            mock_page.rect.width = 600  # Mock page width

            # Create text blocks dict
            text_blocks = {
                "blocks": [
                    {
                        "lines": [{"spans": [{"text": "Left column text 1"}]}],
                        "bbox": (10, 50, 290, 100),  # Left side of page
                    },
                    {
                        "lines": [{"spans": [{"text": "Left column text 2"}]}],
                        "bbox": (10, 150, 290, 200),  # Left side of page
                    },
                    {
                        "lines": [{"spans": [{"text": "Right column text 1"}]}],
                        "bbox": (310, 50, 590, 100),  # Right side of page
                    },
                    {
                        "lines": [{"spans": [{"text": "Right column text 2"}]}],
                        "bbox": (310, 150, 590, 200),  # Right side of page
                    },
                    {
                        "lines": [{"spans": [{"text": "Title spanning both columns"}]}],
                        "bbox": (150, 10, 450, 30),  # Title in the center top
                    },
                ]
            }

            mock_page.get_text.return_value = text_blocks

            # Set up mock document
            mock_doc = MagicMock()
            mock_doc.__iter__.return_value = iter([mock_page])
            mock_doc.__len__.return_value = 1
            mock_fitz_open.return_value = mock_doc

            # Patch the join_blocks_with_spacing method to verify it's called with the right args
            with patch.object(
                self.uploader,
                "_join_blocks_with_spacing",
                # テストのために単純に結合して返す
                side_effect=lambda blocks: "\n".join(block["text"] for block in blocks),
            ) as mock_join:
                # Call the method being tested
                result = self.uploader._extract_with_column_detection(temp_file_path)

                # Verify the results
                assert "[Left Column]" in result
                assert "Left column text 1" in result
                assert "Left column text 2" in result
                assert "[Right Column]" in result
                assert "Right column text 1" in result
                assert "Right column text 2" in result
                assert "Title spanning both columns" in result  # タイトルがどちらかの列に含まれること
                # _join_blocks_with_spacingが呼ばれたことを確認
                assert mock_join.call_count == 2

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_join_blocks_with_spacing(self):
        """Test _join_blocks_with_spacing."""
        uploader = FileUploader()

        blocks = [
            {
                "text": "First block",
                "bbox": [50, 100, 250, 150],
                "x0": 50,
                "y0": 100,
                "y1": 150,
            },
            {
                "text": "Second block",
                "bbox": [50, 300, 250, 350],
                "x0": 50,
                "y0": 300,
                "y1": 350,
            },
        ]

        result = uploader._join_blocks_with_spacing(blocks)

        # ブロック間の垂直ギャップが大きいため、追加の改行が挿入されているか確認
        assert (
            result == "First block\n\nSecond block"
            or result == "First block\n\n\nSecond block"
        )
        # 改行が少なくとも1つ以上あることを確認
        assert "\n\n" in result

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


def test_init():
    """Test initialization of FileUploader."""
    uploader = FileUploader()
    assert uploader.temp_dir is not None
    assert uploader.supported_extensions is not None


def test_extract_text_no_file():
    """Test extract_text with no file."""
    uploader = FileUploader()
    result = uploader.extract_text(None)
    assert result == "Please upload a file."


def test_extract_text_from_path_not_found():
    """Test extract_text_from_path with file not found."""
    uploader = FileUploader()
    result = uploader.extract_text_from_path("nonexistent_file.txt")
    assert result == "File not found."


def test_extract_text_from_path_unsupported_extension():
    """Test extract_text_from_path with unsupported extension."""
    uploader = FileUploader()
    with patch("os.path.exists", return_value=True):
        result = uploader.extract_text_from_path("file.unsupported")
        assert "Unsupported file type" in result


@patch("builtins.open", new_callable=mock_open, read_data="Text content")
@patch("os.path.exists", return_value=True)
def test_extract_from_text_file(mock_exists, mock_file):
    """Test _extract_from_text_file."""
    uploader = FileUploader()
    result = uploader._extract_from_text_file("file.txt")
    assert result == "Text content"
    mock_file.assert_called_with("file.txt", "r", encoding="utf-8")


@patch(
    "builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "test error")
)
@patch("os.path.exists", return_value=True)
def test_extract_from_text_file_unicode_error(mock_exists, mock_file):
    """Test _extract_from_text_file with UnicodeDecodeError."""
    uploader = FileUploader()

    # 2回目の呼び出しではshift-jisでの読み込みに失敗するようにパッチする
    with patch("builtins.open", side_effect=Exception("Failed to read with shift-jis")):
        result = uploader._extract_from_text_file("file.txt")
        assert "Text file reading failed" in result


@patch("fitz.open")
def test_extract_from_pdf(mock_fitz_open):
    """Test _extract_from_pdf."""
    uploader = FileUploader()

    # Set up the mock
    mock_doc = MagicMock()
    mock_fitz_open.return_value = mock_doc

    # Mock extract_with_column_detection
    with patch.object(
        uploader, "_extract_with_column_detection", return_value="PDF Content"
    ):
        result = uploader._extract_from_pdf("file.pdf")
        assert result == "PDF Content"


@patch("fitz.open")
def test_extract_with_column_detection(mock_fitz_open):
    """Test _extract_with_column_detection."""
    uploader = FileUploader()

    # Mock document
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_doc.__len__.return_value = 1
    mock_doc.__iter__.return_value = [mock_page]
    mock_fitz_open.return_value = mock_doc

    # Mock page properties
    mock_page.rect.width = 600

    # Mock text blocks for testing column detection
    mock_blocks = [
        {
            "bbox": [50, 100, 250, 150],
            "lines": [
                {
                    "spans": [
                        {
                            "text": "Left column text",
                            "font": "Helvetica",
                            "size": 12,
                            "flags": 0,
                            "color": 0,
                        }
                    ]
                }
            ],
        },
        {
            "bbox": [350, 100, 550, 150],
            "lines": [
                {
                    "spans": [
                        {
                            "text": "Right column text",
                            "font": "Helvetica",
                            "size": 12,
                            "flags": 0,
                            "color": 0,
                        }
                    ]
                }
            ],
        },
    ]

    # Set up the mock to return blocks
    mock_page.get_text.return_value = {"blocks": mock_blocks}

    # Test column detection
    result = uploader._extract_with_column_detection("file.pdf")

    # Verify the results contain both columns
    assert "[Left Column]" in result
    assert "[Right Column]" in result
    assert "Left column text" in result
    assert "Right column text" in result


def test_process_block_with_lines():
    """Test _process_block_with_lines."""
    uploader = FileUploader()

    # ブロックを作成（INTRODUCTIONセクションタイトルを含む）
    block = {
        "bbox": [50, 100, 250, 150],
        "lines": [
            {
                "spans": [
                    {
                        "text": "INTRODUCTION",
                        "font": "Helvetica-Bold",
                        "size": 14,
                        "flags": 4,
                        "color": 0,
                    }
                ]
            },
            {
                "spans": [
                    {
                        "text": "This is the introduction text.",
                        "font": "Helvetica",
                        "size": 12,
                        "flags": 0,
                        "color": 0,
                    }
                ]
            },
        ],
    }

    result = uploader._process_block_with_lines(block)

    # タイトルと本文の間に改行が挿入されていることを確認
    assert "INTRODUCTION\nThis is the introduction text." in result["text"]


def test_process_block_with_lines_figure_caption():
    """Test _process_block_with_lines with figure caption."""
    uploader = FileUploader()

    # 図のキャプションを含むブロックを作成
    block = {
        "bbox": [50, 300, 250, 330],
        "lines": [
            {
                "spans": [
                    {
                        "text": "Fig. 1: Example figure",
                        "font": "Helvetica-Italic",
                        "size": 10,
                        "flags": 2,
                        "color": 0,
                    }
                ]
            }
        ],
    }

    result = uploader._process_block_with_lines(block)

    # 図のキャプションの後に改行が挿入されていることを確認
    assert result["text"].endswith("\n")
    assert "Fig. 1: Example figure\n" in result["text"]


def test_join_blocks_with_spacing_figure_caption():
    """Test _join_blocks_with_spacing with figure caption."""
    uploader = FileUploader()

    blocks = [
        {
            "text": "Fig. 1: Example figure",
            "bbox": [50, 100, 250, 150],
            "x0": 50,
            "y0": 100,
            "y1": 150,
            "is_figure_caption": True,
        },
        {
            "text": "Text after figure",
            "bbox": [50, 170, 250, 200],
            "x0": 50,
            "y0": 170,
            "y1": 200,
        },
    ]

    result = uploader._join_blocks_with_spacing(blocks)

    # 図のキャプションの後に追加の改行が挿入されていることを確認
    assert "\n\n" in result
    # 3つの連続した改行があることを確認（2行分の空白）
    assert "\n\n\n" in result
    # 正しい順序で結合されていることを確認
    assert "Fig. 1: Example figure" in result
    assert "Text after figure" in result


def test_identify_special_blocks():
    """Test _identify_special_blocks."""
    uploader = FileUploader()

    blocks = [
        {
            "text": "INTRODUCTION",
            "bbox": [50, 100, 250, 150],
            "x0": 50,
            "y0": 100,
            "y1": 150,
        },
        {
            "text": "Fig. 1: Example figure",
            "bbox": [50, 200, 250, 230],
            "x0": 50,
            "y0": 200,
            "y1": 230,
        },
        {
            "text": "Table 1: Data summary",
            "bbox": [50, 300, 250, 330],
            "x0": 50,
            "y0": 300,
            "y1": 330,
        },
        {
            "text": "Regular text",
            "bbox": [50, 400, 250, 430],
            "x0": 50,
            "y0": 400,
            "y1": 430,
        },
    ]

    uploader._identify_special_blocks(blocks)

    # 特殊ブロックが正しく識別されていることを確認
    assert blocks[0]["is_section_title"] is True
    assert blocks[1]["is_figure_caption"] is True
    assert blocks[2]["is_table_caption"] is True
    assert blocks[3]["is_section_title"] is False
    assert blocks[3]["is_figure_caption"] is False
    assert blocks[3]["is_table_caption"] is False
