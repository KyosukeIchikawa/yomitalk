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
# シェルのセットオプション -e を使用して、コマンドが失敗したら即座にDockerビルドを失敗させる
RUN set -e && \
    scripts/download_voicevox.sh \
        --version 0.16.0 \
        --dir voicevox_core \
        --skip-if-exists \
        --accept-agreement

# Python依存関係のインストール（Docker内では仮想環境を使わない）
RUN pip install --upgrade pip

# 大きなパッケージを段階的にインストール
# PyTorch関連のパッケージを先にインストール
RUN pip install --timeout 600 --retries 5 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 残りの依存関係をインストール
RUN pip install --timeout 300 --retries 3 -r requirements.txt

# VOICEVOX Core Python module installation
RUN OS_TYPE="manylinux_2_34_x86_64" && \
    WHEEL_URL="https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.0/voicevox_core-0.16.0-cp310-abi3-${OS_TYPE}.whl" && \
    pip install ${WHEEL_URL}

# パーミッション問題を解決するため、dataディレクトリの権限を設定
RUN mkdir -p /app/data/temp /app/data/output && chmod -R 777 /app/data

# ポート設定
ENV PORT=7860

# アプリ起動
CMD ["python", "app.py"]
