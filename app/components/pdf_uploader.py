"""Module for processing and manipulating PDF files.

Provides functions for PDF file uploads, text extraction, and temporary file management.
"""

import os
from pathlib import Path
from typing import Any, Optional

import pdfplumber
import pypdf


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

    def extract_text_from_path(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file at the specified path.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            str: Extracted text
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return "PDF file not found."

        try:
            # Extract text using both pypdf and pdfplumber
            extracted_text = self._extract_with_pypdf(pdf_path)

            # If pypdf fails, try pdfplumber
            if not extracted_text:
                extracted_text = self._extract_with_pdfplumber(pdf_path)

            # Return extracted text
            if not extracted_text.strip():
                return (
                    "Unable to extract text. Please check if the PDF has text layers."
                )

            return extracted_text

        except Exception as e:
            return f"An error occurred during text extraction: {e}"

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

    def _extract_with_pypdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF using pypdf.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            str: Extracted text, empty string if failed
        """
        extracted_text = ""
        try:
            with open(pdf_path, "rb") as f:
                pdf_reader = pypdf.PdfReader(f)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    extracted_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            return extracted_text
        except Exception as e:
            print(f"pypdf extraction error: {e}")
            return ""

    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text from a PDF using pdfplumber.

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            str: Extracted text, empty string if failed
        """
        extracted_text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    extracted_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            return extracted_text
        except Exception as e:
            return f"PDF parsing failed: {e}"
