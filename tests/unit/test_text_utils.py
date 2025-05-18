"""Tests for text_utils module"""

import pytest

from yomitalk.utils.text_utils import is_romaji_readable


class TestIsRomajiReadable:
    """Test class for is_romaji_readable function"""

    @pytest.mark.parametrize(
        "word, expected",
        [
            # 基本的なローマ字読み可能な単語
            ("HONDA", True),  # ホ・ン・ダ - 単純な子音+母音の組み合わせと撥音
            ("AIKO", True),  # ア・イ・コ - 母音とKOの組み合わせ
            ("TOKYO", True),  # ト・ウ・キョ・ウ - 拗音KYOを含む
            ("SUSHI", True),  # ス・シ - SHIの組み合わせ
            ("SAKURA", True),  # サ・ク・ラ - 基本的なローマ字
            ("NIHON", True),  # ニ・ホ・ン - 語末のN
            ("ICHIBAN", True),  # イ・チ・バ・ン - CHを含む
            ("GENKI", True),  # ゲ・ン・キ - 中間のN
            ("KONNICHIWA", True),  # コ・ン・ニ・チ・ワ - 複数のNを含む
            ("SHINBUN", True),  # シ・ン・ブ・ン - SHを含む
            # 特殊なパターン
            ("TOKYO", True),  # KYの拗音
            ("RYOKO", True),  # RYの拗音
            ("CHANOYU", True),  # チャノユ - CHAの拗音
            ("DENSHA", True),  # デ・ン・シャ - SHAの拗音
            # ローマ字読み不可能な単語
            ("URRI", False),  # RRが続くため不可
            ("LLA", False),  # LLが続くため不可
            ("KITTE", False),  # TTが続くため不可
            ("NISSAN", False),  # SSが続くため不可
            ("XML", False),  # 子音MLだけのため不可
            ("WTF", False),  # 子音WTFだけのため不可
            ("WWW", False),  # 子音WWWだけのため不可
            # エッジケース
            ("A", True),  # 母音1文字は読める
            ("", False),  # 空文字
            ("abc", False),  # 小文字（大文字のみ判定ではじかれる）
            ("HONDA2", False),  # 数字を含む
            ("HONDA-KUN", False),  # 記号を含む
            # 促音を含む場合（現実装では不可）
            ("MOTTO", False),  # モット - TTが促音
            ("RAKKYO", False),  # ラッキョウ - KKが促音
        ],
    )
    def test_romaji_readable_detection(self, word, expected):
        """Test is_romaji_readable function correctly identifies romanizable words"""
        assert is_romaji_readable(word) == expected

    def test_invalid_input_types(self):
        """Test function handles invalid input types"""
        assert is_romaji_readable(None) is False  # type: ignore
        assert is_romaji_readable(123) is False  # type: ignore
        assert is_romaji_readable([]) is False  # type: ignore
        assert is_romaji_readable({}) is False  # type: ignore
