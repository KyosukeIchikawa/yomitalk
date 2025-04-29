#!/usr/bin/env python3
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# テスト対象モジュールのパスを追加してインポート
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", ".pre-commit-hooks")
)
from detect_custom_tokens import (  # noqa: E402
    check_file,
    get_token_patterns,
    is_excluded_path,
    main,
)


class TestDetectCustomTokens(unittest.TestCase):
    """トークン検出スクリプトのテストクラス"""

    def test_get_token_patterns(self):
        """トークンパターンが正しく取得できるか確認"""
        patterns = get_token_patterns()
        self.assertIsInstance(patterns, list)
        self.assertGreater(len(patterns), 0)

    def test_is_excluded_path(self):
        """パス除外機能が正しく動作するか確認"""
        # バイナリファイルは除外される
        self.assertTrue(is_excluded_path("test.jpg"))
        self.assertTrue(is_excluded_path("path/to/file.exe"))
        self.assertTrue(is_excluded_path("/absolute/path/file.zip"))

        # 特定のパスは除外される
        self.assertTrue(is_excluded_path("tests/unit/test_detect_custom_tokens.py"))
        self.assertTrue(is_excluded_path("some/path/detect_custom_tokens.py"))

        # 通常のテキストファイルは除外されない
        self.assertFalse(is_excluded_path("test.py"))
        self.assertFalse(is_excluded_path("path/to/file.js"))
        self.assertFalse(is_excluded_path("/absolute/path/file.txt"))

    def test_check_file_with_tokens(self):
        """トークンを含むファイルを正しく検出できるか確認"""
        # 注意: 実際のトークンを使わないようにダミーデータを使用
        test_cases = [
            # ダミーの長い文字列（実際のトークンではない）
            "This is a test with DUMMY_TOKEN_ABCDEFG1234567890DUMMY_TOKEN",
            # ダミーのAPIキー
            'API_KEY="DUMMY_API_KEY_1234567890ABCDEFG"',
            # ダミーのJWTトークン風
            "JWT token: eyJhbGciOi.eyJzdWIiOiIx.DUMMY_JWT_SIGNATURE",
            # ダミーの環境変数
            "SECRET_KEY=DUMMY_SECRET_KEY_1234567890",
        ]

        for test_content in test_cases:
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".txt", delete=False
            ) as temp:
                temp.write(test_content)
                temp_name = temp.name

            try:
                # テスト実行（print出力をモック化）
                with patch("builtins.print"):
                    result = check_file(temp_name)
                    self.assertTrue(result, "Failed to detect token in test case")
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_name):
                    os.unlink(temp_name)

    def test_check_file_without_tokens(self):
        """トークンを含まないファイルは検出されないか確認"""
        test_cases = [
            "This is a normal text without any tokens",
            "var normalString = 'short_string';",
            "# This is a comment in a Python file",
            "function testFunc() { return 'hello world'; }",
        ]

        for test_content in test_cases:
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".txt", delete=False
            ) as temp:
                temp.write(test_content)
                temp_name = temp.name

            try:
                # テスト実行
                result = check_file(temp_name)
                self.assertFalse(result, "Incorrectly detected token in normal text")
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_name):
                    os.unlink(temp_name)

    def test_binary_file_handling(self):
        """バイナリファイルが正しく除外されるか確認"""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".bin", delete=False
        ) as temp:
            temp.write(b"\x00\x01\x02\x03")  # バイナリデータ
            temp_name = temp.name

        try:
            # テスト実行
            result = check_file(temp_name)
            self.assertFalse(result, "Binary file should be excluded")
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def test_main_function(self):
        """メイン関数が正しく動作するか確認"""
        # トークンを含むファイル
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".txt", delete=False
        ) as temp:
            temp.write("SECRET_KEY=DUMMY_KEY_FOR_TESTING_ONLY")
            token_file = temp.name

        # 通常のファイル
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".txt", delete=False
        ) as temp:
            temp.write("This is a normal text")
            normal_file = temp.name

        try:
            # トークンファイルのみのテスト
            with patch("sys.argv", ["detect_custom_tokens.py", token_file]):
                with patch("builtins.print"):
                    result = main()
                    self.assertEqual(result, 1, "Should detect token and return 1")

            # 通常ファイルのみのテスト
            with patch("sys.argv", ["detect_custom_tokens.py", normal_file]):
                result = main()
                self.assertEqual(result, 0, "Should not detect token and return 0")

            # 両方のファイルを含むテスト
            with patch(
                "sys.argv", ["detect_custom_tokens.py", normal_file, token_file]
            ):
                with patch("builtins.print"):
                    result = main()
                    self.assertEqual(result, 1, "Should detect token and return 1")
        finally:
            # 一時ファイルを削除
            for file_path in [token_file, normal_file]:
                if os.path.exists(file_path):
                    os.unlink(file_path)


if __name__ == "__main__":
    unittest.main()
