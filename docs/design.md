# Yomitalk 設計ドキュメント

## 設計概要
- 論文PDFやテキストを入力として受け取り、「ずんだもん」「四国めたん」などの日本人に馴染みのある声でポッドキャスト形式の解説音声を生成するGradioアプリを開発する
- ユーザーフレンドリーなインターフェースを持ち、簡単に論文やテキストをアップロードして音声生成ができるようにする
- OpenAI APIとGoogle Gemini APIの両方をサポートし、ユーザーが選択できるようにする
- 対話形式の解説を生成し、様々なドキュメントタイプ（論文、マニュアル、議事録など）に対応する

## 技術スタック
- **UI Framework**: Gradio 4.x with Soft theme integration
- **開発環境**: VS Code Dev Container (Docker-based)
- **PDF解析**: PyPDF2/pdfplumber - PDF解析と文書テキスト抽出
- **音声合成**: VOICEVOX Core - 日本語音声合成エンジン（ずんだもん、四国めたん、九州そら、中国うさぎ、中部つるぎなど）
- **LLM統合**:
  - OpenAI API (GPT-4o-mini, GPT-4など) - 論文テキストの要約・解説生成
  - Google Gemini API - 代替のAI文章生成エンジン
- **音声処理**: FFmpeg - 音声ファイルの結合処理
- **テスト**: pytest/pytest-bdd - テスト自動化とBDDによるE2Eテスト
- **E2Eテスト**: Playwright - ブラウザ自動化によるE2Eテスト
- **開発ツール**: Claude Code integration, pre-commit hooks, GitHub Copilot

## アーキテクチャ概要

### 開発環境アーキテクチャ
- **Dev Container**: Docker-based統一開発環境
  - VS Code完全統合（タスク、デバッグ、拡張機能）
  - 自動セットアップ（依存関係、VOICEVOX Core、pre-commit）
  - ボリューム永続化（データ、VOICEVOXモデル）
- **Claude Code統合**: AI支援開発環境
- **Legacy Support**: Makefile/venv setup（下位互換性維持）

### セッション管理システム
- **マルチユーザー対応**: 各ユーザーがGradioセッションハッシュに基づく独立したセッション状態を保持
- **状態の永続化**: ユーザー設定とセッション状態をJSONファイルとして自動保存・復元
- **セキュリティ配慮**: APIキーは保存せず、セッション復元時に再入力を要求
- **自動クリーンアップ**: 1日以上古いセッションディレクトリの自動削除
- **接続復旧**: ブラウザリフレッシュや切断後の状態完全復元

### 進捗表示システム
- **包括的進捗追跡**: リアルタイム進捗バー、経過時間、推定残り時間
- **ビジュアル表示**:
  - グラデーション進捗バー（Gradio Softテーマ統合）
  - パート別進捗（現在/総数、パーセンテージ）
  - 時間情報（経過時間、推定残り時間）
- **状態復元**: 接続断後の進捗状態復元
- **クリーンUI**: 余分な枠線除去、テーマ統合デザイン

### コンポーネント設計
- **UserSession**: セッション管理のコアクラス
  - 各ユーザーの独立したTextProcessorとAudioGeneratorインスタンスを管理
  - セッション状態のシリアライゼーション・デシリアライゼーション機能
  - 音声生成進捗の追跡と復元機能
  - 進捗状態の詳細管理（推定パーツ数、開始時間、ストリーミング状態）
- **グローバルリソース管理**: VOICEVOX Coreマネージャーは全ユーザー間で共有
- **ファイル分離**: ユーザーごとに独立したtempおよびoutputディレクトリ構造

### 音声生成パイプライン
- **ストリーミング生成**:
  - パーツ別音声生成とリアルタイムストリーミング再生
  - 進捗追跡とユーザーフィードバック
  - 最終音声の自動結合
- **フォールバック機構**: 結合失敗時の部分音声使用
- **エラーハンドリング**: 詳細なエラー表示とユーザーガイダンス

### 状態管理パターン
- **Gradio State**: `gr.State()`を使用したセッション状態の管理
- **自動保存**: 設定変更時の自動セッション保存
- **復元処理**: アプリケーション開始時の既存セッション検出と復元
- **エラーハンドリング**: セッション復元失敗時の新規セッション作成
- **音声生成状態**: 詳細な進捗状態管理（パーツ数、時間、ファイルパス）

## フォルダ構成
```
yomitalk/ - メインアプリケーションコード
├── common/ - 共通データモデルおよび定義
│   ├── api_type.py - API種別定義
│   └── character.py - キャラクター音声設定定義
├── components/ - コア機能コンポーネント
│   ├── audio_generator.py - 音声生成機能（ストリーミング対応）
│   ├── content_extractor.py - コンテンツ抽出機能
│   └── text_processor.py - テキスト処理機能
├── models/ - LLMモデル統合
│   ├── openai_model.py - OpenAI API統合
│   └── gemini_model.py - Google Gemini API統合
├── utils/ - ユーティリティ関数
│   ├── logger.py - ロギング設定
│   └── text_utils.py - テキスト処理ユーティリティ
├── templates/ - LLMプロンプトテンプレート
│   ├── common.j2 - 共通ポッドキャスト生成ユーティリティ
│   ├── standard.j2 - 論文解説用テンプレート
│   └── section_by_section.j2 - セクション別詳細解説用テンプレート
├── app.py - メインGradioアプリケーション（進捗表示統合）
├── prompt_manager.py - プロンプト管理および生成
└── user_session.py - ユーザーセッション管理と状態永続化

app.py - ルートレベルエントリーポイント

.devcontainer/ - Dev Container開発環境
├── Dockerfile.dev - 開発用Dockerコンテナ
├── devcontainer.json - VS Code Dev Container設定
├── docker-compose.yml - Docker Compose設定
└── setup.sh - 環境セットアップスクリプト

.vscode/ - VS Code統合
├── launch.json - デバッグ設定
├── settings.json - エディタ設定
└── tasks.json - タスク定義

.github/ - GitHub統合
├── copilot-instructions.md - GitHub Copilot設定
└── workflows/ - CI/CD設定

assets/ - 静的アセット
├── images/
│   └── logo.png - アプリケーションロゴ
└── favicon.ico - ファビコン

data/ - 実行時データ
├── temp/ - 一時データ
│   └── {session_id}/ - セッション別一時ディレクトリ
│       ├── session_state.json - セッション状態永続化
│       └── talks/ - 音声生成パーツ一時保存
├── output/ - 生成音声出力
│   └── {session_id}/ - セッション別出力ディレクトリ
└── logs/ - アプリケーションログ

tests/ - テストスイート
├── unit/ - ユニットテスト
│   ├── conftest.py - テスト設定
│   ├── test_app_audio_state.py - 音声状態管理テスト
│   ├── test_session_persistence.py - セッション永続化テスト
│   └── [...] - その他コンポーネントテスト
├── e2e/ - E2Eテスト
│   ├── features/ - BDD機能定義（Gherkin）
│   ├── steps/ - ステップ実装
│   └── conftest.py - E2Eテスト設定
├── data/ - テストデータ
└── utils/ - テストユーティリティ

docs/ - プロジェクトドキュメント
voicevox_core/ - VOICEVOX Coreライブラリ
scripts/ - 開発・運用スクリプト
```

## 機能要件

### 1. ファイル処理機能
- **マルチフォーマット対応**: PDF、テキストファイルのアップロードと抽出
- **堅牢な解析**: 複数PDF解析エンジン（PyPDF2, pdfplumber）による確実なテキスト抽出
- **URL抽出**: Webページからのコンテンツ抽出
- **自動区切り挿入**: ファイル名・URL情報付き区切り線の自動挿入

### 2. LLM統合とテキスト生成
- **デュアルLLM対応**: OpenAI API/Google Gemini APIの動的切り替え
- **モード選択**: 「概要解説」「詳細解説」の2つの生成モード
- **ドキュメントタイプ対応**: 論文、マニュアル、議事録、ブログ記事等
- **会話形式生成**: 専門家役と初学者役の自然な対話形式
- **トークン監視**: 使用量表示とコスト管理

### 3. 音声合成システム
- **キャラクターボイス**: VOICEVOX Core統合
  - ずんだもん、四国めたん、九州そら、中国うさぎ、中部つるぎ
- **ストリーミング生成**: パーツ別生成とリアルタイム再生
- **進捗表示**: 包括的進捗追跡
  - 視覚的進捗バー（グラデーション、アニメーション）
  - 時間情報（経過時間、推定残り時間）
  - パート別進捗（現在/総数、パーセンテージ）
- **自然な音声**: 適切な間、フィラー、キャラクター特性の再現

### 4. セッション管理
- **マルチユーザー対応**: セッション分離とリソース共有
- **状態永続化**: 設定・進捗状態の自動保存・復元
- **接続復旧**: ブラウザリフレッシュ後の完全状態復元
- **セキュリティ**: APIキー除外、機密情報保護
- **自動クリーンアップ**: 古いセッションの定期削除

### 5. 開発者体験
- **Dev Container**: 統一開発環境とゼロセットアップ
- **Claude Code統合**: AI支援開発
- **VS Code統合**: タスク、デバッグ、拡張機能の完全統合
- **自動テスト**: ユニット・E2E・BDDテストの自動実行
- **品質保証**: pre-commit、linting、型チェックの自動化

## 技術仕様

### 進捗表示システム
- **推定アルゴリズム**: 正規表現によるキャラクター対話行カウント
- **時間計算**: 現在ペースベースの残り時間推定
- **UI統合**: Gradio Softテーマとの完全統合
- **状態管理**: セッション状態での進捗情報永続化

### 音声生成パイプライン
- **ストリーミング**: `yield`ベースの非同期パーツ生成
- **ファイル管理**: セッション別ディレクトリでの分離管理
- **フォールバック**: 結合失敗時の部分音声使用
- **品質保証**: 音声ファイル存在確認と検証

### セッション状態スキーマ
```json
{
  "session_id": "string",
  "audio_generation_state": {
    "is_generating": "boolean",
    "status": "idle|generating|completed|failed",
    "progress": "float (0.0-1.0)",
    "start_time": "timestamp",
    "estimated_total_parts": "integer",
    "streaming_parts": ["array of file paths"],
    "final_audio_path": "string|null"
  },
  "user_settings": {
    "document_type": "enum",
    "podcast_mode": "enum",
    "character_mapping": "object",
    "llm_settings": "object"
  }
}
```

## コーディング規則

### 開発環境
- **推奨**: VS Code Dev Container開発
- **legacy**: Makefile/venv setup（下位互換性）
- **Claude Code**: AI支援開発の活用

### コード品質
- **PEP 8準拠**: black、isort、flake8による自動フォーマット
- **型安全**: mypy厳格型チェック、型ヒント必須
- **テスト駆動**: TDD実践、統合前テスト必須
- **トランクベース**: main branch直接開発、小さな変更単位
- **品質ゲート**: pre-commitフック、CI通過必須

### 国際化対応
- **コード**: 英語（コメント、ログ、エラーメッセージ）
- **UI**: 日本語（ユーザー向けメッセージ、ラベル）
- **ドキュメント**: 日本語（設計書、README）

### セキュリティ
- **機密情報**: APIキー等の永続化禁止
- **検証**: カスタムトークン、printステートメント検出
- **分離**: セッション別リソース分離

## テスト戦略

### テスト構成
- **BDD E2E**: pytest-bdd + Playwright（`.feature`ファイル）
- **ユニット**: 各コンポーネント個別検証
- **統合**: API連携、音声生成パイプライン
- **進捗表示**: 状態管理、UI更新、復元機能

### テストデータ
- **サンプルPDF**: 多様なフォーマット対応検証
- **モック**: LLM API、音声生成の効率的テスト
- **エラーシナリオ**: 接続断、ファイル破損、API制限

### CI/CD
- **自動実行**: GitHub Actions統合
- **品質ゲート**: 静的解析、全テスト通過
- **デプロイ**: Hugging Face Spaces手動デプロイ

## デプロイメント

### ローカル開発
```bash
# Dev Container (推奨)
code . # VS Code Dev Container自動起動

# Legacy setup
make setup && make run

# Direct execution
python app.py --port 7860 --host 0.0.0.0
```

### 依存関係管理
- **Python**: requirements.txt（pip-compile生成）
- **VOICEVOX**: 自動ダウンロード・セットアップ
- **ライセンス**: VOICEVOX利用規約同意必須

### 本番環境
- **コンテナ**: Docker/Dockerfile対応
- **クラウド**: Hugging Face Spaces統合
- **監視**: ログ、エラートラッキング
- **スケーリング**: セッション分離による水平スケール対応

## セキュリティとプライバシー

### データ保護
- **API キー**: メモリ内のみ、永続化禁止
- **ファイル**: セッション別分離、自動クリーンアップ
- **ログ**: 機密情報フィルタリング

### セッション分離
- **ユーザー分離**: 完全な状態・ファイル分離
- **リソース共有**: VOICEVOX Coreのみ安全な共有
- **クリーンアップ**: 定期的な古いセッション削除

## パフォーマンス

### 最適化戦略
- **VOICEVOX**: グローバルインスタンス共有
- **ストリーミング**: 順次生成・再生による体感速度向上
- **セッション**: 必要時のみ状態保存・読込
- **ファイル**: 効率的な一時ファイル管理

### 監視指標
- **音声生成**: パーツ別処理時間、全体処理時間
- **LLM**: API レスポンス時間、トークン使用量
- **セッション**: アクティブセッション数、復元成功率
