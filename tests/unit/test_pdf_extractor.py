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
                self.extractor,
                "_extract_with_column_detection",
                side_effect=Exception("Simulated column detection failure"),
            ):
                # Call the method being tested
                result = self.extractor.extract_from_pdf(temp_file_path)

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

            # Patch the join_blocks_with_spacing method to verify it's called with the right args
            with patch.object(
                self.extractor,
                "_join_blocks_with_spacing",
                # テストのために単純に結合して返す
                side_effect=lambda blocks: "\n".join(block["text"] for block in blocks),
            ) as mock_join:
                # Call the method being tested
                result = self.extractor._extract_with_column_detection(temp_file_path)

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

        # ブロック間の垂直ギャップが大きいため、追加の改行が挿入されているか確認
        assert (
            result == "First block\n\nSecond block"
            or result == "First block\n\n\nSecond block"
        )
        # 改行が少なくとも1つ以上あることを確認
        assert "\n\n" in result


def test_init():
    """Test PDFExtractor initialization."""
    extractor = PDFExtractor()
    assert hasattr(extractor, "_extract_with_column_detection")
    assert hasattr(extractor, "_extract_with_pymupdf")


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
def test_extract_with_pymupdf(mock_fitz_open):
    """Test _extract_with_pymupdf method."""
    extractor = PDFExtractor()

    # Setup mock document with pages
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 content"
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "Page 2 content"

    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [mock_page1, mock_page2]
    mock_fitz_open.return_value = mock_doc

    result = extractor._extract_with_pymupdf("file.pdf")

    assert "--- Page 1 ---" in result
    assert "Page 1 content" in result
    assert "--- Page 2 ---" in result
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

    # Test column detection
    result = extractor._extract_with_column_detection("file.pdf")

    # Verify the results contain both columns
    assert "[Left Column]" in result
    assert "[Right Column]" in result
    assert "Left column text" in result
    assert "Right column text" in result


def test_process_block_with_lines():
    """Test _process_block_with_lines."""
    extractor = PDFExtractor()

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

    result = extractor._process_block_with_lines(block)

    # タイトルと本文の間に改行が挿入されていることを確認
    assert "INTRODUCTION\nThis is the introduction text." in result["text"]


def test_process_block_with_lines_figure_caption():
    """Test _process_block_with_lines with figure caption."""
    extractor = PDFExtractor()

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

    result = extractor._process_block_with_lines(block)

    # 図のキャプションの後に改行が挿入されていることを確認
    assert result["text"].endswith("\n")
    assert "Fig. 1: Example figure\n" in result["text"]


def test_join_blocks_with_spacing_figure_caption():
    """Test _join_blocks_with_spacing with figure caption."""
    extractor = PDFExtractor()

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

    result = extractor._join_blocks_with_spacing(blocks)

    # 図のキャプションの後に追加の改行が挿入されていることを確認
    assert "\n\n" in result
    # 正しい順序で結合されていることを確認
    assert "Fig. 1: Example figure" in result
    assert "Text after figure" in result


def test_identify_special_blocks():
    """Test _identify_special_blocks."""
    extractor = PDFExtractor()

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

    extractor._identify_special_blocks(blocks)

    # 特殊ブロックが正しく識別されていることを確認
    assert blocks[0]["is_section_title"] is True
    assert blocks[1]["is_figure_caption"] is True
    assert blocks[2]["is_table_caption"] is True
    assert blocks[3]["is_section_title"] is False
    assert blocks[3]["is_figure_caption"] is False
    assert blocks[3]["is_table_caption"] is False
