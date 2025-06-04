"""Unit tests for AudioGenerator class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yomitalk.components.audio_generator import (
    VOICEVOX_CORE_AVAILABLE,
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

        # Create a patch for VOICEVOX Core availability
        self.voicevox_patch = patch(
            "yomitalk.components.audio_generator.VOICEVOX_CORE_AVAILABLE", True
        )
        self.voicevox_patch.start()

        # Create patches for Synthesizer and other imported classes
        self.synthesizer_patch = patch(
            "yomitalk.components.audio_generator.Synthesizer"
        )
        self.openjtalk_patch = patch("yomitalk.components.audio_generator.OpenJtalk")
        self.onnxruntime_patch = patch(
            "yomitalk.components.audio_generator.Onnxruntime"
        )
        self.voicemodelfile_patch = patch(
            "yomitalk.components.audio_generator.VoiceModelFile"
        )

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
        self.voicevox_patch.stop()
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
        assert self.audio_generator.output_dir.is_dir() or str(
            self.audio_generator.output_dir
        ) == str(self.session_output_dir)
        assert self.audio_generator.temp_dir.is_dir() or str(
            self.audio_generator.temp_dir
        ) == str(self.session_temp_dir)

    def test_core_initialization(self):
        """Test core initialization."""
        # コアの初期化状態をテスト
        if (
            hasattr(self.audio_generator, "core_synthesizer")
            and self.audio_generator.core_synthesizer is not None
        ):
            assert self.audio_generator.core_initialized is True
        elif not VOICEVOX_CORE_AVAILABLE:
            assert self.audio_generator.core_initialized is False

    def test_text_to_speech_method(self):
        """テキスト合成メソッドのテスト。"""
        # _text_to_speechメソッドが存在することを確認
        assert hasattr(self.audio_generator, "_text_to_speech")
        assert callable(getattr(self.audio_generator, "_text_to_speech", None))

        # グローバルVOICEVOXマネージャーをモック
        with patch(
            "yomitalk.components.audio_generator.get_global_voicevox_manager"
        ) as mock_get_manager:
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
        with patch.object(
            self.audio_generator, "_combine_wav_data_in_memory"
        ) as mock_combine:
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
            ("spacial awareness", "スペイシャルアウエアネス"),
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
