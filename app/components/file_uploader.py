"""Module providing file text extraction functionality.

Provides text extraction functionality for the Paper Podcast Generator application.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz  # PyMuPDF

from app.utils.logger import logger


class FileUploader:
    """Class for uploading files and extracting text."""

    def __init__(self) -> None:
        """Initialize FileUploader."""
        self.temp_dir = Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.supported_text_extensions = [".txt", ".md", ".text"]
        self.supported_pdf_extensions = [".pdf"]
        self.supported_extensions = (
            self.supported_text_extensions + self.supported_pdf_extensions
        )

    def extract_text(self, file: Optional[Any]) -> str:
        """
        Extract text from a file.

        Args:
            file: Uploaded file object

        Returns:
            str: Extracted text
        """
        if file is None:
            return "Please upload a file."

        try:
            # Save temporary file
            temp_path = self._save_uploaded_file(file)

            # Extract text
            return self.extract_text_from_path(temp_path)

        except Exception as e:
            return f"An error occurred: {e}"

    def extract_text_from_path(self, file_path: str) -> str:
        """
        Extract text from a file based on its extension.

        Args:
            file_path (str): Path to the file

        Returns:
            str: Extracted text or error message
        """
        if not file_path or not os.path.exists(file_path):
            return "File not found."

        file_ext = os.path.splitext(file_path)[1].lower()

        # Check if this is a text file
        if file_ext in self.supported_text_extensions:
            return self._extract_from_text_file(file_path)
        # Check if this is a PDF file
        elif file_ext in self.supported_pdf_extensions:
            return self._extract_from_pdf(file_path)
        else:
            return f"Unsupported file type: {file_ext}. Supported types: {', '.join(self.supported_extensions)}"

    def _save_uploaded_file(self, file: Any) -> str:
        """
        Save the uploaded file to the temporary directory.

        Args:
            file: Uploaded file

        Returns:
            str: Path to the saved file
        """
        temp_path = os.path.join(self.temp_dir, os.path.basename(file.name))

        # File object handling
        try:
            with open(temp_path, "wb") as f:
                # Rewind file pointer (just in case)
                if hasattr(file, "seek") and callable(file.seek):
                    try:
                        file.seek(0)
                    except Exception:
                        pass

                # Try direct reading
                if hasattr(file, "read") and callable(file.read):
                    f.write(file.read())
                # If read method is not available, try value
                elif hasattr(file, "value") and isinstance(file.value, bytes):
                    f.write(file.value)
                # If neither is available
                else:
                    raise ValueError("Unsupported file format")

        except Exception as e:
            raise ValueError(f"Failed to save file: {e}")

        return temp_path

    def _extract_from_text_file(self, file_path: str) -> str:
        """
        Extract text from a text file.

        Args:
            file_path (str): Path to the text file

        Returns:
            str: Extracted text
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # UTF-8で開けない場合はSJIS等の日本語エンコーディングを試す
            try:
                with open(file_path, "r", encoding="shift_jis") as f:
                    content = f.read()
                return content
            except Exception as e:
                logger.error(f"Text file reading error: {e}")
                return f"Text file reading failed: {str(e)}"
        except Exception as e:
            logger.error(f"Text file reading error: {e}")
            return f"Text file reading failed: {str(e)}"

    def _extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using PyMuPDF.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        try:
            # 2段組抽出を使用
            return self._extract_with_column_detection(file_path)
        except Exception as e:
            logger.error(f"PyMuPDF extraction with column detection failed: {e}")
            try:
                # 標準の抽出をフォールバックとして使用
                return self._extract_with_pymupdf(file_path)
            except Exception as e2:
                logger.error(f"Standard PyMuPDF extraction failed: {e2}")
                return f"PDF parsing failed: {str(e2)}"

    def _extract_with_pymupdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using standard PyMuPDF method.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        extracted_text = ""
        doc = fitz.open(file_path)

        for i, page in enumerate(doc):
            page_text = page.get_text()
            if page_text:
                extracted_text += f"--- Page {i+1} ---\n{page_text}\n\n"

        return extracted_text

    def _extract_with_column_detection(self, file_path: str) -> str:
        """
        Extract text from a PDF file with column detection using PyMuPDF.
        This method is particularly useful for academic papers with dual columns.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        # PDFファイルを開く
        doc = fitz.open(file_path)

        # 結果を格納するリスト
        all_text = []

        # 各ページを処理
        for page_num, page in enumerate(doc):
            logger.debug(f"Processing page {page_num + 1}/{len(doc)}...")

            # ページの幅を取得
            page_width = page.rect.width

            # テキストブロックを取得
            blocks = page.get_text("dict")["blocks"]

            # テキストを含むブロックのみをフィルタリング
            text_blocks = []
            for block in blocks:
                if "lines" in block:
                    # テキストを持つブロックのみを処理
                    processed_block = self._process_block_with_lines(block)

                    if processed_block["text"].strip():
                        text_blocks.append(processed_block)

            # 列を自動検出
            if text_blocks:
                # ページを2つの領域に分けるための閾値を設定
                # 単純な方法: ページの中央を閾値とする
                threshold = page_width / 2

                # 左列と右列にブロックを分類（ブロックの左端x0を使用）
                left_column_blocks = [
                    block for block in text_blocks if block["x0"] < threshold
                ]
                right_column_blocks = [
                    block for block in text_blocks if block["x0"] >= threshold
                ]

                # y座標でソート（上から下）
                left_column_blocks.sort(key=lambda b: b["y0"])
                right_column_blocks.sort(key=lambda b: b["y0"])

                # 特殊なブロックタイプを識別（図のキャプションなど）
                self._identify_special_blocks(left_column_blocks)
                self._identify_special_blocks(right_column_blocks)

                # 列ごとにテキストを結合（縦方向に離れているブロック間に改行を追加）
                left_text = self._join_blocks_with_spacing(left_column_blocks)
                right_text = self._join_blocks_with_spacing(right_column_blocks)

                # 両方の列が存在する場合は2段組として処理
                if left_text and right_text:
                    page_text = f"--- Page {page_num + 1} ---\n"
                    page_text += f"[Left Column]\n{left_text}\n\n"
                    page_text += f"[Right Column]\n{right_text}\n"
                else:
                    # 片方の列しかない場合は通常のPDFとして処理
                    combined_text = left_text or right_text
                    page_text = f"--- Page {page_num + 1} ---\n{combined_text}\n"
            else:
                # テキストブロックがない場合
                page_text = (
                    f"--- Page {page_num + 1} ---\n[No text found on this page]\n"
                )

            all_text.append(page_text)

        # すべてのテキストを結合
        return "\n".join(all_text)

    def _identify_special_blocks(self, blocks: List[Dict]) -> None:
        """
        特殊なブロック（図のキャプションや表のタイトルなど）を識別し、マークする

        Args:
            blocks (List[Dict]): テキストブロックのリスト
        """
        # 図や表のキャプションを識別
        for block in blocks:
            text = block["text"]
            # 図のキャプションの識別
            if (
                text.startswith("Fig.")
                or text.startswith("Figure ")
                or "hypothetical plans" in text
            ):
                block["is_figure_caption"] = True
            # 表のキャプションの識別
            elif text.startswith("Table "):
                block["is_table_caption"] = True
            # セクションタイトルの識別
            elif any(
                section in text
                for section in [
                    "INTRODUCTION",
                    "RELATED WORK",
                    "METHOD",
                    "RESULTS",
                    "CONCLUSION",
                ]
            ):
                block["is_section_title"] = True
            else:
                # 特殊なブロックではない
                block["is_figure_caption"] = False
                block["is_table_caption"] = False
                block["is_section_title"] = False

    def _process_block_with_lines(self, block: Dict) -> Dict:
        """
        テキストブロックを処理し、セクションタイトルと本文の分離などの特別処理を行う

        Args:
            block (Dict): PDFのテキストブロック

        Returns:
            Dict: 処理されたブロック情報
        """
        x0, y0, x1, y1 = block["bbox"]
        processed_text = ""

        # スタイルの変更を検出するための変数
        prev_font = None
        prev_size = None
        prev_flags = None
        prev_color = None

        # 行ごとに処理
        for line_idx, line in enumerate(block["lines"]):
            line_text = ""

            # 各スパンを処理
            for span_idx, span in enumerate(line["spans"]):
                # スパンのスタイル情報を取得
                font = span.get("font", "")
                size = span.get("size", 0)
                flags = span.get("flags", 0)
                color = span.get("color", 0)

                # スタイルの変更を検出（特にフォントサイズや太字などの変更）
                style_changed = prev_font is not None and (
                    font != prev_font
                    or abs(size - prev_size) > 1  # サイズの大きな変更
                    or flags != prev_flags  # 太字・斜体などの変更
                    or color != prev_color  # 色の変更
                )

                # スタイル変更があり、これがタイトルと本文の境界と思われる場合
                if style_changed and span_idx == 0 and line_idx > 0:
                    # 前のスタイルが大きいサイズまたは太字で、現在が通常テキスト
                    if prev_size > size or (
                        prev_flags is not None and (prev_flags & 4) != 0
                    ):  # 4は太字フラグ
                        processed_text += "\n"  # タイトルと本文の間に改行を挿入

                # テキストを追加
                line_text += span["text"]

                # スタイル情報を更新
                prev_font = font
                prev_size = size
                prev_flags = flags
                prev_color = color

            # 行テキストを追加
            processed_text += line_text

        # セクションタイトルと本文の特別な処理
        # 特定のパターンを検出して改行を挿入
        for section_title in [
            "INTRODUCTION",
            "RELATED WORK",
            "METHOD",
            "RESULTS",
            "CONCLUSION",
            "DISCUSSION",
        ]:
            # セクションタイトルの直後に本文が続く場合、間に改行を挿入
            if section_title in processed_text and not processed_text.endswith(
                section_title
            ):
                pos = processed_text.find(section_title) + len(section_title)
                if pos < len(processed_text) and processed_text[pos] not in ["\n", " "]:
                    processed_text = processed_text[:pos] + "\n" + processed_text[pos:]

        # 図のキャプションの処理
        if processed_text.startswith("Fig.") or "hypothetical plans" in processed_text:
            # キャプションの後に改行を確保
            if not processed_text.endswith("\n"):
                processed_text += "\n"

        return {
            "text": processed_text,
            "bbox": block["bbox"],
            "x0": x0,  # 左端のx座標（カラム判定用）
            "y0": y0,  # 上端のy座標（縦方向ソート用）
            "y1": y1,  # 下端のy座標（改行判定用）
        }

    def _join_blocks_with_spacing(self, blocks: List[Dict]) -> str:
        """
        テキストブロックを結合し、縦方向に離れたブロック間に適切な改行を挿入する

        Args:
            blocks (List[Dict]): テキストブロックのリスト

        Returns:
            str: 適切な改行を含む結合テキスト
        """
        if not blocks:
            return ""

        # 垂直方向の間隔閾値（通常は前ブロック高さの1.5倍以上離れていれば追加の改行を挿入）
        VERTICAL_GAP_FACTOR = 1.5
        # 図のキャプション後の閾値は低めに設定（わずかな間隔でも改行を挿入）
        FIGURE_CAPTION_GAP_FACTOR = 0.3

        result = []
        prev_block = None

        for i, block in enumerate(blocks):
            if prev_block:
                # 前のブロックが図のキャプションかどうかを確認
                is_prev_figure = (
                    prev_block.get("is_figure_caption", False)
                    or "Fig." in prev_block["text"]
                    or "hypothetical plans" in prev_block["text"]
                )

                # 前のブロックとの垂直方向の間隔を計算
                prev_bottom = prev_block["y1"]
                current_top = block["y0"]
                gap = current_top - prev_bottom

                # 前のブロックの高さを計算
                prev_height = prev_block["y1"] - prev_block["y0"]

                # 使用する間隔閾値を決定
                gap_factor = (
                    FIGURE_CAPTION_GAP_FACTOR if is_prev_figure else VERTICAL_GAP_FACTOR
                )

                # 間隔が閾値以上なら追加の改行を挿入
                if gap > (prev_height * gap_factor):
                    # 図のキャプションの後は2行の改行を入れる
                    if is_prev_figure:
                        result.append("\n\n")  # 図のキャプション後は2行の空白
                    else:
                        result.append("\n")  # 通常のブロック間は1行

            # テキストを追加
            result.append(block["text"])
            prev_block = block

        return "\n".join(result)

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List[str]: List of supported file extensions
        """
        return self.supported_extensions
