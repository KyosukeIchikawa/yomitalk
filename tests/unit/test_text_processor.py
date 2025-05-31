"""Unit tests for TextProcessor class."""
from unittest.mock import MagicMock, patch

from yomitalk.common import APIType
from yomitalk.components.text_processor import TextProcessor
from yomitalk.prompt_manager import DocumentType, PodcastMode


class TestTextProcessor:
    """Test class for TextProcessor."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        self.text_processor = TextProcessor()

    def test_initialization(self):
        """Test that TextProcessor initializes correctly."""
        # Check that the basic attributes are initialized
        assert hasattr(self.text_processor, "prompt_manager")
        assert hasattr(self.text_processor, "openai_model")
        assert hasattr(self.text_processor, "gemini_model")
        assert hasattr(self.text_processor, "current_api_type")

        # Check default values
        assert self.text_processor.current_api_type is None

    @patch("yomitalk.components.text_processor.OpenAIModel")
    def test_set_openai_api_key(self, mock_openai_model):
        """Test setting OpenAI API key."""
        # Mock the OpenAI model
        mock_instance = MagicMock()
        mock_instance.set_api_key.return_value = True
        mock_openai_model.return_value = mock_instance
        self.text_processor.openai_model = mock_instance

        # Test with valid API key
        api_key = "sk-valid-api-key"
        result = self.text_processor.set_openai_api_key(api_key)

        # Verify results
        assert result is True
        assert self.text_processor.current_api_type == APIType.OPENAI
        mock_instance.set_api_key.assert_called_once_with(api_key)

    @patch("yomitalk.components.text_processor.GeminiModel")
    def test_set_gemini_api_key(self, mock_gemini_model):
        """Test setting Gemini API key."""
        # Mock the Gemini model
        mock_instance = MagicMock()
        mock_instance.set_api_key.return_value = True
        mock_gemini_model.return_value = mock_instance
        self.text_processor.gemini_model = mock_instance

        # Test with valid API key
        api_key = "valid-gemini-api-key"
        result = self.text_processor.set_gemini_api_key(api_key)

        # Verify results
        assert result is True
        assert self.text_processor.current_api_type == APIType.GEMINI
        mock_instance.set_api_key.assert_called_once_with(api_key)

    def test_get_podcast_mode(self):
        """Test getting podcast mode."""
        # 現在のPodcastモードを取得
        result = self.text_processor.get_podcast_mode()
        # モードがPodcastModeのインスタンスであることを確認
        assert isinstance(result, PodcastMode)

    def test_set_api_type(self):
        """Test setting API type."""
        # APIが設定されていない場合
        assert self.text_processor.set_api_type(APIType.OPENAI) is False
        assert self.text_processor.set_api_type(APIType.GEMINI) is False

        # APIが設定されている場合をシミュレート
        with patch.object(
            self.text_processor.openai_model, "has_api_key", return_value=True
        ):
            assert self.text_processor.set_api_type(APIType.OPENAI) is True
            assert self.text_processor.get_current_api_type() == APIType.OPENAI

        # OpenAI APIキーが設定されていないがGemini APIキーがある場合
        with patch.object(
            self.text_processor.openai_model, "has_api_key", return_value=False
        ), patch.object(
            self.text_processor.gemini_model, "has_api_key", return_value=True
        ):
            assert self.text_processor.set_api_type(APIType.GEMINI) is True
            assert self.text_processor.get_current_api_type() == APIType.GEMINI

    def test_set_document_type(self):
        """Test setting document type."""
        # DocumentTypeを設定するテスト
        result = self.text_processor.set_document_type(DocumentType.PAPER)
        assert result is True

        # 設定されたドキュメントタイプを確認
        assert self.text_processor.get_document_type() == DocumentType.PAPER

    def test_generate_conversation(self):
        """Test generate podcast conversation."""
        # アップストリームを設定
        with patch.object(
            self.text_processor.openai_model, "has_api_key", return_value=True
        ):
            self.text_processor.current_api_type = APIType.OPENAI

            # 簡単なテキストでテスト実行
            result = self.text_processor.generate_podcast_conversation(
                "Test input text"
            )

            # 出力の基本検証
            assert isinstance(result, str)

    def test_api_generation(self):
        """Test API generation methods."""
        # OpenAIとGeminiのAPIがあると仮定したテスト
        # 実際のAPIを呼び出さないでモックする
        with patch.object(
            self.text_processor.openai_model, "generate_text"
        ) as mock_openai, patch.object(
            self.text_processor.openai_model, "has_api_key"
        ) as mock_has_api_key:
            mock_openai.return_value = "OpenAI generated text"
            mock_has_api_key.return_value = True
            self.text_processor.current_api_type = APIType.OPENAI

            # OpenAIによる生成をテスト
            result = self.text_processor.generate_podcast_conversation("Test")
            assert "OpenAI generated text" in result

    def test_gemini_generation(self):
        """Test Gemini generation."""
        # Geminiのモックをセットアップ
        with patch.object(
            self.text_processor.gemini_model, "generate_text"
        ) as mock_gemini, patch.object(
            self.text_processor.gemini_model, "has_api_key"
        ) as mock_has_api_key:
            mock_gemini.return_value = "Gemini generated text"
            mock_has_api_key.return_value = True
            self.text_processor.current_api_type = APIType.GEMINI

            # GeminiによるPodcast会話生成をテスト
            result = self.text_processor.generate_podcast_conversation("Test")
            assert "Gemini generated text" in result

    def test_api_configuration_validation(self):
        """Test API configuration validation."""
        # APIキーが設定されていない場合のエラー処理テスト
        self.text_processor.current_api_type = None

        # エラーメッセージが返ることを確認
        result = self.text_processor.generate_podcast_conversation("Test")
        assert "Error:" in result  # RuntimeError の代わりにエラーメッセージが返る

    def test_get_template_content(self):
        """Test getting template content."""
        # テンプレート内容を取得するテスト
        result = self.text_processor.get_template_content()
        assert isinstance(result, str)
