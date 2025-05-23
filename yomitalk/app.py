#!/usr/bin/env python3

"""Main application module.

Builds the Paper Podcast Generator application using Gradio.
"""
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import gradio as gr

from yomitalk.common.character import DISPLAY_NAMES
from yomitalk.components.audio_generator import VOICEVOX_CORE_AVAILABLE, AudioGenerator
from yomitalk.components.content_extractor import ContentExtractor
from yomitalk.components.text_processor import TextProcessor
from yomitalk.prompt_manager import DocumentType, PodcastMode
from yomitalk.utils.logger import logger
from yomitalk.utils.session_manager import SessionManager

# Check for base directories
os.makedirs("data/temp", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

# E2E test mode for faster startup
E2E_TEST_MODE = os.environ.get("E2E_TEST_MODE", "false").lower() == "true"

# Default port
DEFAULT_PORT = 7860


# Application class
class PaperPodcastApp:
    """Main class for the Paper Podcast Generator application."""

    def __init__(self):
        """Initialize the PaperPodcastApp.

        Creates instances of FileUploader, TextProcessor, and AudioGenerator.
        """
        # セッション管理の初期化
        self.session_manager = SessionManager()
        logger.info(
            f"Initializing app with session ID: {self.session_manager.get_session_id()}"
        )

        self.content_extractor = ContentExtractor()
        self.text_processor = TextProcessor()
        self.audio_generator = AudioGenerator(
            session_output_dir=self.session_manager.get_output_dir(),
            session_temp_dir=self.session_manager.get_talk_temp_dir(),
        )

        # Check if VOICEVOX Core is available
        self.voicevox_core_available = (
            VOICEVOX_CORE_AVAILABLE and self.audio_generator.core_initialized
        )

        # 現在選択されているLLMタイプ
        self.current_llm_type = "openai"

    @property
    def current_podcast_mode(self) -> PodcastMode:
        """現在選択されているポッドキャストモードを取得します。"""
        return self.text_processor.get_podcast_mode()

    @property
    def current_document_type(self) -> DocumentType:
        """現在選択されているドキュメントタイプを取得します。"""
        return self.text_processor.get_document_type()

    def set_openai_api_key(self, api_key: str) -> str:
        """
        Set the OpenAI API key and returns a result message based on the outcome.

        Args:
            api_key (str): OpenAI API key

        Returns:
            str: status_message
        """
        # APIキーが空白や空文字の場合は処理しない
        if not api_key or api_key.strip() == "":
            logger.warning("OpenAI API key is empty")
            return "❌ APIキーが空です。有効なAPIキーを入力してください"

        success = self.text_processor.set_openai_api_key(api_key)
        result = "✅ APIキーが正常に設定されました" if success else "❌ APIキーの設定に失敗しました"
        logger.debug(f"OpenAI API key set: {success}")

        # OpenAIがアクティブになった場合、LLMタイプも更新
        if success:
            self.current_llm_type = "openai"

        return result

    def set_gemini_api_key(self, api_key: str) -> str:
        """
        Set the Google Gemini API key and returns a result message based on the outcome.

        Args:
            api_key (str): Google API key

        Returns:
            str: status_message
        """
        # APIキーが空白や空文字の場合は処理しない
        if not api_key or api_key.strip() == "":
            logger.warning("Gemini API key is empty")
            return "❌ APIキーが空です。有効なAPIキーを入力してください"

        success = self.text_processor.set_gemini_api_key(api_key)
        result = "✅ APIキーが正常に設定されました" if success else "❌ APIキーの設定に失敗しました"
        logger.debug(f"Gemini API key set: {success}")

        # Geminiがアクティブになった場合、LLMタイプも更新
        if success:
            self.current_llm_type = "gemini"

        return result

    def switch_llm_type(self, llm_type: str) -> None:
        """
        LLMタイプを切り替えます。

        Args:
            llm_type (str): "openai" または "gemini"
        """
        if llm_type not in ["openai", "gemini"]:
            logger.warning(f"Invalid LLM type: {llm_type}")
            return

        success = self.text_processor.set_api_type(llm_type)
        if success:
            self.current_llm_type = llm_type
            api_name = "OpenAI" if llm_type == "openai" else "Google Gemini"
            logger.debug(f"LLM type switched to {api_name}")
        else:
            api_name = "OpenAI" if llm_type == "openai" else "Google Gemini"
            logger.warning(f"{api_name} API key not set")

    def extract_file_text(self, file_obj) -> str:
        """
        Extract text from a file.

        Args:
            file_obj: Uploaded file object

        Returns:
            str: extracted_text
        """
        if file_obj is None:
            logger.warning("No file selected for extraction")
            return "Please upload a file."

        # メモリ上でテキスト抽出を行う
        text = self.content_extractor.extract_text(file_obj)
        logger.debug("Text extraction completed (memory-based)")
        return text

    def check_voicevox_core(self):
        """
        Check if VOICEVOX Core is available and properly initialized.

        Returns:
            str: Status message about VOICEVOX Core
        """
        if not VOICEVOX_CORE_AVAILABLE:
            return "❌ VOICEVOX Coreがインストールされていません。'make download-voicevox-core'を実行してインストールしてください。"

        if not self.audio_generator.core_initialized:
            return "⚠️ VOICEVOX Coreはインストールされていますが、正常に初期化されていません。モデルと辞書を確認してください。"

        return "✅ VOICEVOX Coreは使用可能です。"

    def generate_podcast_text(self, text: str) -> str:
        """
        Generate podcast-style text from input text.

        Args:
            text (str): Input text from file

        Returns:
            str: generated_podcast_text
        """
        if not text:
            logger.warning("Podcast text generation: Input text is empty")
            return "Please upload a file and extract text first."

        # Check if API key is set
        if (
            self.current_llm_type == "openai"
            and not self.text_processor.openai_model.api_key
        ):
            logger.warning("Podcast text generation: OpenAI API key not set")
            return "OpenAI API key is not set. Please configure it in the Settings tab."
        elif (
            self.current_llm_type == "gemini"
            and not self.text_processor.gemini_model.api_key
        ):
            logger.warning("Podcast text generation: Gemini API key not set")
            return "Google Gemini API key is not set. Please configure it in the Settings tab."

        try:
            # Generate podcast text
            podcast_text = self.text_processor.process_text(text)

            # トークン使用状況を取得してログに追加
            token_usage = self.text_processor.get_token_usage()
            if token_usage:
                usage_msg = f"Token usage: input {token_usage.get('prompt_tokens', 0)}, output {token_usage.get('completion_tokens', 0)}, total {token_usage.get('total_tokens', 0)}"
                logger.debug(usage_msg)

            logger.debug("Podcast text generation completed")
            return podcast_text
        except Exception as e:
            error_msg = f"Podcast text generation error: {str(e)}"
            logger.error(error_msg)
            return f"Error: {str(e)}"

    def generate_podcast_audio(self, text: str) -> Optional[str]:
        """
        Generate audio from podcast text.

        Args:
            text (str): Generated podcast text

        Returns:
            Optional[str]: audio_path or None
        """
        if not text:
            logger.warning("Audio generation: Text is empty")
            return None

        # Check if VOICEVOX Core is available
        if not self.voicevox_core_available:
            logger.error("Audio generation: VOICEVOX Core is not available")
            return None

        try:
            # Generate audio from text
            audio_path = self.audio_generator.generate_character_conversation(text)
            if audio_path:
                # 絶対パスを取得
                abs_path = str(Path(audio_path).absolute())
                logger.debug("Audio file generated successfully")
                return abs_path
            else:
                logger.error("Audio generation failed: No audio path returned")
                return None
        except Exception as e:
            logger.error(f"Audio generation exception: {str(e)}")
            return None

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
                margin-bottom: 16px !important;
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
                content: "音声が生成されるとここに表示されます";
                display: flex;
                justify-content: center;
                align-items: center;
                height: 140px;
                color: #666;
                font-style: italic;
                background-color: rgba(0,0,0,0.03);
                border-radius: 8px;
            }
            """
            gr.HTML(f"<style>{css}</style>")

            with gr.Column():
                gr.Markdown("""## トーク原稿の生成""")
                with gr.Column(variant="panel"):
                    # サポートしているファイル形式の拡張子を取得
                    supported_extensions = (
                        self.content_extractor.get_supported_extensions()
                    )

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

                    document_type_radio = gr.Radio(
                        choices=DocumentType.get_all_label_names(),
                        value=self.current_document_type.label_name,
                        label="ドキュメントタイプ",
                        elem_id="document_type_radio_group",
                    )

                    podcast_mode_radio = gr.Radio(
                        choices=PodcastMode.get_all_label_names(),
                        value=self.current_podcast_mode.label_name,
                        label="生成モード",
                        elem_id="podcast_mode_radio_group",
                    )

                    # キャラクター設定
                    with gr.Accordion(label="キャラクター設定", open=False):
                        with gr.Row():
                            available_characters = self.get_available_characters()
                            character1_dropdown = gr.Dropdown(
                                choices=available_characters,
                                value="四国めたん",
                                label="キャラクター1（専門家役）",
                            )
                            character2_dropdown = gr.Dropdown(
                                choices=available_characters,
                                value="ずんだもん",
                                label="キャラクター2（初学者役）",
                            )

                with gr.Column(variant="panel"):
                    # LLM API設定タブ
                    llm_tabs = gr.Tabs()
                    with llm_tabs:
                        with gr.TabItem("OpenAI") as openai_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    openai_api_key_input = gr.Textbox(
                                        placeholder="sk-...",
                                        type="password",
                                        label="OpenAI APIキー",
                                    )
                                with gr.Column(scale=2):
                                    openai_model_dropdown = gr.Dropdown(
                                        choices=self.get_openai_available_models(),
                                        value=self.get_openai_current_model(),
                                        label="モデル",
                                    )
                            with gr.Row():
                                openai_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=32768,
                                    value=self.get_openai_max_tokens(),
                                    step=100,
                                    label="最大トークン数",
                                )

                        with gr.TabItem("Google Gemini") as gemini_tab:
                            with gr.Row():
                                with gr.Column(scale=3):
                                    gemini_api_key_input = gr.Textbox(
                                        placeholder="AIza...",
                                        type="password",
                                        label="Google Gemini APIキー",
                                    )
                                with gr.Column(scale=2):
                                    gemini_model_dropdown = gr.Dropdown(
                                        choices=self.get_gemini_available_models(),
                                        value=self.get_gemini_current_model(),
                                        label="モデル",
                                    )
                            with gr.Row():
                                gemini_max_tokens_slider = gr.Slider(
                                    minimum=100,
                                    maximum=65536,
                                    value=self.get_gemini_max_tokens(),
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
                    audio_output = gr.Audio(
                        type="filepath",
                        format="wav",
                        interactive=False,
                        show_download_button=True,
                        show_label=True,
                        label="生成された音声（ダウンロードボタンで保存可能）",
                        value=None,
                        elem_id="audio_output",
                        waveform_options=gr.WaveformOptions(
                            show_recording_waveform=True,
                            waveform_color="#3498db",
                            waveform_progress_color="#27ae60",
                        ),
                        min_width=300,
                    )
                    # ダウンロードボタンは不要 - gr.Audio自体にダウンロード機能が内蔵されています

            # Set up event handlers
            # ファイルがアップロードされたら自動的にテキストを抽出
            file_input.change(
                fn=self.extract_file_text,
                inputs=[file_input],
                outputs=[extracted_text],
            ).then(
                fn=self.update_process_button_state,
                inputs=[extracted_text],
                outputs=[process_btn],
            )

            # OpenAI API key - ユーザが入力したらすぐに保存
            openai_api_key_input.change(
                fn=self.set_openai_api_key,
                inputs=[openai_api_key_input],
                outputs=[],
            ).then(
                fn=self.update_process_button_state,
                inputs=[extracted_text],
                outputs=[process_btn],
            )

            # Gemini API key
            gemini_api_key_input.change(
                fn=self.set_gemini_api_key,
                inputs=[gemini_api_key_input],
                outputs=[],
            ).then(
                fn=self.update_process_button_state,
                inputs=[extracted_text],
                outputs=[process_btn],
            )

            # タブ切り替え時のLLMタイプ変更
            openai_tab.select(
                fn=lambda: self.switch_llm_type("openai"),
                outputs=[],
            )

            gemini_tab.select(
                fn=lambda: self.switch_llm_type("gemini"),
                outputs=[],
            )

            # OpenAI Model selection
            openai_model_dropdown.change(
                fn=self.set_openai_model_name,
                inputs=[openai_model_dropdown],
                outputs=[],
            )

            # Gemini Model selection
            gemini_model_dropdown.change(
                fn=self.set_gemini_model_name,
                inputs=[gemini_model_dropdown],
                outputs=[],
            )

            # OpenAI Max tokens selection
            openai_max_tokens_slider.change(
                fn=self.set_openai_max_tokens,
                inputs=[openai_max_tokens_slider],
                outputs=[],
            )

            # Gemini Max tokens selection
            gemini_max_tokens_slider.change(
                fn=self.set_gemini_max_tokens,
                inputs=[gemini_max_tokens_slider],
                outputs=[],
            )

            character1_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown],
                outputs=[],
            )

            character2_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown],
                outputs=[],
            )

            # VOICEVOX Terms checkbox - 音声生成ボタンに対してイベントハンドラを更新
            terms_checkbox.change(
                fn=self.update_audio_button_state,
                inputs=[terms_checkbox, podcast_text],
                outputs=[generate_btn],
            )

            process_btn.click(
                fn=self.generate_podcast_text,
                inputs=[extracted_text],
                outputs=[podcast_text],
            ).then(
                # トークン使用状況をUIに反映
                fn=self.update_token_usage_display,
                outputs=[token_usage_info],
            ).then(
                # トーク原稿生成後に音声生成ボタンの状態を更新
                fn=self.update_audio_button_state,
                inputs=[terms_checkbox, podcast_text],
                outputs=[generate_btn],
            )

            # 音声生成ボタンのイベントハンドラ
            generate_btn.click(
                fn=self.generate_podcast_audio,
                inputs=[podcast_text],
                outputs=[audio_output],
            )

            # ドキュメントタイプ選択のイベントハンドラ
            document_type_radio.change(
                fn=self.set_document_type,
                inputs=[document_type_radio],
                outputs=[],
            )

            # ポッドキャストモード選択のイベントハンドラ
            podcast_mode_radio.change(
                fn=self.set_podcast_mode,
                inputs=[podcast_mode_radio],
                outputs=[],
            )

            # podcast_textの変更時にも音声生成ボタンの状態を更新
            podcast_text.change(
                fn=self.update_audio_button_state,
                inputs=[terms_checkbox, podcast_text],
                outputs=[generate_btn],
            )

        return app

    def get_openai_available_models(self) -> List[str]:
        """
        利用可能なOpenAIモデルのリストを取得します。

        Returns:
            List[str]: 利用可能なモデル名のリスト
        """
        return self.text_processor.openai_model.get_available_models()

    def get_openai_current_model(self) -> str:
        """
        現在設定されているOpenAIモデル名を取得します。

        Returns:
            str: 現在のモデル名
        """
        return self.text_processor.openai_model.model_name

    def get_gemini_available_models(self) -> List[str]:
        """
        利用可能なGeminiモデルのリストを取得します。

        Returns:
            List[str]: 利用可能なモデル名のリスト
        """
        return self.text_processor.gemini_model.get_available_models()

    def get_gemini_current_model(self) -> str:
        """
        現在設定されているGeminiモデル名を取得します。

        Returns:
            str: 現在のモデル名
        """
        return self.text_processor.gemini_model.model_name

    def set_openai_model_name(self, model_name: str) -> None:
        """
        OpenAIモデル名を設定します。

        Args:
            model_name (str): 使用するモデル名
        """
        success = self.text_processor.openai_model.set_model_name(model_name)
        logger.debug(f"OpenAI model set to {model_name}: {success}")

    def set_gemini_model_name(self, model_name: str) -> None:
        """
        Geminiモデル名を設定します。

        Args:
            model_name (str): 使用するモデル名
        """
        success = self.text_processor.gemini_model.set_model_name(model_name)
        logger.debug(f"Gemini model set to {model_name}: {success}")

    def get_openai_max_tokens(self) -> int:
        """
        現在設定されているOpenAIの最大トークン数を取得します。

        Returns:
            int: 現在の最大トークン数
        """
        return self.text_processor.openai_model.get_max_tokens()

    def get_gemini_max_tokens(self) -> int:
        """
        現在設定されているGeminiの最大トークン数を取得します。

        Returns:
            int: 現在の最大トークン数
        """
        return self.text_processor.gemini_model.get_max_tokens()

    def set_openai_max_tokens(self, max_tokens: int) -> None:
        """
        OpenAIの最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数
        """
        success = self.text_processor.openai_model.set_max_tokens(max_tokens)
        logger.debug(f"OpenAI max tokens set to {max_tokens}: {success}")

    def set_gemini_max_tokens(self, max_tokens: int) -> None:
        """
        Geminiの最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数
        """
        success = self.text_processor.gemini_model.set_max_tokens(max_tokens)
        logger.debug(f"Gemini max tokens set to {max_tokens}: {success}")

    def get_available_characters(self) -> List[str]:
        """利用可能なキャラクターのリストを取得します。

        Returns:
            List[str]: 利用可能なキャラクター名のリスト
        """
        return DISPLAY_NAMES

    def set_character_mapping(self, character1: str, character2: str) -> None:
        """キャラクターマッピングを設定します。

        Args:
            character1 (str): Character1に割り当てるキャラクター名
            character2 (str): Character2に割り当てるキャラクター名
        """
        success = self.text_processor.set_character_mapping(character1, character2)
        logger.debug(f"Character mapping set: {character1}, {character2}: {success}")

    def update_process_button_state(self, extracted_text: str) -> Dict[str, Any]:
        """
        抽出されたテキストとAPIキーの状態に基づいて"トーク原稿を生成"ボタンの有効/無効を切り替えます。

        Args:
            extracted_text (str): 抽出されたテキスト

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

        if self.current_llm_type == "openai":
            has_api_key = bool(self.text_processor.openai_model.api_key)
        elif self.current_llm_type == "gemini":
            has_api_key = bool(self.text_processor.gemini_model.api_key)

        is_enabled = has_text and has_api_key

        # gr.update()を使用して、Gradioのコンポーネントを更新する
        # Dict[str, Any]型にキャストして型チェッカーを満足させる
        result = gr.update(
            interactive=is_enabled, variant="primary" if is_enabled else "secondary"
        )
        return result  # type: ignore

    def set_podcast_mode(self, mode: str) -> None:
        """
        ポッドキャスト生成モードを設定します。

        Args:
            mode (str): ポッドキャストモードのラベル名
        """
        try:
            # ラベル名からPodcastModeを取得
            podcast_mode = PodcastMode.from_label_name(mode)

            # TextProcessorを使ってPodcastModeのEnumを設定
            success = self.text_processor.set_podcast_mode(podcast_mode.value)

            logger.debug(f"Podcast mode set to {mode}: {success}")

        except ValueError as e:
            logger.error(f"Error setting podcast mode: {str(e)}")

    def get_podcast_modes(self):
        """
        利用可能なポッドキャスト生成モードのリストを取得します。

        Returns:
            list: 利用可能なモードのラベル名リスト
        """
        return PodcastMode.get_all_label_names()

    def update_token_usage_display(self) -> str:
        """
        トークン使用状況を表示用のHTMLとして返します。

        Returns:
            str: トークン使用状況のHTML
        """
        token_usage = self.text_processor.get_token_usage()
        if not token_usage:
            return "<div>トークン使用状況: データがありません</div>"

        prompt_tokens = token_usage.get("prompt_tokens", math.nan)
        completion_tokens = token_usage.get("completion_tokens", math.nan)
        total_tokens = token_usage.get("total_tokens", math.nan)

        # API名を取得
        api_name = (
            "OpenAI API"
            if self.text_processor.current_api_type == "openai"
            else "Google Gemini API"
        )

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

    def set_document_type(self, doc_type: str) -> None:
        """
        ドキュメントタイプを設定します。

        Args:
            doc_type (str): ドキュメントタイプのラベル名
        """
        try:
            # ラベル名からDocumentTypeを取得
            document_type = DocumentType.from_label_name(doc_type)

            # TextProcessorを使ってドキュメントタイプを設定
            success = self.text_processor.set_document_type(document_type)

            logger.debug(f"Document type set to {doc_type}: {success}")

        except ValueError as e:
            logger.error(f"Error setting document type: {str(e)}")


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

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        favicon_path="assets/favicon.ico",
        inbrowser=inbrowser,
    )


if __name__ == "__main__":
    main()
