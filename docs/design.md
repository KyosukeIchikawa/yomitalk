# Yomitalk 設計ドキュメント

## 設計概要
- 論文PDFやテキストを入力として受け取り、「ずんだもん」「四国めたん」などの日本人に馴染みのある声でポッドキャスト形式の解説音声を生成するGradioアプリを開発する
- ユーザーフレンドリーなインターフェースを持ち、簡単に論文やテキストをアップロードして音声生成ができるようにする
- OpenAI APIとGoogle Gemini APIの両方をサポートし、ユーザーが選択できるようにする
- 対話形式の解説を生成し、様々なドキュメントタイプ（論文、マニュアル、議事録など）に対応する

## 技術スタック
- Gradio: ウェブインターフェース構築
- PyPDF2/pdfplumber: PDF解析と文書テキスト抽出
- VOICEVOX Core: 日本語音声合成エンジン（ずんだもん、四国めたん、九州そら、中国うさぎ、中部つるぎなど）
- OpenAI API (GPT-4o-mini, GPT-4など): 論文テキストの要約・解説生成
- Google Gemini API: 代替のAI文章生成エンジン
- FFmpeg: 音声ファイルの結合処理
- pytest/pytest-bdd: テスト自動化とBDDによるE2Eテスト
- playwright: ブラウザ自動化によるE2Eテスト

## フォルダ構成
- yomitalk/ - メインアプリケーションコード
  - common/ - 共通データモデルおよび定義
    - character.py - キャラクター音声設定定義
  - components/ - Gradioコンポーネント
    - audio_generator.py - 音声生成機能
    - content_extractor.py - コンテンツ抽出機能
    - text_processor.py - テキスト処理機能
  - models/ - モデル関連コード
    - openai_model.py - OpenAI APIとの連携
    - gemini_model.py - Google Gemini APIとの連携
  - utils/ - ユーティリティ関数
  - app.py - Gradioアプリ構築
  - prompt_manager.py - プロンプト管理および生成
  - templates/ - テンプレートファイル
    - common_podcast_utils.j2 - 共通のポッドキャスト生成ユーティリティ
    - paper_to_podcast.j2 - 論文解説用テンプレート
    - section_by_section.j2 - セクションごとの詳細解説用テンプレート
- app/ - 追加のアプリケーション機能
  - utils/ - 追加のユーティリティ機能
- app.py - ルートレベルのエントリーポイント
- assets/ - 静的アセット
  - images/ - 画像ファイル
    - logo.png - アプリケーションロゴ
  - favicon.ico - ファビコン
- data/ - 一時データ保存用
  - temp/ - アップロードされたファイルの一時保存
  - output/ - 生成された音声ファイル
  - logs/ - ログファイル保存用
- tests/ - テストコード
  - data/ - テスト用データ
  - unit/ - ユニットテスト
  - e2e/ - エンドツーエンドテスト
  - utils/ - テスト用ユーティリティ
- docs/ - ドキュメント
  - design.md - 設計ドキュメント
- voicevox_core/ - VOICEVOXコアライブラリとモデル
- scripts/ - 開発用スクリプト

## 機能要件
1. ファイルアップロード機能
   - PDFファイルおよびテキストファイルのアップロードとテキスト抽出
   - 複数のPDF解析エンジン（PyPDF2, pdfplumber）を使用した堅牢なテキスト抽出
2. テキスト抽出・前処理
   - PDFやテキストファイルからのテキスト抽出とフォーマット処理
3. ポッドキャスト形式テキスト生成
   - OpenAI API/Google Gemini APIを使用した会話形式テキスト生成
   - 「概要解説」と「詳細解説」の2つのモード搭載
   - 専門家役と初学者役の対話形式でわかりやすく内容を解説
4. ドキュメントタイプ対応
   - 論文、マニュアル、議事録、ブログ記事、一般ドキュメントなど様々なタイプに対応
   - ドキュメントタイプに応じた適切な解説スタイルの調整
5. 音声合成（キャラクターボイスで生成）
   - VOICEVOX Coreによる日本語音声合成
   - ずんだもん、四国めたん、九州そら、中国うさぎ、中部つるぎなどの複数キャラクター対応
   - 専門家役と初学者役それぞれに異なる声を割り当て可能
6. 自然な会話と音声表現
   - 文の途中に適切な間を入れる機能
   - 自然なフィラーやリアクションの挿入
   - キャラクター特有の話し方パターンの再現（一人称や語尾の特徴など）
7. 生成された音声のダウンロード
   - 生成音声のダウンロード機能
8. マルチLLMサポート
   - OpenAI APIとGoogle Gemini APIの切り替え機能
   - 各APIのモデル選択とパラメータ調整機能
   - トークン使用状況の表示機能

## コーディング規則
- PEP 8準拠のPythonコード
  - black、isort、flake8による自動フォーマットとリンティング
  - pre-commitフックによる自動検証
- 型ヒントの積極的な活用（mypy対応）
  - 新規ファイルでは厳格な型チェックを適用
  - 既存コードにも段階的に型アノテーションを追加
- テスト駆動開発（TDD）の実践
  - トランクベース開発（main branchへの直接コミット）
  - 小さな変更単位での開発と統合
- 関数・クラスには適切なドキュメンテーション（docstring）を付ける
- コードレビューとCI通過を統合の条件とする
- 例外処理の適切な実装
- 長いテキスト処理のチャンク分割処理
- 音声ファイル生成時のFFmpeg活用
- ソースコード内のメッセージ・ログは全て英語で記述する
- ドキュメント（README.md, design.md等）は日本語のまま維持する
- カスタムトークンやprintステートメントの検出と警告

## テスト規則
- BDDフレームワーク（pytest-bdd）を使用したE2Eテスト
  - テストシナリオは `tests/e2e/features/` ディレクトリに `.feature` ファイルとして記述
  - ステップ実装は `tests/e2e/features/steps/` ディレクトリに配置
- Playwrightによるブラウザテスト
- ユニットテストによる各コンポーネントの個別検証
  - テストファイルは `tests/unit/` ディレクトリに配置
  - 各クラス・モジュールごとに独立したテストファイルを作成
- モックを使用したAPIのテスト（OpenAI API、Gemini API）
- テスト用のサンプルPDFおよびテキストデータを用意した自動テスト
- GitHubワークフローによるCI自動実行
  - 静的解析（pre-commit）
  - E2Eテストの自動実行
  - 自動デプロイ（Hugging Faceへ）

## デプロイメント
- ローカル開発環境での実行: `python app.py` または `python -m yomitalk.app`
- セットアップ: `make setup` コマンドで環境構築
- 必要なパッケージ: requirements.txtに記載（requirements.inから生成）
- VOICEVOX Core: `make download-voicevox-core` でセットアップ
  - VOICEVOXのライセンス規約に同意する必要あり
- OpenAI API / Google Gemini API: APIキー設定が必要
- Docker: `Dockerfile` を使用してコンテナ化可能
- CI/CD: GitHub Actions による自動テスト・デプロイ
  - Hugging Face Spaces へ自動デプロイ
