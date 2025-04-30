"""Module providing PDF text extraction functionality.

Provides PDF extraction functionality for the Paper Podcast Generator application.
"""

import os
from pathlib import Path
from typing import Any, Optional

# PyMuPDFはSWIG関連の警告を引き起こすため、完全に削除します
# fitz (PyMuPDF) は任意の依存関係であり、PDFパーサーとしてPyPDFとpdfplumberで十分です

import pdfplumber
from pypdf import PdfReader

from app.utils.logger import logger


class PDFUploader:
    """Class for uploading PDF files and extracting text."""

    def __init__(self) -> None:
        """Initialize PDFUploader."""
        self.temp_dir = Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract_text(self, file: Optional[Any]) -> str:
        """
        Extract text from a PDF file.

        Args:
            file: Uploaded PDF file object

        Returns:
            str: Extracted text
        """
        if file is None:
            return "Please upload a PDF file."

        try:
            # Save temporary file
            temp_path = self._save_uploaded_file(file)

            # Extract text
            return self.extract_text_from_path(temp_path)

        except Exception as e:
            return f"An error occurred: {e}"

    def extract_text_from_path(self, file_path: str) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text or error message
        """
        if not file_path or not os.path.exists(file_path):
            return "PDF file not found."

        try:
            # First attempt using PyPDF
            return self._extract_with_pypdf(file_path)
        except Exception as e1:
            logger.error(f"PyPDF extraction failed: {e1}")
            try:
                # Second attempt using pdfplumber
                return self._extract_with_pdfplumber(file_path)
            except Exception as e2:
                logger.error(f"pdfplumber extraction failed: {e2}")
                return f"PDF parsing failed: {str(e2)}"

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

    def _extract_with_pypdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file using PyPDF.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        extracted_text = ""
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"--- Page {i+1} ---\n{page_text}\n\n"

        return extracted_text

    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """
        Extract text from a PDF file using pdfplumber.

        Args:
            file_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        extracted_text = ""
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"--- Page {i+1} ---\n{page_text}\n\n"

        return extracted_text
