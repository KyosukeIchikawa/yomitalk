# Yomitalk

論文PDFやテキストファイルからポッドキャスト風の解説音声を自動生成するアプリケーション

## 特徴

- 論文PDFやテキストファイルから内容を抽出
- OpenAI API または Google Gemini API を使用して会話形式の解説テキストを生成
- 様々なドキュメントタイプに対応（論文、マニュアル、議事録、ブログ記事、一般ドキュメント）
- 「概要解説」と「詳細解説」の2つのモードを搭載
- VOICEVOXを使用してキャラクター音声に変換（専門家役と初学者役に別々の声を割当可能）
- キャラクターの個性に合わせた話し方の再現（一人称や語尾の特徴など）
- 自然な間やフィラーの挿入による聞きやすい音声生成
- Gradioベースの使いやすいWebインターフェース

## サポートキャラクター

- ずんだもん
- 四国めたん
- 九州そら
- 中国うさぎ
- 中部つるぎ

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

2. 環境構築
   ```
   make setup
   ```

   下記が実行されます
   - 仮想環境の作成
   - 依存パッケージのインストール
   - VOICEVOX Coreのダウンロード
   - pre-commitの設定

## 使い方

1. アプリケーションを起動:
   ```
   python main.py
   ```

2. ブラウザで `http://localhost:7860` にアクセス

3. PDFファイルやテキストファイルをアップロードしてテキストを抽出

4. OpenAI API キー または Google Gemini API キーを設定

5. ドキュメントタイプを選択（論文、マニュアル、議事録など）

6. 解説モードを選択（「概要解説」または「詳細解説」）

7. キャラクターを選択（専門家役と初学者役）

8. 「トーク原稿を生成」ボタンをクリックして会話形式の解説テキストを生成
   - 使用するLLM（OpenAIまたはGemini）を切り替え可能
   - 各LLMのモデル種類やパラメータを調整可能

9. VOICEVOX利用規約に同意し、「音声を生成」ボタンをクリックして音声を生成

10. 生成された音声を再生またはダウンロード

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
