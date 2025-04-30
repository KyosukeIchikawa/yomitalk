"""
Common step definitions for paper podcast e2e tests
"""

import os
from pathlib import Path

import pytest
from playwright.sync_api import Page
from pytest_bdd import given

from tests.utils.logger import test_logger as logger

# Path to the test PDF
TEST_PDF_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../tests/data/sample_paper.pdf"
)

# データディレクトリ内にもサンプルPDFがあるか確認
DATA_PDF_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../data/sample_paper.pdf"
)
# テスト用PDFが存在するか確認
if not os.path.exists(TEST_PDF_PATH):
    # テストデータフォルダにPDFがない場合、データディレクトリのファイルを使用
    if os.path.exists(DATA_PDF_PATH):
        TEST_PDF_PATH = DATA_PDF_PATH
    else:
        # どちらにもない場合はエラーログ出力
        logger.warning(f"警告: サンプルPDFが見つかりません。パス: {TEST_PDF_PATH}")

# テスト用テキストファイルのパス
TEST_TEXT_PATH = os.path.join(
    os.path.dirname(__file__), "../../../../tests/data/sample_text.txt"
)

# テスト用テキストファイルが存在しない場合は作成する
if not os.path.exists(TEST_TEXT_PATH):
    try:
        # テスト用ディレクトリがない場合は作成
        os.makedirs(os.path.dirname(TEST_TEXT_PATH), exist_ok=True)

        # サンプルテキストファイルを作成
        with open(TEST_TEXT_PATH, "w", encoding="utf-8") as f:
            f.write(
                """# YomiTalk サンプルテキスト

このテキストファイルは、YomiTalkのテキストファイル読み込み機能をテストするためのサンプルです。

## 機能概要

YomiTalkは以下の機能を備えています:

1. PDFファイルからのテキスト抽出
2. テキストファイル（.txt, .md）からの読み込み
3. OpenAI APIを使用した会話形式テキスト生成
4. VOICEVOX Coreを使用した音声合成

このサンプルテキストが正常に読み込まれると、上記のテキストが抽出され、トークが生成されます。
その後、音声合成がされるとずんだもんと四国めたんの声でポッドキャスト音声が作成されます。

テストが正常に完了することを願っています！
"""
            )

        logger.info(f"サンプルテキストファイルを作成しました: {TEST_TEXT_PATH}")
    except Exception as e:
        logger.error(f"サンプルテキストファイルの作成に失敗しました: {e}")
        # 作成に失敗した場合はPDFファイルと同じパスを使用
        TEST_TEXT_PATH = TEST_PDF_PATH


# テスト用のヘルパー関数
def voicevox_core_exists():
    """VOICEVOXのライブラリファイルが存在するかを確認する"""
    from pathlib import Path

    project_root = Path(os.path.dirname(__file__)).parent.parent.parent.parent
    voicevox_dir = project_root / "voicevox_core"

    if not voicevox_dir.exists():
        return False

    # ライブラリファイルを探す
    has_so = len(list(voicevox_dir.glob("**/*.so"))) > 0
    has_dll = len(list(voicevox_dir.glob("**/*.dll"))) > 0
    has_dylib = len(list(voicevox_dir.glob("**/*.dylib"))) > 0

    return has_so or has_dll or has_dylib


# VOICEVOX Coreが利用可能かどうかを確認
# まずファイルシステム上でVOICEVOXの存在を確認
VOICEVOX_DEFAULT_AVAILABLE = voicevox_core_exists()
# 環境変数で上書き可能だが、指定がなければファイルの存在確認結果を使用
VOICEVOX_AVAILABLE = (
    os.environ.get("VOICEVOX_AVAILABLE", str(VOICEVOX_DEFAULT_AVAILABLE).lower())
    == "true"
)

# 環境変数がfalseでも、VOICEVOXの存在を報告
if VOICEVOX_AVAILABLE:
    logger.info("VOICEVOXのライブラリファイルが見つかりました。利用可能としてマーク。")
else:
    if VOICEVOX_DEFAULT_AVAILABLE:
        logger.info("VOICEVOXのライブラリファイルは存在しますが、環境変数でオフにされています。")
    else:
        logger.info("VOICEVOXディレクトリが見つからないか、ライブラリファイルがありません。")


# VOICEVOX利用可能時のみ実行するテストをマークするデコレータ
def require_voicevox(func):
    """VOICEVOXが必要なテストをスキップするデコレータ"""

    def wrapper(*args, **kwargs):
        if not VOICEVOX_AVAILABLE:
            message = f"""
        -------------------------------------------------------
        VOICEVOX Coreが必要なテストがスキップされました。

        VOICEVOXのステータス:
        - ファイル存在チェック: {"成功" if VOICEVOX_DEFAULT_AVAILABLE else "失敗"}
        - 環境変数設定: {os.environ.get("VOICEVOX_AVAILABLE", "未設定")}

        テストを有効にするには以下のコマンドを実行してください:
        $ VOICEVOX_AVAILABLE=true make test-e2e

        VOICEVOXがインストールされていない場合は:
        $ make download-voicevox-core
        -------------------------------------------------------
            """
            logger.warning(message)
            pytest.skip("VOICEVOX Coreが利用できないためスキップします")
        return func(*args, **kwargs)

    return wrapper


@given("the user has opened the application")
def user_opens_app(page_with_server: Page, server_port):
    """User has opened the application"""
    page = page_with_server
    # Wait for the page to fully load - reduced timeout
    page.wait_for_load_state("networkidle", timeout=2000)
    assert page.url.rstrip("/") == f"http://localhost:{server_port}"


@given("a sample PDF file is available")
def sample_pdf_file_exists():
    """Verify sample PDF file exists"""
    assert Path(TEST_PDF_PATH).exists(), "Test PDF file not found"
