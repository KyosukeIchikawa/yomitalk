"""Module providing file text extraction functionality.

Provides text extraction functionality for the Paper Podcast Generator application.
"""

import os
from pathlib import Path
from typing import Any, List, Optional

from app.utils.logger import logger
from app.utils.pdf_extractor import PDFExtractor


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
        self.pdf_extractor = PDFExtractor()

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
            return self.pdf_extractor.extract_from_pdf(file_path)
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

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported file extensions.

        Returns:
            List[str]: List of supported file extensions
        """
        return self.supported_extensions
