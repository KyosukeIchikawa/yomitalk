"""
Pytest configuration for e2e tests with Gherkin support
"""

import http.client
import os
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import URLError

import pytest
from playwright.sync_api import sync_playwright


def pytest_configure(config):
    """タグを登録する"""
    config.addinivalue_line("markers", "requires_voicevox: VOICEVOX Coreを必要とするテスト")
    # Add marker for slow tests
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


def pytest_collection_modifyitems(config, items):
    """VOICEVOXの有無に基づいてテストをスキップする"""
    voicevox_available = os.environ.get("VOICEVOX_AVAILABLE", "false").lower() == "true"
    if not voicevox_available:
        skip_voicevox = pytest.mark.skip(reason="VOICEVOX Coreがインストールされていないためスキップします")
        for item in items:
            if "requires_voicevox" in item.keywords:
                item.add_marker(skip_voicevox)


def get_free_port():
    """
    利用可能なポートを取得する
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


# サーバープロセス保持用のグローバル変数
_server_process = None
_server_port = None


@pytest.fixture(scope="session", autouse=True)
def setup_voicevox_core():
    """
    VOICEVOX Coreの状態を確認します。

    テスト前にVOICEVOX Coreがインストールされているか確認し、
    インストールされていない場合は手動インストール手順を表示します。
    """
    # プロジェクトルートに移動
    os.chdir(os.path.join(os.path.dirname(__file__), "../.."))

    # VOICEVOX Coreがインストール済みかチェック
    voicevox_path = Path("voicevox_core")

    # ライブラリファイルが存在するか確認
    dll_exists = list(voicevox_path.glob("*.dll"))
    so_exists = list(voicevox_path.glob("*.so"))
    dylib_exists = list(voicevox_path.glob("*.dylib"))

    if not voicevox_path.exists() or not (dll_exists or so_exists or dylib_exists):
        message = """
        -------------------------------------------------------
        VOICEVOX Coreがインストールされていません。
        オーディオ生成テストを実行するには、VOICEVOX Coreが必要です。

        以下のコマンドを手動で実行してインストールしてください：

        $ make download-voicevox-core

        このコマンドを実行すると、ライセンス条項が表示されます。
        内容を確認後、同意する場合は「y」を入力してインストールを続行してください。
        -------------------------------------------------------
        """
        print(message)

        # テストをスキップするのではなく、テストを実行可能にするため
        # VOICEVOXが必要なテストだけを明示的にスキップ
    else:
        print("VOICEVOX Coreはすでにインストールされています。")

    yield


@pytest.fixture(scope="session")
def browser():
    """
    Set up the browser for testing.

    Returns:
        Browser: Playwright browser instance
    """
    with sync_playwright() as playwright:
        # Use chromium browser (can also be firefox or webkit)
        browser = playwright.chromium.launch(
            headless=os.environ.get("CI") == "true",
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def server_port():
    """
    Get a port for the server to use.
    """
    global _server_port

    # If already set, return it
    if _server_port is not None:
        return _server_port

    # Get a free port
    _server_port = get_free_port()
    print(f"Using port {_server_port} for server")
    return _server_port


@pytest.fixture(scope="session")
def server_process(server_port):
    """
    Start the Gradio server for testing.

    Runs the server in the background during tests and stops it after completion.

    Yields:
        process: Running server process
    """
    global _server_process

    # If we already have a server process, reuse it
    if _server_process is not None:
        # Check if process is still running
        if _server_process.poll() is None:
            print(f"Reusing existing server on port {server_port}")
            yield _server_process
            return
        else:
            print(
                f"Previous server process exited with code {_server_process.returncode}"
            )
            _server_process = None

    print(f"Starting server on port {server_port}")

    # Change to the project root directory
    os.chdir(os.path.join(os.path.dirname(__file__), "../.."))

    # Check if VOICEVOX Core exists and set environment variables
    voicevox_path = Path("voicevox_core")

    # Check for library files (recursive search)
    has_so = len(list(voicevox_path.glob("**/*.so"))) > 0
    has_dll = len(list(voicevox_path.glob("**/*.dll"))) > 0
    has_dylib = len(list(voicevox_path.glob("**/*.dylib"))) > 0

    # VOICEVOXの有無を環境変数に設定（後でテストでこの情報を使用する）
    os.environ["VOICEVOX_AVAILABLE"] = str(has_so or has_dll or has_dylib).lower()

    if not (has_so or has_dll or has_dylib):
        print("VOICEVOX Coreがインストールされていません。音声生成テストのみスキップします。")
    else:
        print("VOICEVOX Coreライブラリが見つかりました。適切な環境変数を設定します。")

        # Set environment variables for VOICEVOX Core
        os.environ["VOICEVOX_CORE_PATH"] = str(
            os.path.abspath("voicevox_core/voicevox_core/c_api/lib/libvoicevox_core.so")
        )
        os.environ["VOICEVOX_CORE_LIB_PATH"] = str(
            os.path.abspath("voicevox_core/voicevox_core/c_api/lib")
        )
        os.environ[
            "LD_LIBRARY_PATH"
        ] = f"{os.path.abspath('voicevox_core/voicevox_core/c_api/lib')}:{os.environ.get('LD_LIBRARY_PATH', '')}"

    # Make sure we kill any existing server using the same port
    try:
        subprocess.run(["pkill", "-f", f"PORT={server_port}"], check=False)
        time.sleep(1)  # Give it time to die
    except Exception as e:
        print(f"Failed to kill existing process: {e}")

    # Use environment variable to pass test mode flag
    env = os.environ.copy()
    env["E2E_TEST_MODE"] = "true"  # Add test mode flag to speed up app initialization
    env["PORT"] = str(server_port)  # Set custom port for testing

    # Start the server process with appropriate environment
    print(f"Starting server on port {server_port}")
    _server_process = subprocess.Popen(
        [f"{os.environ.get('VENV_PATH', './venv')}/bin/python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,  # Pass current environment with VOICEVOX settings
    )

    print(f"Waiting for server to start on port {server_port}...")

    # Wait for the server to start and be ready
    max_retries = 60  # Increase max retries
    retry_interval = 1  # Longer interval between retries

    for i in range(max_retries):
        try:
            conn = http.client.HTTPConnection("localhost", server_port, timeout=1)
            conn.request("HEAD", "/")
            response = conn.getresponse()
            conn.close()
            if response.status < 400:
                print(f"Server is ready on port {server_port} after {i+1} attempts")
                break
        except (
            ConnectionRefusedError,
            http.client.HTTPException,
            URLError,
            socket.timeout,
        ):
            if i < max_retries - 1:
                time.sleep(retry_interval)

                # Check if process is still running
                if _server_process.poll() is not None:
                    stdout, stderr = _server_process.communicate()
                    print(
                        f"Server process exited with code {_server_process.returncode}"
                    )
                    print(f"Server stdout: {stdout.decode('utf-8', errors='ignore')}")
                    print(f"Server stderr: {stderr.decode('utf-8', errors='ignore')}")
                    pytest.fail("Server process died before becoming available")

                continue
            else:
                # Last attempt failed
                if _server_process.poll() is not None:
                    stdout, stderr = _server_process.communicate()
                    print(f"Server stdout: {stdout.decode('utf-8', errors='ignore')}")
                    print(f"Server stderr: {stderr.decode('utf-8', errors='ignore')}")
                pytest.fail(
                    f"Failed to connect to the server on port {server_port} after multiple attempts"
                )

    yield _server_process

    # Note: We don't terminate the server here, as we want to reuse it for all tests


@pytest.fixture(scope="function")
def page_with_server(browser, server_process, server_port):
    """
    Prepare a page for testing.

    Args:
        browser: Playwright browser instance
        server_process: Running server process

    Yields:
        Page: Playwright page object
    """
    # Open a new page
    context = browser.new_context(
        viewport={"width": 1280, "height": 1024}, ignore_https_errors=True
    )

    # Set timeouts at context level - reduced for faster failures
    context.set_default_timeout(3000)  # Reduced from 5000
    context.set_default_navigation_timeout(5000)  # Reduced from 10000

    # コンソールログをキャプチャする
    context.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))

    page = context.new_page()

    # Access the Gradio app with shorter timeout
    try:
        page.goto(
            f"http://localhost:{server_port}", timeout=5000
        )  # Use the dynamic port
    except Exception as e:
        print(f"Failed to navigate to server: {e}")
        # Try one more time
        time.sleep(2)
        page.goto(f"http://localhost:{server_port}", timeout=10000)

    # Wait for the page to fully load - with reduced timeout
    page.wait_for_load_state("networkidle", timeout=3000)  # Reduced from 5000

    # Always wait for the Gradio UI to be visible
    page.wait_for_selector("button", timeout=5000)

    yield page

    # Close the page after testing
    page.close()
    context.close()


# テスト終了時にサーバープロセスをクリーンアップするための関数
@pytest.fixture(scope="session", autouse=True)
def cleanup_server_process():
    """
    After all tests are done, ensure the server process is terminated.
    """
    # This will run after all tests are done
    yield

    global _server_process

    if _server_process is not None:
        print("Terminating server process...")
        try:
            # Try to terminate the process gracefully first
            _server_process.terminate()
            try:
                # Wait a bit for the process to terminate
                _server_process.wait(timeout=5)
                print("Server process terminated gracefully")
            except subprocess.TimeoutExpired:
                # If it doesn't terminate within the timeout, kill it
                print("Server process didn't terminate gracefully, killing it")
                _server_process.kill()
                _server_process.wait()
        except Exception as e:
            print(f"Error terminating server process: {e}")

        _server_process = None
        print("Server process cleanup complete")
