---
title: Yomitalk
emoji: 💬
colorFrom: purple
colorTo: blue
sdk: docker
python_version: 3.11
pinned: false
license: mit
short_description: ドキュメントからポッドキャスト風の解説音声を生成するアプリケーション
---

# <img src="assets/images/logo.png" width="300" alt="Yomitalk">

ドキュメントからポッドキャスト風の解説音声を生成するアプリケーション

## 特徴

- ドキュメント（PDF, テキストファイルなど）から内容を抽出
- OpenAI API または Google Gemini API を使用して会話形式の解説テキストを生成
  - 「概要解説」と「詳細解説」の2つのモードを搭載
- VOICEVOXを使用してキャラクター音声に変換

## サポートキャラクター

- ずんだもん
- 四国めたん
- 九州そら
- 中国うさぎ
- 中部つるぎ

## 必要条件

- [Docker](https://docs.docker.com/get-docker/)
- [VS Code](https://code.visualstudio.com/) (開発時)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) (開発時)
- OpenAI API キー または Google Gemini API キー

## 開発環境セットアップ（推奨）

### Dev Containers を使用（推奨）

1. **リポジトリをクローン:**
   ```bash
   git clone https://github.com/yourusername/yomitalk.git
   cd yomitalk
   ```

2. **VS Code で開く:**
   ```bash
   code .
   ```

3. **Dev Container で開く:**
   - `F1` を押して "Dev Containers: Reopen in Container" を選択
   - または通知ポップアップの "Reopen in Container" をクリック
   - 初回は環境構築に数分かかります

4. **開発開始:**
   - すべての依存関係が自動でインストールされます
   - VOICEVOX Core も自動でセットアップされます

### 従来の方法（Makefile/venv）

<details>
<summary>Makefile を使った従来のセットアップ方法</summary>

```bash
# 環境構築
make setup

# 実行内容:
# - 仮想環境の作成
# - 依存パッケージのインストール
# - VOICEVOX Coreのダウンロード
# - pre-commitの設定
```

</details>

## 使い方

1. **アプリケーションを起動:**
   ```bash
   python app.py
   ```

2. **ブラウザでアクセス:** `http://localhost:7860`

3. ドキュメント（PDF、テキストファイルなど）をアップロードしてテキストを抽出

4. OpenAI API キー または Google Gemini API キーを設定

5. ドキュメントタイプを選択（論文、マニュアル、議事録など）

6. 解説モードを選択（「概要解説」または「詳細解説」）

7. OpenAI APIまたはGeminiのAPIトークンを入力（どちらのAPIを使うかはタブで切替可能）

8. 使用するLLMのモデルや出力最大トークン数を選択

9. 「トーク原稿を生成」ボタンをクリックして会話形式の解説テキストを生成

10. [VOICEVOX 音源利用規約](https://zunko.jp/con_ongen_kiyaku.html)を確認して問題なければ同意し、「音声を生成」ボタンをクリックして音声を生成（同意しない場合は使用不可）

11. 生成された音声を再生またはダウンロード

## 開発者向け情報

### Dev Container での開発

Dev Container 環境では以下のコマンドとタスクが利用できます：

| タスク | コマンド | VS Code タスク |
|--------|----------|---------------|
| アプリ実行 | `python app.py` | "Run Yomitalk App" |
| 全テスト | `pytest tests/` | "Run All Tests" |
| 単体テスト | `pytest tests/unit/` | "Run Unit Tests" |
| E2Eテスト | `E2E_TEST_MODE=true pytest tests/e2e/` | "Run E2E Tests" |
| コード整形 | `black . && isort .` | "Format Code" |
| 静的解析 | `flake8 . && mypy .` | "Run Linting" |
| Pre-commit | `pre-commit run --all-files` | "Run Pre-commit" |

### ファイル構成

詳細な設計情報は [`docs/design.md`](docs/design.md) を参照してください。

### 開発ルール

- **コミット前チェック必須**: すべてのコミットは pre-commit フックを通過する必要があります
- **`--no-verify` 禁止**: pre-commit フックのバイパスは禁止されています
- **型チェック**: mypy による型チェックを通過する必要があります
- **テスト**: 新機能には適切なテストを追加してください

## APIキーの取得方法

### OpenAI APIキー
1. OpenAIのアカウントを作成: https://platform.openai.com/
2. APIキーを作成: https://platform.openai.com/api-keys

### Google Gemini APIキー
1. Google AIのアカウントを作成: https://ai.google.dev/
2. APIキーを作成: https://makersuite.google.com/app/apikey

## 免責事項

このアプリケーションはLLM（大規模言語モデル）を使用しています。
生成される内容の正確性、完全性、適切性について保証することはできません。
また、秘密文書のアップロードは推奨されません。
当アプリケーションの使用により生じた、いかなる損害についても責任を負いません。

## ライセンス情報

- このアプリケーション: MIT License
- VOICEVOX: [VOICEVOX CORE LICENSE](https://github.com/VOICEVOX/voicevox_core/blob/main/LICENSE)
