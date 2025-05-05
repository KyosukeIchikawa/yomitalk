"""Prompt management module.

This module provides functionality to manage prompt templates.
It includes the PromptManager class which handles Jinja2 templates and generation.
"""

from pathlib import Path
from typing import Dict, List, Optional

import jinja2

from app.utils.logger import logger


class PromptManager:
    """プロンプトテンプレートを管理するクラス。

    このクラスは、ポッドキャスト生成用のプロンプトテンプレートを管理します。
    Jinja2ライブラリを使用して、テンプレートの管理と変数の置換を行います。
    """

    def __init__(self) -> None:
        """Initialize the PromptManager class."""
        # テンプレートディレクトリのパス
        self.template_dir = Path("app/templates")

        # Jinja2環境の設定
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # デフォルトテンプレートのパス
        self.default_template_path = "paper_to_podcast.j2"
        # セクション解説モード用テンプレートのパス
        self.section_by_section_template_path = "section_by_section.j2"

        # カスタムテンプレートをメモリに保持
        self.custom_template: Optional[str] = None

        # 現在使用中のテンプレート
        self.use_custom_template = False

        # 現在のモード（標準またはセクション解説）
        self.current_mode = "standard"

        # キャラクターマッピング
        self.character_mapping = {"Character1": "四国めたん", "Character2": "ずんだもん"}

        # 有効なキャラクターのリスト
        self.valid_characters = ["ずんだもん", "四国めたん", "九州そら", "中国うさぎ", "中部つるぎ"]

        # キャラクターの口調パターン
        self.character_speech_patterns = {
            "ずんだもん": {
                "first_person": "ぼく",
                "sentence_end": ["のだ", "なのだ", "のだよ", "なのだよ"],
                "characteristic": "元気で子供っぽく、ややくだけた話し方（タメ口）になることが多い。調子がいいときは語尾が「〜のだよ！」などになる。",
            },
            "四国めたん": {
                "first_person": "わたし",
                "sentence_end": ["です", "ます"],
                "characteristic": "丁寧さを保ちつつ、文末までフラットなトーンで話すことが多い。疑問形でも「〜ですか？」のように、丁寧さを崩さない。",
            },
            "九州そら": {
                "first_person": "わたし",
                "sentence_end": ["ですね", "ですよ"],
                "characteristic": "全体的に柔らかく、おっとりとした、少し「天然」な雰囲気を感じさせる話し方。",
            },
            "中国うさぎ": {
                "first_person": "わし",
                "sentence_end": ["じゃ", "のじゃ", "じゃろ", "のう"],
                "characteristic": "くだけた、あるいは少し尊大な印象を与える言い回しが多い。古風、あるいはステレオタイプの広島弁のような話し方をする。",
            },
            "中部つるぎ": {
                "first_person": "ぼく",
                "sentence_end": ["だ", "だぞ", "だぞ"],
                "characteristic": "ややトーンが低めで、ぶっきらぼう、あるいは「ツンデレ」の「ツン」の部分を思わせるような、少しトゲのある（あるいは素っ気ない）話し方をする。",
            },
        }

        # 初期化時にテンプレートファイルの存在を確認
        self._check_template_files()

    def _check_template_files(self) -> None:
        """
        テンプレートファイルの存在を確認します。
        初期化時に呼び出され、警告ログを出力します。
        """
        # デフォルトテンプレートの確認
        default_path = self.template_dir / self.default_template_path
        if not default_path.exists():
            logger.warning(f"デフォルトテンプレートファイルが見つかりません: {default_path}")
        else:
            logger.info(f"デフォルトテンプレートファイル確認: {default_path}")

        # セクション解説モード用テンプレートの確認
        section_path = self.template_dir / self.section_by_section_template_path
        if not section_path.exists():
            logger.warning(f"セクション解説モード用テンプレートファイルが見つかりません: {section_path}")
        else:
            logger.info(f"セクション解説モード用テンプレートファイル確認: {section_path}")

    def set_prompt_template(self, prompt_template: str) -> bool:
        """カスタムプロンプトテンプレートを設定します。

        Args:
            prompt_template (str): カスタムプロンプトテンプレート

        Returns:
            bool: テンプレートが正常に設定されたかどうか
        """
        if not prompt_template or prompt_template.strip() == "":
            # カスタムテンプレートをクリア
            self.custom_template = None
            self.use_custom_template = False
            return True

        try:
            # テンプレート文字列の検証
            template_str = prompt_template.strip()
            try:
                # Jinja2テンプレートとして構文チェック
                jinja2.Template(template_str)
                # 問題なければメモリに保存
                self.custom_template = template_str
                self.use_custom_template = True
                return True
            except Exception as e:
                logger.error(f"Custom template syntax error: {e}")
                # エラーの場合はクリア
                self.custom_template = None
                self.use_custom_template = False
                return False

        except Exception as e:
            logger.error(f"Error setting prompt template: {e}")
            return False

    def set_podcast_mode(self, mode: str) -> bool:
        """ポッドキャスト生成モードを設定します。

        Args:
            mode (str): 'standard' または 'section_by_section'

        Returns:
            bool: モードが正常に設定されたかどうか
        """
        if mode not in ["standard", "section_by_section"]:
            return False

        self.current_mode = mode
        return True

    def get_podcast_mode(self) -> str:
        """現在のポッドキャスト生成モードを取得します。

        Returns:
            str: 現在のモード ('standard' または 'section_by_section')
        """
        return self.current_mode

    def get_current_prompt_template(self) -> str:
        """現在のプロンプトテンプレートを取得します。

        Returns:
            str: 現在のプロンプトテンプレート（カスタムが設定されている場合はカスタム、そうでなければモードに応じたデフォルト）
        """
        if self.use_custom_template and self.custom_template:
            return self.custom_template

        try:
            # モードに応じたテンプレートファイルを選択
            template_path = (
                self.section_by_section_template_path
                if self.current_mode == "section_by_section"
                else self.default_template_path
            )

            # ファイルの存在を確認
            full_path = self.template_dir / template_path
            logger.info(f"テンプレートファイルパス: {full_path}")

            if not full_path.exists():
                logger.error(f"テンプレートファイルが見つかりません: {full_path}")
                # セクション解説モードでファイルが見つからない場合は標準モードのテンプレートを使用
                if (
                    self.current_mode == "section_by_section"
                    and (self.template_dir / self.default_template_path).exists()
                ):
                    logger.warning("代わりに標準モードのテンプレートを使用します")
                    full_path = self.template_dir / self.default_template_path
                else:
                    return "エラー: テンプレートファイルが見つかりません。"

            # ファイルを読み込み
            with open(full_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # 内容を確認
            if not template_content or template_content.strip() == "":
                logger.error(f"テンプレートファイルが空です: {full_path}")
                return "エラー: テンプレートファイルが空です。"

            return template_content

        except Exception as e:
            logger.error(f"テンプレートファイル読み込みエラー: {e}")
            # デフォルトテンプレートが読めない場合は緊急措置としてエラーメッセージを返す
            return f"エラー: テンプレートファイルの読み込みに失敗しました: {e}"

    def set_character_mapping(self, character1: str, character2: str) -> bool:
        """
        キャラクターマッピングを設定します。

        Args:
            character1 (str): Character1に割り当てるキャラクターの名前
            character2 (str): Character2に割り当てるキャラクターの名前

        Returns:
            bool: 設定が成功したかどうか
        """
        if (
            character1 not in self.valid_characters
            or character2 not in self.valid_characters
        ):
            return False

        self.character_mapping["Character1"] = character1
        self.character_mapping["Character2"] = character2
        return True

    def get_character_mapping(self) -> Dict[str, str]:
        """
        現在のキャラクターマッピングを取得します。

        Returns:
            dict: 現在のキャラクターマッピング
        """
        return self.character_mapping

    def get_valid_characters(self) -> List[str]:
        """
        有効なキャラクターのリストを取得します。

        Returns:
            list: 有効なキャラクター名のリスト
        """
        return self.valid_characters

    def convert_abstract_to_real_characters(self, text: str) -> str:
        """
        抽象的なキャラクター名（Character1, Character2）を実際のキャラクター名に変換します。

        Args:
            text (str): 変換するテキスト

        Returns:
            str: 変換後のテキスト
        """
        result = text
        for abstract, real in self.character_mapping.items():
            result = result.replace(f"{abstract}:", f"{real}:")
            result = result.replace(f"{abstract}：", f"{real}：")  # 全角コロンも対応
        return result

    def generate_podcast_conversation(self, paper_text: str) -> str:
        """
        論文テキストからポッドキャスト形式の会話テキストを生成します。

        Args:
            paper_text (str): 論文テキスト（全文または一部）

        Returns:
            str: 会話形式のポッドキャストテキスト
        """
        if not paper_text.strip():
            return "Error: No paper text provided."

        try:
            character1 = self.character_mapping["Character1"]
            character2 = self.character_mapping["Character2"]

            # キャラクターの口調情報を取得
            char1_speech_pattern = self.character_speech_patterns.get(character1, {})
            char2_speech_pattern = self.character_speech_patterns.get(character2, {})

            try:
                if self.use_custom_template and self.custom_template:
                    # カスタムテンプレートがある場合はメモリから使用
                    logger.info("カスタムテンプレートを使用します")
                    template = jinja2.Template(self.custom_template)
                else:
                    # モードに応じたテンプレートを使用
                    template_path = (
                        self.section_by_section_template_path
                        if self.current_mode == "section_by_section"
                        else self.default_template_path
                    )
                    logger.info(
                        f"モード '{self.current_mode}' のテンプレート '{template_path}' を使用します"
                    )

                    # ファイルの存在を確認
                    if not (self.template_dir / template_path).exists():
                        logger.error(f"テンプレートファイルが見つかりません: {template_path}")
                        if (
                            self.current_mode == "section_by_section"
                            and (
                                self.template_dir / self.default_template_path
                            ).exists()
                        ):
                            # セクション解説モードでファイルが見つからない場合は標準モードのテンプレートを使用
                            logger.warning("代わりに標準モードのテンプレートを使用します")
                            template_path = self.default_template_path
                        else:
                            raise FileNotFoundError(
                                f"テンプレートファイルが見つかりません: {template_path}"
                            )

                    # テンプレートを取得
                    template = self.jinja_env.get_template(template_path)
            except Exception as template_error:
                logger.error(f"テンプレート取得エラー: {template_error}")
                return f"Error: テンプレートの取得に失敗しました: {template_error}"

            # テンプレートをレンダリング
            try:
                prompt: str = template.render(
                    paper_text=paper_text,
                    character1=character1,
                    character2=character2,
                    char1_speech_pattern=char1_speech_pattern,
                    char2_speech_pattern=char2_speech_pattern,
                )
                return prompt
            except Exception as render_error:
                logger.error(f"テンプレートレンダリングエラー: {render_error}")
                return f"Error: テンプレートのレンダリングに失敗しました: {render_error}"

        except Exception as e:
            logger.error(f"ポッドキャスト会話生成エラー: {e}")
            error_message: str = f"Error generating podcast conversation: {e}"
            return error_message
