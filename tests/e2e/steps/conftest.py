"""E2E test common environment settings module.

Provides setup for test environment and common steps.
"""
import os
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests
from playwright.sync_api import Page
from pytest_bdd import given

from tests.utils.logger import test_logger as logger

# Test data path
TEST_DATA_DIR = Path(__file__).parent.parent.parent / "data"

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
    Set up the test environment

    Returns:
        int: Test port number
    """
    global APP_PROCESS, APP_PORT

    # Find an available port
    APP_PORT = find_free_port()

    # Set environment variables
    env = os.environ.copy()
    env["PORT"] = str(APP_PORT)
    env["E2E_TEST_MODE"] = "true"

    # プロジェクトのルートパスを取得
    project_root = Path(__file__).parent.parent.parent.parent.absolute()

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
                # プロセス出力を非ブロッキングでチェック (communicate()は使わない)
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
    テスト環境を提供するフィクスチャ
    """
    try:
        # テスト環境のセットアップを試行
        setup_test_environment()
        yield  # テスト実行を許可
    except Exception as e:
        # セットアップに失敗した場合の詳細エラー表示
        logger.error(f"ERROR setting up test environment: {e}")
        raise
    finally:
        # 必ず後片付けを実行
        teardown_test_environment()


@given("the application is running")
def app_is_running(page: Page):
    """
    Verify that the application is running and navigate to the application page

    This step also navigates to the application page, making it a common entry point
    for all test scenarios.

    Args:
        page: Playwright page object
    """
    assert APP_PROCESS is not None, "Application is not running"

    # Application health check
    if APP_PROCESS.poll() is not None:
        stdout, stderr = APP_PROCESS.communicate()
        pytest.fail(
            f"Application process exited with code {APP_PROCESS.returncode}\n"
            f"stdout: {stdout.decode('utf-8', errors='ignore')}\n"
            f"stderr: {stderr.decode('utf-8', errors='ignore')}"
        )

    # Navigate to the application page with retry logic
    max_retries = 3
    last_exception = None

    for i in range(max_retries):
        try:
            # Navigate with timeout
            page.goto(f"http://localhost:{APP_PORT}", timeout=20000)

            # Wait for critical elements to load
            page.wait_for_selector("h1, h2", timeout=5000)  # Wait for headings

            # Verify the page loaded successfully
            title = page.title()
            assert title != "", "Failed to load the application page - empty title"
            logger.info(f"Successfully loaded application with title: {title}")
            return  # Success - return early
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Retry {i+1}/{max_retries}: Failed to connect to the application: {e}"
            )
            time.sleep(2)  # Wait before retrying

    # All retries failed
    pytest.fail(
        f"Failed to connect to the application after {max_retries} attempts: {last_exception}"
    )
