"""Module implementing common test steps shared across all scenarios."""
from playwright.sync_api import Page
from pytest_bdd import given

from tests.utils.logger import test_logger as logger


@given("the application is running")
def application_is_running(page: Page, app_environment):
    """
    フロントエンド側のテスト：ブラウザでアプリケーションにアクセスする

    Note: バックエンド側のアプリケーションは app_environment フィクスチャによって
          既に起動されています（tests/e2e/conftest.py で定義）

    Args:
        page: Playwright page object
        app_environment: バックエンドのフィクスチャ(TestEnvironmentインスタンス)
    """
    # アプリケーションが起動していることを確認
    assert (
        app_environment.app_port is not None
    ), "Application port is not set. Test environment might not be properly initialized."

    # ブラウザでアプリケーションにアクセス
    app_url = app_environment.app_url
    logger.info(f"Opening application in browser at {app_url}")
    page.goto(app_url)

    # ページの読み込み完了を待つ
    page.wait_for_load_state("networkidle")

    # 重要なUI要素が表示されるのを待つ
    page.wait_for_selector("h1, h2", timeout=5000)  # 見出し要素を待つ

    # ページが正しく読み込まれたことを検証
    title = page.title()
    assert title != "", "Application failed to load properly"
    logger.info(f"Successfully loaded application in browser with title: {title}")
