# テストディレクトリ構成

このディレクトリには、プロジェクトのテストに関連するファイルが含まれています。

## ディレクトリ構成

- `unit/`: ユニットテスト
- `e2e/`: エンドツーエンドテスト
- `data/`: テスト用データ
- `test_templates/`: テスト用テンプレート
- `utils/`: テストユーティリティ

## テスト用テンプレート

`test_templates/prompts/` ディレクトリには、テスト専用のテンプレートファイルが含まれています。これらは実際のアプリケーションでは使用されず、テスト時のみ使用されます。

テンプレートファイル:
- `test_default.j2`: デフォルトテンプレートのテスト用
- `test_simple.j2`: シンプルテンプレートのテスト用
- `test_technical.j2`: 技術的テンプレートのテスト用

## テスト実行方法

テストを実行するには以下のコマンドを使用します:

```bash
# すべてのテストを実行
pytest

# 特定のテストファイルを実行
pytest tests/unit/test_prompt_manager.py

# テスト用テンプレートを使用したテストを実行
pytest tests/unit/test_prompt_manager_with_test_templates.py
```

## テンプレートテスト

テスト用テンプレートを使用したテストでは、`conftest.py`で定義された`test_templates_dir`フィクスチャを使用してテンプレートディレクトリを取得できます。例:

```python
def test_my_function(test_templates_dir):
    # テスト用テンプレートディレクトリを使用
    templates_path = os.path.join(test_templates_dir, "prompts")
    # テストコード...
```
