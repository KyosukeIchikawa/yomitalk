import unittest
from unittest.mock import patch

from app.components.audio_generator import AudioGenerator


class TestAudioGenerator(unittest.TestCase):
    """AudioGeneratorのテストクラス"""

    def setUp(self):
        """テスト実行前のセットアップ"""
        # VOICEVOXの初期化をモックする
        with patch("app.components.audio_generator.VOICEVOX_CORE_AVAILABLE", False):
            self.audio_generator = AudioGenerator()

    def test_convert_english_to_katakana_basic(self):
        """基本的な英単語のカタカナ変換テスト"""
        # alkana.get_kanaをモックする
        with patch("app.components.audio_generator.alkana.get_kana") as mock_get_kana:
            # モックの戻り値を設定
            mock_get_kana.side_effect = lambda word: {
                "hello": "ハロー",
                "world": "ワールド",
            }.get(word, None)

            # 通常の英単語
            result = self.audio_generator._convert_english_to_katakana("Hello World!")
            self.assertEqual(result, "ハロー ワールド!")

    def test_convert_english_to_katakana_with_hyphen(self):
        """ハイフンを含む英単語のカタカナ変換テスト"""
        # alkana.get_kanaをモックする
        with patch("app.components.audio_generator.alkana.get_kana") as mock_get_kana:
            # モックの戻り値を設定
            mock_get_kana.side_effect = lambda word: {
                "user": "ユーザー",
                "friendly": "フレンドリー",
            }.get(word, None)

            # ハイフンを含む英単語
            result = self.audio_generator._convert_english_to_katakana("user-friendly")
            self.assertEqual(result, "ユーザー-フレンドリー")

    def test_convert_english_to_katakana_with_multiple_hyphens(self):
        """複数のハイフンを含む英単語のカタカナ変換テスト"""
        # alkana.get_kanaをモックする
        with patch("app.components.audio_generator.alkana.get_kana") as mock_get_kana:
            # モックの戻り値を設定
            mock_get_kana.side_effect = lambda word: {
                "deep": "ディープ",
                "learning": "ラーニング",
                "ai": "エーアイ",
            }.get(word, None)

            # 複数のハイフンを含む英単語
            result = self.audio_generator._convert_english_to_katakana(
                "deep-learning-ai"
            )
            self.assertEqual(result, "ディープ-ラーニング-エーアイ")

    def test_convert_english_to_katakana_with_unknown_parts(self):
        """変換できない部分を含む英単語のカタカナ変換テスト"""
        # alkana.get_kanaをモックする
        with patch("app.components.audio_generator.alkana.get_kana") as mock_get_kana:
            # モックの戻り値を設定
            mock_get_kana.side_effect = lambda word: {
                "user": "ユーザー",
                "test": "テスト",
                # unknownはNoneを返す（変換できない）
            }.get(word, None)

            # 変換できない部分を含む英単語
            result = self.audio_generator._convert_english_to_katakana(
                "user-unknown-test"
            )
            self.assertEqual(result, "ユーザー-unknown-テスト")

    def test_convert_english_to_katakana_with_consecutive_hyphens(self):
        """連続したハイフンを含む英単語のカタカナ変換テスト"""
        # alkana.get_kanaをモックする
        with patch("app.components.audio_generator.alkana.get_kana") as mock_get_kana:
            # モックの戻り値を設定
            mock_get_kana.side_effect = lambda word: {
                "test": "テスト",
                "hello": "ハロー",
            }.get(word, None)

            # 連続したハイフンを含む英単語
            result = self.audio_generator._convert_english_to_katakana("test--hello")
            self.assertEqual(result, "テスト--ハロー")


if __name__ == "__main__":
    unittest.main()
