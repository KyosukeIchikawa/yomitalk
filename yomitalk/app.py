#!/usr/bin/env python3

"""Main application module.

Builds the Paper Podcast Generator application using Gradio.
"""
import math
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr

from yomitalk.common import APIType
from yomitalk.common.character import DISPLAY_NAMES
from yomitalk.components.audio_generator import (
    initialize_global_voicevox_manager,
)
from yomitalk.components.content_extractor import ContentExtractor
from yomitalk.models.gemini_model import GeminiModel
from yomitalk.models.openai_model import OpenAIModel
from yomitalk.prompt_manager import DocumentType, PodcastMode, PromptManager
from yomitalk.user_session import UserSession
from yomitalk.utils.logger import logger

# Initialize global VOICEVOX Core manager once for all users
# This is done at application startup, outside of any function
logger.info("Initializing global VOICEVOX Core manager for all users")
global_voicevox_manager = initialize_global_voicevox_manager()

# E2E test mode for faster startup
E2E_TEST_MODE = os.environ.get("E2E_TEST_MODE", "false").lower() == "true"

# Default port
DEFAULT_PORT = 7860


# Application class
class PaperPodcastApp:
    """Main class for the Paper Podcast Generator application."""

    def __init__(self):
        """Initialize the PaperPodcastApp."""
        logger.info("Initializing PaperPodcastApp for multi-user support")

        # Cleanup old sessions on startup using dummy session instance
        dummy_session = UserSession("dummy")
        dummy_session.cleanup_old_sessions()

    def create_user_session(self, request: gr.Request) -> UserSession:
        """Create a new user session with unique session ID."""
        session_id = request.session_hash
        return UserSession(session_id)

    def clear_extracted_text(self) -> str:
        """Clear the extracted text area."""
        return ""

    def set_openai_api_key(self, api_key: str, user_session: UserSession):
        """Set the OpenAI API key for the specific user session."""
        if not api_key or api_key.strip() == "":
            logger.debug("OpenAI API key is empty")
            return user_session

        success = user_session.text_processor.set_openai_api_key(api_key)
        logger.debug(
            f"OpenAI API key set for session {user_session.session_id}: {success}"
        )
        return user_session

    def set_gemini_api_key(self, api_key: str, user_session: UserSession):
        """Set the Google Gemini API key for the specific user session."""
        if not api_key or api_key.strip() == "":
            logger.debug("Gemini API key is empty")
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
            logger.debug(
                f"{api_type.display_name} API key not set for session {user_session.session_id}"
            )
        return user_session

    def extract_file_text(
        self,
        file_obj,
        existing_text: str,
        add_separator: bool,
        user_session: UserSession,
    ) -> Tuple[None, str, UserSession]:
        """Extract text from a file and append to existing text for the specific user session."""
        if file_obj is None:
            logger.debug("No file selected for extraction")
            return None, existing_text, user_session

        # Extract new text from file
        new_text = ContentExtractor.extract_text(file_obj)

        # Get source name from file
        source_name = ContentExtractor.get_source_name_from_file(file_obj)

        # Append to existing text with source information
        combined_text = ContentExtractor.append_text_with_source(
            existing_text, new_text, source_name, add_separator
        )

        logger.debug(
            f"File text extraction completed for session {user_session.session_id}"
        )
        return (
            None,
            combined_text,
            user_session,
        )  # Return None for file_input to clear it

    def extract_url_text(
        self,
        url: str,
        existing_text: str,
        add_separator: bool,
        user_session: UserSession,
    ) -> Tuple[str, UserSession]:
        """Extract text from a URL and append to existing text for the specific user session."""
        if not url or not url.strip():
            logger.warning("No URL provided for extraction")
            # Return error message for empty URL input
            error_message = "Please enter a valid URL"
            if existing_text.strip():
                # If there's existing text, append error message with separator
                if add_separator:
                    combined_text = (
                        existing_text.rstrip()
                        + "\n\n---\n**Error**\n\n"
                        + error_message
                    )
                else:
                    combined_text = existing_text.rstrip() + "\n\n" + error_message
            else:
                # If no existing text, just show error message
                combined_text = error_message
            return combined_text, user_session

        # Extract new text from URL
        new_text = ContentExtractor.extract_from_url(url.strip())

        # Use URL as source name
        source_name = url.strip()

        # Append to existing text with source information
        combined_text = ContentExtractor.append_text_with_source(
            existing_text, new_text, source_name, add_separator
        )

        logger.debug(
            f"URL text extraction completed for session {user_session.session_id}"
        )
        return combined_text, user_session

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

    def extract_file_text_auto(
        self,
        file_obj,
        existing_text: str,
        add_separator: bool,
        user_session: UserSession,
    ) -> Tuple[None, str, UserSession]:
        """Extract text from uploaded file automatically (for file upload mode)."""
        if file_obj is None:
            logger.warning("No file provided for automatic extraction")
            return None, existing_text, user_session

        # Extract new text from file
        new_text = ContentExtractor.extract_text(file_obj)

        # Get source name from file
        source_name = ContentExtractor.get_source_name_from_file(file_obj)

        # Append to existing text with source information
        combined_text = ContentExtractor.append_text_with_source(
            existing_text, new_text, source_name, add_separator
        )

        logger.debug(
            f"Auto file text extraction completed for session {user_session.session_id}"
        )
        # Return None for file_input to clear it after extraction
        return None, combined_text, user_session

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
            user_session.update_audio_generation_state(
                status="failed", is_generating=False
            )
            yield None
            return

        # Check if VOICEVOX Core is available
        if not user_session.audio_generator.core_initialized:
            logger.error("Streaming audio generation: VOICEVOX Core is not available")
            user_session.update_audio_generation_state(
                status="failed", is_generating=False
            )
            yield None
            return

        try:
            # 音声生成状態を初期化
            generation_id = str(uuid.uuid4())
            user_session.update_audio_generation_state(
                is_generating=True,
                status="generating",
                current_script=text,
                generation_id=generation_id,
                start_time=time.time(),
                progress=0.0,
                generated_parts=[],
                streaming_parts=[],
                final_audio_path=None,
            )

            # 初回のyieldを行って、Gradioのストリーミングモードを確実に有効化
            logger.debug(
                f"Initializing streaming audio generation (ID: {generation_id})"
            )
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

                    # 状態を更新
                    current_parts = list(
                        user_session.audio_generation_state["streaming_parts"]
                    )
                    current_parts.append(audio_path)
                    user_session.update_audio_generation_state(
                        streaming_parts=current_parts,
                        progress=min(0.9, len(current_parts) * 0.1),  # 部分的な進捗
                    )

                    logger.debug(
                        f"ストリーム音声パーツ ({len(parts_paths)}): {audio_path}"
                    )
                    yield audio_path  # ストリーミング再生用にyield
                    time.sleep(0.05)  # 連続再生のタイミング調整
                elif filename.startswith("audio_"):
                    # 最終結合ファイルの場合
                    final_combined_path = audio_path
                    user_session.update_audio_generation_state(
                        final_audio_path=audio_path, progress=1.0
                    )
                    logger.info(
                        f"結合済み最終音声ファイルを受信: {final_combined_path}"
                    )

            # 音声生成の完了処理
            self._finalize_audio_generation(
                final_combined_path, parts_paths, user_session
            )

        except Exception as e:
            logger.error(f"Streaming audio generation exception: {str(e)}")
            user_session.update_audio_generation_state(
                status="failed", is_generating=False, progress=0.0
            )
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
            user_session.update_audio_generation_state(progress=0.9)
            logger.info(f"最終結合音声ファイル: {final_combined_path}")

            # 最終的な音声ファイルのパスを保存
            user_session.audio_generator.final_audio_path = final_combined_path

            # ファイルの書き込みを確実にするため少し待機
            time.sleep(0.2)

            if os.path.exists(final_combined_path):
                filesize = os.path.getsize(final_combined_path)
                # 進捗を完了状態に更新
                user_session.audio_generator.audio_generation_progress = 1.0
                user_session.update_audio_generation_state(
                    progress=1.0,
                    status="completed",
                    is_generating=False,
                    final_audio_path=final_combined_path,
                )
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
            logger.warning(
                "結合音声ファイルを取得できなかったため、最後のパートを使用します"
            )
            user_session.audio_generator.final_audio_path = parts_paths[-1]
            user_session.audio_generator.audio_generation_progress = 1.0
            user_session.update_audio_generation_state(
                status="completed",
                is_generating=False,
                progress=1.0,
                final_audio_path=parts_paths[-1],
            )

            if os.path.exists(parts_paths[-1]):
                filesize = os.path.getsize(parts_paths[-1])
                logger.info(
                    f"部分音声ファイル使用: {parts_paths[-1]} (ファイルサイズ: {filesize} bytes)"
                )
            else:
                logger.error(f"フォールバックファイルも存在しません: {parts_paths[-1]}")
                user_session.audio_generator.audio_generation_progress = 0.0
                user_session.update_audio_generation_state(
                    status="failed", is_generating=False, progress=0.0
                )
        else:
            logger.warning("音声ファイルが生成されませんでした")
            user_session.audio_generator.audio_generation_progress = 0.0
            user_session.update_audio_generation_state(
                status="failed", is_generating=False, progress=0.0
            )

    def disable_generate_button(self):
        """音声生成ボタンを無効化します。

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        return gr.update(interactive=False, value="音声生成中...")

    def enable_generate_button(self, terms_agreed: bool, podcast_text: str):
        """音声生成ボタンを再び有効化します。

        Args:
            terms_agreed (bool): VOICEVOX利用規約への同意状態
            podcast_text (str): 生成されたトーク原稿（状態確認用）

        Returns:
            Dict[str, Any]: gr.update()の結果
        """
        return self.update_audio_button_state(terms_agreed, podcast_text)

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
                    supported_extensions = ContentExtractor.SUPPORTED_EXTENSIONS

                    # Content extraction tabs
                    gr.Markdown("### 解説対象テキストの作成")

                    extraction_tabs = gr.Tabs()
                    with extraction_tabs:
                        with gr.TabItem("ファイルアップロード"):
                            file_input = gr.File(
                                file_types=supported_extensions,
                                type="filepath",
                                label=f"ファイルをアップロード（{', '.join(supported_extensions)}）",
                                height=120,
                                interactive=False,
                            )

                        with gr.TabItem("Webページ抽出"):
                            url_input = gr.Textbox(
                                placeholder="初期化中です。少しお待ちください...",
                                label="WebページのURLを入力",
                                info="注: Hugging Face Spacesで利用する場合はYouTubeなどの一部サイトからの抽出ができません",
                                lines=2,
                                interactive=False,
                            )
                            url_extract_btn = gr.Button(
                                "初期化中...",
                                variant="secondary",
                                size="lg",
                                interactive=False,
                            )

                    # Auto separator checkbox and clear button in the same row
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=3):
                            auto_separator_checkbox = gr.Checkbox(
                                label="テキスト抽出時に区切りを自動挿入",
                                value=True,
                                info="ファイル名やURLの情報を含む区切り線を自動挿入します",
                                interactive=False,
                            )
                        with gr.Column(scale=1):
                            clear_text_btn = gr.Button(
                                "初期化中...",
                                variant="secondary",
                                size="sm",
                                interactive=False,
                            )

                    # Extracted text display
                    extracted_text = gr.Textbox(
                        label="解説対象テキスト（トークの元ネタ）",
                        placeholder="初期化中です。少しお待ちください...",
                        lines=10,
                        interactive=False,
                    )

                with gr.Column(variant="panel"):
                    gr.Markdown("### プロンプト設定")
                    document_type_radio = gr.Radio(
                        choices=DocumentType.get_all_label_names(),
                        value=PromptManager.DEFAULT_DOCUMENT_TYPE.label_name,  # 後でユーザーセッションの値で更新される
                        label="ドキュメントタイプ",
                        elem_id="document_type_radio_group",
                        interactive=False,
                    )

                    podcast_mode_radio = gr.Radio(
                        choices=PodcastMode.get_all_label_names(),
                        value=PromptManager.DEFAULT_MODE.label_name,  # 後でユーザーセッションの値で更新される
                        label="生成モード",
                        elem_id="podcast_mode_radio_group",
                        interactive=False,
                    )

                    # キャラクター設定
                    with gr.Accordion(label="キャラクター設定", open=False):
                        with gr.Row():
                            character1_dropdown = gr.Dropdown(
                                choices=DISPLAY_NAMES,
                                value=PromptManager.DEFAULT_CHARACTER1.display_name,  # 後でユーザーセッションの値で更新される
                                label="キャラクター1（専門家役）",
                                interactive=False,
                            )
                            character2_dropdown = gr.Dropdown(
                                choices=DISPLAY_NAMES,
                                value=PromptManager.DEFAULT_CHARACTER2.display_name,  # 後でユーザーセッションの値で更新される
                                label="キャラクター2（初学者役）",
                                interactive=False,
                            )

                with gr.Column(variant="panel"):
                    # LLM API設定タブ
                    llm_tabs = gr.Tabs()
                    with llm_tabs:
                        with gr.TabItem("Google Gemini") as gemini_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    gemini_api_key_input = gr.Textbox(
                                        placeholder="初期化中...",
                                        type="password",
                                        label="Google Gemini APIキー",
                                        info="APIキーの取得: https://aistudio.google.com/app/apikey",
                                        interactive=False,
                                    )
                                with gr.Column(scale=2):
                                    gemini_model_dropdown = gr.Dropdown(
                                        choices=GeminiModel.AVAILABLE_MODELS,
                                        value=GeminiModel.DEFAULT_MODEL,
                                        label="モデル",
                                        interactive=False,
                                    )
                            with gr.Row():
                                gemini_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=65536,
                                    value=GeminiModel.DEFAULT_MAX_TOKENS,
                                    step=100,
                                    label="最大トークン数",
                                    interactive=False,
                                )

                        with gr.TabItem("OpenAI") as openai_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    openai_api_key_input = gr.Textbox(
                                        placeholder="初期化中...",
                                        type="password",
                                        label="OpenAI APIキー",
                                        info="APIキーの取得: https://platform.openai.com/api-keys",
                                        interactive=False,
                                    )
                                with gr.Column(scale=2):
                                    openai_model_dropdown = gr.Dropdown(
                                        choices=OpenAIModel.AVAILABLE_MODELS,
                                        value=OpenAIModel.DEFAULT_MODEL,
                                        label="モデル",
                                        interactive=False,
                                    )
                            with gr.Row():
                                openai_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=32768,
                                    value=OpenAIModel.DEFAULT_MAX_TOKENS,
                                    step=100,
                                    label="最大トークン数",
                                    interactive=False,
                                )

                    # トーク原稿を生成ボタン
                    process_btn = gr.Button(
                        "初期化中...", variant="secondary", interactive=False
                    )
                    podcast_text = gr.Textbox(
                        label="生成されたトーク原稿",
                        placeholder="初期化中です。少しお待ちください...",
                        lines=15,
                        interactive=False,
                    )

                    # トークン使用状況の表示
                    token_usage_info = gr.HTML(
                        "<div>トークン使用状況: まだ生成されていません</div>",
                        elem_id="token-usage-info",
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
                        interactive=False,
                    )
                    generate_btn = gr.Button(
                        "初期化中...", variant="secondary", interactive=False
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
            ).then(
                # Enable UI components after initialization is complete
                fn=self.enable_ui_components_after_initialization,
                inputs=[user_session],
                outputs=[
                    file_input,
                    url_input,
                    url_extract_btn,
                    auto_separator_checkbox,
                    clear_text_btn,
                    extracted_text,
                    document_type_radio,
                    podcast_mode_radio,
                    character1_dropdown,
                    character2_dropdown,
                    gemini_api_key_input,
                    gemini_model_dropdown,
                    gemini_max_tokens_slider,
                    openai_api_key_input,
                    openai_model_dropdown,
                    openai_max_tokens_slider,
                    process_btn,
                    podcast_text,
                    terms_checkbox,
                    generate_btn,
                ],
                queue=False,
            ).then(
                # Connection recovery on page load/reconnection (includes audio state restoration)
                fn=self.handle_connection_recovery,
                inputs=[user_session, terms_checkbox, podcast_text],
                outputs=[streaming_audio_output, audio_output, generate_btn],
                api_name="connection_recovery",
                queue=False,
            )

            # Set up event handlers
            # Clear text button
            clear_text_btn.click(
                fn=self.clear_extracted_text,
                outputs=[extracted_text],
                queue=False,
            )

            # Auto file extraction when file is uploaded (file upload mode)
            file_input.change(
                fn=self.extract_file_text_auto,
                inputs=[
                    file_input,
                    extracted_text,
                    auto_separator_checkbox,
                    user_session,
                ],
                outputs=[file_input, extracted_text, user_session],
                concurrency_limit=1,  # 同時実行数を1に制限（Hugging Face Spaces対応）
                concurrency_id="file_queue",  # ファイル処理用キューID
            ).then(
                fn=self.enable_process_button,
                inputs=[extracted_text, user_session],
                outputs=[process_btn],
            )

            # URL抽出ボタンのイベントハンドラー
            url_extract_btn.click(
                fn=self.extract_url_text,
                inputs=[
                    url_input,
                    extracted_text,
                    auto_separator_checkbox,
                    user_session,
                ],
                outputs=[extracted_text, user_session],
                concurrency_limit=1,  # 同時実行数を1に制限（Hugging Face Spaces対応）
                concurrency_id="url_queue",  # URL処理用キューID
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
                outputs=[streaming_audio_output, audio_output],
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
                show_progress="hidden",  # ストリーミング表示では独自の進捗バーを表示しない
                api_name="generate_streaming_audio",  # APIエンドポイント名（デバッグ用）
            )

            # 2. 波形表示用のコンポーネントを更新 (進捗表示とともに最終波形表示)
            # こちらは独立したイベントとして実行し、音声生成の進捗を表示してから最終ファイルを返す
            wave_display_event = audio_events.then(
                fn=self.wait_for_audio_completion,
                inputs=[podcast_text, user_session],
                outputs=[audio_output],
                concurrency_limit=1,  # 同時実行数を1に制限
                concurrency_id="progress_queue",  # 進捗表示用キューID
                show_progress="full",  # 進捗バーを表示（関数内で更新）
                api_name="update_progress_display",  # APIエンドポイント名（デバッグ用）
            )

            # 3. 処理完了後にボタンを再度有効化
            wave_display_event.then(
                fn=self.enable_generate_button,
                inputs=[terms_checkbox, podcast_text],
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

        return app

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
        has_text = bool(podcast_text and podcast_text.strip() != "")
        is_enabled = bool(checked and has_text)

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
                    logger.info(
                        f"最終音声ファイルを返します: {abs_path} (サイズ: {filesize} bytes)"
                    )
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
                progress(
                    current_value, desc=f"{emoji} 音声生成中... {progress_percent}%"
                )

            # 一定時間待機してから再チェック
            time.sleep(0.5)

    def reset_audio_state_and_components(self, user_session: UserSession):
        """
        音声生成状態をリセットし、音声コンポーネントをクリアする

        Args:
            user_session: ユーザーセッション

        Returns:
            Tuple[None, None]: (streaming_audio_clear, audio_output_clear)
        """
        # 音声生成状態をリセット
        user_session.reset_audio_generation_state()
        logger.debug("Audio generation state and components reset")

        # 音声コンポーネントをクリア
        return None, None

    def enable_ui_components_after_initialization(
        self, user_session: UserSession
    ) -> Tuple[
        Dict[str, Any],  # file_input
        Dict[str, Any],  # url_input
        Dict[str, Any],  # url_extract_btn
        Dict[str, Any],  # auto_separator_checkbox
        Dict[str, Any],  # clear_text_btn
        Dict[str, Any],  # extracted_text
        Dict[str, Any],  # document_type_radio
        Dict[str, Any],  # podcast_mode_radio
        Dict[str, Any],  # character1_dropdown
        Dict[str, Any],  # character2_dropdown
        Dict[str, Any],  # gemini_api_key_input
        Dict[str, Any],  # gemini_model_dropdown
        Dict[str, Any],  # gemini_max_tokens_slider
        Dict[str, Any],  # openai_api_key_input
        Dict[str, Any],  # openai_model_dropdown
        Dict[str, Any],  # openai_max_tokens_slider
        Dict[str, Any],  # process_btn
        Dict[str, Any],  # podcast_text
        Dict[str, Any],  # terms_checkbox
        Dict[str, Any],  # generate_btn
    ]:
        """Initialize UI components after session creation is complete.

        Args:
            user_session: User session

        Returns:
            Tuple of gr.update() objects to enable all UI components
        """
        logger.info(f"Enabling UI components for session {user_session.session_id}")

        # Enable file input
        file_input_update = gr.update(interactive=True)

        # Enable URL input
        url_input_update = gr.update(
            placeholder="https://example.com/page", interactive=True
        )

        # Enable URL extract button
        url_extract_btn_update = gr.update(
            value="URLからテキストを抽出", variant="primary", interactive=True
        )

        # Enable auto separator checkbox
        auto_separator_checkbox_update = gr.update(interactive=True)

        # Enable clear text button
        clear_text_btn_update = gr.update(value="テキストをクリア", interactive=True)

        # Enable extracted text
        extracted_text_update = gr.update(
            placeholder="ファイルをアップロードするか、URLを入力するか、直接ここにテキストを入力してください...",
            interactive=True,
        )

        # Enable document type radio
        document_type_radio_update = gr.update(interactive=True)

        # Enable podcast mode radio
        podcast_mode_radio_update = gr.update(interactive=True)

        # Enable character dropdowns
        character1_dropdown_update = gr.update(interactive=True)
        character2_dropdown_update = gr.update(interactive=True)

        # Enable API key inputs
        gemini_api_key_input_update = gr.update(placeholder="AIza...", interactive=True)
        openai_api_key_input_update = gr.update(placeholder="sk-...", interactive=True)

        # Enable model dropdowns
        gemini_model_dropdown_update = gr.update(interactive=True)
        openai_model_dropdown_update = gr.update(interactive=True)

        # Enable token sliders
        gemini_max_tokens_slider_update = gr.update(interactive=True)
        openai_max_tokens_slider_update = gr.update(interactive=True)

        # Enable process button (but check API key status)
        process_btn_update = gr.update(
            interactive=False, variant="secondary", value="トーク原稿を生成"
        )

        # Enable podcast text
        podcast_text_update = gr.update(
            placeholder="テキストを処理してトーク原稿を生成してください...",
            interactive=True,
        )

        # Enable terms checkbox
        terms_checkbox_update = gr.update(interactive=True)

        # Enable generate button (but check conditions)
        generate_btn_update = self.update_audio_button_state(False, "")

        return (
            file_input_update,
            url_input_update,
            url_extract_btn_update,
            auto_separator_checkbox_update,
            clear_text_btn_update,
            extracted_text_update,
            document_type_radio_update,
            podcast_mode_radio_update,
            character1_dropdown_update,
            character2_dropdown_update,
            gemini_api_key_input_update,
            gemini_model_dropdown_update,
            gemini_max_tokens_slider_update,
            openai_api_key_input_update,
            openai_model_dropdown_update,
            openai_max_tokens_slider_update,
            process_btn_update,
            podcast_text_update,
            terms_checkbox_update,
            generate_btn_update,
        )

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

    def check_and_restore_audio_generation(
        self, user_session: UserSession
    ) -> Tuple[Optional[str], Optional[str], str]:
        """
        接続復帰時に音声生成の状態をチェックして復元する

        Args:
            user_session: ユーザーセッション

        Returns:
            Tuple[Optional[str], Optional[str], str]: (streaming_audio, final_audio, status_message)
        """
        try:
            # 音声生成が進行中かチェック
            if user_session.is_audio_generation_active():
                # 生成中の場合、バックグラウンドプロセスをチェック
                logger.info("Active audio generation detected, checking progress...")
                return self._resume_audio_generation_monitoring(user_session)

            # 完了済みの音声があるかチェック
            elif user_session.has_generated_audio():
                logger.info("Completed audio detected, restoring audio components...")
                status = user_session.get_audio_generation_status()

                streaming_audio = None
                final_audio = status.get("final_audio_path")

                # ストリーミング音声が残っている場合
                streaming_parts = status.get("streaming_parts", [])
                if streaming_parts:
                    # 最新のストリーミング音声を使用
                    streaming_audio = streaming_parts[-1] if streaming_parts else None

                return streaming_audio, final_audio, "✅ 音声生成完了（復帰）"

            else:
                # 音声生成がない場合
                return None, None, ""

        except Exception as e:
            logger.error(f"Error during audio generation restoration: {e}")
            return None, None, "⚠️ 音声復帰中にエラーが発生"

    def _resume_audio_generation_monitoring(
        self, user_session: UserSession
    ) -> Tuple[Optional[str], Optional[str], str]:
        """
        音声生成の監視を再開する

        Args:
            user_session: ユーザーセッション

        Returns:
            Tuple[Optional[str], Optional[str], str]: (streaming_audio, final_audio, status_message)
        """
        status = user_session.get_audio_generation_status()
        progress = status.get("progress", 0.0)

        # 生成された部分があるかチェック
        streaming_parts = status.get("streaming_parts", [])
        final_audio = status.get("final_audio_path")

        # 最新のストリーミング音声
        streaming_audio = streaming_parts[-1] if streaming_parts else None

        # プログレスに基づくステータスメッセージ
        if progress >= 1.0:
            status_message = "✅ 音声生成完了（復帰）"
        elif progress > 0.0:
            progress_percent = int(progress * 100)
            status_message = f"🎵 音声生成中... {progress_percent}%（復帰）"
        else:
            status_message = "🎤 音声生成開始中...（復帰）"

        return streaming_audio, final_audio, status_message

    def handle_connection_recovery(
        self, user_session: UserSession, terms_agreed: bool, podcast_text: str
    ) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        """
        Handle connection recovery when page loads/reconnects
        Combines audio state restoration and button state management

        Args:
            user_session: User session
            terms_agreed: Whether VOICEVOX terms are agreed
            podcast_text: Generated podcast text

        Returns:
            Tuple[Optional[str], Optional[str], Dict[str, Any]]:
                (streaming_audio, final_audio, button_update)
        """
        logger.info("Connection recovery triggered - checking audio state")

        try:
            # Check if there's any audio to restore
            if (
                not user_session.is_audio_generation_active()
                and not user_session.has_generated_audio()
            ):
                logger.debug("No audio to restore - setting normal button state")
                return (
                    None,
                    None,
                    self.update_audio_button_state(terms_agreed, podcast_text),
                )

            # Restore audio state using the existing restoration logic
            streaming_audio, final_audio, status_message = (
                self.check_and_restore_audio_generation(user_session)
            )

            logger.info("Audio state detected - restoring components")

            # If audio generation is active, avoid race conditions with timer and events
            if user_session.is_audio_generation_active():
                logger.debug(
                    "Audio generation active - avoiding race condition with timer"
                )
                # Return gr.update() for audio components to avoid conflicts with ongoing processes
                return (
                    gr.update(),  # Preserve current streaming audio state
                    gr.update(),  # Preserve current final audio state
                    gr.update(interactive=False, value="音声生成中...（復帰）"),
                )
            else:
                # Audio generation completed - safe to restore audio components
                button_state = self.update_audio_button_state(
                    terms_agreed, podcast_text
                )
                return (streaming_audio, final_audio, button_state)

        except Exception as e:
            logger.error(f"Error in connection recovery: {e}")
            return (
                None,
                None,
                self.update_audio_button_state(terms_agreed, podcast_text),
            )

    def monitor_audio_session_state(
        self, user_session: UserSession
    ) -> Tuple[Dict[str, Any], Optional[str], Optional[str]]:
        """
        Monitor and update audio generation state from user session.

        Note: This method is deprecated and no longer used.
        Timer-based monitoring was removed to avoid conflicts with progress display.
        Audio generation now directly updates user_session state in
        self.generate_podcast_audio_streaming method without timer monitoring.

        Args:
            user_session: User session containing audio state

        Returns:
            Tuple[Dict[str, Any], Optional[str], Optional[str]]:
                (timer_update, streaming_audio_update, final_audio_update)
        """
        try:
            # Get current audio generation status
            status = user_session.get_audio_generation_status()

            # Check if audio generation is active
            if not user_session.is_audio_generation_active():
                # Stop timer if no active generation
                logger.debug("No active audio generation - stopping timer")
                return gr.update(active=False), None, None

            # Update streaming audio if new parts are available
            streaming_parts = status.get("streaming_parts", [])
            streaming_audio = streaming_parts[-1] if streaming_parts else None

            # Update final audio if available
            final_audio = status.get("final_audio_path")

            # Check if generation is completed
            if status.get("status") == "completed":
                logger.debug("Audio generation completed - stopping timer")
                return gr.update(active=False), streaming_audio, final_audio

            # Continue monitoring
            progress = status.get("progress", 0.0)
            logger.debug(f"Audio generation progress: {progress:.1%}")

            return gr.update(active=True), streaming_audio, final_audio
        except Exception as e:
            logger.error(f"Error monitoring audio session state: {e}")
            return gr.update(active=False), None, None


def main() -> None:
    """
    Main function to launch the Gradio app.

    This function creates an instance of PaperPodcastApp and launches
    the Gradio interface with appropriate configuration.
    """
    import argparse

    # Get port from environment variable if available
    env_port = os.environ.get("PORT")
    default_port = int(env_port) if env_port else DEFAULT_PORT

    parser = argparse.ArgumentParser(description="Yomitalk - Paper Podcast Generator")
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to run the server on (default: {default_port})",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the server on (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--share", action="store_true", help="Create a public link via Gradio tunneling"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Initialize the application
    app_instance = PaperPodcastApp()
    gradio_app = app_instance.ui()

    # Launch configuration
    launch_kwargs = {
        "server_name": args.host,
        "server_port": args.port,
        "share": args.share,
        "debug": args.debug,
        "show_error": True,
        "quiet": not args.debug,
        "favicon_path": (
            "assets/favicon.ico" if Path("assets/favicon.ico").exists() else None
        ),
    }

    # Add authentication for production environment
    if not args.debug and not E2E_TEST_MODE:
        # In production, you might want to add authentication
        # auth = ("username", "password")  # Set your credentials
        # launch_kwargs["auth"] = auth
        pass

    # Special handling for E2E test mode
    if E2E_TEST_MODE:
        logger.info("Running in E2E test mode - using special configuration")
        launch_kwargs.update(
            {
                "prevent_thread_lock": False,  # Keep app running for E2E tests
                "show_error": True,  # Show errors in test mode for debugging
                "quiet": False,  # Show output in test mode for debugging
            }
        )

    logger.info(f"Starting Yomitalk application on http://{args.host}:{args.port}")
    if args.share:
        logger.info("Public sharing enabled - this will create a public URL")

    try:
        gradio_app.launch(**launch_kwargs)
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
