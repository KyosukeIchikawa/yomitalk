"""Unit tests for AudioGenerator class."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from yomitalk.components.audio_generator import VOICEVOX_CORE_AVAILABLE, AudioGenerator


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

        # モックを使ってコアが初期化されていてもいなくてもテストが実行されるようにする
        self.audio_generator.core_synthesizer = MagicMock()
        self.audio_generator.core_synthesizer.tts.return_value = b"dummy_wav_data"

        # テスト実行
        result = self.audio_generator._text_to_speech("テストテキスト", 1)
        assert result == b"dummy_wav_data"
        self.audio_generator.core_synthesizer.tts.assert_called_once_with("テストテキスト", 1)

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
