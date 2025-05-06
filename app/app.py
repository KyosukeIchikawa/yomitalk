"""Main application module.

Builds the Paper Podcast Generator application using Gradio.
"""

import math
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

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

        # 利用可能なキャラクター
        self.available_characters = (
            self.text_processor.openai_model.get_valid_characters()
        )

        # ポッドキャスト生成モード
        self.podcast_modes = ["標準モード", "セクション解説モード"]

        # 現在選択されているUIモード
        self.current_ui_mode = "標準モード"

    def set_api_key(self, api_key: str) -> Tuple[str, str]:
        """
        Set the OpenAI API key and returns a result message based on the outcome.

        Args:
            api_key (str): OpenAI API key

        Returns:
            tuple: (status_message, system_log)
        """
        # APIキーが空白や空文字の場合は処理しない
        if not api_key or api_key.strip() == "":
            result = "❌ APIキーが空です。有効なAPIキーを入力してください"
            self.update_log(f"OpenAI API: {result}")
            return result, self.system_log

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
        現在のプロンプトテンプレートを取得します。

        Returns:
            str: 現在のプロンプトテンプレート
        """
        return self.text_processor.get_prompt_template()

    def get_prompt_template_for_mode(self, mode=None) -> str:
        """
        指定されたモードに基づいたプロンプトテンプレートを取得します。
        UIのプロンプトテンプレート表示更新用に使用します。

        Args:
            mode (str, optional): モード名（"標準モード"または"セクション解説モード"）

        Returns:
            str: モードに対応するプロンプトテンプレート
        """
        # UIでの表示用にハードコードされたテンプレートを返す
        try:
            if mode == "セクション解説モード":
                # セクション解説モード用のテンプレートをハードコード
                template_path = Path("app/templates/section_by_section.j2")
                if template_path.exists():
                    with open(template_path, "r", encoding="utf-8") as f:
                        return f.read()
                else:
                    self.update_log(f"セクション解説モード用テンプレートが見つかりません: {template_path}")

            # 標準モードまたは不明なモードの場合、デフォルトテンプレートを返す
            template_path = Path("app/templates/paper_to_podcast.j2")
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                self.update_log(f"標準モード用テンプレートが見つかりません: {template_path}")
                return "テンプレートファイルが見つかりません。"

        except Exception as e:
            error_msg = f"テンプレート読み込みエラー: {str(e)}"
            self.update_log(error_msg)
            logger.error(error_msg)
            return f"エラー: {error_msg}"

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

            # トークン使用状況を取得してログに追加
            token_usage = self.text_processor.get_token_usage()
            if token_usage:
                usage_msg = f"トークン使用: 入力 {token_usage.get('prompt_tokens', 0)}、出力 {token_usage.get('completion_tokens', 0)}、合計 {token_usage.get('total_tokens', 0)}"
                self.update_log(usage_msg)

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
                # 絶対パスを取得
                abs_path = str(Path(audio_path).absolute())
                self.update_log(f"音声生成: ✅ 完了 ({abs_path})")
                logger.info(f"Generated audio file: {abs_path}")
                return abs_path, self.system_log
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

                テキストファイルやPDFから"ずんだもん"と"四国めたん"によるポッドキャスト音声を生成します。
                """
            )

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
                    extract_btn = gr.Button(
                        "テキストを抽出", variant="primary", interactive=False
                    )

            with gr.Row():
                # Text processing
                with gr.Column():
                    gr.Markdown("## 抽出テキスト（トークの元ネタ）")
                    extracted_text = gr.Textbox(
                        placeholder="ファイルを選択してテキストを抽出してください...",
                        lines=10,
                        show_label=False,
                    )

                    # ポッドキャスト生成モード選択
                    podcast_mode_radio = gr.Radio(
                        choices=self.get_podcast_modes(),
                        value=self.get_current_podcast_mode(),
                        label="生成モード",
                        info="標準モード: 論文全体を要約したポッドキャスト形式の会話を生成します。\nセクション解説モード: 論文のセクションごとに順を追って解説する会話を生成します。",
                    )

                    # キャラクター設定
                    with gr.Accordion(label="キャラクター設定", open=False):
                        with gr.Row():
                            character1_dropdown = gr.Dropdown(
                                choices=self.get_available_characters(),
                                value="四国めたん",
                                label="キャラクター1（専門家役）",
                            )
                            character2_dropdown = gr.Dropdown(
                                choices=self.get_available_characters(),
                                value="ずんだもん",
                                label="キャラクター2（初学者役）",
                            )

                    # Prompt template settings accordion
                    with gr.Accordion(label="プロンプトテンプレート設定", open=False) as _:
                        with gr.Column():
                            prompt_template = gr.Textbox(
                                placeholder="プロンプトテンプレートを入力してください...",
                                lines=10,
                                elem_id="prompt-template",
                                value=self.get_prompt_template(),
                                show_label=False,
                            )

                    # OpenAI API設定
                    with gr.Row():
                        with gr.Column(scale=3):
                            api_key_input = gr.Textbox(
                                placeholder="sk-...",
                                type="password",
                                label="OpenAI APIキー",
                            )
                        with gr.Column(scale=2):
                            model_dropdown = gr.Dropdown(
                                choices=self.get_available_models(),
                                value=self.get_current_model(),
                                label="モデル",
                            )
                    with gr.Row():
                        max_tokens_slider = gr.Slider(
                            minimum=100,
                            maximum=32768,
                            value=self.get_max_tokens(),
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

            with gr.Row():
                # Audio generation section
                with gr.Column():
                    gr.Markdown("## トーク音声")

                    # VOICEVOX利用規約チェックボックスをここに配置
                    terms_checkbox = gr.Checkbox(
                        label="VOICEVOX 音源利用規約に同意する",
                        value=False,
                        info="音声を生成するには[VOICEVOX 音源利用規約](https://zunko.jp/con_ongen_kiyaku.html)への同意が必要です。",
                    )
                    generate_btn = gr.Button(
                        "音声を生成", variant="primary", interactive=False
                    )
                    audio_output = gr.Audio(
                        type="filepath",
                        format="wav",
                        interactive=False,
                        show_download_button=True,
                        show_label=False,
                        elem_id="audio_output",
                    )
                    download_btn = gr.Button(
                        "音声が生成されていません",
                        elem_id="download_audio_btn",
                        interactive=False,
                        variant="secondary",
                    )

            # システムログ表示エリア（VOICEVOXステータスを含む）
            system_log_display = gr.Textbox(
                label="システム状態",
                value=self.system_log,
                interactive=False,
                show_label=True,
            )

            # Set up event handlers
            # ファイルがアップロードされたらボタンを有効化
            file_input.change(
                fn=lambda x: gr.update(interactive=bool(x)),
                inputs=[file_input],
                outputs=[extract_btn],
            )

            extract_btn.click(
                fn=self.extract_file_text,
                inputs=[file_input],
                outputs=[extracted_text, system_log_display],
            ).then(
                fn=self.update_process_button_state,
                inputs=[extracted_text],
                outputs=[process_btn],
            )

            # API key - ユーザが入力したらすぐに保存
            api_key_input.change(
                fn=self.set_api_key,
                inputs=[api_key_input],
                outputs=[system_log_display],
            ).then(
                fn=self.update_process_button_state,
                inputs=[extracted_text],
                outputs=[process_btn],
            )

            # Model selection
            model_dropdown.change(
                fn=self.set_model_name,
                inputs=[model_dropdown],
                outputs=[system_log_display],
            )

            # Max tokens selection
            max_tokens_slider.change(
                fn=self.set_max_tokens,
                inputs=[max_tokens_slider],
                outputs=[system_log_display],
            )

            # Prompt template
            prompt_template.change(
                fn=self.set_prompt_template,
                inputs=[prompt_template],
                outputs=[system_log_display],
            )

            # キャラクター設定 - ドロップダウンが変更されたらすぐに保存
            character1_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown],
                outputs=[system_log_display],
            )

            character2_dropdown.change(
                fn=self.set_character_mapping,
                inputs=[character1_dropdown, character2_dropdown],
                outputs=[system_log_display],
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
            ).then(
                # トークン使用状況をUIに反映
                fn=self.update_token_usage_display,
                outputs=[token_usage_info],
            )

            # 音声生成ボタンのイベントハンドラ
            generate_btn.click(
                fn=self.generate_podcast_audio,
                inputs=[podcast_text],
                outputs=[audio_output, system_log_display],
            ).then(
                # Gradio 5.xでは、Button.updateではなくUpdateクラスを使用
                fn=lambda x: gr.update(
                    interactive=bool(x),
                    value="音声をダウンロード" if bool(x) else "音声が生成されていません",
                    variant="primary" if bool(x) else "secondary",
                ),
                inputs=[audio_output],
                outputs=[download_btn],
            )

            # audio_outputが変更された時もダウンロードボタンの状態を更新
            audio_output.change(
                fn=lambda x: gr.update(
                    interactive=bool(x),
                    value="音声をダウンロード" if bool(x) else "音声が生成されていません",
                    variant="primary" if bool(x) else "secondary",
                ),
                inputs=[audio_output],
                outputs=[download_btn],
            )

            # ダウンロードボタンの実装
            download_btn.click(
                fn=lambda x: (
                    x,
                    self.update_log("音声ファイル: ダウンロード処理中")
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
                        console.log("ダウンロード処理を開始します:", audio_path);

                        // 異なる形式への対応
                        let url;
                        let filename;

                        // audio_pathの型によって処理を分岐
                        if (typeof audio_path === 'string') {
                            url = audio_path;
                            filename = audio_path.split('/').pop();
                        } else if (typeof audio_path === 'object') {
                            // オブジェクトの形式を調査
                            console.log("オーディオオブジェクト:", audio_path);

                            if (audio_path.url) {
                                url = audio_path.url;
                                filename = audio_path.name || url.split('/').pop();
                            } else if (audio_path.data) {
                                url = audio_path.data;
                                filename = audio_path.name || "audio.wav";
                            } else if (audio_path.value) {
                                url = audio_path.value;
                                filename = url.split('/').pop();
                            } else {
                                // プロパティを列挙して調査
                                for (const key in audio_path) {
                                    console.log(`プロパティ ${key}:`, audio_path[key]);
                                }
                                throw new Error("認識できない音声ファイル形式です");
                            }
                        } else {
                            throw new Error("不明な音声ファイル形式です: " + typeof audio_path);
                        }

                        console.log("ダウンロード情報:", { url, filename });

                        // ダウンロード処理
                        if (url) {
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = filename;
                            a.target = "_blank";
                            document.body.appendChild(a);
                            a.click();

                            // 成功メッセージ
                            console.log("ダウンロード処理が実行されました:", filename);

                            // クリーンアップ
                            setTimeout(() => {
                                document.body.removeChild(a);
                            }, 100);
                        } else {
                            throw new Error("ダウンロードURLが取得できませんでした");
                        }
                    } catch (error) {
                        console.error("ダウンロードエラー:", error);
                        alert("ダウンロードに失敗しました: " + error.message);
                    }
                }
                """,
            )

            # ポッドキャストモード選択のイベントハンドラ
            podcast_mode_radio.change(
                fn=self.set_podcast_mode,
                inputs=[podcast_mode_radio],
                outputs=[system_log_display],
            ).then(
                # モード変更後にプロンプトテンプレートを更新
                fn=self.get_prompt_template_for_mode,
                inputs=[podcast_mode_radio],  # モード情報を明示的に渡す
                outputs=[prompt_template],
            )

        return app

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
        button = gr.Button(value="トーク原稿を生成", variant="primary", interactive=checked)
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

    def set_character_mapping(
        self, character1: str, character2: str
    ) -> Tuple[str, str]:
        """
        キャラクターマッピングを設定する。

        Args:
            character1 (str): Character1に割り当てるキャラクター名
            character2 (str): Character2に割り当てるキャラクター名

        Returns:
            tuple: (status_message, system_log)
        """
        success = self.text_processor.openai_model.set_character_mapping(
            character1, character2
        )
        result = "✅ キャラクター設定が完了しました" if success else "❌ キャラクター設定に失敗しました"
        self.update_log(f"キャラクター設定: {result}")
        return result, self.system_log

    def get_character_mapping(self) -> dict:
        """
        現在のキャラクターマッピングを取得する。

        Returns:
            dict: 現在のキャラクターマッピング
        """
        return self.text_processor.openai_model.get_character_mapping()

    def get_available_characters(self) -> List[str]:
        """
        利用可能なキャラクターのリストを取得する。

        Returns:
            List[str]: 利用可能なキャラクター名のリスト
        """
        return self.available_characters

    def set_max_tokens(self, max_tokens: int) -> str:
        """
        最大トークン数を設定します。

        Args:
            max_tokens (int): 設定する最大トークン数

        Returns:
            str: システムログ
        """
        success = self.text_processor.openai_model.set_max_tokens(max_tokens)
        result = "✅ 最大トークン数が正常に設定されました" if success else "❌ 最大トークン数の設定に失敗しました"
        self.update_log(f"最大トークン数: {result} ({max_tokens})")
        return self.system_log

    def get_max_tokens(self) -> int:
        """
        現在設定されている最大トークン数を取得します。

        Returns:
            int: 現在の最大トークン数
        """
        return self.text_processor.openai_model.get_max_tokens()

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
        has_api_key = bool(self.text_processor.openai_model.api_key)

        is_enabled = has_text and has_api_key

        # gr.update()を使用して、Gradioのコンポーネントを更新する
        # Dict[str, Any]型にキャストして型チェッカーを満足させる
        result = gr.update(
            interactive=is_enabled, variant="primary" if is_enabled else "secondary"
        )
        return result  # type: ignore

    def set_podcast_mode(self, mode: str) -> str:
        """
        ポッドキャスト生成モードを設定します。
        注: 内部のモード切替機能は廃止され、UIでの表示切替のみを行います。

        Args:
            mode (str): '標準モード' または 'セクション解説モード'

        Returns:
            str: 結果メッセージとシステムログ
        """
        # モードの妥当性チェック
        if mode not in self.get_podcast_modes():
            self.update_log(f"ポッドキャストモード: ❌ 不明なモード '{mode}'")
            return self.system_log

        # 現在のUIで選択されているモードを記録
        self.current_ui_mode = mode

        # ログ記録
        self.update_log(f"ポッドキャストモード: ✅ モードを '{mode}' に設定しました")
        return self.system_log

    def get_podcast_modes(self):
        """
        利用可能なポッドキャスト生成モードのリストを取得します。

        Returns:
            list: 利用可能なモードのリスト
        """
        return self.podcast_modes

    def get_current_podcast_mode(self):
        """
        現在のポッドキャスト生成モードを取得します。

        Returns:
            str: 現在のポッドキャストモード
        """
        if not hasattr(self, "current_ui_mode"):
            self.current_ui_mode = "標準モード"
        return self.current_ui_mode

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

        html = f"""
        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px;">
            <h3 style="margin-top: 0; margin-bottom: 8px;">OpenAI API Token Usage</h3>
            <div style="display: flex; justify-content: space-between;">
                <div><strong>Input Tokens:</strong> {prompt_tokens}</div>
                <div><strong>Output Tokens:</strong> {completion_tokens}</div>
                <div><strong>Total Tokens:</strong> {total_tokens}</div>
            </div>
        </div>
        """
        return html


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
