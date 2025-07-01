"""Module implementing common test steps shared across all scenarios."""

from playwright.sync_api import Page, expect
from pytest_bdd import given, then

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
    assert app_environment.app_port is not None, "Application port is not set. Test environment might not be properly initialized."

    # ブラウザでアプリケーションにアクセス
    app_url = app_environment.app_url
    logger.info(f"Opening application in browser at {app_url}")
    page.goto(app_url, timeout=30000)  # Increase timeout to 30 seconds

    # ページの基本的な読み込み完了を待つ
    page.wait_for_load_state("domcontentloaded")

    # 重要なUI要素が表示されるのを待つ - より具体的なセレクターを使用
    try:
        # Gradioアプリの主要コンテナが表示されるのを待つ
        page.wait_for_selector(".gradio-container, #root, main", timeout=5000)
        logger.debug("Gradio container found")

        # アプリケーション固有の要素が表示されるのを待つ
        page.wait_for_selector("h1, h2, .gr-button", timeout=5000)
        logger.debug("Main UI elements found")

        # アプリケーションが完全にロードされたことを確認
        # Gradioアプリでよく使用される要素の存在確認
        page.wait_for_function(
            "() => document.readyState === 'complete' && (document.querySelector('h1') || document.querySelector('h2') || document.querySelector('.gr-button'))",
            timeout=8000,
        )
        logger.debug("Application fully loaded")

    except Exception as e:
        logger.warning(f"UI element wait failed, continuing with basic checks: {e}")
        # フォールバック: 基本的な読み込み完了のみ確認
        page.wait_for_load_state("load")

    # ページが正しく読み込まれたことを検証
    title = page.title()
    assert title != "", "Application failed to load properly"
    logger.info(f"Successfully loaded application in browser with title: {title}")


@given("I wait for the interface to be ready")
def wait_for_interface_ready(page: Page):
    """
    Wait for the UI interface to be fully initialized and interactive.
    This step waits for the app initialization to complete and UI components to become enabled.
    """
    logger.info("Waiting for interface to be ready")

    # Wait for the main UI components to be available and interactive
    try:
        # Wait for key input elements to be enabled (not in loading state)
        page.wait_for_function(
            """() => {
                // Check if URL input is available and interactive
                const urlInput = document.querySelector('input[placeholder*="https://"]');
                const hasUrlInput = urlInput && !urlInput.disabled;

                // Check if any non-disabled buttons exist
                const buttons = document.querySelectorAll('button:not([disabled])');
                const hasEnabledButtons = buttons.length > 0;

                // Check if text areas are available
                const textAreas = document.querySelectorAll('textarea:not([disabled])');
                const hasTextAreas = textAreas.length > 0;

                return hasUrlInput && hasEnabledButtons && hasTextAreas;
            }""",
            timeout=15000,
        )
        logger.info("Interface is ready - UI components are initialized and interactive")

    except Exception as e:
        logger.warning(f"Interface readiness check failed, proceeding anyway: {e}")
        # Fallback: just wait a bit for the interface to stabilize
        page.wait_for_timeout(2000)


@given("the user has accessed the application page")
def user_has_accessed_application_page(page: Page, app_environment):
    """The user has accessed the application page."""
    # Ensure the application is running
    application_is_running(page, app_environment)

    # Verify main UI elements are visible
    logger.info("Verifying main UI elements are visible")

    # Verify the script generation section is displayed
    heading = page.locator('text="トーク原稿の生成"')
    expect(heading).to_be_visible(timeout=10000)

    # Verify tabs are present
    file_upload_tab = page.get_by_role("tab", name="ファイルアップロード")
    expect(file_upload_tab).to_be_visible()

    web_extraction_tab = page.get_by_role("tab", name="Webページ抽出")
    expect(web_extraction_tab).to_be_visible()

    # Verify file input element is available (may be hidden initially due to tabs)
    file_input = page.locator('input[type="file"]')
    expect(file_input).to_be_attached()

    # Verify extracted text area is visible
    extracted_text_area = page.locator("textarea").nth(1)
    expect(extracted_text_area).to_be_visible()

    logger.info("All main UI elements are visible and accessible")


@given("I have accessed the application page")
def access_application_page(page: Page, app_environment):
    """
    Access the application page - same as the common step

    Args:
        page: Playwright page object
        app_environment: Test environment fixture
    """
    user_has_accessed_application_page(page, app_environment)


@then('the "トーク原稿を生成" button is enabled')
def process_button_is_enabled(page: Page):
    """The script generation button is enabled."""
    logger.info("Checking if process button becomes enabled")

    # Set API key if not already set
    try:
        # Look for OpenAI API key input field
        api_input = page.locator('input[placeholder="sk-..."]')
        logger.info(f"API input field visible: {api_input.is_visible()}")

        if api_input.is_visible():
            logger.info("Setting dummy API key for testing")
            api_input.fill("sk-dummy-key-for-testing")
            # Wait a bit before checking button state
            page.wait_for_timeout(500)
        else:
            # Also check Gemini API key field
            gemini_input = page.locator('input[placeholder="AIza..."]')
            logger.info(f"Gemini input field visible: {gemini_input.is_visible()}")

            if gemini_input.is_visible():
                logger.info("Setting dummy Gemini API key for testing")
                gemini_input.fill("AIza-dummy-key-for-testing")
                page.wait_for_timeout(500)
            else:
                logger.warning("No API key input fields found")
    except Exception as e:
        logger.warning(f"Could not set API key: {e}")

    process_button = page.locator('button:has-text("トーク原稿を生成")')
    expect(process_button).to_be_visible()

    # Check current button state
    is_enabled = process_button.is_enabled()
    logger.info(f"Process button current state: enabled={is_enabled}")

    # Wait for button to become enabled (max 10 seconds)
    expect(process_button).to_be_enabled(timeout=10000)

    logger.info("Process button is now enabled")


@then('the "トーク原稿を生成" button remains disabled')
def process_button_remains_disabled(page: Page):
    """The script generation button remains disabled."""
    logger.info("Checking if process button remains disabled")

    process_button = page.locator('button:has-text("トーク原稿を生成")')
    expect(process_button).to_be_visible()

    # Verify button remains disabled
    expect(process_button).to_be_disabled()

    logger.info("Process button remains disabled")
