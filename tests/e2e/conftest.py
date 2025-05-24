"""E2Eテスト用のフィクスチャとユーティリティ。

テスト環境の初期化とページオブジェクトを提供します。
元々 tests/e2e/steps/conftest.py に分かれていた機能を統合しています。
"""
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import Browser, Page, sync_playwright

from tests.utils.logger import test_logger as logger

# Test data path
TEST_DATA_DIR = Path(__file__).parent.parent / "data"

# Application process
APP_PROCESS = None
APP_PORT = None


def find_free_port():
    """
    Find an available port

    Returns:
        int: Available port number
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def setup_test_environment():
    """
    バックエンド側のテスト環境をセットアップする

    Returns:
        int: テストポート番号
    """
    global APP_PROCESS, APP_PORT

    # Find an available port
    APP_PORT = find_free_port()

    # Set environment variables
    env = os.environ.copy()
    env["PORT"] = str(APP_PORT)
    env["E2E_TEST_MODE"] = "true"

    # プロジェクトのルートパスを取得
    project_root = Path(__file__).parent.parent.parent.absolute()

    # CI環境での仮想環境のPythonパスを設定
    venv_path = os.environ.get("VENV_PATH", "./venv")
    python_executable = os.path.join(venv_path, "bin", "python")

    # 仮想環境内のPythonが存在しない場合はデフォルトのPythonを使用
    if not os.path.exists(python_executable):
        python_executable = "python"
        logger.warning(
            f"Virtual environment Python not found at {python_executable}, using system Python"
        )
    else:
        logger.info(f"Using Python from virtual environment: {python_executable}")

    # Launch application as a subprocess
    # 仮想環境のPythonを使用してアプリケーションを起動
    APP_PROCESS = subprocess.Popen(
        [python_executable, "-m", "yomitalk.app"],
        env=env,
        cwd=str(project_root),  # プロジェクトルートディレクトリを設定
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # アプリケーション起動を待つために適切な時間を確保
    logger.info(f"Starting application on port {APP_PORT}...")
    time.sleep(3)  # 最初に少し長めに待機

    # Wait for application to start with improved retry logic
    max_retries = 20  # より多くのリトライを許容
    retry_interval = 1.5  # 短いインターバルで頻繁にチェック

    for i in range(max_retries):
        try:
            # タイムアウト設定を短く
            response = requests.get(f"http://localhost:{APP_PORT}", timeout=2)
            if response.status_code == 200:
                logger.info(f"✓ Application started successfully on port {APP_PORT}")
                # プロセスが稼働中かチェック
                if APP_PROCESS.poll() is None:
                    logger.info("Application is running normally")
                    return APP_PORT
                else:
                    raise Exception(
                        f"Application process terminated unexpectedly with code {APP_PROCESS.returncode}"
                    )
        except (requests.ConnectionError, requests.Timeout) as e:
            # エラーの種類を詳細に記録
            error_msg = str(e)
            if APP_PROCESS.poll() is not None:
                # プロセスが終了している場合
                stdout, stderr = APP_PROCESS.communicate()
                logger.error(
                    f"Application process exited with code {APP_PROCESS.returncode}"
                )
                logger.error(f"stdout: {stdout.decode('utf-8', errors='ignore')}")
                logger.error(f"stderr: {stderr.decode('utf-8', errors='ignore')}")
                raise Exception(
                    f"Application process exited prematurely with code {APP_PROCESS.returncode}"
                )

            logger.info(
                f"Waiting for application to start (attempt {i+1}/{max_retries}): {error_msg[:100]}..."
            )
            time.sleep(retry_interval)

    # 最終的に失敗した場合
    if APP_PROCESS.poll() is None:
        # プロセスがまだ実行中なら、ログを表示
        logger.error(
            "Application is still running but not responding to HTTP requests."
        )
    else:
        # プロセスが終了している場合
        stdout, stderr = APP_PROCESS.communicate()
        logger.error(f"Application process exited with code {APP_PROCESS.returncode}")
        logger.error(f"stdout: {stdout.decode('utf-8', errors='ignore')}")
        logger.error(f"stderr: {stderr.decode('utf-8', errors='ignore')}")

    raise Exception("Failed to start application after multiple retries")


def teardown_test_environment():
    """
    テスト環境を終了する
    """
    global APP_PROCESS, APP_PORT

    if APP_PROCESS:
        logger.info(f"Terminating application process on port {APP_PORT}...")

        try:
            # まず正常終了を試みる
            APP_PROCESS.terminate()
            try:
                # 終了を待つ（短めのタイムアウト）
                APP_PROCESS.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 強制終了
                logger.warning(
                    "Application did not terminate gracefully, killing process..."
                )
                APP_PROCESS.kill()
                APP_PROCESS.wait(timeout=2)
        except Exception as e:
            logger.error(f"Error during application process termination: {e}")

        # 状態確認
        if APP_PROCESS.poll() is None:
            logger.warning("WARNING: Application process could not be terminated")
        else:
            logger.info(
                f"Application process terminated with code {APP_PROCESS.returncode}"
            )

        # リソースをクリア
        APP_PROCESS = None
        APP_PORT = None


@pytest.fixture(scope="session", autouse=True)
def app_environment():
    """
    バックエンド側のテスト環境を提供するフィクスチャ

    セッション全体で一度だけアプリケーションを起動し、
    全テスト終了時に自動的に終了する
    """
    try:
        # バックエンド側のテスト環境のセットアップ
        port = setup_test_environment()
        logger.info(f"Application backend is running on port {port}")
        yield  # テスト実行を許可
    except Exception as e:
        # セットアップに失敗した場合の詳細エラー表示
        logger.error(f"ERROR setting up test environment: {e}")
        raise
    finally:
        # 必ず後片付けを実行
        teardown_test_environment()


@pytest.fixture(scope="function")
def page(browser: Browser) -> Page:
    """
    Provides a test page fixture

    This creates a new page for each test function but does not navigate to any URL.
    Navigation should be handled by the 'the application is running' step in the Background
    section of each feature file.

    Args:
        browser: Playwright browser instance

    Returns:
        Page: Configured page object
    """
    # Create page
    page = browser.new_page(viewport={"width": 1280, "height": 720})

    # Set timeout
    page.set_default_timeout(20000)  # 20 seconds

    yield page

    # Close page after test completion
    page.close()


@pytest.fixture(scope="session")
def browser():
    """
    ブラウザインスタンスを提供するフィクスチャ

    Returns:
        Browser: Playwrightブラウザインスタンス
    """
    with sync_playwright() as playwright:
        if os.environ.get("HEADLESS", "true").lower() == "true":
            browser = playwright.chromium.launch(headless=True)
        else:
            browser = playwright.chromium.launch(headless=False, slow_mo=100)

        yield browser

        # セッション終了時にブラウザを閉じる
        browser.close()


def pytest_bdd_apply_tag(tag, function):
    """
    タグに基づいてテストをスキップするためのフック

    Args:
        tag: BDDタグ
        function: テスト関数

    Returns:
        bool: スキップするかどうか
    """
    if tag == "skip":
        return pytest.mark.skip(reason="明示的にスキップされました")

    if tag == "slow" and os.environ.get("SKIP_SLOW_TESTS", "false").lower() == "true":
        return pytest.mark.skip(reason="遅いテストはスキップします")

    return None


def pytest_bdd_step_error(
    request, feature, scenario, step, step_func, step_func_args, exception
):
    """
    ステップが失敗した場合のフック

    Args:
        各種パラメータ
    """
    logger.error(f"Error in step: {step}")

    # Playwrightページオブジェクトが存在する場合、スクリーンショットを撮る
    page = step_func_args.get("page")
    if page and hasattr(page, "screenshot"):
        screenshot_dir = os.path.join("tests", "e2e", "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)

        scenario_name = scenario.name.replace(" ", "_")
        step_name = step.name.replace(" ", "_")
        timestamp = int(time.time())

        screenshot_path = os.path.join(
            screenshot_dir, f"error_{scenario_name}_{step_name}_{timestamp}.png"
        )

        page.screenshot(path=screenshot_path)
        logger.error(f"スクリーンショットが保存されました: {screenshot_path}")
