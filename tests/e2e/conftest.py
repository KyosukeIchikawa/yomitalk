"""E2Eテスト用のフィクスチャとユーティリティ。

テスト環境の初期化とページオブジェクトを提供します。
元々 tests/e2e/steps/conftest.py に分かれていた機能を統合しています。
"""

import os
import time
from pathlib import Path
from typing import Generator

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from tests.utils.logger import test_logger as logger
from tests.utils.test_environment import TestEnvironment
from yomitalk.components.audio_generator import initialize_global_voicevox_manager

# Test data path
TEST_DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture(scope="session", autouse=True)
def initialize_voicevox():
    """Initialize global VOICEVOX manager for all tests."""
    try:
        manager = initialize_global_voicevox_manager()
        if manager:
            logger.info("Global VOICEVOX manager initialized successfully for tests")
        else:
            logger.warning("VOICEVOX manager initialization returned None")
    except Exception as e:
        logger.warning(f"VOICEVOX initialization failed in tests: {e}")
    yield
    # No cleanup needed as this is a global singleton


@pytest.fixture(scope="session", autouse=True)
def app_environment() -> Generator[TestEnvironment, None, None]:
    """
    バックエンド側のテスト環境を提供するフィクスチャ

    セッション全体で一度だけアプリケーションを起動し、
    全テスト終了時に自動的に終了する
    """
    test_env = TestEnvironment()
    try:
        # バックエンド側のテスト環境のセットアップ
        app_url = test_env.setup()
        logger.info(f"Application backend is running at {app_url}")
        yield test_env  # テスト実行を許可、TestEnvironmentインスタンスを返す
    except Exception as e:
        # セットアップに失敗した場合の詳細エラー表示
        logger.error(f"ERROR setting up test environment: {e}")
        raise
    finally:
        # 必ず後片付けを実行
        test_env.teardown()


@pytest.fixture(scope="function")
def page(browser: Browser) -> Generator[Page, None, None]:
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
