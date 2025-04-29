# YomiTalk

テキストをアップロードして、日本語での解説音声を自動生成するGradioアプリケーションです。

## 機能

### モード

- 論文からポッドキャスト形式での解説音声を自動生成

### 対応ファイル形式

- PDF

### 音声キャラクター

- ずんだもん
- 四国めたん

## 必要条件

- Python 3.10以上
- FFmpeg
- OpenAI APIキー（テキスト生成に必要）

## インストール

1. リポジトリをクローンします：

```bash
git clone https://github.com/KyosukeIchikawa/yomitalk.git
cd yomitalk
```

2. 環境セットアップを一括で行います：

```bash
make setup
```

このコマンドは以下の処理を自動的に実行します：
- Python仮想環境の作成
- 必要パッケージのインストール
- VOICEVOXコアのダウンロードとセットアップ
- pre-commitフックの設定

## 使用方法

1. アプリケーションを起動します：

```bash
python main.py
```

2. ブラウザで表示されるGradioインターフェースにアクセスします（通常は http://127.0.0.1:7860）

3. 使用手順：
   - 論文PDFをアップロードします
   - 「Extract Text」ボタンをクリックしてテキストを抽出します
   - OpenAI API設定セクションでAPIキーを設定します
   - 「Generate Podcast Text」ボタンをクリックして会話形式のテキストを生成します
   - 音声キャラクターを選択し、「Generate Audio」ボタンをクリックして音声を生成します
   - 生成された音声はダウンロード可能です

## テスト

次のコマンドでテストを実行できます：

```bash
make test

# unit testのみ
make test-unit

# e2e testのみ
make test-e2e
```

## 開発

- pre-commitフックが自動的にlintチェックを実行します

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 謝辞

- [VOICEVOX](https://voicevox.hiroshiba.jp/) - 日本語音声合成エンジン
- [Gradio](https://gradio.app/) - インタラクティブなUIフレームワーク
- [OpenAI](https://openai.com/) - 自然言語処理API
