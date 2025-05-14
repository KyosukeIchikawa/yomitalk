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

        # 通常の英単語 - 連続する英単語の空白は除去される
        result = self.audio_generator._convert_english_to_katakana("Hello World!")
        self.assertEqual(result, "ヘローワールド!")

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
        }.get(word.lower(), None)

        # NGramモデルは常にTrueを返す設定
        self.mock_ngram.return_value = True

        # 複数のハイフンを含む英単語（AIは大文字のみなのでカタカナ変換されない）
        result = self.audio_generator._convert_english_to_katakana("deep-learning-AI")
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

        # 連続したハイフンを含む英単語 - ハイフンは単語間で無視される
        result = self.audio_generator._convert_english_to_katakana("test--hello")
        self.assertEqual(result, "テストヘロー")

    def test_convert_english_to_katakana_space_removal(self):
        """カタカナに変換された英単語間の空白削除のテスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "machine": "マシン",
            "learning": "ラーニング",
            "deep": "ディープ",
        }.get(word, None)

        # 空白区切りの英単語（英単語間の空白は除去される）
        result = self.audio_generator._convert_english_to_katakana("machine learning")
        self.assertEqual(result, "マシンラーニング")

        # 複数の英単語の連続
        result = self.audio_generator._convert_english_to_katakana(
            "deep machine learning"
        )
        self.assertEqual(result, "ディープマシンラーニング")

    def test_convert_english_to_katakana_mixed_content(self):
        """英語と日本語が混在したテキストの空白処理テスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "machine": "マシン",
            "learning": "ラーニング",
            # AIはカタカナ変換しない（大文字のみの2〜5文字の単語）
        }.get(word.lower(), None)

        # 日本語と英語が混在
        result = self.audio_generator._convert_english_to_katakana(
            "今日は machine learning と AI の勉強をします"
        )
        self.assertEqual(result, "今日は マシンラーニング と AI の勉強をします")

    def test_convert_english_to_katakana_preserve_spaces(self):
        """日本語や他の文字間の空白を保持することのテスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "machine": "マシン",
            "learning": "ラーニング",
        }.get(word.lower(), None)

        # 日本語の文章中の空白は保持
        result = self.audio_generator._convert_english_to_katakana(
            "これは machine learning の例です。他の 単語 の間隔はそのままです"
        )
        self.assertEqual(result, "これは マシンラーニング の例です。他の 単語 の間隔はそのままです")

    def test_convert_english_to_katakana_multiple_spaces(self):
        """複数の空白文字がある場合のテスト"""
        # e2k.C2Kのモック設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "machine": "マシン",
            "learning": "ラーニング",
            "deep": "ディープ",
        }.get(word.lower(), None)

        # 複数の空白を含むテキスト - すべての空白が除去される
        result = self.audio_generator._convert_english_to_katakana(
            "machine  learning   deep"
        )
        self.assertEqual(result, "マシンラーニングディープ")

    def test_convert_english_to_katakana_uppercase_acronyms(self):
        """大文字のみで構成された略語のテスト（変換されないことを確認）"""
        # e2k.C2Kのモック設定 - 呼び出されても意味がないが念のため設定
        self.mock_c2k.side_effect = lambda word, *args, **kwargs: {
            "ai": "アイ",
            "nlp": "エヌエルピー",
        }.get(word.lower(), None)

        # 大文字のみの略語はカタカナ変換されない
        result = self.audio_generator._convert_english_to_katakana("AI NLP")
        self.assertEqual(result, "AI NLP")

        # 混合ケース - AIはそのままでmachine learningは変換される
        result = self.audio_generator._convert_english_to_katakana(
            "AI machine learning"
        )
        self.assertEqual(result, "AI マシンラーニング")


if __name__ == "__main__":
    unittest.main()
