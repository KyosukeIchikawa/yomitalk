"""Module providing PDF text extraction functionality.

Provides PDF text extraction with Markdown conversion for the Paper Podcast Generator application.
"""

import argparse
import os
import sys

from markitdown import MarkItDown
from markitdown._document import DocumentConverterResult

from app.utils.logger import logger


class PDFExtractor:
    """Class for extracting text from PDF files with markdown conversion."""

    def __init__(self):
        """Initialize the PDFExtractor with MarkItDown converter."""
        self.markdown_converter = MarkItDown()

    def extract_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using MarkItDown.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text in Markdown format
        """
        try:
            # PDFからMarkdownへの変換
            logger.debug(f"Processing PDF file: {file_path}")
            result: DocumentConverterResult = self.markdown_converter.convert(file_path)
            # DocumentConverterResultからテキスト内容を取得
            markdown_content: str = result.text_content
            logger.debug("PDF successfully converted to Markdown")
            return markdown_content
        except Exception as e:
            # エラーが発生した場合はログに記録して再度発生させる
            logger.error(f"PDF to Markdown conversion failed: {e}")
            raise


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
