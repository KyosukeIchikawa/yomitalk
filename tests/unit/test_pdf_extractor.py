"""Test module for the PDF Extractor."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from app.utils.pdf_extractor import PDFExtractor


class TestPDFExtractor:
    """Test class for the PDFExtractor."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.extractor = PDFExtractor()

    @patch("app.utils.pdf_extractor.fitz.open")
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

            # _process_block_with_linesメソッドをモック化
            with patch.object(
                self.extractor,
                "_process_block_with_lines",
                side_effect=lambda block: {
                    "text": block["lines"][0]["spans"][0]["text"],
                    "bbox": block["bbox"],
                    "x0": block["bbox"][0],
                    "y0": block["bbox"][1],
                    "y1": block["bbox"][3],
                    "height": block["bbox"][3] - block["bbox"][1],
                    "width": block["bbox"][2] - block["bbox"][0],
                },
            ):
                # Patch the join_blocks_with_spacing method to verify it's called with the right args
                with patch.object(
                    self.extractor,
                    "_join_blocks_with_spacing",
                    # テストのために単純に結合して返す
                    side_effect=lambda blocks: "\n".join(
                        block["text"] for block in blocks
                    ),
                ) as mock_join:
                    # Call the method being tested
                    result = self.extractor._extract_with_column_detection(
                        temp_file_path
                    )

                    # Verify the results
                    assert "### Left Column" in result
                    assert "Left column text 1" in result
                    assert "Left column text 2" in result
                    assert "### Right Column" in result
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

        result = self.extractor._join_blocks_with_spacing(blocks)

        # 常に2つのブロック間に"\n\n"が入ることを確認
        assert result == "First block\n\nSecond block"


def test_init():
    """Test PDFExtractor initialization."""
    extractor = PDFExtractor()
    assert hasattr(extractor, "_extract_with_column_detection")
    # _extract_with_pymupdfは削除されたので、チェックしない


@patch("app.utils.pdf_extractor.fitz.open")
def test_class_extract_from_pdf(mock_fitz_open):
    """Test successful text extraction from a PDF file using PyMuPDF."""
    extractor = PDFExtractor()

    # Create a mock file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        temp_file_path = temp_file.name

    try:
        # Mock extract_with_column_detection instead of using real implementation
        with patch.object(
            extractor,
            "_extract_with_column_detection",
            return_value="## Page 1\nTest content\n",
        ):
            result = extractor.extract_from_pdf(temp_file_path)

            # Verify the results
            assert "## Page 1" in result
            assert "Test content" in result
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@patch("fitz.open")
def test_extract_from_pdf(mock_fitz_open):
    """Test extract_from_pdf method."""
    extractor = PDFExtractor()

    # Set up the mock
    mock_doc = MagicMock()
    mock_fitz_open.return_value = mock_doc

    # Mock extract_with_column_detection
    with patch.object(
        extractor, "_extract_with_column_detection", return_value="PDF Content"
    ):
        result = extractor.extract_from_pdf("file.pdf")
        assert result == "PDF Content"


@patch("fitz.open")
def test_simple_pdf_extraction(mock_fitz_open):
    """Test simple PDF extraction with default method."""
    extractor = PDFExtractor()

    # Setup mock document with pages
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 content"
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Page 2 content"

    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [mock_page1, mock_page2]
    mock_doc.__len__.return_value = 2
    mock_fitz_open.return_value = mock_doc

    # _extract_with_pymupdfが削除されたので、代わりにextract_from_pdfをテスト
    with patch.object(
        extractor,
        "_extract_with_column_detection",
        side_effect=lambda path: "## Page 1\nPage 1 content\n\n## Page 2\nPage 2 content",
    ):
        result = extractor.extract_from_pdf("file.pdf")

        # 期待する出力形式をチェック
        assert "## Page 1" in result
        assert "Page 1 content" in result
        assert "## Page 2" in result
        assert "Page 2 content" in result


@patch("fitz.open")
def test_extract_with_column_detection_detailed(mock_fitz_open):
    """Test _extract_with_column_detection in more detail."""
    extractor = PDFExtractor()

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

    # _process_block_with_linesメソッドをモック化
    with patch.object(
        extractor,
        "_process_block_with_lines",
        side_effect=lambda block: {
            "text": "Left column text"
            if block["bbox"][0] < 300
            else "Right column text",
            "bbox": block["bbox"],
            "x0": block["bbox"][0],
            "y0": block["bbox"][1],
            "y1": block["bbox"][3],
            "height": block["bbox"][3] - block["bbox"][1],
            "width": block["bbox"][2] - block["bbox"][0],
        },
    ):
        # Test column detection
        result = extractor._extract_with_column_detection("file.pdf")

        # Verify the results contain both columns
        assert "### Left Column" in result
        assert "### Right Column" in result
        assert "Left column text" in result
        assert "Right column text" in result


def test_process_block_with_lines():
    """Test _process_block_with_lines."""
    extractor = PDFExtractor()

    # スタイル変更を含むブロックを作成
    block = {
        "bbox": [50, 100, 250, 150],
        "lines": [
            {
                "spans": [
                    {
                        "text": "Title",
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
                        "text": "Regular text",
                        "font": "Helvetica",
                        "size": 12,
                        "flags": 0,
                        "color": 0,
                    }
                ]
            },
        ],
    }

    result = extractor._process_block_with_lines(block)

    # ブロックの空間的特性が正しく計算されていることを確認
    assert "height" in result
    assert "width" in result
    assert result["height"] == 50  # y1 - y0 = 150 - 100
    assert result["width"] == 200  # x1 - x0 = 250 - 50

    # テキストにスタイル変更に基づく改行が含まれていることを確認
    assert "Title" in result["text"]
    assert "Regular text" in result["text"]


def test_process_block_with_lines_with_style_changes():
    """Test _process_block_with_lines with style changes."""
    extractor = PDFExtractor()

    # スタイル変更を伴うブロックを作成
    block = {
        "bbox": [50, 100, 250, 150],
        "lines": [
            {
                "spans": [
                    {
                        "text": "Bold text",
                        "font": "Helvetica-Bold",
                        "size": 12,
                        "flags": 4,  # Bold flag
                        "color": 0,
                    }
                ]
            },
            {
                "spans": [
                    {
                        "text": "Regular text",
                        "font": "Helvetica",
                        "size": 12,
                        "flags": 0,  # Regular flag
                        "color": 0,
                    }
                ]
            },
        ],
    }

    result = extractor._process_block_with_lines(block)

    # 太字からレギュラーへのスタイル変更の後に改行が挿入されることを確認
    assert "Bold text\nRegular text" in result["text"]
