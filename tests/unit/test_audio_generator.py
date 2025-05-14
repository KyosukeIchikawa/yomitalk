import unittest
from unittest.mock import MagicMock, patch

from app.components.audio_generator import AudioGenerator


class TestAudioGenerator(unittest.TestCase):
    """AudioGeneratorのテストクラス"""

    def setUp(self):
        """テスト実行前のセットアップ"""
        # VOICEVOXの初期化をモック
        with patch("app.components.audio_generator.VOICEVOX_CORE_AVAILABLE", False):
            # e2kのモックを作成
            with patch(
                "app.components.audio_generator.e2k.C2K"
            ) as mock_c2k_class, patch(
                "app.components.audio_generator.e2k.NGram"
            ) as mock_ngram_class:
                # モックインスタンスの作成
                self.mock_c2k = MagicMock()
                self.mock_ngram = MagicMock()

                # モッククラスがモックインスタンスを返すように設定
                mock_c2k_class.return_value = self.mock_c2k
                mock_ngram_class.return_value = self.mock_ngram

                # デフォルトのNGram振る舞いを設定
                self.mock_ngram.side_effect = None
                self.mock_ngram.return_value = True  # デフォルトで単語は有効と判定

                self.audio_generator = AudioGenerator()

    def test_convert_english_to_katakana_basic(self):
        """基本的な英単語のカタカナ変換テスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "hello": "ヘロー",
            "world": "ワールド",
        }.get(word, None)

        # NGramモデルは常にTrueを返す設定
        self.mock_ngram.return_value = True

        # 通常の英単語
        result = self.audio_generator._convert_english_to_katakana("Hello World!")
        self.assertEqual(result, "ヘロー ワールド!")

    def test_convert_english_to_katakana_with_hyphen(self):
        """ハイフンを含む英単語のカタカナ変換テスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "user": "ユーザー",
            "friendly": "フレンドリー",
        }.get(word, None)

        # NGramモデルは常にTrueを返す設定
        self.mock_ngram.return_value = True

        # ハイフンを含む英単語
        result = self.audio_generator._convert_english_to_katakana("user-friendly")
        self.assertEqual(result, "ユーザーフレンドリー")

    def test_convert_english_to_katakana_with_multiple_hyphens(self):
        """複数のハイフンを含む英単語のカタカナ変換テスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "deep": "ディープ",
            "learning": "ラーニング",
            "AI": "AI",
        }.get(word, None)

        # NGramモデルは常にTrueを返す設定
        self.mock_ngram.return_value = True

        # 複数のハイフンを含む英単語
        result = self.audio_generator._convert_english_to_katakana("deep-learning-ai")
        self.assertEqual(result, "ディープラーニングAI")

    def test_convert_english_to_katakana_with_unknown_parts(self):
        """変換できない部分を含む英単語のカタカナ変換テスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "user": "ユーザー",
            "test": "テスト",
            # unknownはNoneを返す（変換できない）
        }.get(word, None)

        # NGramモデルの設定 - unknownは無効な単語として処理
        def ngram_side_effect(word):
            return word != "unknown"

        self.mock_ngram.side_effect = ngram_side_effect

        # as_is関数のモックを設定
        self.mock_ngram.as_is.return_value = "アンノウン"

        # 変換できない部分を含む英単語
        result = self.audio_generator._convert_english_to_katakana("user-unknown-test")
        self.assertEqual(result, "ユーザーアンノウンテスト")

    def test_convert_english_to_katakana_with_consecutive_hyphens(self):
        """連続したハイフンを含む英単語のカタカナ変換テスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "test": "テスト",
            "hello": "ヘロー",
        }.get(word, None)

        # NGramモデルは常にTrueを返す設定
        self.mock_ngram.return_value = True

        # 連続したハイフンを含む英単語
        result = self.audio_generator._convert_english_to_katakana("test--hello")
        self.assertEqual(result, "テストヘロー")


if __name__ == "__main__":
    unittest.main()
