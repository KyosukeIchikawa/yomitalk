# Yomitalk

論文PDFやテキストファイルからポッドキャスト風の解説音声を自動生成するアプリケーション

## 特徴

- 論文PDFやテキストファイルから内容を抽出
- OpenAI API または Google Gemini API を使用して会話形式の解説テキストを生成
- 「論文の概要解説」と「論文の詳細解説」の2つのモードを搭載
- VOICEVOXを使用してキャラクター音声に変換（ホスト役とゲスト役に別々の声を割当可能）
- Gradioベースの使いやすいWebインターフェース

## 必要条件

- Python 3.8以上
- OpenAI API キー または Google Gemini API キー
- VOICEVOX Core (音声生成に必要)

## インストール方法

1. リポジトリをクローン:
   ```
   git clone https://github.com/yourusername/yomitalk.git
   cd yomitalk
   ```

2. 依存パッケージのインストール:
   ```
   pip install -r requirements.txt
   ```

3. VOICEVOX Coreのインストール:
   ```
   make download-voicevox-core
   ```

## 使い方

1. アプリケーションを起動:
   ```
   python main.py
   ```

2. ブラウザで `http://localhost:7860` にアクセス

3. PDFファイルやテキストファイルをアップロードしてテキストを抽出

4. OpenAI API キー または Google Gemini API キーを設定

5. 「トーク原稿を生成」ボタンをクリックして会話形式の解説テキストを生成
   - 「論文の概要解説」または「論文の詳細解説」モードを選択可能
   - 使用するLLM（OpenAIまたはGemini）を切り替え可能
   - 各LLMのモデル種類やパラメータを調整可能

6. VOICEVOX利用規約に同意し、「音声を生成」ボタンをクリックして音声を生成

7. 生成された音声をダウンロード

## APIキーの取得方法

### OpenAI APIキー
1. OpenAIのアカウントを作成: https://platform.openai.com/
2. APIキーを作成: https://platform.openai.com/api-keys

### Google Gemini APIキー
1. Google AIのアカウントを作成: https://ai.google.dev/
2. APIキーを作成: https://makersuite.google.com/app/apikey

## ライセンス情報

- このアプリケーション: MIT License
- VOICEVOX: [VOICEVOX CORE LICENSE](https://github.com/VOICEVOX/voicevox_core/blob/main/LICENSE)

音声を生成する際には、[VOICEVOX 音源利用規約](https://zunko.jp/con_ongen_kiyaku.html)への同意が必要です。
