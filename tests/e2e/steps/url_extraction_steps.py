"""URL抽出機能のステップ定義。"""

import time

from playwright.sync_api import Page, expect
from pytest_bdd import then, when

from tests.utils.logger import test_logger as logger


@when('the user enters "<url>" into the URL input field')
def user_enters_url(page: Page, url: str):
    """The user enters a URL into the URL input field."""
    logger.info(f"Entering URL: {url}")

    # URL入力フィールドを見つけて入力
    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_visible()
    url_input.fill(url)

    logger.info(f"URL entered successfully: {url}")


@when("the user enters a GitHub README URL into the URL input field")
def user_enters_github_readme_url(page: Page):
    """The user enters a GitHub README URL into the URL input field."""
    github_readme_url = (
        "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"
    )
    logger.info(f"Entering GitHub README URL: {github_readme_url}")

    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_visible()
    url_input.fill(github_readme_url)

    logger.info(f"GitHub README URL entered successfully: {github_readme_url}")


@when("the user leaves the URL input field empty")
def user_leaves_url_field_empty(page: Page):
    """The user leaves the URL input field empty."""
    logger.info("Leaving URL field empty")

    # URL入力フィールドが存在することを確認（何も入力しない）
    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_visible()

    logger.info("URL field left empty")


@when('the user clicks the "URLからテキストを抽出" button')
def user_clicks_url_extract_button(page: Page):
    """The user clicks the URL text extraction button."""
    logger.info("Clicking URL extract button")

    # URL抽出ボタンを見つけてクリック
    extract_button = page.locator('button:has-text("URLからテキストを抽出")')
    expect(extract_button).to_be_visible()
    extract_button.click()

    # 抽出処理の完了を待つ（より長い時間待機）
    time.sleep(5)

    logger.info("URL extract button clicked successfully")


@then("the extracted text area shows content")
def text_area_shows_content(page: Page):
    """The extracted text area shows content."""
    logger.info("Checking if extracted text area shows content")

    # 抽出されたテキストエリアを見つける
    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    # テキストエリアにコンテンツが入力されていることを確認
    # 空でないことを確認
    text_content = text_area.input_value()
    logger.info(f"Extracted text content: '{text_content}'")

    if not text_content or len(text_content.strip()) == 0:
        # デバッグのため、ページの状態を確認
        logger.info("Text area is empty, checking page state...")

        # スクリーンショットを撮影
        screenshot_path = (
            f"tests/e2e/screenshots/debug_url_extraction_{int(time.time())}.png"
        )
        page.screenshot(path=screenshot_path)
        logger.info(f"Debug screenshot saved: {screenshot_path}")

        # 他のtextarea要素も確認
        all_textareas = page.locator("textarea").all()
        for i, textarea in enumerate(all_textareas):
            content = textarea.input_value()
            placeholder = textarea.get_attribute("placeholder")
            logger.info(
                f"Textarea {i}: placeholder='{placeholder}', content='{content[:50] if content else 'EMPTY'}'"
            )

    assert (
        len(text_content.strip()) > 0
    ), "Extracted text area should contain content, but found empty content"

    # example.comの場合は "Example Domain" が含まれることを確認
    if (
        "example domain" in text_content.lower()
        or "example.com" in text_content.lower()
    ):
        logger.info("Successfully extracted content from example.com")
    else:
        # その他のエラーメッセージでないことを確認
        error_indicators = [
            "conversion error",
            "failed to extract",
            "an error occurred",
        ]
        contains_error = any(
            indicator in text_content.lower() for indicator in error_indicators
        )
        content_preview = (
            text_content[:150] + "..." if len(text_content) > 150 else text_content
        )
        assert (
            not contains_error
        ), f"Extracted text should not contain error. Content preview: {content_preview}"

    # Log only a preview of the content for readability
    content_preview = (
        text_content[:100] + "..." if len(text_content) > 100 else text_content
    )
    logger.info(f"Extracted text area contains content: {content_preview}")
    logger.info(f"Total content length: {len(text_content)} characters")


@then("the extracted text area shows GitHub README content")
def text_area_shows_github_content(page: Page):
    """The extracted text area shows GitHub README content."""
    logger.info("Checking if extracted text area shows GitHub README content")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert (
        len(text_content.strip()) > 0
    ), "Extracted text area should contain GitHub README content"

    # Check for actual error messages, not just the word "error" anywhere in content
    error_indicators = [
        "conversion error",
        "failed to extract",
        "an error occurred",
        "error:",
        "failed:",
    ]
    contains_actual_error = any(
        indicator in text_content.lower() for indicator in error_indicators
    )

    # Create preview for logging and error messages to improve readability
    content_preview = (
        text_content[:150] + "..." if len(text_content) > 150 else text_content
    )

    assert (
        not contains_actual_error
    ), f"GitHub README extraction should not contain actual error messages. Content preview: {content_preview}"

    # Check that content contains README-related keywords
    readme_keywords = [
        "yomitalk",
        "readme",
        "テキスト",
        "音声",
        "gradio",
        "アプリケーション",
    ]
    contains_readme_content = any(
        keyword in text_content.lower() for keyword in readme_keywords
    )
    assert (
        contains_readme_content
    ), f"Content should contain README-related keywords. Content preview: {content_preview}"

    # Log only a preview of the content for readability
    logger.info(
        f"GitHub README content extracted successfully. Preview: {content_preview}"
    )
    logger.info(f"Total content length: {len(text_content)} characters")


@then("the extracted text area shows an error message")
def text_area_shows_error_message(page: Page):
    """The extracted text area shows an error message."""
    logger.info("Checking if extracted text area shows error message")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert (
        len(text_content.strip()) > 0
    ), "Extracted text area should contain error message"

    # エラーメッセージのキーワードが含まれていることを確認
    error_keywords = [
        "invalid url",
        "conversion error",
        "failed to extract",
        "not a valid url",
        "please enter a valid url",
        "please enter a url",
    ]
    contains_error_keyword = any(
        keyword in text_content.lower() for keyword in error_keywords
    )

    # Create preview for logging
    content_preview = (
        text_content[:150] + "..." if len(text_content) > 150 else text_content
    )
    assert (
        contains_error_keyword
    ), f"Text should contain error message. Content preview: {content_preview}"

    logger.info(f"Error message displayed: {content_preview}")


@then("the extracted text area content is replaced with file content")
def text_area_replaced_with_file_content(page: Page):
    """The extracted text area content is replaced with file content."""
    logger.info("Checking if extracted text area content is replaced with file content")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert (
        len(text_content.strip()) > 0
    ), "Extracted text area should contain file content"

    # ファイルの内容が含まれていることを確認（テストファイルの内容による）
    # 少なくとも何らかのコンテンツが表示されていることを確認
    content_preview = (
        text_content[:100] + "..." if len(text_content) > 100 else text_content
    )
    logger.info(f"File content displayed: {content_preview}")
    logger.info(f"Total content length: {len(text_content)} characters")


@when("the user uploads a text file")
def user_uploads_text_file(page: Page):
    """The user uploads a text file."""
    logger.info("Uploading text file")

    # テストデータディレクトリからテキストファイルを取得
    from pathlib import Path

    test_data_dir = Path(__file__).parent.parent / "data"
    test_file = test_data_dir / "sample.txt"

    # テストファイルが存在しない場合は作成
    if not test_file.exists():
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text(
            "This is a test text file content for URL extraction testing."
        )

    # ファイルアップロード
    file_input = page.locator('input[type="file"]')
    expect(file_input).to_be_attached()
    file_input.set_input_files(str(test_file))

    # ファイル処理の完了を待つ
    time.sleep(3)

    logger.info(f"Text file uploaded successfully: {test_file}")


@when('the user enters "https://example.com" into the URL input field')
def user_enters_example_url(page: Page):
    """The user enters "https://example.com" into the URL input field."""
    logger.info("Entering https://example.com into URL field")

    # URL入力フィールドを探す（textareaとして表示される）
    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_attached()
    url_input.fill("https://example.com")

    logger.info("URL entered successfully")


@when('the user enters "invalid-url" into the URL input field')
def user_enters_invalid_url(page: Page):
    """The user enters "invalid-url" into the URL input field."""
    logger.info("Entering invalid-url into URL field")

    # URL入力フィールドを探す（textareaとして表示される）
    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_attached()
    url_input.fill("invalid-url")

    logger.info("Invalid URL entered successfully")
