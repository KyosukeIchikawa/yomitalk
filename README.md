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

## 開発環境セットアップ

### Makefile を使ったセットアップ方法

```bash
# 環境構築
make setup

# 実行内容:
# - 仮想環境の作成
# - 依存パッケージのインストール
# - VOICEVOX Coreのダウンロード
# - pre-commitの設定
```

## 使い方

1. **アプリケーションを起動:**
   ```bash
   ./venv/bin/python app.py
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
