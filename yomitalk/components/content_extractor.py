"""Module providing content extraction functionality.

Provides content extraction functionality for the Paper Podcast Generator application.
Supports extracting text content from various sources including files (PDF, text) and URLs.
"""

import io
import os
from pathlib import Path
from typing import Any, Optional, Tuple

from markitdown import MarkItDown, StreamInfo

from yomitalk.utils.logger import logger

# Global markdown converter shared by all instances and users
_markdown_converter = MarkItDown()


class ContentExtractor:
    """Class for extracting text content from various sources."""

    # Class constants for supported file extensions
    SUPPORTED_TEXT_EXTENSIONS = [".txt", ".md", ".text", ".tmp"]
    SUPPORTED_PDF_EXTENSIONS = [".pdf"]
    SUPPORTED_EXTENSIONS = SUPPORTED_TEXT_EXTENSIONS + SUPPORTED_PDF_EXTENSIONS

    @classmethod
    def extract_file_content(
        cls, file_obj: Any
    ) -> Tuple[Optional[str], Optional[bytes]]:
        """
        メモリ上でファイルコンテンツを抽出します。

        Args:
            file_obj: Gradioのファイルオブジェクト

        Returns:
            tuple: (ファイル拡張子, ファイルコンテンツのバイト列)
        """
        if file_obj is None:
            return None, None

        try:
            # リスト形式の場合は最初の要素を取得
            if isinstance(file_obj, list) and len(file_obj) > 0:
                file_obj = file_obj[0]

            # ファイル拡張子を取得
            original_extension = ".txt"  # デフォルト拡張子
            if hasattr(file_obj, "name"):
                # 元のファイルの拡張子を取得
                original_extension = os.path.splitext(Path(file_obj.name).name)[
                    1
                ].lower()
                # 拡張子がない場合はデフォルト値を使用
                if not original_extension:
                    original_extension = ".txt"

            # ファイル内容を読み込む
            file_content = None
            if hasattr(file_obj, "read") and callable(file_obj.read):
                # 現在位置を記録
                if hasattr(file_obj, "tell") and callable(file_obj.tell):
                    pos = file_obj.tell()
                else:
                    pos = 0

                # コンテンツを読み込み
                file_content = file_obj.read()

                # 位置を戻す（ファイルを再利用可能にする）
                if hasattr(file_obj, "seek") and callable(file_obj.seek):
                    file_obj.seek(pos)
            elif hasattr(file_obj, "name") and os.path.exists(file_obj.name):
                # ファイルパスからコンテンツを読み込み
                with open(file_obj.name, "rb") as source:
                    file_content = source.read()

            return original_extension, file_content

        except Exception as e:
            logger.error(f"File content extraction error: {e}")
            return None, None

    @classmethod
    def extract_text(cls, file_obj: Any) -> str:
        """
        メモリ上でファイルからテキストを抽出します。
        ファイルをディスクに保存せずに直接処理します。

        Args:
            file_obj: Gradioのファイルオブジェクト

        Returns:
            str: 抽出されたテキスト
        """
        if file_obj is None:
            return "Please upload a file."

        try:
            # ファイルコンテンツを取得
            result = cls.extract_file_content(file_obj)
            file_ext, file_content = result

            if file_content is None or file_ext is None:
                return "Failed to read file."

            # ファイルの種類に応じて処理
            if isinstance(file_ext, str):
                return cls.extract_from_bytes(file_content, file_ext)

        except Exception as e:
            logger.error(f"File processing error: {e}")
            return f"Error processing file: {str(e)}"

    @classmethod
    def extract_from_bytes(cls, file_content: bytes, file_ext: str) -> str:
        """
        Extract text from file content in memory.

        Args:
            file_content (bytes): File content as bytes
            file_ext (str): File extension (e.g., ".pdf", ".txt")

        Returns:
            str: Extracted text content
        """
        # テキストファイル
        if file_ext in cls.SUPPORTED_TEXT_EXTENSIONS:
            # テキストの解読を試みる
            try:
                # UTF-8で試みる
                return file_content.decode("utf-8")
            except UnicodeDecodeError:
                # Shift-JISで試みる
                try:
                    return file_content.decode("shift_jis")
                except Exception:
                    # その他のエンコーディングで試みる
                    try:
                        # CP932（Windows日本語）
                        return file_content.decode("cp932")
                    except Exception as e:
                        logger.error(f"Text decoding error: {e}")
                        return f"Text file decoding failed: {str(e)}"

        # PDFファイル
        elif file_ext in cls.SUPPORTED_PDF_EXTENSIONS:
            try:
                # BytesIOオブジェクトとしてバイト列をラップする
                pdf_stream = io.BytesIO(file_content)

                # StreamInfoを作成して、これがPDFであることを明示する
                stream_info = StreamInfo(extension=".pdf", mimetype="application/pdf")

                # メモリ上のPDFストリームを直接変換
                logger.debug("Processing PDF from memory stream")
                result = _markdown_converter.convert(
                    pdf_stream, stream_info=stream_info
                )

                # 変換結果からテキストコンテンツを取得
                markdown_content = result.text_content
                logger.debug("PDF memory stream successfully converted to Markdown")
                return markdown_content or ""
            except Exception as e:
                # エラーが発生した場合はログに記録して再度発生させる
                logger.error(f"PDF memory stream to Markdown conversion failed: {e}")
                return f"PDF conversion error: {str(e)}"
        else:
            return f"Unsupported file type: {file_ext}. Supported types: {', '.join(cls.SUPPORTED_EXTENSIONS)}"
