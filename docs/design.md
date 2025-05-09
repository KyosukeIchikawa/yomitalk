# YomiTalk 設計ドキュメント

## 設計概要
- 論文PDFやテキストを入力として受け取り、「ずんだもん」などの日本人に馴染みのある声でポッドキャスト形式の解説音声を生成するGradioアプリを開発する
- ユーザーフレンドリーなインターフェースを持ち、簡単に論文やテキストをアップロードして音声生成ができるようにする
- OpenAI APIとGoogle Gemini APIの両方をサポートし、ユーザーが選択できるようにする

## 技術スタック
- Gradio: ウェブインターフェース構築
- PyPDF2/pdfplumber: PDF解析と文書テキスト抽出
- VOICEVOX Core: 日本語音声合成エンジン（ずんだもんなど日本語音声）
- OpenAI API (GPT-4o-mini): 論文テキストの要約・解説生成
- Google Gemini API: 代替のAI文章生成エンジン
- FFmpeg: 音声ファイルの結合処理
- pytest/pytest-bdd: テスト自動化とBDDによるE2Eテスト
- playwright: ブラウザ自動化によるE2Eテスト

## フォルダ構成
- app/ - メインアプリケーションコード
  - components/ - Gradioコンポーネント
    - audio_generator.py - 音声生成機能
    - file_uploader.py - ファイル処理機能
    - text_processor.py - テキスト処理機能
  - models/ - モデル関連コード
    - openai_model.py - OpenAI APIとの連携
    - gemini_model.py - Google Gemini APIとの連携
  - utils/ - ユーティリティ関数
  - app.py - Gradioアプリ構築
  - prompt_manager.py - プロンプト管理および生成
  - templates/ - テンプレートファイル
- assets/ - 静的アセット（画像、音声サンプルなど）
- data/ - 一時データ保存用
  - temp/ - アップロードされたファイルの一時保存
  - output/ - 生成された音声ファイル
- tests/ - テストコード
  - data/ - テスト用データ
  - unit/ - ユニットテスト
  - integration/ - 統合テスト
  - e2e/ - エンドツーエンドテスト
    - features/ - BDDシナリオ定義
    - steps/ - BDDステップ実装
- docs/ - ドキュメント
- voicevox_core/ - VOICEVOXコアライブラリとモデル

## 機能要件
1. ファイルアップロード機能
   - PDFファイルおよびテキストファイルのアップロードとテキスト抽出
   - 複数のPDF解析エンジン（PyPDF2, pdfplumber）を使用した堅牢なテキスト抽出
2. テキスト抽出・前処理
   - PDFやテキストファイルからのテキスト抽出とフォーマット処理
3. ポッドキャスト形式テキスト生成
   - OpenAI API/Google Gemini APIを使用した会話形式テキスト生成
   - 「論文の概要解説」と「論文の詳細解説」の2つのモード搭載
   - ホストとゲストの対話形式でわかりやすく内容を解説
4. 音声合成（ずんだもん等の声で生成）
   - VOICEVOX Coreによる日本語音声合成
   - 複数の音声キャラクター対応と役割設定
   - ホストとゲスト役それぞれに異なる声を割り当て可能
5. 生成された音声のダウンロード
   - 生成音声のダウンロード機能
6. マルチLLMサポート
   - OpenAI APIとGoogle Gemini APIの切り替え機能
   - 各APIのモデル選択とパラメータ調整機能

## コーディング規則
- PEP 8準拠のPythonコード
- 型ヒントの積極的な活用（mypy対応）
- 関数・クラスには適切なドキュメンテーション（docstring）を付ける
- 例外処理の適切な実装
- 長いテキスト処理のチャンク分割処理
- 音声ファイル生成時のFFmpeg活用
- ソースコード内のメッセージ・ログは全て英語で記述する
- ドキュメント（README.md, design.md等）は日本語のまま維持する

## テスト規則
- BDDフレームワーク（pytest-bdd）を使用したE2Eテスト
- ユニットテストによる各コンポーネントの検証
- モックを使用したAPIのテスト
- テスト用のサンプルPDFを用意した自動テスト
- CIパイプラインでのテスト自動実行

## デプロイメント
- ローカル開発環境での実行: `python main.py` または `python -m app.app`
- 必要なパッケージ: requirements.txtに記載
- VOICEVOX Core: `make download-voicevox-core` でセットアップ
- OpenAI API / Google Gemini API: APIキー設定が必要
