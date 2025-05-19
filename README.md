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

- Python 3.11以上
- OpenAI API キー または Google Gemini API キー
- VOICEVOX Core (音声生成に必要)

## インストール方法

1. リポジトリをクローン:
   ```
   git clone https://github.com/yourusername/yomitalk.git
   cd yomitalk
   ```

2. 環境構築
   ```
   make setup
   ```

   下記等が実行されます
   - 仮想環境の作成
   - 依存パッケージのインストール
   - VOICEVOX Coreのダウンロード
   - pre-commitの設定

## 使い方

1. アプリケーションを起動:
   ```
   python app.py
   ```

2. ブラウザで `http://localhost:7860` にアクセス

3. ドキュメント（PDF、テキストファイルなど）をアップロードしてテキストを抽出

4. OpenAI API キー または Google Gemini API キーを設定

5. ドキュメントタイプを選択（論文、マニュアル、議事録など）

6. 解説モードを選択（「概要解説」または「詳細解説」）

7. OpenAI APIまたはGeminiのAPIトークンを入力（どちらのAPIを使うかはタブで切替可能）

8. 使用するLLMのモデルや出力最大トークン数を選択

9. 「トーク原稿を生成」ボタンをクリックして会話形式の解説テキストを生成

10. [VOICEVOX 音源利用規約](https://zunko.jp/con_ongen_kiyaku.html)を確認して問題なければ同意し、「音声を生成」ボタンをクリックして音声を生成（同意しない場合は使用不可）

11. 生成された音声を再生またはダウンロード

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
