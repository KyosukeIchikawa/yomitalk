FROM python:3.11-slim

WORKDIR /app

# VOICEVOX規約に自動同意するための環境変数を設定
ENV VOICEVOX_ACCEPT_AGREEMENT=true
# 対話型プロンプトを無効化し、ページャーをcatに置き換える
ENV PAGER=cat
ENV LESSCHARSET=utf-8

# システム依存パッケージのインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends make sudo curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# リポジトリのコードをコピー
COPY . /app/

# 自動ダウンロードをCIモードで行う
RUN make download-voicevox-core-ci

# Python依存関係のインストール
RUN make install-python-packages

# パーミッション問題を解決するため、dataディレクトリの権限を設定
RUN mkdir -p /app/data/temp /app/data/output /app/data/logs \
    && chmod -R 777 /app/data

# ポート設定
ENV PORT=7860

# アプリ起動
CMD ["venv/bin/python", "app.py"]
