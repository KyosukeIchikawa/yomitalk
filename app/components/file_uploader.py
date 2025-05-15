"""Module providing file text extraction functionality.

Provides text extraction functionality for the Paper Podcast Generator application.
"""

import os
from pathlib import Path
from typing import List

from app.utils.logger import logger
from app.utils.pdf_extractor import PDFExtractor


class FileUploader:
    """Class for uploading files and extracting text."""

    def __init__(self) -> None:
        """Initialize FileUploader."""
        self.temp_dir = Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.supported_text_extensions = [".txt", ".md", ".text", ".tmp"]
        self.supported_pdf_extensions = [".pdf"]
        self.supported_extensions = (
            self.supported_text_extensions + self.supported_pdf_extensions
        )
        self.pdf_extractor = PDFExtractor()

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

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List[str]: List of supported file extensions
        """
        return self.supported_extensions
