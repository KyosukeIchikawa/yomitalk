"""Unit tests for text utility functions."""

import pytest

from yomitalk.utils.text_utils import is_romaji_readable


class TestTextUtils:
    """Test class for text utility functions."""

    @pytest.mark.parametrize(
        "input_text, expected_result",
        [
            ("HELLO", False),  # 英単語はローマ字読みできない
            ("HONDA", True),  # HONDAはローマ字読みできる
            ("TOYOTA", True),  # TOYOTAもローマ字読みできる
            ("AIKO", True),  # AIKOもOK
            ("SUZUKI", True),  # 子音+母音の組み合わせはOK
            ("こんにちは", False),  # 日本語はfalse
            ("123", False),  # 数字はfalse
            ("URRI", False),  # 促音が含まれる場合はfalse
            ("LLA", False),  # 同上
            ("", False),  # 空文字列はFalse (実装に合わせる)
            ("A", True),  # 単母音はTrue
            ("N", False),  # 撥音のみはFalse (実装に合わせる)
            ("SHI", True),  # 特殊な複合子音
            ("CHI", True),  # 同上
            ("SHA", True),  # 拗音
            ("CHU", True),  # 同上
            ("KYA", True),  # 子音+Y+母音の拗音
            ("RYU", True),  # 同上
            ("GYO", True),  # 同上
            ("SHINZO", True),  # 複合文字を含む単語
            ("CHIKYUGI", True),  # 同上
        ],
    )
    def test_is_romaji_readable(self, input_text, expected_result):
        """Test checking if text is romaji readable."""
        result = is_romaji_readable(input_text)
        assert result == expected_result, f"Expected {expected_result} for '{input_text}', but got {result}"
