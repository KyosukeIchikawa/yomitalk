"""Unit tests for TextProcessor class."""

import unittest
from unittest.mock import MagicMock, patch

from yomitalk.components.text_processor import TextProcessor
from yomitalk.prompt_manager import DocumentType, PodcastMode


class TestTextProcessor(unittest.TestCase):
    """Test case for TextProcessor class."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # TextProcessorをパッチして作成
        with patch(
            "yomitalk.prompt_manager.PromptManager"
        ) as mock_prompt_manager_class:
            # PromptManagerのモックを設定
            self.mock_prompt_manager = MagicMock()
            mock_prompt_manager_class.return_value = self.mock_prompt_manager

            # OpenAIModelのモックを設定
            with patch(
                "yomitalk.models.openai_model.OpenAIModel"
            ) as mock_openai_model_class:
                self.mock_openai_model = MagicMock()
                mock_openai_model_class.return_value = self.mock_openai_model

                # GeminiModelのモックを設定
                with patch(
                    "yomitalk.models.gemini_model.GeminiModel"
                ) as mock_gemini_model_class:
                    self.mock_gemini_model = MagicMock()
                    mock_gemini_model_class.return_value = self.mock_gemini_model

                    # TextProcessorを作成
                    self.text_processor = TextProcessor()

                    # モックを直接適用
                    self.text_processor.prompt_manager = self.mock_prompt_manager
                    self.text_processor.openai_model = self.mock_openai_model
                    self.text_processor.gemini_model = self.mock_gemini_model

    def test_init(self):
        """Test initialization of TextProcessor."""
        self.assertIsNotNone(self.text_processor)
        self.assertFalse(self.text_processor.use_openai)
        self.assertFalse(self.text_processor.use_gemini)
        self.assertEqual(self.text_processor.current_api_type, "openai")
        self.assertIsNotNone(self.text_processor.openai_model)
        self.assertIsNotNone(self.text_processor.gemini_model)
        self.assertIsNotNone(self.text_processor.prompt_manager)

    def test_preprocess_text(self):
        """Test text preprocessing functionality."""
        # Test with page markers and empty lines
        input_text = "## Page 1\nLine 1\n\nLine 2\n## Page 2\nLine 3"
        expected = "Line 1 Line 2 Line 3"
        result = self.text_processor._preprocess_text(input_text)
        self.assertEqual(result, expected)

        # Test with empty input
        self.assertEqual(self.text_processor._preprocess_text(""), "")

    def test_set_openai_api_key(self):
        """Test setting the OpenAI API key."""
        # Test with valid API key
        self.mock_openai_model.set_api_key.return_value = True
        result = self.text_processor.set_openai_api_key("valid-api-key")
        self.assertTrue(result)
        self.assertTrue(self.text_processor.use_openai)
        self.assertEqual(self.text_processor.current_api_type, "openai")
        self.mock_openai_model.set_api_key.assert_called_with("valid-api-key")

        # Test with invalid API key
        self.mock_openai_model.set_api_key.return_value = False
        result = self.text_processor.set_openai_api_key("invalid-api-key")
        self.assertFalse(result)
        self.mock_openai_model.set_api_key.assert_called_with("invalid-api-key")

    def test_set_gemini_api_key(self):
        """Test setting the Gemini API key."""
        # Test with valid API key
        self.mock_gemini_model.set_api_key.return_value = True
        result = self.text_processor.set_gemini_api_key("valid-api-key")
        self.assertTrue(result)
        self.assertTrue(self.text_processor.use_gemini)
        self.assertEqual(self.text_processor.current_api_type, "gemini")
        self.mock_gemini_model.set_api_key.assert_called_with("valid-api-key")

        # Test with invalid API key
        self.mock_gemini_model.set_api_key.return_value = False
        result = self.text_processor.set_gemini_api_key("invalid-api-key")
        self.assertFalse(result)
        self.mock_gemini_model.set_api_key.assert_called_with("invalid-api-key")

    def test_set_api_type(self):
        """Test setting API type."""
        # OpenAIが設定されている場合
        self.text_processor.use_openai = True
        self.text_processor.use_gemini = False

        # OpenAIに切り替え（成功）
        result = self.text_processor.set_api_type("openai")
        self.assertTrue(result)
        self.assertEqual(self.text_processor.current_api_type, "openai")

        # Geminiに切り替え（失敗：APIキーが設定されていない）
        result = self.text_processor.set_api_type("gemini")
        self.assertFalse(result)
        self.assertEqual(self.text_processor.current_api_type, "openai")  # 変更されない

        # 無効なタイプの指定
        result = self.text_processor.set_api_type("invalid-type")
        self.assertFalse(result)

        # 両方設定されている場合
        self.text_processor.use_openai = True
        self.text_processor.use_gemini = True

        # Geminiに切り替え（成功）
        result = self.text_processor.set_api_type("gemini")
        self.assertTrue(result)
        self.assertEqual(self.text_processor.current_api_type, "gemini")

    def test_get_current_api_type(self):
        """Test getting current API type."""
        self.text_processor.current_api_type = "openai"
        self.assertEqual("openai", self.text_processor.get_current_api_type())

        self.text_processor.current_api_type = "gemini"
        self.assertEqual("gemini", self.text_processor.get_current_api_type())

    def test_get_template_content(self):
        """Test getting prompt template content."""
        self.mock_prompt_manager.get_template_content.return_value = "テストテンプレート"
        result = self.text_processor.get_template_content()
        self.assertEqual(result, "テストテンプレート")
        self.mock_prompt_manager.get_template_content.assert_called_once()

    def test_set_podcast_mode(self):
        """Test setting podcast mode."""
        # 正常系のテスト - 有効なモード
        self.mock_prompt_manager.set_podcast_mode.return_value = True
        result = self.text_processor.set_podcast_mode("section_by_section")
        self.assertTrue(result)
        self.mock_prompt_manager.set_podcast_mode.assert_called_with(
            PodcastMode.SECTION_BY_SECTION
        )

        # 正常系のテスト - standardモード
        self.mock_prompt_manager.set_podcast_mode.reset_mock()
        result = self.text_processor.set_podcast_mode("standard")
        self.assertTrue(result)
        self.mock_prompt_manager.set_podcast_mode.assert_called_with(
            PodcastMode.STANDARD
        )

        # エラー系のテスト - PromptManagerがTypeErrorをスロー
        self.mock_prompt_manager.set_podcast_mode.reset_mock()
        self.mock_prompt_manager.set_podcast_mode.side_effect = TypeError(
            "mode must be an instance of PodcastMode"
        )
        result = self.text_processor.set_podcast_mode("standard")
        self.assertFalse(result)
        self.mock_prompt_manager.set_podcast_mode.assert_called_once()

        # エラー系のテスト - 無効なモード
        self.mock_prompt_manager.set_podcast_mode.reset_mock()
        self.mock_prompt_manager.set_podcast_mode.side_effect = None
        result = self.text_processor.set_podcast_mode("invalid_mode")
        self.assertFalse(result)
        self.mock_prompt_manager.set_podcast_mode.assert_not_called()

    def test_get_podcast_mode(self):
        """Test getting podcast mode."""
        # PodcastMode.STANDARDを返すよう設定
        self.mock_prompt_manager.get_podcast_mode.return_value = PodcastMode.STANDARD
        result = self.text_processor.get_podcast_mode()
        self.assertEqual(result, PodcastMode.STANDARD)
        self.mock_prompt_manager.get_podcast_mode.assert_called_once()

        # PodcastMode.SECTION_BY_SECTIONの場合もテスト
        self.mock_prompt_manager.get_podcast_mode.reset_mock()
        self.mock_prompt_manager.get_podcast_mode.return_value = (
            PodcastMode.SECTION_BY_SECTION
        )
        result = self.text_processor.get_podcast_mode()
        self.assertEqual(result, PodcastMode.SECTION_BY_SECTION)
        self.mock_prompt_manager.get_podcast_mode.assert_called_once()

    def test_generate_podcast_conversation_with_openai(self):
        """Test generating podcast conversation with OpenAI."""
        # OpenAIモデルのセットアップ
        self.text_processor.current_api_type = "openai"
        self.text_processor.use_openai = True

        # モックの設定
        self.mock_prompt_manager.generate_podcast_conversation.return_value = "テストプロンプト"
        self.mock_openai_model.generate_text.return_value = (
            "Character1: こんにちは\nCharacter2: はじめまして"
        )
        self.mock_prompt_manager.convert_abstract_to_real_characters.return_value = (
            "ずんだもん: こんにちは\n四国めたん: はじめまして"
        )

        # メソッド実行
        result = self.text_processor.generate_podcast_conversation("テスト論文")

        # 検証
        self.assertEqual("ずんだもん: こんにちは\n四国めたん: はじめまして", result)
        self.mock_prompt_manager.generate_podcast_conversation.assert_called_with(
            "テスト論文"
        )
        self.mock_openai_model.generate_text.assert_called_with("テストプロンプト")
        self.mock_prompt_manager.convert_abstract_to_real_characters.assert_called_with(
            "Character1: こんにちは\nCharacter2: はじめまして"
        )

    def test_generate_podcast_conversation_with_gemini(self):
        """Test generating podcast conversation with Gemini."""
        # Geminiモデルのセットアップ
        self.text_processor.current_api_type = "gemini"
        self.text_processor.use_gemini = True

        # モックの設定
        self.mock_prompt_manager.generate_podcast_conversation.return_value = "テストプロンプト"
        self.mock_gemini_model.generate_text.return_value = (
            "Character1: こんにちは\nCharacter2: はじめまして"
        )
        self.mock_prompt_manager.convert_abstract_to_real_characters.return_value = (
            "ずんだもん: こんにちは\n四国めたん: はじめまして"
        )

        # メソッド実行
        result = self.text_processor.generate_podcast_conversation("テスト論文")

        # 検証
        self.assertEqual("ずんだもん: こんにちは\n四国めたん: はじめまして", result)
        self.mock_prompt_manager.generate_podcast_conversation.assert_called_with(
            "テスト論文"
        )
        self.mock_gemini_model.generate_text.assert_called_with("テストプロンプト")
        self.mock_prompt_manager.convert_abstract_to_real_characters.assert_called_with(
            "Character1: こんにちは\nCharacter2: はじめまして"
        )

    def test_generate_podcast_conversation_no_api(self):
        """Test generating podcast conversation without valid API."""
        # APIが設定されていない状態
        self.text_processor.current_api_type = "openai"
        self.text_processor.use_openai = False
        self.text_processor.use_gemini = False

        # メソッド実行
        result = self.text_processor.generate_podcast_conversation("テスト論文")

        # 検証
        self.assertEqual(
            "Error: No API key is set or valid API type is not selected.", result
        )

    def test_convert_abstract_to_real_characters(self):
        """Test converting abstract characters to real characters."""
        self.mock_prompt_manager.convert_abstract_to_real_characters.return_value = (
            "ずんだもん: こんにちは"
        )
        result = self.text_processor.convert_abstract_to_real_characters(
            "Character1: こんにちは"
        )
        self.assertEqual(result, "ずんだもん: こんにちは")
        self.mock_prompt_manager.convert_abstract_to_real_characters.assert_called_with(
            "Character1: こんにちは"
        )

    def test_process_text_with_openai(self):
        """Test text processing with OpenAI API."""
        # OpenAIの設定
        self.text_processor.current_api_type = "openai"
        self.text_processor.use_openai = True

        # モックの設定
        with patch.object(
            self.text_processor,
            "generate_podcast_conversation",
            return_value="ずんだもん: こんにちは",
        ) as mock_gen:
            result = self.text_processor.process_text("Test text")
            self.assertEqual(result, "ずんだもん: こんにちは")
            mock_gen.assert_called_once_with("Test text")

    def test_process_text_with_gemini(self):
        """Test text processing with Gemini API."""
        # Geminiの設定
        self.text_processor.current_api_type = "gemini"
        self.text_processor.use_gemini = True

        # モックの設定
        with patch.object(
            self.text_processor,
            "generate_podcast_conversation",
            return_value="ずんだもん: こんにちは",
        ) as mock_gen:
            result = self.text_processor.process_text("Test text")
            self.assertEqual(result, "ずんだもん: こんにちは")
            mock_gen.assert_called_once_with("Test text")

    def test_process_text_no_api(self):
        """Test text processing without API configured."""
        # OpenAIタイプだがAPIキーが設定されていない
        self.text_processor.current_api_type = "openai"
        self.text_processor.use_openai = False

        result = self.text_processor.process_text("Test text")
        self.assertIn("OpenAI API key is not set", result)

        # GeminiタイプだがAPIキーが設定されていない
        self.text_processor.current_api_type = "gemini"
        self.text_processor.use_gemini = False

        result = self.text_processor.process_text("Test text")
        self.assertIn("Google Gemini API key is not set", result)

    def test_process_text_empty(self):
        """Test text processing with empty input."""
        result = self.text_processor.process_text("")
        self.assertEqual(result, "No text has been input for processing.")

    def test_get_token_usage_openai(self):
        """Test getting token usage information from OpenAI."""
        # OpenAIを使用
        self.text_processor.current_api_type = "openai"

        self.mock_openai_model.get_last_token_usage.return_value = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

        usage = self.text_processor.get_token_usage()
        self.assertEqual(100, usage.get("prompt_tokens"))
        self.assertEqual(50, usage.get("completion_tokens"))
        self.assertEqual(150, usage.get("total_tokens"))
        self.mock_openai_model.get_last_token_usage.assert_called_once()

    def test_get_token_usage_gemini(self):
        """Test getting token usage information from Gemini."""
        # Geminiを使用
        self.text_processor.current_api_type = "gemini"

        self.mock_gemini_model.get_last_token_usage.return_value = {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
        }

        usage = self.text_processor.get_token_usage()
        self.assertEqual(200, usage.get("prompt_tokens"))
        self.assertEqual(100, usage.get("completion_tokens"))
        self.assertEqual(300, usage.get("total_tokens"))
        self.mock_gemini_model.get_last_token_usage.assert_called_once()

    def test_set_model_name_openai(self):
        """Test setting OpenAI model name."""
        # OpenAIを使用
        self.text_processor.current_api_type = "openai"

        self.mock_openai_model.set_model_name.return_value = True
        result = self.text_processor.set_model_name("gpt-4.1")
        self.assertTrue(result)
        self.mock_openai_model.set_model_name.assert_called_with("gpt-4.1")

    def test_set_model_name_gemini(self):
        """Test setting Gemini model name."""
        # Geminiを使用
        self.text_processor.current_api_type = "gemini"

        self.mock_gemini_model.set_model_name.return_value = True
        result = self.text_processor.set_model_name("gemini-1.5-pro")
        self.assertTrue(result)
        self.mock_gemini_model.set_model_name.assert_called_with("gemini-1.5-pro")

    def test_get_current_model_openai(self):
        """Test getting current OpenAI model."""
        # OpenAIを使用
        self.text_processor.current_api_type = "openai"
        self.mock_openai_model.model_name = "gpt-4.1-mini"

        model = self.text_processor.get_current_model()
        self.assertEqual("gpt-4.1-mini", model)

    def test_get_current_model_gemini(self):
        """Test getting current Gemini model."""
        # Geminiを使用
        self.text_processor.current_api_type = "gemini"
        self.mock_gemini_model.model_name = "gemini-pro"

        model = self.text_processor.get_current_model()
        self.assertEqual("gemini-pro", model)

    def test_get_available_models_openai(self):
        """Test getting available OpenAI models."""
        # OpenAIを使用
        self.text_processor.current_api_type = "openai"

        self.mock_openai_model.get_available_models.return_value = [
            "gpt-4.1",
            "gpt-4.1-mini",
        ]
        models = self.text_processor.get_available_models()
        self.assertEqual(["gpt-4.1", "gpt-4.1-mini"], models)
        self.mock_openai_model.get_available_models.assert_called_once()

    def test_get_available_models_gemini(self):
        """Test getting available Gemini models."""
        # Geminiを使用
        self.text_processor.current_api_type = "gemini"

        self.mock_gemini_model.get_available_models.return_value = [
            "gemini-pro",
            "gemini-1.5-pro",
        ]
        models = self.text_processor.get_available_models()
        self.assertEqual(["gemini-pro", "gemini-1.5-pro"], models)
        self.mock_gemini_model.get_available_models.assert_called_once()

    def test_set_max_tokens_openai(self):
        """Test setting OpenAI max tokens."""
        # OpenAIを使用
        self.text_processor.current_api_type = "openai"

        self.mock_openai_model.set_max_tokens.return_value = True
        result = self.text_processor.set_max_tokens(1000)
        self.assertTrue(result)
        self.mock_openai_model.set_max_tokens.assert_called_with(1000)

    def test_set_max_tokens_gemini(self):
        """Test setting Gemini max tokens."""
        # Geminiを使用
        self.text_processor.current_api_type = "gemini"

        self.mock_gemini_model.set_max_tokens.return_value = True
        result = self.text_processor.set_max_tokens(2000)
        self.assertTrue(result)
        self.mock_gemini_model.set_max_tokens.assert_called_with(2000)

    def test_get_max_tokens_openai(self):
        """Test getting OpenAI max tokens."""
        # OpenAIを使用
        self.text_processor.current_api_type = "openai"

        self.mock_openai_model.get_max_tokens.return_value = 32768
        tokens = self.text_processor.get_max_tokens()
        self.assertEqual(32768, tokens)
        self.mock_openai_model.get_max_tokens.assert_called_once()

    def test_get_max_tokens_gemini(self):
        """Test getting Gemini max tokens."""
        # Geminiを使用
        self.text_processor.current_api_type = "gemini"

        self.mock_gemini_model.get_max_tokens.return_value = 8192
        tokens = self.text_processor.get_max_tokens()
        self.assertEqual(8192, tokens)
        self.mock_gemini_model.get_max_tokens.assert_called_once()

    def test_set_character_mapping(self):
        """Test setting character mapping."""
        self.mock_prompt_manager.set_character_mapping.return_value = True
        result = self.text_processor.set_character_mapping("ずんだもん", "四国めたん")
        self.assertTrue(result)
        self.mock_prompt_manager.set_character_mapping.assert_called_with(
            "ずんだもん", "四国めたん"
        )

    def test_get_character_mapping(self):
        """Test getting character mapping."""
        self.mock_prompt_manager.get_character_mapping.return_value = {
            "Character1": "ずんだもん",
            "Character2": "四国めたん",
        }
        mapping = self.text_processor.get_character_mapping()
        self.assertEqual("ずんだもん", mapping["Character1"])
        self.assertEqual("四国めたん", mapping["Character2"])
        self.mock_prompt_manager.get_character_mapping.assert_called_once()

    def test_set_document_type(self):
        """Test setting document type."""
        # 正常系のテスト - 有効なドキュメントタイプ
        self.mock_prompt_manager.set_document_type.return_value = True
        result = self.text_processor.set_document_type(DocumentType.PAPER)
        self.assertTrue(result)

        # 正常系のテスト - blog
        self.mock_prompt_manager.set_document_type.reset_mock()
        result = self.text_processor.set_document_type(DocumentType.BLOG)
        self.assertTrue(result)

    def test_get_document_type(self):
        """Test getting document type."""
        from yomitalk.prompt_manager import DocumentType

        # モックオブジェクトの設定
        mock_document_type = MagicMock(spec=DocumentType)
        # TextProcessorは、prompt_manager.get_document_type()を呼び出すのではなく、
        # prompt_manager.current_document_typeプロパティを直接参照している
        self.mock_prompt_manager.current_document_type = mock_document_type

        # メソッドを実行して結果を取得
        result = self.text_processor.get_document_type()

        # prompt_manager.get_document_typeは呼び出されないので、assertIsで結果を検証
        self.assertIs(result, mock_document_type)

    def test_get_document_type_name(self):
        """Test getting document type name."""
        self.mock_prompt_manager.get_document_type_name.return_value = "論文"
        result = self.text_processor.get_document_type_name()
        self.assertEqual(result, "論文")
        self.mock_prompt_manager.get_document_type_name.assert_called_once()
