"""Module implementing common test steps shared across all scenarios."""
from playwright.sync_api import Page
from pytest_bdd import given

# conftest.pyから必要な関数やフィクスチャをインポート
from tests.utils.logger import test_logger as logger


@given("the application is running")
def application_is_running(page: Page, app_environment):
    """
    フロントエンド側のテスト：ブラウザでアプリケーションにアクセスする

    Note: バックエンド側のアプリケーションは app_environment フィクスチャによって
          既に起動されています（tests/e2e/conftest.py で定義）

    Args:
        page: Playwright page object
        app_environment: バックエンドのフィクスチャ
    """
    # conftest.pyから直接APP_PORTを取得（モジュールレベルの変数）
    from tests.e2e.conftest import APP_PORT

    # アプリケーションが起動していることを確認
    assert (
        APP_PORT is not None
    ), "Application port is not set. Test environment might not be properly initialized."

    # ブラウザでアプリケーションにアクセス
    logger.info(f"Opening application in browser at http://localhost:{APP_PORT}")
    app_url = f"http://localhost:{APP_PORT}"
    page.goto(app_url)

    # ページの読み込み完了を待つ
    page.wait_for_load_state("networkidle")

    # 重要なUI要素が表示されるのを待つ
    page.wait_for_selector("h1, h2", timeout=5000)  # 見出し要素を待つ

    # ページが正しく読み込まれたことを検証
    title = page.title()
    assert title != "", "Application failed to load properly"
    logger.info(f"Successfully loaded application in browser with title: {title}")
