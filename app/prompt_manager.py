"""Prompt management module.

This module provides functionality to manage prompt templates.
It includes the PromptManager class which handles prompt templates and generation.
"""

from typing import Dict, List, Optional

from prompt_template import PromptTemplate

from app.utils.logger import logger


class PromptManager:
    """プロンプトテンプレートを管理するクラス。

    このクラスは、ポッドキャスト生成用のシステムプロンプトとユーザープロンプトを管理します。
    prompt-templateライブラリを使用して、テンプレートの管理と変数の置換を行います。
    """

    def __init__(self) -> None:
        """Initialize the PromptManager class."""
        # デフォルトのプロンプトテンプレート
        self.default_template = self._create_default_template()
        self.custom_template: Optional[PromptTemplate] = None

        # キャラクターマッピング
        self.character_mapping = {"Character1": "ずんだもん", "Character2": "四国めたん"}

        # 有効なキャラクターのリスト
        self.valid_characters = ["ずんだもん", "四国めたん", "九州そら"]

    def _create_default_template(self) -> PromptTemplate:
        """デフォルトのプロンプトテンプレートを作成します。

        Returns:
            PromptTemplate: デフォルトのプロンプトテンプレート
        """
        template_str = """
Please generate a Japanese conversation-style podcast text between "Character1" and "Character2"
based on the following paper text.

Character roles:
- Character1: A beginner in the paper's field with basic knowledge but sometimes makes common mistakes.
  Asks curious and sometimes naive questions. Slightly ditzy but eager to learn.
- Character2: An expert on the paper's subject who explains concepts clearly and corrects Character1's misunderstandings.
  Makes complex topics understandable through metaphors and examples.

Format (STRICTLY FOLLOW THIS FORMAT):
Character1: [Character1's speech in Japanese]
Character2: [Character2's speech in Japanese]
Character1: [Character1's next line]
Character2: [Character2's next line]
...

IMPORTANT FORMATTING RULES:
1. ALWAYS start each new speaker's line with their name followed by a colon ("Character1:" or "Character2:").
2. ALWAYS put each speaker's line on a new line.
3. NEVER combine multiple speakers' lines into a single line.
4. ALWAYS use the exact names "Character1" and "Character2" (not variations or translations).
5. NEVER add any other text, headings, or explanations outside the conversation format.

Guidelines for content:
1. Create an engaging, fun podcast that explains the paper to beginners while also providing value to experts
2. Include examples and metaphors to help listeners understand difficult concepts
3. Have Character1 make some common beginner mistakes that Character2 corrects politely
4. Cover the paper's key findings, methodology, and implications
5. Keep the conversation natural, friendly and entertaining
6. Make sure the podcast has a clear beginning, middle, and conclusion

Paper text:
${paper_text}
"""
        template = PromptTemplate(name="default_podcast", template=template_str)
        return template

    def set_prompt_template(self, prompt_template: str) -> bool:
        """カスタムプロンプトテンプレートを設定します。

        Args:
            prompt_template (str): カスタムプロンプトテンプレート

        Returns:
            bool: テンプレートが正常に設定されたかどうか
        """
        if not prompt_template or prompt_template.strip() == "":
            self.custom_template = None
            return False

        try:
            template = PromptTemplate(
                name="custom_podcast", template=prompt_template.strip()
            )
            self.custom_template = template
            return True
        except Exception as e:
            logger.error(f"Error setting prompt template: {e}")
            return False

    def get_current_prompt_template(self) -> str:
        """現在のプロンプトテンプレートを取得します。

        Returns:
            str: 現在のプロンプトテンプレート（カスタムが設定されている場合はカスタム、そうでなければデフォルト）
        """
        current_template: PromptTemplate = self.custom_template or self.default_template
        template_str: str = current_template.template
        return template_str

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

        # Get current template (custom or default)
        current_template: PromptTemplate = self.custom_template or self.default_template

        try:
            # テンプレートに値を適用して最終的なプロンプトを生成
            prompt: str = current_template.to_string(paper_text=paper_text)
            return prompt
        except Exception as e:
            logger.error(f"Error rendering prompt: {e}")
            error_message: str = f"Error generating podcast conversation: {e}"
            return error_message
