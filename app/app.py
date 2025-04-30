"""Main application module.

Builds the Paper Podcast Generator application using Gradio.
"""

import os
import uuid
from pathlib import Path
from typing import List, Tuple

import gradio as gr

from app.components.audio_generator import VOICEVOX_CORE_AVAILABLE, AudioGenerator
from app.components.file_uploader import FileUploader
from app.components.text_processor import TextProcessor
from app.utils.logger import logger

# Check for temporary file directories
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
        self.file_uploader = FileUploader()
        self.text_processor = TextProcessor()
        self.audio_generator = AudioGenerator()

        # Check if VOICEVOX Core is available
        self.voicevox_core_available = (
            VOICEVOX_CORE_AVAILABLE and self.audio_generator.core_initialized
        )

        # APIキーの状態を確認
        api_key_status = (
            "✅ 設定済み" if self.text_processor.openai_model.api_key else "❌ 未設定"
        )

        # システムログの初期化
        self.system_log = (
            f"OpenAI API: {api_key_status}\nVOICEVOXステータス: {self.check_voicevox_core()}"
        )

    def set_api_key(self, api_key: str) -> Tuple[str, str]:
        """
        Set the OpenAI API key and returns a result message based on the outcome.

        Args:
            api_key (str): OpenAI API key

        Returns:
            tuple: (status_message, system_log)
        """
        success = self.text_processor.set_openai_api_key(api_key)
        result = "✅ APIキーが正常に設定されました" if success else "❌ APIキーの設定に失敗しました"
        self.update_log(f"OpenAI API: {result}")
        return result, self.system_log

    def set_prompt_template(self, prompt_template: str) -> Tuple[str, str]:
        """
        Set the prompt template and returns a result message.

        Args:
            prompt_template (str): Custom prompt template

        Returns:
            tuple: (status_message, system_log)
        """
        success = self.text_processor.set_prompt_template(prompt_template)
        result = "✅ プロンプトテンプレートが保存されました" if success else "❌ プロンプトテンプレートの保存に失敗しました"
        self.update_log(f"プロンプトテンプレート: {result}")
        return result, self.system_log

    def get_prompt_template(self) -> str:
        """
        Get the current prompt template.

        Returns:
            str: The current prompt template
        """
        return self.text_processor.get_prompt_template()

    def handle_file_upload(self, file_obj):
        """
        Process file uploads.

        Properly handles file objects from Gradio's file upload component.

        Args:
            file_obj: Gradio's file object

        Returns:
            str: Path to the temporary file
        """
        if file_obj is None:
            return None

        try:
            # Temporary directory path
            temp_dir = Path("data/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Get filename
            if isinstance(file_obj, list) and len(file_obj) > 0:
                file_obj = file_obj[0]  # Get first element if it's a list

            if hasattr(file_obj, "name"):
                filename = Path(file_obj.name).name
            else:
                # Generate temporary name using UUID if no name is available
                filename = f"uploaded_{uuid.uuid4().hex}.txt"

            # Create temporary file path
            temp_path = temp_dir / filename

            # Get and save file data
            if hasattr(file_obj, "read") and callable(file_obj.read):
                with open(temp_path, "wb") as f:
                    f.write(file_obj.read())
            elif hasattr(file_obj, "name"):
                with open(temp_path, "wb") as f:
                    with open(file_obj.name, "rb") as source:
                        f.write(source.read())

            return str(temp_path)

        except Exception as e:
            logger.error(f"File processing error: {e}")
            return None

    def extract_file_text(self, file_obj) -> Tuple[str, str]:
        """
        Extract text from a file.

        Args:
            file_obj: Uploaded file object

        Returns:
            tuple: (extracted_text, system_log)
        """
        if file_obj is None:
            self.update_log("ファイルアップロード: ファイルが選択されていません")
            return "Please upload a file.", self.system_log

        # Save file locally
        temp_path = self.handle_file_upload(file_obj)
        if not temp_path:
            self.update_log("ファイルアップロード: ファイル処理に失敗しました")
            return "Failed to process the file.", self.system_log

        # Extract text using FileUploader
        text = self.file_uploader.extract_text_from_path(temp_path)
        self.update_log(f"テキスト抽出: 完了 ({len(text)} 文字)")
        return text, self.system_log

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

    def update_log(self, message: str) -> str:
        """
        システムログにメッセージを追加します。

        Args:
            message (str): 追加するメッセージ

        Returns:
            str: 更新されたログ
        """
        self.system_log = f"{message}\n{self.system_log}"
        # 最大3行に制限
        lines = self.system_log.split("\n")
        if len(lines) > 3:
            self.system_log = "\n".join(lines[:3])
        return self.system_log

    def generate_podcast_text(self, text: str):
        """
        Generate podcast-style text from input text.

        Args:
            text (str): Input text from file

        Returns:
            tuple: (generated_podcast_text, system_log)
        """
        if not text:
            self.update_log("ポッドキャストテキスト生成: ❌ 入力テキストが空です")
            return "Please upload a file and extract text first.", self.system_log

        # Check if API key is set
        if not self.text_processor.openai_model.api_key:
            self.update_log("ポッドキャストテキスト生成: ❌ OpenAI APIキーが設定されていません")
            return (
                "OpenAI API key is not set. Please configure it in the Settings tab.",
                self.system_log,
            )

        try:
            # Generate podcast text
            podcast_text = self.text_processor.process_text(text)
            self.update_log("ポッドキャストテキスト生成: ✅ 完了")
            logger.info(f"Podcast text sample: {text[:200]}...")
            return podcast_text, self.system_log
        except Exception as e:
            error_msg = f"ポッドキャストテキスト生成: ❌ エラー - {str(e)}"
            self.update_log(error_msg)
            logger.error(f"Podcast text generation error: {str(e)}")
            return f"Error: {str(e)}", self.system_log

    def generate_podcast_audio(self, text: str):
        """
        Generate audio from podcast text.

        Args:
            text (str): Generated podcast text

        Returns:
            tuple: (audio_path or None, system_log)
        """
        if not text:
            self.update_log("音声生成: ❌ テキストが空です")
            return None, self.system_log

        # Check if VOICEVOX Core is available
        if not self.voicevox_core_available:
            self.update_log("音声生成: ❌ VOICEVOX Coreが利用できません")
            return None, self.system_log

        try:
            # Generate audio from text
            audio_path = self.audio_generator.generate_character_conversation(text)
            if audio_path:
                self.update_log("音声生成: ✅ 完了")
                return audio_path, self.system_log
            else:
                logger.error("Audio generation failed: No audio path returned")
                self.update_log("音声生成: ❌ 音声生成に失敗しました")
                return None, self.system_log
        except Exception as e:
            logger.error(f"Audio generation exception: {str(e)}")
            self.update_log(f"音声生成: ❌ エラー - {str(e)}")
            return None, self.system_log

    def ui(self) -> gr.Blocks:
        """
        Create the Gradio interface.

        Returns:
            gr.Blocks: Gradio Blocks instance
        """
        app = gr.Blocks(
            title="Paper Podcast Generator", css="footer {display: none !important;}"
        )

        with app:
            gr.Markdown(
                """
                # YomiTalk

                テキストファイルやPDFから「ずんだもん」と「四国めたん」によるポッドキャスト音声を生成します。
                """
            )

            with gr.Row():
                # OpenAI API settings at the top
                with gr.Column():
                    gr.Markdown("## OpenAI API設定")
                    with gr.Row():
                        api_key_input = gr.Textbox(
                            placeholder="sk-...",
                            type="password",
                            show_label=False,
                            scale=3,
                        )
                        api_key_status = gr.Textbox(
                            interactive=False,
                            placeholder="APIキーをセットしてください",
                            value=self.get_api_key_status(),
                            show_label=False,
                            scale=3,
                        )

                    with gr.Row():
                        model_dropdown = gr.Dropdown(
                            choices=self.get_available_models(),
                            value=self.get_current_model(),
                            label="モデル",
                            scale=3,
                        )

                    api_key_btn = gr.Button("保存", variant="primary")

            with gr.Row():
                # File upload and text extraction
                with gr.Column():
                    gr.Markdown("## ファイルアップロード")

                    # サポートしているファイル形式の拡張子を取得
                    supported_extensions = self.file_uploader.get_supported_extensions()

                    # ファイルをアップロードするコンポーネント
                    file_input = gr.File(
                        file_types=supported_extensions,
                        type="filepath",
                        label=f"サポートしているファイル形式: {', '.join(supported_extensions)}",
                    )
                    extract_btn = gr.Button("テキストを抽出", variant="primary")

            with gr.Row():
                # Text processing
                with gr.Column():
                    gr.Markdown("## 抽出テキスト（トークの元ネタ）")
                    extracted_text = gr.Textbox(
                        placeholder="ファイルを選択してテキストを抽出してください...",
                        lines=10,
                        show_label=False,
                    )

                    # Prompt template settings accordion
                    with gr.Accordion(label="プロンプトテンプレート設定", open=False):
                        with gr.Column():
                            prompt_template = gr.Textbox(
                                placeholder="プロンプトテンプレートを入力してください...",
                                lines=10,
                                elem_id="prompt-template",
                                value=self.get_prompt_template(),
                                show_label=False,
                            )
                            prompt_template_status = gr.Textbox(
                                interactive=False,
                                placeholder="変更すると自動保存されます",
                                show_label=False,
                            )

                    # VOICEVOX利用規約チェックボックスをここに移動
                    terms_checkbox = gr.Checkbox(
                        label="VOICEVOX 音源利用規約に同意する",
                        value=False,
                        info="音声を生成するには[VOICEVOX 音源利用規約](https://zunko.jp/con_ongen_kiyaku.html)への同意が必要です。",
                    )
                    process_btn = gr.Button("トークを生成", variant="primary")
                    podcast_text = gr.Textbox(
                        label="生成されたトーク",
                        placeholder="テキストを処理してトークを生成してください...",
                        lines=15,
                    )

            with gr.Row():
                # Audio generation section
                with gr.Column():
                    gr.Markdown("## トーク音声")

                    generate_btn = gr.Button(
                        "音声を生成", variant="primary", interactive=False
                    )
                    audio_output = gr.Audio(
                        type="filepath",
                        format="wav",
                        interactive=False,
                        show_download_button=True,
                        show_label=False,
                    )
                    download_btn = gr.Button("音声をダウンロード", elem_id="download_audio_btn")

            # システムログ表示エリア（VOICEVOXステータスを含む）
            system_log_display = gr.Textbox(
                label="システム状態",
                value=self.system_log,
                interactive=False,
                show_label=True,
            )

            # Set up event handlers
            extract_btn.click(
                fn=self.extract_file_text,
                inputs=[file_input],
                outputs=[extracted_text, system_log_display],
            )

            # API key
            api_key_btn.click(
                fn=self.set_api_key,
                inputs=[api_key_input],
                outputs=[api_key_status, system_log_display],
            )

            # Model selection
            model_dropdown.change(
                fn=self.set_model_name,
                inputs=[model_dropdown],
                outputs=[system_log_display],
            )

            # Prompt template
            prompt_template.change(
                fn=self.set_prompt_template,
                inputs=[prompt_template],
                outputs=[prompt_template_status, system_log_display],
            )

            # VOICEVOX Terms checkbox - 音声生成ボタンに対してイベントハンドラを更新
            terms_checkbox.change(
                fn=self.update_audio_button_state,
                inputs=[terms_checkbox],
                outputs=[generate_btn],
            )

            process_btn.click(
                fn=self.generate_podcast_text,
                inputs=[extracted_text],
                outputs=[podcast_text, system_log_display],
            )

            generate_btn.click(
                fn=self.generate_podcast_audio,
                inputs=[podcast_text],
                outputs=[audio_output, system_log_display],
            )

            # ダウンロードボタンの実装を改善
            # Gradio 4.xのダウンロード機能を使用
            download_btn.click(
                fn=lambda x: (
                    x if x else None,
                    self.update_log("音声ファイル: ダウンロードしました")
                    if x
                    else self.update_log("音声ファイル: ダウンロードできません"),
                ),
                inputs=[audio_output],
                outputs=[audio_output, system_log_display],
            ).then(
                lambda x: x,
                inputs=[audio_output],
                outputs=None,
                js="""
                async (audio_path) => {
                    if (!audio_path) {
                        console.error("オーディオパスがありません");
                        return;
                    }

                    try {
                        // グローバル変数にダウンロード情報を保存（テスト用）
                        window.lastDownloadedFile = audio_path;

                        // ダウンロード処理
                        const response = await fetch(audio_path);
                        if (!response.ok) throw new Error(`ダウンロード失敗: ${response.status}`);

                        const blob = await response.blob();
                        const filename = audio_path.split('/').pop();

                        // ダウンロードリンク作成
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = filename;
                        a.style.display = "none";
                        document.body.appendChild(a);

                        // ダウンロード開始
                        a.click();

                        // クリーンアップ
                        setTimeout(() => {
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                        }, 100);

                        console.log("ダウンロード完了:", filename);
                    } catch (error) {
                        console.error("ダウンロードエラー:", error);
                    }
                }
                """,
            )

        return app

    # 既存のAPIキー状態を取得するメソッドを追加
    def get_api_key_status(self) -> str:
        """
        現在のAPIキーの状態を取得します。

        Returns:
            str: APIキーのステータスメッセージ
        """
        return (
            "✅ APIキーが設定されています"
            if self.text_processor.openai_model.api_key
            else "APIキーをセットしてください"
        )

    def set_model_name(self, model_name: str) -> str:
        """
        OpenAIモデル名を設定します。

        Args:
            model_name (str): 使用するモデル名

        Returns:
            str: システムログ
        """
        success = self.text_processor.openai_model.set_model_name(model_name)
        result = "✅ モデルが正常に設定されました" if success else "❌ モデル設定に失敗しました"
        self.update_log(f"OpenAI モデル: {result} ({model_name})")
        return self.system_log

    def get_available_models(self) -> List[str]:
        """
        利用可能なOpenAIモデルのリストを取得します。

        Returns:
            List[str]: 利用可能なモデル名のリスト
        """
        return self.text_processor.openai_model.get_available_models()

    def get_current_model(self) -> str:
        """
        現在設定されているOpenAIモデル名を取得します。

        Returns:
            str: 現在のモデル名
        """
        return self.text_processor.openai_model.model_name

    def update_button_state(self, checked: bool) -> gr.Button:
        """
        利用規約チェックボックスの状態に基づいてボタンの有効/無効を切り替えます。

        Args:
            checked (bool): チェックボックスの状態

        Returns:
            gr.Button: 更新されたボタン
        """
        button = gr.Button(value="トークを生成", variant="primary", interactive=checked)
        return button

    def update_audio_button_state(self, checked: bool) -> gr.Button:
        """
        VOICEVOX利用規約チェックボックスの状態に基づいて音声生成ボタンの有効/無効を切り替えます。

        Args:
            checked (bool): チェックボックスの状態

        Returns:
            gr.Button: 更新されたボタン
        """
        button = gr.Button(value="音声を生成", variant="primary", interactive=checked)
        return button


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
