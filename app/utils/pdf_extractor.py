"""Module providing PDF text extraction functionality.

Provides advanced PDF text extraction with column detection for the Paper Podcast Generator application.
"""

import argparse
import os
import sys
from typing import Dict, List

import fitz  # PyMuPDF

from app.utils.logger import logger


class PDFExtractor:
    """Class for extracting text from PDF files with column detection."""

    def extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using PyMuPDF.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        # 2段組対応の抽出方法
        return self._extract_with_column_detection(file_path)

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

                # 列ごとにテキストを結合（縦方向に離れているブロック間に改行を追加）
                left_text = self._join_blocks_with_spacing(left_column_blocks)
                right_text = self._join_blocks_with_spacing(right_column_blocks)

                # 両方の列が存在する場合は2段組として処理
                if left_text and right_text:
                    page_text = f"## Page {page_num + 1}\n"
                    page_text += f"### Left Column\n{left_text}\n\n"
                    page_text += f"### Right Column\n{right_text}\n"
                else:
                    # 片方の列しかない場合は通常のPDFとして処理
                    combined_text = left_text or right_text
                    page_text = f"## Page {page_num + 1}\n{combined_text}\n"
            else:
                # テキストブロックがない場合
                page_text = f"## Page {page_num + 1}\n[No text found on this page]\n"

            all_text.append(page_text)

        # すべてのテキストを結合
        return "\n".join(all_text)

    def _process_block_with_lines(self, block: Dict) -> Dict:
        """
        テキストブロックを処理し、スタイル変更に基づいて改行を適切に挿入

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

                # スタイル変更があり、行の先頭にあるスパンの場合
                if style_changed and span_idx == 0 and line_idx > 0:
                    # スタイル変化に基づいて改行を挿入
                    # 太字から普通、または大きいサイズから小さいサイズへの変化はタイトルから本文への移行の可能性
                    if prev_size > size or (
                        prev_flags is not None and (prev_flags & 4) != 0
                    ):
                        processed_text += "\n"

                # テキストを追加
                line_text += span["text"]

                # スタイル情報を更新
                prev_font = font
                prev_size = size
                prev_flags = flags
                prev_color = color

            # 行テキストを追加
            processed_text += line_text

        # 空間的特性を記録
        return {
            "text": processed_text,
            "bbox": block["bbox"],
            "x0": x0,  # 左端のx座標（カラム判定用）
            "y0": y0,  # 上端のy座標（縦方向ソート用）
            "y1": y1,  # 下端のy座標（改行判定用）
            "height": y1 - y0,  # ブロックの高さ
            "width": x1 - x0,  # ブロックの幅
        }

    def _join_blocks_with_spacing(self, blocks: List[Dict]) -> str:
        """
        テキストブロックを改行を挿入つつ結合する

        Args:
            blocks (List[Dict]): テキストブロックのリスト

        Returns:
            str: 改行を含む結合テキスト
        """
        if not blocks:
            return ""

        # 常にブロック間に2つ分の改行を挿入
        return "\n\n".join(block["text"] for block in blocks)


def configure_logging():
    """コンソールにログを出力するシンプルな設定"""
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main():
    """メイン関数: コマンドライン引数からPDFを読み込み、テキスト抽出を実行"""
    parser = argparse.ArgumentParser(description="PDFからテキストを抽出するツール")
    parser.add_argument("pdf_path", help="処理するPDFファイルのパス")
    parser.add_argument("-o", "--output", help="出力テキストファイルのパス（省略時は標準出力）")
    parser.add_argument("-d", "--debug", action="store_true", help="デバッグモードを有効化")

    args = parser.parse_args()

    # デバッグモードの場合はログレベルを設定
    if args.debug:
        configure_logging()

    # PDFファイルの存在確認
    if not os.path.exists(args.pdf_path):
        logger.error(f"エラー: '{args.pdf_path}' は存在しません")
        return 1

    try:
        # PDFからテキストを抽出
        extractor = PDFExtractor()
        extracted_text = extractor.extract_from_pdf(args.pdf_path)

        # 出力先の決定
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            logger.info(f"テキストを '{args.output}' に保存しました")
        else:
            logger.info(extracted_text)

        return 0
    except Exception as e:
        logger.error(f"エラー: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
