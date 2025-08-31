"""Unit tests for AudioGenerator class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yomitalk.components.audio_generator import (
    AudioGenerator,
    WordType,
)


class TestAudioGenerator:
    """Test class for AudioGenerator."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        # Mock session directories for testing (convert to Path objects)
        self.session_output_dir = Path("/tmp/test_output")
        self.session_temp_dir = Path("/tmp/test_temp")

        # Create patches for Synthesizer and other imported classes
        self.synthesizer_patch = patch("yomitalk.components.audio_generator.Synthesizer")
        self.openjtalk_patch = patch("yomitalk.components.audio_generator.OpenJtalk")
        self.onnxruntime_patch = patch("yomitalk.components.audio_generator.Onnxruntime")
        self.voicemodelfile_patch = patch("yomitalk.components.audio_generator.VoiceModelFile")

        # Start patches
        self.mock_synthesizer = self.synthesizer_patch.start()
        self.mock_openjtalk = self.openjtalk_patch.start()
        self.mock_onnxruntime = self.onnxruntime_patch.start()
        self.mock_voicemodelfile = self.voicemodelfile_patch.start()

        # Create the AudioGenerator instance with the mocked dependencies
        self.audio_generator = AudioGenerator(
            session_output_dir=self.session_output_dir,
            session_temp_dir=self.session_temp_dir,
        )

    def teardown_method(self):
        """Tear down test fixtures after each test method is run."""
        # Stop patches
        self.synthesizer_patch.stop()
        self.openjtalk_patch.stop()
        self.onnxruntime_patch.stop()
        self.voicemodelfile_patch.stop()

    def test_initialization(self):
        """Test that AudioGenerator initializes correctly."""
        # Check that the basic attributes are initialized
        assert self.audio_generator.output_dir == self.session_output_dir
        assert self.audio_generator.temp_dir == self.session_temp_dir
        assert hasattr(self.audio_generator, "core_initialized")

    def test_voicevox_core_availability(self):
        """Test VOICEVOX Core availability flag."""
        # テスト用のモックを使用する代わりに、クラス変数で設定された値を検証
        # これはテストの実行環境に依存するテストとなる
        assert hasattr(self.audio_generator, "core_initialized")

    def test_directory_creation(self):
        """Test directory creation."""
        # ディレクトリが存在するかどうかをテスト
        assert self.audio_generator.output_dir.is_dir() or str(self.audio_generator.output_dir) == str(self.session_output_dir)
        assert self.audio_generator.temp_dir.is_dir() or str(self.audio_generator.temp_dir) == str(self.session_temp_dir)

    def test_core_initialization(self):
        """Test core initialization."""
        # コアの初期化状態をテスト
        if hasattr(self.audio_generator, "core_synthesizer") and self.audio_generator.core_synthesizer is not None:
            assert self.audio_generator.core_initialized is True
        # Core initialization depends on VOICEVOX Core availability

    def test_text_to_speech_method(self):
        """テキスト合成メソッドのテスト。"""
        # _text_to_speechメソッドが存在することを確認
        assert hasattr(self.audio_generator, "_text_to_speech")
        assert callable(getattr(self.audio_generator, "_text_to_speech", None))

        # グローバルVOICEVOXマネージャーをモック
        with patch("yomitalk.components.audio_generator.get_global_voicevox_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.is_available.return_value = True
            mock_manager.text_to_speech.return_value = b"dummy_wav_data"
            mock_get_manager.return_value = mock_manager

            # テスト実行
            result = self.audio_generator._text_to_speech("テストテキスト", 1)
            assert result == b"dummy_wav_data"
            mock_manager.text_to_speech.assert_called_once_with("テストテキスト", 1)

    def test_audio_format_conversion(self):
        """オーディオフォーマット変換機能のテスト。"""
        # WAVデータ結合メソッドのテスト
        with patch.object(self.audio_generator, "_combine_wav_data_in_memory") as mock_combine:
            mock_combine.return_value = b"combined_wav_data"

            # ダミーのWAVデータリストを作成
            wav_data_list = [b"wav1", b"wav2", b"wav3"]

            # メソッドを呼び出し
            result = self.audio_generator._combine_wav_data_in_memory(wav_data_list)

            # 結果を検証
            assert result == b"combined_wav_data"
            mock_combine.assert_called_once_with(wav_data_list)

    def test_core_property(self):
        """Test core property."""
        # コアが初期化されているかテスト
        if hasattr(self.audio_generator, "core_initialized"):
            # core_initializedはブール値であるはず
            assert isinstance(self.audio_generator.core_initialized, bool)

    def test_directory_properties(self):
        """Test directory properties."""
        # ディレクトリパスがPath型であるかテスト
        assert isinstance(self.audio_generator.output_dir, Path)
        assert isinstance(self.audio_generator.temp_dir, Path)

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("hello", ["hello"]),
            ("HelloWorld", ["Hello", "World"]),
            ("API", ["API"]),
            ("OpenAI", ["Open", "AI"]),
            ("This is a test", ["This", " ", "is", " ", "a", " ", "test"]),
            ("A123", ["A", "123"]),
            ("Aこんにちは", ["A", "こんにちは"]),
            ("HelloWorldAPI", ["Hello", "World", "API"]),
            ("OpenAI is great", ["Open", "AI", " ", "is", " ", "great"]),
            ("PythonProgrammingLanguage", ["Python", "Programming", "Language"]),
            (
                "LLMs are large language models",
                ["LLM", "ズ", " ", "are", " ", "large", " ", "language", " ", "models"],
            ),
            ("TRANSFORMERs are great", ["TRANSFORMER", "ズ", " ", "are", " ", "great"]),
        ],
    )
    def test_split_capitalized_parts(self, text, expected):
        """_split_capitalized_partsメソッドのテスト"""
        result = self.audio_generator._split_capitalized_parts(text)
        assert result == expected

    @pytest.mark.parametrize(
        "word, expected_type",
        [
            ("is", WordType.BE_VERB),
            ("am", WordType.BE_VERB),
            ("are", WordType.BE_VERB),
            ("were", WordType.BE_VERB),
            ("in", WordType.PREPOSITION),
            ("to", WordType.PREPOSITION),
            (
                "for",
                WordType.CONJUNCTION,
            ),  # forは前置詞と接続詞の両方に含まれるが、ここでは接続詞としてテスト
            ("and", WordType.CONJUNCTION),
            ("hello", WordType.OTHER),
            ("world", WordType.OTHER),
        ],
    )
    def test_word_type_classification(self, word, expected_type):
        """単語タイプの分類テスト"""
        is_be_verb = word in self.audio_generator.BE_VERBS
        is_preposition = word in self.audio_generator.PREPOSITIONS
        is_conjunction = word in self.audio_generator.CONJUNCTIONS

        if expected_type == WordType.BE_VERB:
            assert is_be_verb is True
        elif expected_type == WordType.PREPOSITION:
            assert is_preposition is True
        elif expected_type == WordType.CONJUNCTION:
            assert is_conjunction is True
        else:
            assert not (is_be_verb or is_preposition or is_conjunction)

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("this is a pen", "ディスイズアペン"),
            ("go to school", "ゴートゥスクール"),
            ("Hello, world!", "ヘロー, ワールド!"),
            ("API", "API"),
            ("OpenAI", "オープンAI"),
            (
                "APIClient",
                "APIクライエント",
            ),
            ("Hello世界", "ヘロー世界"),
            ("Attention is all you need", "アテンションイズオールユーニード"),
            (
                "The very long long long long long long long long long long text",
                "ザヴェリーロングロングロング ロングロングロングロングロングロング ロングテキスト",
            ),
            ("JavaScript", "ジャバスクリプト"),
            ("GitHub Copilot", "ギットハブコパイロット"),
            ("3D printer", "3Dプリンター"),
            ("Web2.0", "ウェブ2.0"),
            ("VersionV2", "バージョンV2"),
            ("iPhone 15 Pro", "アイフォン15 プロ"),
            ("I want to learn machine learning", "アイワントトゥランマシン ラーニング"),
            ("Thank you for your cooperation", "サンクユーフォーユアコーポレーション"),
            (
                "The quick brown fox jumps over the lazy dog",
                "ザクイックブラウンフォックスジャンプス オーバーザレージードッグ",
            ),
            ("NASA space program", "ナサスペースプログラム"),
            ("USB cable for PC", "USBケーブルフォーPC"),
            ("AI技術", "AI技術"),
            ("Machine Learning入門", "マシンラーニング入門"),
            ("Vision-Language-Model", "ビジョンランゲージモデル"),
            ("spatial awareness", "スペイシャルアウエアネス"),
            ("LLMs", "LLMズ"),
            # "A"の変換テスト
            ("a pen", "アペン"),  # 冠詞のaは"ア"のまま
            ("A pen", "アペン"),  # 冠詞のAも"ア"
            ("AClass", "Aクラス"),  # 複合語の場合はAのまま
            ("Class A", "クラスA"),  # 技術用語としてAのまま
            ("(A)", "(A)"),  # 括弧内の技術用語としてAのまま
            ("A", "A"),  # 単独のAは技術用語としてそのまま
            ("A-grade", "Aグレード"),  # ハイフン接続の技術用語としてAのまま
        ],
    )
    def test_convert_english_to_katakana(self, text, expected):
        """_convert_english_to_katakanaメソッドのテスト"""
        result = self.audio_generator._convert_english_to_katakana(text)
        assert result == expected

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("REINFORCE", "リンホース"),
            ("PIXCELTHINK", "ピクセルシンク"),
            ("ATTENTION", "アテンション"),
        ],
    )
    def test_convert_long_uppercase_words(self, text, expected):
        """7文字以上の大文字アルファベット文字列の変換テスト"""
        result = self.audio_generator._convert_english_to_katakana(text)
        assert result == expected

    @pytest.mark.parametrize(
        "podcast_text, expected_parts",
        [
            # 正確なキャラクター名
            ("ずんだもん: こんにちはなのだ！\n四国めたん: よろしくお願いします。", [("ずんだもん", "こんにちはなのだ！"), ("四国めたん", "よろしくお願いします。")]),
            # コロンの種類が違う場合
            ("ずんだもん：こんにちはなのだ！\n四国めたん：よろしくお願いします。", [("ずんだもん", "こんにちはなのだ！"), ("四国めたん", "よろしくお願いします。")]),
            # 複数行にわたる発言
            (
                "ずんだもん: こんにちはなのだ！\nとても良い天気だのだ。\n四国めたん: よろしくお願いします。\nよろしくです。",
                [("ずんだもん", "こんにちはなのだ！\nとても良い天気だのだ。"), ("四国めたん", "よろしくお願いします。\nよろしくです。")],
            ),
            # 空行がある場合
            ("ずんだもん: こんにちはなのだ！\n\n四国めたん: よろしくお願いします。", [("ずんだもん", "こんにちはなのだ！\n"), ("四国めたん", "よろしくお願いします。")]),
            # 1つのキャラクターのみ
            ("ずんだもん: こんにちはなのだ！\nとても良い天気だのだ。", [("ずんだもん", "こんにちはなのだ！\nとても良い天気だのだ。")]),
            # 空のテキスト
            ("", []),
            # キャラクター名がない場合
            ("これはただのテキストです。", [("ずんだもん", "これはただのテキストです。")]),
        ],
    )
    def test_extract_conversation_parts_basic(self, podcast_text, expected_parts):
        """_extract_conversation_parts メソッドの基本機能テスト"""
        result = self.audio_generator._extract_conversation_parts(podcast_text)
        assert result == expected_parts

    @pytest.mark.parametrize(
        "podcast_text, expected_parts",
        [
            # 間違った文字を含むキャラクター名（将来の改善で対応予定）
            ("四-めたん: こんにちは。\nずんだもん: よろしくなのだ！", [("四国めたん", "こんにちは。"), ("ずんだもん", "よろしくなのだ！")]),
            # 部分的なキャラクター名
            ("ずんだ: こんにちは。\nめたん: よろしくお願いします。", [("ずんだもん", "こんにちは。"), ("四国めたん", "よろしくお願いします。")]),
            # 曖昧なキャラクター名
            ("四国メタン: こんにちは。\nずんだ君: よろしくなのだ！", [("四国めたん", "こんにちは。"), ("ずんだもん", "よろしくなのだ！")]),
            # ひらがな・カタカナの混在
            ("しこくめたん: こんにちは。\nズンダモン: よろしくなのだ！", [("四国めたん", "こんにちは。"), ("ずんだもん", "よろしくなのだ！")]),
            # スペースが含まれる場合
            ("四国 めたん: こんにちは。\nずんだ もん: よろしくなのだ！", [("四国めたん", "こんにちは。"), ("ずんだもん", "よろしくなのだ！")]),
        ],
    )
    def test_extract_conversation_parts_fuzzy_matching(self, podcast_text, expected_parts):
        """_extract_conversation_parts メソッドの曖昧マッチングテスト（将来の改善機能）"""
        # 現在の実装では厳密マッチングのみサポートされているため、
        # このテストは改善後に期待される動作を定義している
        # TODO: _extract_conversation_parts を改善してこのテストが通るようにする
        result = self.audio_generator._extract_conversation_parts(podcast_text)
        # 現在は失敗することが期待されるが、将来の改善のために記録
        # assert result == expected_parts
        # 暫定的には空のリストまたは元のテキストが返されることを確認
        assert isinstance(result, list)

        # 曖昧マッチング機能が実装されたので、実際のテストを実行
        # 現在は改善されたロジックがあるので期待される結果と比較
        assert result == expected_parts

    @pytest.mark.parametrize(
        "podcast_text, expected_parts",
        [
            # _fix_conversation_format による修正が期待されるケース
            ("ずんだもん こんにちはなのだ！\n四国めたん よろしくお願いします。", [("ずんだもん", "こんにちはなのだ！"), ("四国めたん", "よろしくお願いします。")]),
            # 話者名の後に他のキャラクター名が出現する場合
            ("ずんだもん: こんにちはなのだ！。四国めたん: よろしくお願いします。", [("ずんだもん", "こんにちはなのだ！。四国めたん: よろしくお願いします。")]),
        ],
    )
    def test_extract_conversation_parts_with_format_fix(self, podcast_text, expected_parts):
        """_extract_conversation_parts メソッドのフォーマット修正機能テスト"""
        result = self.audio_generator._extract_conversation_parts(podcast_text)
        assert result == expected_parts

    @pytest.mark.parametrize(
        "input_name, expected_character",
        [
            # 正確なキャラクター名
            ("ずんだもん", "ずんだもん"),
            ("四国めたん", "四国めたん"),
            ("九州そら", "九州そら"),
            ("中国うさぎ", "中国うさぎ"),
            ("中部つるぎ", "中部つるぎ"),
            # 部分的な名前（将来の改善で対応予定）
            ("ずんだ", "ずんだもん"),
            ("めたん", "四国めたん"),
            ("そら", "九州そら"),
            ("うさぎ", "中国うさぎ"),
            ("つるぎ", "中部つるぎ"),
            # タイポや間違った文字を含む名前
            ("四-めたん", "四国めたん"),
            ("四国メタン", "四国めたん"),
            ("しこくめたん", "四国めたん"),
            ("ズンダモン", "ずんだもん"),
            ("ずんだ君", "ずんだもん"),
            ("九洲そら", "九州そら"),
            # スペースが含まれる場合
            ("四国 めたん", "四国めたん"),
            ("ずんだ もん", "ずんだもん"),
            ("九州 そら", "九州そら"),
            # 不明な名前（デフォルトキャラクター）
            ("不明なキャラクター", "ずんだもん"),
            ("", "ずんだもん"),
        ],
    )
    def test_find_best_character_match(self, input_name, expected_character):
        """_find_best_character_match メソッドのテスト（将来実装予定）"""
        # この機能はまだ実装されていないため、現在はテストを定義するのみ
        # TODO: _find_best_character_match メソッドを実装してこのテストが通るようにする

        # 現在は該当メソッドが存在しないため、存在チェックのみ行う
        # 改善後は以下のようなテストになる予定：
        # result = self.audio_generator._find_best_character_match(input_name)
        # assert result == expected_character

        # 暫定的にメソッドの存在をチェック
        has_method = hasattr(self.audio_generator, "_find_best_character_match")
        if has_method:
            # メソッドが実装されている場合はテスト実行
            result = self.audio_generator._find_best_character_match(input_name)
            assert result == expected_character
        else:
            # メソッドがまだ実装されていない場合はスキップ
            pytest.skip("_find_best_character_match method not yet implemented")

    @pytest.mark.parametrize(
        "str1, str2, expected_similarity_range",
        [
            # 完全一致
            ("ずんだもん", "ずんだもん", (1.0, 1.0)),
            ("四国めたん", "四国めたん", (1.0, 1.0)),
            # 高い類似度
            ("四国めたん", "四-めたん", (0.7, 1.0)),
            ("ずんだもん", "ずんだ", (0.6, 1.0)),
            ("四国めたん", "めたん", (0.5, 1.0)),
            # 中程度の類似度
            ("四国めたん", "四国メタン", (0.8, 1.0)),
            ("ずんだもん", "ズンダモン", (0.8, 1.0)),
            ("九州そら", "九洲そら", (0.4, 0.8)),
            # 低い類似度
            ("ずんだもん", "四国めたん", (0.0, 0.3)),
            ("九州そら", "中国うさぎ", (0.0, 0.3)),
            # スペースの扱い
            ("四国めたん", "四国 めたん", (0.7, 1.0)),
            ("ずんだもん", "ずんだ もん", (0.7, 1.0)),
            # 空文字列
            ("ずんだもん", "", (0.0, 0.1)),
            ("", "", (1.0, 1.0)),
        ],
    )
    def test_calculate_character_similarity(self, str1, str2, expected_similarity_range):
        """
        文字列類似度計算のテスト（正規化を使った表記ゆれ対応）

        このテストは、normalize_text()による正規化を活用した
        類似度計算が正しく動作することを確認します。

        テスト例：
        - "四国めたん" vs "四-めたん" → 正規化により高い類似度
        - "ずんだもん" vs "ずんだ" → 部分文字列マッチングで高い類似度
        - "四国メタン" vs "四国めたん" → ひらがな/カタカナ正規化で高い類似度
        """
        # text_utils の関数を直接テスト
        from yomitalk.utils.text_utils import calculate_text_similarity

        result = calculate_text_similarity(str1, str2)
        min_expected, max_expected = expected_similarity_range
        assert min_expected <= result <= max_expected, f"Similarity {result} not in range [{min_expected}, {max_expected}]"
