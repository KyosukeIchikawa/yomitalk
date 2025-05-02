# テンプレート管理

このドキュメントでは、テンプレート管理についての情報を提供します。

## テンプレートディレクトリ構成

テンプレートは以下のディレクトリに保存されています:

```
app/templates/prompts/  # アプリケーションのテンプレート
tests/test_templates/prompts/  # テスト用テンプレート
```

## テンプレートファイル

アプリケーションで使用される標準テンプレート:

- `default.j2`: デフォルトの会話テンプレート
- `simple.j2`: シンプルな会話テンプレート
- `technical.j2`: 技術的な会話テンプレート

テスト用テンプレート:

- `test_default.j2`
- `test_simple.j2`
- `test_technical.j2`

## テンプレートの使用方法

`PromptManager` クラスを使用してテンプレートを管理します:

```python
from app.prompt_manager import PromptManager

# プロンプトマネージャーの初期化
pm = PromptManager()

# 利用可能なテンプレート一覧の取得
templates = pm.get_available_template_names()
print(f"利用可能なテンプレート: {templates}")

# テンプレートの選択
pm.set_template_by_name("technical.j2")

# ポッドキャスト会話の生成
paper_text = "これは論文のテキストです..."
conversation = pm.generate_podcast_conversation(paper_text)
print(conversation)
```

## カスタムテンプレートの使用

カスタムテンプレート文字列を直接指定することもできます:

```python
custom_template = """
ずんだもん: こんにちは、今日は「{{ paper_text }}」について話します。
四国めたん: わかりました、詳しく説明しましょう。
"""

pm.set_prompt_template(custom_template)
conversation = pm.generate_podcast_conversation("論文タイトル")
```

## テスト用テンプレートディレクトリの指定

テスト時に別のテンプレートディレクトリを使用する場合は、コンストラクタで指定できます:

```python
# テスト用テンプレートディレクトリを指定
test_templates_dir = "path/to/test/templates"
pm = PromptManager(custom_templates_dir=test_templates_dir)
```

## 注意事項

- テンプレートファイルは `.j2` 拡張子を持つJinja2テンプレートである必要があります
- テンプレート内では `{{ paper_text }}` 変数を使用して論文テキストを参照できます
- キャラクター名のマッピングは `PromptManager.set_character_mapping()` メソッドで変更できます
