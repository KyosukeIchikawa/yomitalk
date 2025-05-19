"""Module providing file text extraction functionality.

Provides text extraction functionality for the Paper Podcast Generator application.
"""

import os
from typing import List

from yomitalk.utils.logger import logger
from yomitalk.utils.pdf_extractor import PDFExtractor


class FileUploader:
    """Class for uploading files and extracting text."""

    def __init__(self, temp_dir=None) -> None:
        """
        Initialize FileUploader.

        Args:
            temp_dir (Optional[Path]): Session-specific temporary directory path.
                If not provided, defaults to "data/temp"
        """
        self.supported_text_extensions = [".txt", ".md", ".text", ".tmp"]
        self.supported_pdf_extensions = [".pdf"]
        self.supported_extensions = (
            self.supported_text_extensions + self.supported_pdf_extensions
        )
        self.pdf_extractor = PDFExtractor()

        # Set temporary directory
        from pathlib import Path

        self.temp_dir = Path(temp_dir) if temp_dir else Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

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
            return self.pdf_extractor.extract_from_pdf(file_path)
        else:
            return f"Unsupported file type: {file_ext}. Supported types: {', '.join(self.supported_extensions)}"

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

    def handle_file_upload(self, file_obj):
        """
        Process file uploads.

        Properly handles file objects from Gradio's file upload component.

        Args:
            file_obj: Gradio's file object

        Returns:
            str: Path to the temporary file
        """
        if file_obj is None:
            return None

        try:
            # Get filename
            if isinstance(file_obj, list) and len(file_obj) > 0:
                file_obj = file_obj[0]  # Get first element if it's a list

            # セキュリティのため、オリジナルファイル名は使用せず、一意のIDを生成
            # ただし、元のファイル拡張子は保持する
            import os
            import uuid
            from pathlib import Path

            original_extension = ".txt"  # デフォルト拡張子
            if hasattr(file_obj, "name"):
                # 元のファイルの拡張子を取得
                original_extension = os.path.splitext(Path(file_obj.name).name)[1]
                # 拡張子がない場合はデフォルト値を使用
                if not original_extension:
                    original_extension = ".txt"

            # 安全なファイル名を生成（UUIDと元の拡張子を組み合わせる）
            filename = f"uploaded_{uuid.uuid4().hex}{original_extension}"

            # セッション固有のtemp_dirを使用
            temp_path = self.temp_dir / filename

            # Get and save file data
            if hasattr(file_obj, "read") and callable(file_obj.read):
                with open(temp_path, "wb") as f:
                    f.write(file_obj.read())
            elif hasattr(file_obj, "name"):
                with open(temp_path, "wb") as f:
                    with open(file_obj.name, "rb") as source:
                        f.write(source.read())

            return str(temp_path)

        except Exception as e:
            logger.error(f"File processing error: {e}")
            return None

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List[str]: List of supported file extensions
        """
        return self.supported_extensions
