"""Module providing content extraction functionality.

Provides content extraction functionality for the Paper Podcast Generator application.
Supports extracting text content from various sources including files (PDF, text) and URLs.
"""

import io
import os
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import urlparse

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
    def is_url(cls, text: Optional[str]) -> bool:
        """
        Check if the input text is a valid HTTP/HTTPS URL.

        Args:
            text (Optional[str]): Text to check

        Returns:
            bool: True if text is a valid HTTP/HTTPS URL, False otherwise
        """
        if not text or not isinstance(text, str):
            return False

        try:
            parsed = urlparse(text.strip())
            # Only accept HTTP and HTTPS schemes for web content extraction
            return bool(parsed.scheme in ["http", "https"] and parsed.netloc)
        except Exception:
            return False

    @classmethod
    def extract_from_url(cls, url: str) -> str:
        """
        Extract text content from a URL using MarkItDown web converters.

        Args:
            url (str): URL to extract content from

        Returns:
            str: Extracted text content
        """
        if not cls.is_url(url):
            return "Invalid URL format."

        try:
            logger.debug(f"Processing URL: {url}")
            result = _markdown_converter.convert(url)

            # Extract the text content from the conversion result
            markdown_content = result.text_content
            logger.debug(f"URL successfully converted to Markdown: {url}")
            return markdown_content or ""

        except Exception as e:
            logger.error(f"URL to Markdown conversion failed: {e}")
            return f"URL conversion error: {str(e)}"

    @classmethod
    def extract_file_content(cls, file_obj: Any) -> Tuple[Optional[str], Optional[bytes]]:
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
                original_extension = os.path.splitext(Path(file_obj.name).name)[1].lower()
                # 拡張子がない場合はデフォルト値を使用
                if not original_extension:
                    original_extension = ".txt"

            # ファイル内容を読み込む
            file_content = None
            if hasattr(file_obj, "read") and callable(file_obj.read):
                # 現在位置を記録
                pos = file_obj.tell() if hasattr(file_obj, "tell") and callable(file_obj.tell) else 0

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
                result = _markdown_converter.convert(pdf_stream, stream_info=stream_info)

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

    @classmethod
    def append_text_with_source(cls, existing_text: str, new_text: str, source: str, add_separator: bool = True) -> str:
        """
        Append new text to existing text with source information.

        Args:
            existing_text (str): Current text content
            new_text (str): New text to append
            source (str): Source name (filename or URL)
            add_separator (bool): Whether to add separator with source info

        Returns:
            str: Combined text with source information
        """
        if not new_text or not new_text.strip():
            return existing_text

        # Prepare the new text content
        content_to_append = new_text.strip()

        if add_separator:
            # Create markdown-style separator with source information
            separator = f"\n\n---\n**Source: {source}**\n\n"
            result = existing_text.rstrip() + separator + content_to_append if existing_text.strip() else f"**Source: {source}**\n\n" + content_to_append
        else:
            # Just append with minimal spacing
            result = existing_text.rstrip() + "\n\n" + content_to_append if existing_text.strip() else content_to_append

        return result

    @classmethod
    def get_source_name_from_file(cls, file_obj: Any) -> str:
        """
        Extract source name from file object.

        Args:
            file_obj: Gradio file object

        Returns:
            str: Source name for display
        """
        if file_obj is None:
            return "Unknown File"

        # Handle list format
        if isinstance(file_obj, list) and len(file_obj) > 0:
            file_obj = file_obj[0]

        if hasattr(file_obj, "name"):
            # Get just the filename from the path
            from pathlib import Path

            return Path(file_obj.name).name

        return "Uploaded File"
