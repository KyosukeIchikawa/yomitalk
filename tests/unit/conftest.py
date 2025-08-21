"""Common test fixtures for unit tests."""

from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    """Fixture providing the path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_text_file(tmp_path):
    """Fixture providing a sample text file for testing."""
    file_path = tmp_path / "sample.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("This is sample text for testing.\nLine 2 of the sample text.")
    return file_path


@pytest.fixture
def sample_pdf_content():
    """Fixture providing sample content that would be extracted from a PDF."""
    return """Sample PDF Content

    Abstract
    This is a sample abstract for testing PDF extraction.

    Introduction
    This sample document tests the content extraction capabilities.

    Conclusion
    Tests are important for ensuring code quality.
    """


@pytest.fixture
def sample_script():
    """Fixture providing a sample podcast script for testing."""
    return """東北きりたん: こんにちは、今回のテーマは機械学習についてです。
ずんだもん: よろしくお願いします！機械学習について教えてください。
東北きりたん: 機械学習は、コンピュータがデータから学習し、予測や判断を行う技術です。
ずんだもん: なるほど！どんな応用例がありますか？
東北きりたん: 画像認識、自然言語処理、レコメンデーションシステムなど様々です。
ずんだもん: すごいのだ！これからも発展していきそうですね。
東北きりたん: そうですね。今後の発展が期待される分野です。
"""
