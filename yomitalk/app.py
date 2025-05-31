#!/usr/bin/env python3

"""Main application module.

Builds the Paper Podcast Generator application using Gradio.
"""
import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from yomitalk.common import APIType
from yomitalk.common.character import DISPLAY_NAMES
from yomitalk.components.audio_generator import (
    AudioGenerator,
    initialize_global_voicevox_manager,
)
from yomitalk.components.content_extractor import ContentExtractor
from yomitalk.components.text_processor import TextProcessor
from yomitalk.models.gemini_model import GeminiModel
from yomitalk.models.openai_model import OpenAIModel
from yomitalk.prompt_manager import DocumentType, PodcastMode
from yomitalk.utils.logger import logger
from yomitalk.utils.session_manager import SessionManager

# Check for base directories
os.makedirs("data/temp", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

# Initialize global VOICEVOX Core manager once for all users
# This is done at application startup, outside of any function
logger.info("Initializing global VOICEVOX Core manager for all users")
global_voicevox_manager = initialize_global_voicevox_manager()

# E2E test mode for faster startup
E2E_TEST_MODE = os.environ.get("E2E_TEST_MODE", "false").lower() == "true"

# Default port
DEFAULT_PORT = 7860


# User session data structure for managing per-user state
class UserSession:
    """Class for managing per-user session data."""

    def __init__(self, session_id: str):
        """Initialize user session with unique session ID."""
        self.session_id = session_id
        self.session_manager = SessionManager()

        # Initialize per-user components
        self.content_extractor = ContentExtractor()
        self.text_processor = TextProcessor()
        self.audio_generator = AudioGenerator(
            session_output_dir=self.session_manager.get_output_dir(),
            session_temp_dir=self.session_manager.get_talk_temp_dir(),
        )

        # Default API type is Gemini
        self.text_processor.set_api_type(APIType.GEMINI)

        logger.info(f"User session initialized: {session_id}")

    @property
    def current_document_type(self) -> str:
        """Get current document type label name.

        Returns:
            str: Current document type label name
        """
        return self.text_processor.prompt_manager.current_document_type.label_name

    @property
    def current_podcast_mode(self) -> str:
        """Get current podcast mode label name.

        Returns:
            str: Current podcast mode label name
        """
        return self.text_processor.prompt_manager.current_mode.label_name

    @property
    def current_character_mapping(self) -> Tuple[str, str]:
        """Get current character mapping.

        Returns:
            Tuple[str, str]: (character1, character2)
        """
        char_mapping = self.text_processor.prompt_manager.char_mapping
        return char_mapping["Character1"], char_mapping["Character2"]

    @property
    def openai_max_tokens(self) -> int:
        """Get current OpenAI max tokens.

        Returns:
            int: Current OpenAI max tokens
        """
        return self.text_processor.openai_model.get_max_tokens()

    @property
    def gemini_max_tokens(self) -> int:
        """Get current Gemini max tokens.

        Returns:
            int: Current Gemini max tokens
        """
        return self.text_processor.gemini_model.get_max_tokens()

    def get_ui_sync_values(self) -> Tuple[str, str, str, str, int, int]:
        """Get values for syncing UI components with session state.

        Returns:
            Tuple[str, str, str, str, int, int]: (document_type, podcast_mode, character1, character2, openai_max_tokens, gemini_max_tokens)
        """
        character1, character2 = self.current_character_mapping
        return (
            self.current_document_type,
            self.current_podcast_mode,
            character1,
            character2,
            self.openai_max_tokens,
            self.gemini_max_tokens,
        )

    def cleanup(self):
        """Clean up session resources."""
        logger.info(f"Cleaning up user session: {self.session_id}")
        self.session_manager.cleanup_session_data()


# Application class
class PaperPodcastApp:
    """Main class for the Paper Podcast Generator application."""

    def __init__(self):
        """Initialize the PaperPodcastApp."""
        logger.info("Initializing PaperPodcastApp for multi-user support")

    @staticmethod
    def get_static_openai_models() -> Tuple[List[str], str]:
        """Get OpenAI models and default model without requiring UserSession."""
        return OpenAIModel.DEFAULT_MODELS.copy(), OpenAIModel.DEFAULT_MODEL

    @staticmethod
    def get_static_gemini_models() -> Tuple[List[str], str]:
        """Get Gemini models and default model without requiring UserSession."""
        return GeminiModel.DEFAULT_MODELS.copy(), GeminiModel.DEFAULT_MODEL

    @staticmethod
    def get_static_openai_max_tokens() -> int:
        """Get OpenAI default max tokens."""
        return OpenAIModel.DEFAULT_MAX_TOKENS

    @staticmethod
    def get_static_gemini_max_tokens() -> int:
        """Get Gemini default max tokens."""
        return GeminiModel.DEFAULT_MAX_TOKENS

    @staticmethod
    def get_static_document_types() -> Tuple[List[str], str]:
        """Get document type choices and default without requiring UserSession."""
        from yomitalk.prompt_manager import PromptManager

        return PromptManager.get_default_document_type_info()

    @staticmethod
    def get_static_podcast_modes() -> Tuple[List[str], str]:
        """Get podcast mode choices and default without requiring UserSession."""
        from yomitalk.prompt_manager import PromptManager

        return PromptManager.get_default_podcast_mode_info()

    @staticmethod
    def get_static_characters() -> Tuple[List[str], str, str]:
        """Get character choices and defaults without requiring UserSession."""
        from yomitalk.prompt_manager import PromptManager

        return PromptManager.get_default_character_info()

    def create_user_session(self, request: gr.Request) -> UserSession:
        """Create a new user session with unique session ID."""
        session_id = request.session_hash
        return UserSession(session_id)

    def set_openai_api_key(self, api_key: str, user_session: UserSession):
        """Set the OpenAI API key for the specific user session."""
        if not api_key or api_key.strip() == "":
            logger.warning("OpenAI API key is empty")
            return user_session

        success = user_session.text_processor.set_openai_api_key(api_key)
        logger.debug(
            f"OpenAI API key set for session {user_session.session_id}: {success}"
        )
        return user_session

    def set_gemini_api_key(self, api_key: str, user_session: UserSession):
        """Set the Google Gemini API key for the specific user session."""
        if not api_key or api_key.strip() == "":
            logger.warning("Gemini API key is empty")
            return user_session

        success = user_session.text_processor.set_gemini_api_key(api_key)
        logger.debug(
            f"Gemini API key set for session {user_session.session_id}: {success}"
        )
        return user_session

    def switch_llm_type(
        self, api_type: APIType, user_session: UserSession
    ) -> UserSession:
        """Switch LLM type for the specific user session."""
        success = user_session.text_processor.set_api_type(api_type)
        if success:
            logger.debug(
                f"LLM type switched to {api_type.display_name} for session {user_session.session_id}"
            )
        else:
            logger.warning(
                f"{api_type.display_name} API key not set for session {user_session.session_id}"
            )
        return user_session

    def extract_file_text(
        self, file_obj, user_session: UserSession
    ) -> Tuple[str, UserSession]:
        """Extract text from a file for the specific user session."""
        if file_obj is None:
            logger.warning("No file selected for extraction")
            return "Please upload a file.", user_session

        text = user_session.content_extractor.extract_text(file_obj)
        logger.debug(f"Text extraction completed for session {user_session.session_id}")
        return text, user_session

    def generate_podcast_text(
        self, text: str, user_session: UserSession
    ) -> Tuple[str, UserSession]:
        """Generate podcast-style text from input text for the specific user session."""
        if not text:
            logger.warning("Podcast text generation: Input text is empty")
            return "Please upload a file and extract text first.", user_session

        # Check if API key is set
        current_llm_type = user_session.text_processor.get_current_api_type()

        if (
            current_llm_type == APIType.OPENAI
            and not user_session.text_processor.openai_model.has_api_key()
        ):
            logger.warning(
                f"Podcast text generation: OpenAI API key not set for session {user_session.session_id}"
            )
            return (
                "OpenAI API key is not set. Please configure it in the Settings tab.",
                user_session,
            )
        elif (
            current_llm_type == APIType.GEMINI
            and not user_session.text_processor.gemini_model.has_api_key()
        ):
            logger.warning(
                f"Podcast text generation: Gemini API key not set for session {user_session.session_id}"
            )
            return (
                "Google Gemini API key is not set. Please configure it in the Settings tab.",
                user_session,
            )

        try:
            podcast_text = user_session.text_processor.process_text(text)

            token_usage = user_session.text_processor.get_token_usage()
            if token_usage:
                usage_msg = f"Token usage: input {token_usage.get('prompt_tokens', 0)}, output {token_usage.get('completion_tokens', 0)}, total {token_usage.get('total_tokens', 0)}"
                logger.debug(usage_msg)

            logger.debug(
                f"Podcast text generation completed for session {user_session.session_id}"
            )
            return podcast_text, user_session
        except Exception as e:
            error_msg = f"Podcast text generation error: {str(e)}"
            logger.error(error_msg)
            return f"Error: {str(e)}", user_session

    def generate_podcast_audio_streaming(
        self, text: str, user_session: UserSession, progress=gr.Progress()
    ):
        """
        Generate streaming audio from podcast text.
        最終的な音声ファイルも生成し、クラス変数に保持する
        進捗情報もクラス変数に保存する（進捗表示は行わない）

        Args:
            text (str): Generated podcast text
            progress (gr.Progress): Gradio Progress object (not used directly)

        Yields:
            str: Path to audio file chunks for streaming playback
        """
        if not text:
            logger.warning("Streaming audio generation: Text is empty")
            yield None
            return

        # Check if VOICEVOX Core is available
        if not user_session.audio_generator.core_initialized:
            logger.error("Streaming audio generation: VOICEVOX Core is not available")
            yield None
            return

        try:
            # 初回のyieldを行って、Gradioのストリーミングモードを確実に有効化
            logger.debug("Initializing streaming audio generation")
            yield None

            # ストリーミング用の各パートのパスを保存
            parts_paths = []
            final_combined_path = None

            # 個別の音声パートを生成・ストリーミング
            for (
                audio_path
            ) in user_session.audio_generator.generate_character_conversation(text):
                if not audio_path:
                    continue

                filename = os.path.basename(audio_path)

                # 'part_'を含むものは部分音声ファイル、'audio_'から始まるものは最終結合ファイル
                if "part_" in filename:
                    parts_paths.append(audio_path)
                    logger.debug(f"ストリーム音声パーツ ({len(parts_paths)}): {audio_path}")
                    yield audio_path  # ストリーミング再生用にyield
                    time.sleep(0.05)  # 連続再生のタイミング調整
                elif filename.startswith("audio_"):
                    # 最終結合ファイルの場合
                    final_combined_path = audio_path
                    logger.info(f"結合済み最終音声ファイルを受信: {final_combined_path}")

            # 音声生成の完了処理
            self._finalize_audio_generation(
                final_combined_path, parts_paths, user_session
            )

        except Exception as e:
            logger.error(f"Streaming audio generation exception: {str(e)}")
            user_session.audio_generator.audio_generation_progress = 0.0  # エラー時は進捗をリセット
            yield None

    def _finalize_audio_generation(
        self, final_combined_path, parts_paths, user_session: UserSession
    ):
        """
        音声生成の最終処理を行う

        Args:
            final_combined_path (str): 結合された最終音声ファイルのパス
            parts_paths (List[str]): 部分音声ファイルのパスのリスト
        """
        # 最終結合ファイルのパスが取得できた場合
        if final_combined_path and os.path.exists(final_combined_path):
            # 進捗を更新
            user_session.audio_generator.audio_generation_progress = 0.9
            logger.info(f"最終結合音声ファイル: {final_combined_path}")

            # 最終的な音声ファイルのパスを保存
            user_session.audio_generator.final_audio_path = final_combined_path

            # ファイルの書き込みを確実にするため少し待機
            time.sleep(0.2)

            if os.path.exists(final_combined_path):
                filesize = os.path.getsize(final_combined_path)
                # 進捗を完了状態に更新
                user_session.audio_generator.audio_generation_progress = 1.0
                logger.info(
                    f"音声生成完了: {final_combined_path} (ファイルサイズ: {filesize} bytes)"
                )
            else:
                logger.error(f"ファイルが存在しなくなりました: {final_combined_path}")
                self._use_fallback_audio(parts_paths, user_session)

        # 最終結合ファイルがない場合はフォールバック処理
        else:
            self._use_fallback_audio(parts_paths, user_session)

    def _use_fallback_audio(self, parts_paths, user_session: UserSession):
        """
        結合ファイルが取得できない場合のフォールバック処理

        Args:
            parts_paths (List[str]): 部分音声ファイルのパスのリスト
        """
        # 部分音声ファイルがある場合は最後のパートを使用
        if parts_paths:
            logger.warning("結合音声ファイルを取得できなかったため、最後のパートを使用します")
            user_session.audio_generator.final_audio_path = parts_paths[-1]
            user_session.audio_generator.audio_generation_progress = 1.0

            if os.path.exists(parts_paths[-1]):
                filesize = os.path.getsize(parts_paths[-1])
                logger.info(
                    f"部分音声ファイル使用: {parts_paths[-1]} (ファイルサイズ: {filesize} bytes)"
                )
            else:
                logger.error(f"フォールバックファイルも存在しません: {parts_paths[-1]}")
                user_session.audio_generator.audio_generation_progress = 0.0
        else:
            logger.warning("音声ファイルが生成されませんでした")
            user_session.audio_generator.audio_generation_progress = 0.0

    def disable_generate_button(self):
        """音声生成ボタンを無効化します。

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        return gr.update(interactive=False, value="音声生成中...")

    def enable_generate_button(self, podcast_text):
        """音声生成ボタンを再び有効化します。

        Args:
            podcast_text (str): 生成されたトーク原稿（状態確認用）

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        has_text = podcast_text and podcast_text.strip() != ""
        return gr.update(
            interactive=True,
            value="音声を生成",
            variant="primary" if has_text else "secondary",
        )

    def disable_process_button(self):
        """トーク原稿生成ボタンを無効化します。

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        return gr.update(interactive=False, value="トーク原稿生成中...")

    def enable_process_button(self, extracted_text, user_session: UserSession):
        """トーク原稿生成ボタンを再び有効化します。

        Args:
            extracted_text (str): テキストエリアの内容（状態確認用）

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        # 現在のAPIキーとテキストの状態に基づいてボタンの状態を更新
        has_text = (
            extracted_text
            and extracted_text.strip() != ""
            and extracted_text
            not in ["Please upload a file.", "Failed to process the file."]
        )
        has_api_key = False

        current_llm_type = user_session.text_processor.get_current_api_type()
        if current_llm_type == APIType.OPENAI:
            has_api_key = user_session.text_processor.openai_model.has_api_key()
        elif current_llm_type == APIType.GEMINI:
            has_api_key = user_session.text_processor.gemini_model.has_api_key()

        is_enabled = has_text and has_api_key

        return gr.update(
            interactive=is_enabled,
            value="トーク原稿を生成",
            variant="primary" if is_enabled else "secondary",
        )

    def ui(self) -> gr.Blocks:
        """
        Create the Gradio interface.

        Returns:
            gr.Blocks: Gradio Blocks instance
        """
        app = gr.Blocks(
            title="Yomitalk",
            css="footer {display: none !important;}",
            theme=gr.themes.Soft(),
        )

        # アプリケーション全体でキューイングを有効化
        # Hugging Face Spacesの無料CPUを効率的に使うため、同時実行数を1に制限
        app.queue(
            default_concurrency_limit=1,  # デフォルトの同時実行数を1に制限
            api_open=False,  # APIアクセスを制限
            max_size=5,  # キュー内の最大タスク数を制限
            status_update_rate=1,  # ステータス更新頻度（秒）
        )

        with app:
            # ヘッダー部分をロゴと免責事項を含むレイアウトに変更
            with gr.Row(equal_height=True, variant="panel", elem_classes="header-row"):
                with gr.Column(scale=1, min_width=200, elem_classes="logo-column"):
                    gr.Image(
                        "assets/images/logo.png",
                        show_label=False,
                        show_download_button=False,
                        show_fullscreen_button=False,
                        container=False,
                        scale=1,
                    )
                with gr.Column(scale=3, elem_classes="disclaimer-column"):
                    with gr.Row(elem_id="disclaimer-container"):
                        gr.Markdown(
                            """**ドキュメントからポッドキャスト風の解説音声を生成するアプリケーション**

                            **免責事項**: このアプリケーションはLLM（大規模言語モデル）を使用しています。生成される内容の正確性、完全性、適切性について保証することはできません。
                            また、秘密文書のアップロードは推奨されません。当アプリケーションの使用により生じた、いかなる損害についても責任を負いません。""",
                            elem_id="disclaimer-text",
                        )

            # カスタムCSSスタイルを追加
            css = """
            /* ロゴ画像のスタイル調整 */
            .gradio-image {
                margin: 0 !important;
                padding: 0 !important;
                display: flex !important;
                align-items: flex-end !important;
            }

            /* ロゴ画像コンテナの左余白を削除 */
            .gradio-column:has(> .gradio-image) {
                padding-left: 0 !important;
            }

            /* ヘッダー行のスタイル調整 */
            .header-row {
                display: flex !important;
                align-items: flex-end !important;
                min-height: 80px !important;
            }

            /* 免責事項の列のスタイル調整 */
            .disclaimer-column {
                display: flex !important;
                align-items: flex-end !important;
            }

            /* 免責事項のコンテナスタイル */
            #disclaimer-container {
                display: flex !important;
                align-items: flex-end !important;
                height: 100% !important;
                margin-bottom: 0 !important;
                padding: 5px 0 !important;
                width: 100% !important;
            }

            /* 免責事項のテキストスタイル */
            #disclaimer-text p {
                margin: 0 !important;
                padding-bottom: 5px !important;
                font-size: 0.9em !important;
                line-height: 1.4 !important;
                max-width: 100% !important;
            }

            /* オーディオ出力のスタイル調整 */
            #audio_output {
                min-height: 180px !important;
                margin-bottom: 10px;
            }

            #audio_output.empty::before {
                content: "音声生成が完了すると、ここに波形と再生コントロールが表示されます";
                display: flex;
                justify-content: center;
                align-items: center;
                height: 140px;
                color: #555;
                font-style: italic;
                background-color: rgba(0,0,0,0.03);
                border-radius: 8px;
                text-align: center;
                padding: 10px;
            }

            #streaming_audio_output.empty::before {
                content: "音声生成が開始されると、ここでストリーミング再生できます";
                display: flex;
                justify-content: center;
                align-items: center;
                height: 80px;
                color: #555;
                font-style: italic;
                background-color: rgba(0,0,0,0.03);
                border-radius: 8px;
                text-align: center;
                padding: 10px;
            }
            """
            gr.HTML(f"<style>{css}</style>")

            with gr.Column():
                gr.Markdown("""## トーク原稿の生成""")
                with gr.Column(variant="panel"):
                    # サポートしているファイル形式の拡張子を取得
                    # UIの初期化時は一時的なContentExtractorインスタンスを使用
                    from yomitalk.components.content_extractor import ContentExtractor

                    temp_extractor = ContentExtractor()
                    supported_extensions = temp_extractor.get_supported_extensions()

                    # ファイルをアップロードするコンポーネント
                    file_input = gr.File(
                        file_types=supported_extensions,
                        type="filepath",
                        label=f"解説対象ファイルをアップロード（{', '.join(supported_extensions)}）",
                    )

                    extracted_text = gr.Textbox(
                        label="解説対象テキスト（トークの元ネタ）",
                        placeholder="ファイルをアップロードするか、直接ここにテキストを貼り付けてください...",
                        lines=10,
                    )

                with gr.Column(variant="panel"):
                    gr.Markdown("### プロンプト設定")

                    # Get document type info from PromptManager
                    (
                        doc_type_choices,
                        doc_type_default,
                    ) = self.get_static_document_types()
                    document_type_radio = gr.Radio(
                        choices=doc_type_choices,
                        value=doc_type_default,  # 後でユーザーセッションの値で更新される
                        label="ドキュメントタイプ",
                        elem_id="document_type_radio_group",
                    )

                    # Get podcast mode info from PromptManager
                    (
                        podcast_mode_choices,
                        podcast_mode_default,
                    ) = self.get_static_podcast_modes()
                    podcast_mode_radio = gr.Radio(
                        choices=podcast_mode_choices,
                        value=podcast_mode_default,  # 後でユーザーセッションの値で更新される
                        label="生成モード",
                        elem_id="podcast_mode_radio_group",
                    )

                    # キャラクター設定
                    with gr.Accordion(label="キャラクター設定", open=False):
                        with gr.Row():
                            # Get character info from PromptManager
                            (
                                char_choices,
                                char1_default,
                                char2_default,
                            ) = self.get_static_characters()
                            character1_dropdown = gr.Dropdown(
                                choices=char_choices,
                                value=char1_default,  # 後でユーザーセッションの値で更新される
                                label="キャラクター1（専門家役）",
                            )
                            character2_dropdown = gr.Dropdown(
                                choices=char_choices,
                                value=char2_default,  # 後でユーザーセッションの値で更新される
                                label="キャラクター2（初学者役）",
                            )

                with gr.Column(variant="panel"):
                    # LLM API設定タブ
                    llm_tabs = gr.Tabs()
                    with llm_tabs:
                        with gr.TabItem("Google Gemini") as gemini_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    gemini_api_key_input = gr.Textbox(
                                        placeholder="AIza...",
                                        type="password",
                                        label="Google Gemini APIキー",
                                        info="APIキーの取得: https://aistudio.google.com/app/apikey",
                                    )
                                with gr.Column(scale=2):
                                    # Get Gemini models from model class
                                    (
                                        gemini_models,
                                        gemini_default,
                                    ) = self.get_static_gemini_models()
                                    gemini_model_dropdown = gr.Dropdown(
                                        choices=gemini_models,
                                        value=gemini_default,
                                        label="モデル",
                                    )
                            with gr.Row():
                                gemini_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=65536,
                                    value=self.get_static_gemini_max_tokens(),
                                    step=100,
                                    label="最大トークン数",
                                )

                        with gr.TabItem("OpenAI") as openai_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    openai_api_key_input = gr.Textbox(
                                        placeholder="sk-...",
                                        type="password",
                                        label="OpenAI APIキー",
                                        info="APIキーの取得: https://platform.openai.com/api-keys",
                                    )
                                with gr.Column(scale=2):
                                    # Get OpenAI models from model class
                                    (
                                        openai_models,
                                        openai_default,
                                    ) = self.get_static_openai_models()
                                    openai_model_dropdown = gr.Dropdown(
                                        choices=openai_models,
                                        value=openai_default,
                                        label="モデル",
                                    )
                            with gr.Row():
                                openai_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=32768,
                                    value=self.get_static_openai_max_tokens(),
                                    step=100,
                                    label="最大トークン数",
                                )

                    # トーク原稿を生成ボタン
                    process_btn = gr.Button(
                        "トーク原稿を生成", variant="secondary", interactive=False
                    )
                    podcast_text = gr.Textbox(
                        label="生成されたトーク原稿",
                        placeholder="テキストを処理してトーク原稿を生成してください...",
                        lines=15,
                    )

                    # トークン使用状況の表示
                    token_usage_info = gr.HTML(
                        "<div>トークン使用状況: まだ生成されていません</div>", elem_id="token-usage-info"
                    )

            with gr.Column():
                gr.Markdown("## トーク音声の生成")
                with gr.Column(variant="panel"):
                    msg = """音声は下記の音源を使用して生成されます。
                    VOICEVOX:四国めたん、VOICEVOX:ずんだもん、VOICEVOX:九州そら、VOICEVOX:中国うさぎ、VOICEVOX:中部つるぎ
                    音声を生成するには[VOICEVOX 音源利用規約](https://zunko.jp/con_ongen_kiyaku.html)への同意が必要です。
                    """
                    # VOICEVOX利用規約チェックボックスをここに配置
                    terms_checkbox = gr.Checkbox(
                        label="VOICEVOX 音源利用規約に同意する",
                        value=False,
                        info=msg,
                    )
                    generate_btn = gr.Button(
                        "音声を生成", variant="primary", interactive=False
                    )

                    # ストリーミング再生用のオーディオコンポーネント
                    streaming_audio_output = gr.Audio(
                        type="filepath",
                        format="wav",
                        interactive=False,
                        show_download_button=False,
                        show_label=True,
                        label="プレビュー",
                        value=None,
                        elem_id="streaming_audio_output",
                        streaming=True,
                    )

                    # 最終的な音声ファイル用のオーディオコンポーネント
                    # NOTE: gradioの仕様上, ストリーミング用のAudioでは波形が表示できないため, このコンポーネントで波形を表示する
                    audio_output = gr.Audio(
                        type="filepath",
                        format="wav",
                        interactive=False,
                        show_download_button=True,
                        show_label=True,
                        label="完成音声",
                        value=None,
                        elem_id="audio_output",
                        waveform_options=gr.WaveformOptions(
                            show_recording_waveform=True,
                            waveform_color="#3498db",
                            waveform_progress_color="#27ae60",
                        ),
                        min_width=300,
                    )

            # Initialize user session and sync UI components with session values
            user_session = gr.State()
            app.load(
                fn=self.create_user_session, outputs=[user_session], queue=False
            ).then(
                # ユーザーセッション作成後にUIコンポーネントの値を同期
                fn=self.sync_ui_with_session,
                inputs=[user_session],
                outputs=[
                    document_type_radio,
                    podcast_mode_radio,
                    character1_dropdown,
                    character2_dropdown,
                    openai_max_tokens_slider,
                    gemini_max_tokens_slider,
                ],
                queue=False,
            )

            # Set up event handlers
            # ファイルがアップロードされたら自動的にテキストを抽出（大きなファイルの場合は時間がかかるのでキューイング）
            file_input.change(
                fn=self.extract_file_text,
                inputs=[file_input, user_session],
                outputs=[extracted_text, user_session],
                concurrency_limit=1,  # 同時実行数を1に制限（Hugging Face Spaces対応）
                concurrency_id="file_queue",  # ファイル処理用キューID
            ).then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # OpenAI API key - ユーザが入力したらすぐに保存
            openai_api_key_input.change(
                fn=self.set_openai_api_key,
                inputs=[openai_api_key_input, user_session],
                outputs=[user_session],
            ).then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # Gemini API key
            gemini_api_key_input.change(
                fn=self.set_gemini_api_key,
                inputs=[gemini_api_key_input, user_session],
                outputs=[user_session],
            ).then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # タブ切り替え時のLLMタイプ変更
            gemini_tab.select(
                fn=lambda user_session: self.switch_llm_type(
                    APIType.GEMINI, user_session
                ),
                inputs=[user_session],
                outputs=[user_session],
            )

            openai_tab.select(
                fn=lambda user_session: self.switch_llm_type(
                    APIType.OPENAI, user_session
                ),
                inputs=[user_session],
                outputs=[user_session],
            )

            # OpenAI Model selection
            openai_model_dropdown.change(
                fn=self.set_openai_model_name,
                inputs=[openai_model_dropdown, user_session],
                outputs=[user_session],
            )

            # Gemini Model selection
            gemini_model_dropdown.change(
                fn=self.set_gemini_model_name,
                inputs=[gemini_model_dropdown, user_session],
                outputs=[user_session],
            )

            # OpenAI Max tokens selection
            openai_max_tokens_slider.change(
                fn=self.set_openai_max_tokens,
                inputs=[openai_max_tokens_slider, user_session],
                outputs=[user_session],
            )

            # Gemini Max tokens selection
            gemini_max_tokens_slider.change(
                fn=self.set_gemini_max_tokens,
                inputs=[gemini_max_tokens_slider, user_session],
                outputs=[user_session],
            )

            character1_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown, user_session],
                outputs=[user_session],
            )

            character2_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown, user_session],
                outputs=[user_session],
            )

            # VOICEVOX Terms checkbox - 音声生成ボタンに対してイベントハンドラを更新
            terms_checkbox.change(
                fn=self.update_audio_button_state,
                inputs=[terms_checkbox, podcast_text],
                outputs=[generate_btn],
            )

            # トーク原稿の生成処理（時間のかかるLLM処理なのでキューイングを適用）
            # 1. まずボタンを無効化
            process_events = process_btn.click(
                fn=self.disable_process_button,
                inputs=[],
                outputs=[process_btn],
                queue=False,  # 即時実行
                api_name="disable_process_button",
            )

            # 2. トーク原稿の生成処理
            process_events.then(
                fn=self.generate_podcast_text,
                inputs=[extracted_text, user_session],
                outputs=[podcast_text, user_session],
                concurrency_limit=1,  # 同時実行数を1に制限（Hugging Face Spaces対応）
                concurrency_id="llm_queue",  # LLM関連のリクエスト用キューID
            ).then(
                # トークン使用状況をUIに反映
                fn=self.update_token_usage_display,
                inputs=[user_session],
                outputs=[token_usage_info],
            ).then(
                # トーク原稿生成後に音声生成ボタンの状態を更新
                fn=self.update_audio_button_state,
                inputs=[terms_checkbox, podcast_text],
                outputs=[generate_btn],
            ).then(
                # 3. 最後にトーク原稿生成ボタンを再度有効化
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
                queue=False,  # 即時実行
                api_name="enable_process_button",
            )

            # 音声生成ボタンのイベントハンドラ（ストリーミング再生と最終波形表示を並列処理）

            # ボタンを無効化する（クリック時）
            disable_btn_event = generate_btn.click(
                fn=self.disable_generate_button,
                inputs=[],
                outputs=[generate_btn],
                queue=False,  # 即時実行
                api_name="disable_generate_button",
            )

            # 0. 音声生成状態をリセットしてストリーミング再生コンポーネントをクリア
            audio_events = disable_btn_event.then(
                fn=self.reset_audio_state_and_components,
                inputs=[user_session],
                outputs=[streaming_audio_output],
                concurrency_id="audio_reset",
                concurrency_limit=1,  # 同時実行数を1に制限
                api_name="reset_audio_state",
            )

            # 1. ストリーミング再生開始 (音声パーツ生成とストリーミング再生)
            audio_events.then(
                fn=self.generate_podcast_audio_streaming,
                inputs=[podcast_text, user_session],
                outputs=[streaming_audio_output],
                concurrency_limit=1,  # 音声生成は1つずつ実行
                concurrency_id="audio_queue",  # 音声生成用キューID
                show_progress=False,  # ストリーミング表示では独自の進捗バーを表示しない
                api_name="generate_streaming_audio",  # APIエンドポイント名（デバッグ用）
            )

            # 2. 波形表示用のコンポーネントを更新 (進捗表示とともに最終波形表示)
            # こちらは独立したイベントとして実行し、音声生成の進捗を表示してから最終ファイルを返す
            wave_display_event = generate_btn.click(
                fn=self.wait_for_audio_completion,
                inputs=[podcast_text, user_session],
                outputs=[audio_output],
                concurrency_limit=1,  # 同時実行数を1に制限
                concurrency_id="progress_queue",  # 進捗表示用キューID
                show_progress=True,  # 進捗バーを表示（関数内で更新）
                api_name="update_progress_display",  # APIエンドポイント名（デバッグ用）
            )

            # 3. 処理完了後にボタンを再度有効化
            wave_display_event.then(
                fn=self.enable_generate_button,
                inputs=[podcast_text],
                outputs=[generate_btn],
                queue=False,  # 即時実行
                api_name="enable_generate_button",
            )

            # ドキュメントタイプ選択のイベントハンドラ
            document_type_radio.change(
                fn=self.set_document_type,
                inputs=[document_type_radio, user_session],
                outputs=[user_session],
            )

            # ポッドキャストモード選択のイベントハンドラ
            podcast_mode_radio.change(
                fn=self.set_podcast_mode,
                inputs=[podcast_mode_radio, user_session],
                outputs=[user_session],
            )

            # podcast_textの変更時にも音声生成ボタンの状態を更新
            podcast_text.change(
                fn=self.update_audio_button_state,
                inputs=[terms_checkbox, podcast_text],
                outputs=[generate_btn],
            )

            # Note: Gradio's unload event doesn't support session-specific cleanup
            # Session cleanup will be handled by garbage collection or periodic cleanup

        return app

    def get_openai_available_models(self, user_session: UserSession) -> List[str]:
        """
        利用可能なOpenAIモデルのリストを取得します。

        Returns:
            List[str]: 利用可能なモデル名のリスト
        """
        return user_session.text_processor.openai_model.get_available_models()

    def get_openai_current_model(self, user_session: UserSession) -> str:
        """
        現在設定されているOpenAIモデル名を取得します。

        Returns:
            str: 現在のモデル名
        """
        return user_session.text_processor.openai_model.model_name

    def get_gemini_available_models(self, user_session: UserSession) -> List[str]:
        """
        利用可能なGeminiモデルのリストを取得します。

        Returns:
            List[str]: 利用可能なモデル名のリスト
        """
        return user_session.text_processor.gemini_model.get_available_models()

    def get_gemini_current_model(self, user_session: UserSession) -> str:
        """
        現在設定されているGeminiモデル名を取得します。

        Returns:
            str: 現在のモデル名
        """
        return user_session.text_processor.gemini_model.model_name

    def set_openai_model_name(
        self, model_name: str, user_session: UserSession
    ) -> UserSession:
        """
        OpenAIモデル名を設定します。

        Args:
            model_name (str): 使用するモデル名
        """
        success = user_session.text_processor.openai_model.set_model_name(model_name)
        logger.debug(f"OpenAI model set to {model_name}: {success}")
        return user_session

    def set_gemini_model_name(
        self, model_name: str, user_session: UserSession
    ) -> UserSession:
        """
        Geminiモデル名を設定します。

        Args:
            model_name (str): 使用するモデル名
        """
        success = user_session.text_processor.gemini_model.set_model_name(model_name)
        logger.debug(f"Gemini model set to {model_name}: {success}")
        return user_session

    def get_openai_max_tokens(self, user_session: UserSession) -> int:
        """
        現在設定されているOpenAIの最大トークン数を取得します。

        Returns:
            int: 現在の最大トークン数
        """
        return user_session.text_processor.openai_model.get_max_tokens()

    def get_gemini_max_tokens(self, user_session: UserSession) -> int:
        """
        現在設定されているGeminiの最大トークン数を取得します。

        Returns:
            int: 現在の最大トークン数
        """
        return user_session.text_processor.gemini_model.get_max_tokens()

    def set_openai_max_tokens(
        self, max_tokens: int, user_session: UserSession
    ) -> UserSession:
        """
        OpenAIの最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数
        """
        success = user_session.text_processor.openai_model.set_max_tokens(max_tokens)
        logger.debug(f"OpenAI max tokens set to {max_tokens}: {success}")
        return user_session

    def set_gemini_max_tokens(
        self, max_tokens: int, user_session: UserSession
    ) -> UserSession:
        """
        Geminiの最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数
        """
        success = user_session.text_processor.gemini_model.set_max_tokens(max_tokens)
        logger.debug(f"Gemini max tokens set to {max_tokens}: {success}")
        return user_session

    def get_available_characters(self) -> List[str]:
        """利用可能なキャラクターのリストを取得します。

        Returns:
            List[str]: 利用可能なキャラクター名のリスト
        """
        return DISPLAY_NAMES

    def set_character_mapping(
        self, character1: str, character2: str, user_session: UserSession
    ) -> UserSession:
        """キャラクターマッピングを設定します。

        Args:
            character1 (str): Character1に割り当てるキャラクター名
            character2 (str): Character2に割り当てるキャラクター名
        """
        success = user_session.text_processor.set_character_mapping(
            character1, character2
        )
        logger.debug(f"Character mapping set: {character1}, {character2}: {success}")
        return user_session

    def update_process_button_state(
        self, extracted_text: str, user_session: UserSession
    ) -> Dict[str, Any]:
        """
        抽出されたテキストとAPIキーの状態に基づいて"トーク原稿を生成"ボタンの有効/無効を切り替えます。

        Args:
            extracted_text (str): 抽出されたテキスト
            user_session (UserSession): ユーザーセッション

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        # テキストが有効かつAPIキーが設定されている場合のみボタンを有効化
        has_text = (
            extracted_text
            and extracted_text.strip() != ""
            and extracted_text
            not in ["Please upload a file.", "Failed to process the file."]
        )
        has_api_key = False

        if user_session.text_processor.current_api_type == APIType.OPENAI:
            has_api_key = user_session.text_processor.openai_model.has_api_key()
        elif user_session.text_processor.current_api_type == APIType.GEMINI:
            has_api_key = user_session.text_processor.gemini_model.has_api_key()

        is_enabled = has_text and has_api_key

        # gr.update()を使用して、Gradioのコンポーネントを更新する
        # Dict[str, Any]型にキャストして型チェッカーを満足させる
        result = gr.update(
            interactive=is_enabled, variant="primary" if is_enabled else "secondary"
        )
        return result  # type: ignore

    def set_podcast_mode(self, mode: str, user_session: UserSession) -> UserSession:
        """
        ポッドキャスト生成モードを設定します。

        Args:
            mode (str): ポッドキャストモードのラベル名
        """
        try:
            # ラベル名からPodcastModeを取得
            podcast_mode = PodcastMode.from_label_name(mode)

            # TextProcessorを使ってPodcastModeのEnumを設定
            success = user_session.text_processor.set_podcast_mode(podcast_mode.value)

            logger.debug(f"Podcast mode set to {mode}: {success}")

        except ValueError as e:
            logger.error(f"Error setting podcast mode: {str(e)}")

        return user_session

    def get_podcast_modes(self):
        """
        利用可能なポッドキャスト生成モードのリストを取得します。

        Returns:
            list: 利用可能なモードのラベル名リスト
        """
        return PodcastMode.get_all_label_names()

    def update_token_usage_display(self, user_session: UserSession) -> str:
        """
        トークン使用状況を表示用のHTMLとして返します。

        Returns:
            str: トークン使用状況のHTML
        """
        token_usage = user_session.text_processor.get_token_usage()
        if not token_usage:
            return "<div>トークン使用状況: データがありません</div>"

        prompt_tokens = token_usage.get("prompt_tokens", math.nan)
        completion_tokens = token_usage.get("completion_tokens", math.nan)
        total_tokens = token_usage.get("total_tokens", math.nan)

        # API名を取得
        api_name = f"{user_session.text_processor.current_api_type.display_name if user_session.text_processor.current_api_type else 'API'} API"

        html = f"""
        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px;">
            <h3 style="margin-top: 0; margin-bottom: 8px;">{api_name} Token Usage</h3>
            <div style="display: flex; justify-content: space-between;">
                <div><strong>Input Tokens:</strong> {prompt_tokens}</div>
                <div><strong>Output Tokens:</strong> {completion_tokens}</div>
                <div><strong>Total Tokens:</strong> {total_tokens}</div>
            </div>
        </div>
        """
        return html

    def update_audio_button_state(
        self, checked: bool, podcast_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        VOICEVOX利用規約チェックボックスの状態とトーク原稿の有無に基づいて音声生成ボタンの有効/無効を切り替えます。

        Args:
            checked (bool): チェックボックスの状態
            podcast_text (Optional[str], optional): 生成されたトーク原稿

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        has_text = podcast_text and podcast_text.strip() != ""
        is_enabled = checked and has_text

        message = ""
        if not checked:
            message = "（VOICEVOX利用規約に同意が必要です）"
        elif not has_text:
            message = "（トーク原稿が必要です）"

        # gr.update()を使用して、既存のボタンを更新
        result: Dict[str, Any] = gr.update(
            value=f"音声を生成{message}",
            interactive=is_enabled,
            variant="primary" if is_enabled else "secondary",
        )
        return result

    def set_document_type(
        self, doc_type: str, user_session: UserSession
    ) -> UserSession:
        """
        ドキュメントタイプを設定します。

        Args:
            doc_type (str): ドキュメントタイプのラベル名
        """
        try:
            # ラベル名からDocumentTypeを取得
            document_type = DocumentType.from_label_name(doc_type)

            # TextProcessorを使ってドキュメントタイプを設定
            success = user_session.text_processor.set_document_type(document_type)

            logger.debug(f"Document type set to {doc_type}: {success}")

        except ValueError as e:
            logger.error(f"Error setting document type: {str(e)}")

        return user_session

    def wait_for_audio_completion(
        self, text: str, user_session: UserSession, progress=gr.Progress()
    ):
        """
        ストリーミング処理の進捗を表示し、最終的な結合音声ファイルを返す
        波形表示用コンポーネントの更新に使用する
        音声生成が完了するまで待機し、最終的な結合音声ファイルを返す

        Args:
            text (str): Generated podcast text (使用しない)
            progress (gr.Progress): Gradio Progress object for updating progress

        Returns:
            Optional[str]: 最終結合音声ファイルのパス（すべての会話を含む）
        """
        if not text or not user_session.audio_generator.core_initialized:
            logger.warning(
                "Cannot display progress: Text is empty or VOICEVOX is not available"
            )
            progress(1.0, desc="⚠️ 音声生成できません")
            return None

        # 進捗表示の初期化
        progress(0, desc="音声生成準備中...")

        # 音声生成の完了を待ちながら進捗表示を行う
        last_progress = -math.inf
        while True:
            current_value = user_session.audio_generator.audio_generation_progress

            # 生成完了したら音声ファイル取得を試みる
            if current_value >= 1.0:
                if user_session.audio_generator.final_audio_path is None:
                    progress(1.0, desc="✅ 音声生成完了! 音声ファイル取得中...")
                else:
                    abs_path = str(
                        Path(user_session.audio_generator.final_audio_path).absolute()
                    )
                    # ファイルが存在しなければエラー
                    if not os.path.exists(abs_path):
                        logger.error(f"ファイルが存在しません: {abs_path}")
                        progress(1.0, desc="⚠️ 音声生成に問題が発生しました")
                        return None
                    filesize = os.path.getsize(abs_path)
                    logger.info(f"最終音声ファイルを返します: {abs_path} (サイズ: {filesize} bytes)")
                    progress(1.0, desc="✅ 音声ファイル取得完了!")
                    return abs_path

            # 1%以上変化があれば更新
            if abs(current_value - last_progress) > 0.01:
                last_progress = current_value
                progress_percent = int(current_value * 100)

                # 進捗に応じた絵文字表示
                if progress_percent < 25:
                    emoji = "🎤"
                elif progress_percent < 50:
                    emoji = "🎵"
                elif progress_percent < 75:
                    emoji = "🎶"
                else:
                    emoji = "🔊"

                # 進捗を更新
                progress(current_value, desc=f"{emoji} 音声生成中... {progress_percent}%")

            # 一定時間待機してから再チェック
            time.sleep(0.5)

    def reset_audio_state_and_components(self, user_session: UserSession):
        """
        音声生成状態をリセットし、UIコンポーネントもクリアする
        新しい音声生成を開始する前に呼び出す

        Returns:
            None: ストリーミング再生コンポーネントをクリアするためにNoneを返す
        """
        # 音声生成状態をリセット
        user_session.audio_generator.reset_audio_generation_state()

        # ストリーミングコンポーネントをリセット - gradio UIの更新のためNoneを返す
        logger.debug("Audio components and generation state reset")
        return None

    def cleanup_session(self, user_session: UserSession):
        """
        セッションが終了した時に呼び出されるクリーンアップ関数。
        ユーザーがブラウザタブを閉じたり更新したりした時に実行される。

        セッションのテンポラリファイルと出力ファイルを削除する。

        Returns:
            None
        """
        logger.info(f"Session {user_session.session_id} ended, cleaning up...")
        user_session.cleanup()
        logger.info("Session cleanup completed successfully")

    def sync_ui_with_session(
        self, user_session: UserSession
    ) -> Tuple[str, str, str, str, int, int]:
        """Sync UI components with user session values.

        Args:
            user_session (UserSession): User session

        Returns:
            Tuple[str, str, str, str, int, int]: (document_type, podcast_mode, character1, character2, openai_max_tokens, gemini_max_tokens)
        """
        return user_session.get_ui_sync_values()


# Create and launch application instance
def main():
    """Application entry point.

    Creates an instance of PaperPodcastApp and launches the application.
    """
    app_instance = PaperPodcastApp()
    app = app_instance.ui()

    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", DEFAULT_PORT))

    # E2E test mode options
    inbrowser = not E2E_TEST_MODE  # Don't open browser in test mode

    # キューイングはlaunchの前にqueueメソッドで設定済み
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        favicon_path="assets/favicon.ico",
        inbrowser=inbrowser,
        quiet=False,  # デバッグ情報表示
        pwa=True,  # Progressive Web App（インストール可能）を有効化
    )


if __name__ == "__main__":
    main()
