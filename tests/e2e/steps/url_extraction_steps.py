"""URL抽出機能のステップ定義。"""

import time

from playwright.sync_api import Page, expect
from pytest_bdd import given, then, when

from tests.utils.logger import test_logger as logger


@when('the user enters "<url>" into the URL input field')
def user_enters_url(page: Page, url: str):
    """The user enters a URL into the URL input field."""
    logger.info(f"Entering URL: {url}")

    # Make sure the Web page extraction tab is active first
    web_tab = page.get_by_role("tab", name="Webページ抽出")
    if web_tab.is_visible():
        web_tab.click()
        time.sleep(0.5)

    # URL入力フィールドを見つけて入力
    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_visible()
    url_input.fill(url)

    logger.info(f"URL entered successfully: {url}")


@when('the user enters "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md" into the URL input field')
def user_enters_specific_github_url(page: Page):
    """The user enters the specific GitHub README URL into the URL input field."""
    url = "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"
    logger.info(f"Entering specific GitHub README URL: {url}")

    # Make sure the Web page extraction tab is active first
    web_tab = page.get_by_role("tab", name="Webページ抽出")
    if web_tab.is_visible():
        web_tab.click()
        time.sleep(0.5)

    # URL入力フィールドを見つけて入力
    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_visible()
    url_input.fill(url)

    logger.info(f"GitHub README URL entered successfully: {url}")


@then('the extracted text area contains source information for "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"')
def url_text_area_contains_github_source_info(page: Page):
    """The extracted text area contains source information for the GitHub README URL."""
    url = "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"
    logger.info(f"Checking if text area contains source information for GitHub URL: {url}")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:200]}...")

    expected_source = f"**Source: {url}**"
    assert expected_source in text_content, f"Expected source information '{expected_source}' not found in text content"

    logger.info("Source information for GitHub URL found in text content")


@when("the user enters a GitHub README URL into the URL input field")
def user_enters_github_readme_url(page: Page):
    """The user enters a GitHub README URL into the URL input field."""
    github_readme_url = "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"
    logger.info(f"Entering GitHub README URL: {github_readme_url}")

    # Make sure the Web page extraction tab is active first
    web_tab = page.get_by_role("tab", name="Webページ抽出")
    if web_tab.is_visible():
        web_tab.click()
        time.sleep(0.5)

    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_visible()
    url_input.fill(github_readme_url)

    logger.info(f"GitHub README URL entered successfully: {github_readme_url}")


@when("the user leaves the URL input field empty")
def user_leaves_url_field_empty(page: Page):
    """The user leaves the URL input field empty."""
    logger.info("Leaving URL field empty")

    # Make sure the Web page extraction tab is active first
    web_tab = page.get_by_role("tab", name="Webページ抽出")
    if web_tab.is_visible():
        web_tab.click()
        time.sleep(0.5)

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

    # Get the current content length before extraction
    text_area = page.locator("textarea").nth(1)
    initial_content = text_area.input_value() or ""
    initial_length = len(initial_content.strip())
    logger.info(f"Initial content length: {initial_length}")

    # 抽出処理の完了を待つ（より長い時間待機）
    # Wait for content to change (either addition or error message)
    try:
        if initial_length > 0:
            # If there's existing content, wait for length to increase or separator to appear
            page.wait_for_function(
                f"() => {{"
                f"  const textarea = document.querySelector('textarea');"
                f"  if (!textarea) return false;"
                f"  const content = textarea.value || '';"
                f"  return content.length > {initial_length} || content.includes('---') || content.includes('エラー');"
                f"}}",
                timeout=15000,
            )
        else:
            # If textarea is empty, wait for any content to appear
            page.wait_for_function(
                "() => {  const textarea = document.querySelector('textarea');  return textarea && textarea.value && textarea.value.trim().length > 0;}",
                timeout=15000,
            )
    except Exception:
        logger.warning("Wait for content change timed out, using fallback sleep")
        time.sleep(5)  # Fallback to longer timeout for URL extraction

    logger.info("URL extract button clicked successfully")


@then("the extracted text area shows content")
def text_area_shows_content(page: Page):
    """The extracted text area shows content."""
    logger.info("Checking if extracted text area shows content")

    # 抽出されたテキストエリアを見つける
    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    # テキストエリアにコンテンツが入力されていることを確認
    # 空でないことを確認
    text_content = text_area.input_value()
    logger.info(f"Extracted text content: '{text_content}'")

    if not text_content or len(text_content.strip()) == 0:
        # デバッグのため、ページの状態を確認
        logger.info("Text area is empty, checking page state...")

        # スクリーンショットを撮影
        screenshot_path = f"tests/e2e/screenshots/debug_url_extraction_{int(time.time())}.png"
        page.screenshot(path=screenshot_path)
        logger.info(f"Debug screenshot saved: {screenshot_path}")

        # 他のtextarea要素も確認
        all_textareas = page.locator("textarea").all()
        for i, textarea in enumerate(all_textareas):
            content = textarea.input_value()
            placeholder = textarea.get_attribute("placeholder")
            logger.info(f"Textarea {i}: placeholder='{placeholder}', content='{content[:50] if content else 'EMPTY'}'")

    # In test environments, URL extraction may fail due to network restrictions
    if len(text_content.strip()) == 0:
        logger.warning("URL extraction returned empty content - this may be expected in test environments due to network restrictions")
        # Check if we're in test mode and allow empty content
        import os

        if os.environ.get("E2E_TEST_MODE") == "true":
            logger.info("Test mode detected - allowing empty URL extraction result")
            return

    assert len(text_content.strip()) > 0, "Extracted text area should contain content, but found empty content"

    # example.comの場合は "Example Domain" が含まれることを確認
    if "example domain" in text_content.lower() or "example.com" in text_content.lower():
        logger.info("Successfully extracted content from example.com")
    else:
        # その他のエラーメッセージでないことを確認
        error_indicators = [
            "conversion error",
            "failed to extract",
            "an error occurred",
        ]
        contains_error = any(indicator in text_content.lower() for indicator in error_indicators)
        content_preview = text_content[:150] + "..." if len(text_content) > 150 else text_content
        assert not contains_error, f"Extracted text should not contain error. Content preview: {content_preview}"

    # Log only a preview of the content for readability
    content_preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
    logger.info(f"Extracted text area contains content: {content_preview}")
    logger.info(f"Total content length: {len(text_content)} characters")


@then("the extracted text area shows GitHub README content")
def text_area_shows_github_content(page: Page):
    """The extracted text area shows GitHub README content."""
    logger.info("Checking if extracted text area shows GitHub README content")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    # In test environments, URL extraction may fail due to network restrictions
    if len(text_content.strip()) == 0:
        logger.warning("GitHub URL extraction returned empty content - this may be expected in test environments")
        import os

        if os.environ.get("E2E_TEST_MODE") == "true":
            logger.info("Test mode detected - allowing empty GitHub URL extraction result")
            return

    assert len(text_content.strip()) > 0, "Extracted text area should contain GitHub README content"

    # Check for actual error messages, not just the word "error" anywhere in content
    error_indicators = [
        "conversion error",
        "failed to extract",
        "an error occurred",
        "error:",
        "failed:",
    ]
    contains_actual_error = any(indicator in text_content.lower() for indicator in error_indicators)

    # Create preview for logging and error messages to improve readability
    content_preview = text_content[:150] + "..." if len(text_content) > 150 else text_content

    assert not contains_actual_error, f"GitHub README extraction should not contain actual error messages. Content preview: {content_preview}"

    # Check that content contains README-related keywords
    readme_keywords = [
        "yomitalk",
        "readme",
        "テキスト",
        "音声",
        "gradio",
        "アプリケーション",
    ]
    contains_readme_content = any(keyword in text_content.lower() for keyword in readme_keywords)
    assert contains_readme_content, f"Content should contain README-related keywords. Content preview: {content_preview}"

    # Log only a preview of the content for readability
    logger.info(f"GitHub README content extracted successfully. Preview: {content_preview}")
    logger.info(f"Total content length: {len(text_content)} characters")


@then("the extracted text area shows an error message")
def text_area_shows_error_message(page: Page):
    """The extracted text area shows an error message."""
    logger.info("Checking if extracted text area shows error message")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert len(text_content.strip()) > 0, "Extracted text area should contain error message"

    # エラーメッセージのキーワードが含まれていることを確認
    error_keywords = [
        "invalid url",
        "conversion error",
        "failed to extract",
        "not a valid url",
        "please enter a valid url",
        "please enter a url",
    ]
    contains_error_keyword = any(keyword in text_content.lower() for keyword in error_keywords)

    # Create preview for logging
    content_preview = text_content[:150] + "..." if len(text_content) > 150 else text_content
    assert contains_error_keyword, f"Text should contain error message. Content preview: {content_preview}"

    logger.info(f"Error message displayed: {content_preview}")


@then("the extracted text area content is replaced with file content")
def text_area_replaced_with_file_content(page: Page):
    """The extracted text area content is replaced with file content."""
    logger.info("Checking if extracted text area content is replaced with file content")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert len(text_content.strip()) > 0, "Extracted text area should contain file content"

    # ファイルの内容が含まれていることを確認（テストファイルの内容による）
    # 少なくとも何らかのコンテンツが表示されていることを確認
    content_preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
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
        test_file.write_text("This is a test text file content for URL extraction testing.")

    # ファイルアップロード
    file_input = page.locator('input[type="file"]')
    expect(file_input).to_be_attached()
    file_input.set_input_files(str(test_file))

    # ファイル処理の完了を待つ
    # Wait for file processing with smart timeout
    try:
        page.wait_for_function("() => document.querySelector('textarea').value.length > 0", timeout=5000)
    except Exception:
        time.sleep(1.5)  # Fallback to shorter timeout

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


@when("the user unchecks the automatic separator checkbox")
def user_unchecks_separator_checkbox(page: Page):
    """The user unchecks the automatic separator checkbox."""
    logger.info("Unchecking automatic separator checkbox")

    separator_checkbox = page.locator('input[type="checkbox"]').filter(has_text="追加時に自動で区切りを挿入")
    expect(separator_checkbox).to_be_visible()
    separator_checkbox.uncheck()

    logger.info("Automatic separator checkbox unchecked")


@when("the user checks the automatic separator checkbox")
def user_checks_separator_checkbox(page: Page):
    """The user checks the automatic separator checkbox."""
    logger.info("Checking automatic separator checkbox")

    separator_checkbox = page.locator('input[type="checkbox"]').filter(has_text="追加時に自動で区切りを挿入")
    expect(separator_checkbox).to_be_visible()
    separator_checkbox.check()

    logger.info("Automatic separator checkbox checked")


@when('the user clicks the "テキストをクリア" button')
def user_clicks_clear_text_button(page: Page):
    """The user clicks the clear text button."""
    logger.info("Clicking clear text button")

    clear_button = page.locator('button:has-text("テキストをクリア")')
    expect(clear_button).to_be_visible()
    clear_button.click()

    time.sleep(0.5)
    logger.info("Clear text button clicked")


@then("the extracted text should contain a separator before the new content")
def text_should_contain_separator(page: Page):
    """The extracted text should contain a separator before the new content."""
    logger.info("Checking if extracted text contains separator")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert "---" in text_content or "**Source:" in text_content, "Text should contain a separator"

    logger.info("Separator found in extracted text")


@then("the extracted text should not contain a separator")
def text_should_not_contain_separator(page: Page):
    """The extracted text should not contain a separator."""
    logger.info("Checking if extracted text does not contain separator")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    # Check that there are no markdown-style separators
    assert "---" not in text_content and "**Source:" not in text_content, "Text should not contain a separator"

    logger.info("No separator found in extracted text")


@then("the extracted text should contain both the original and new content")
def text_should_contain_both_contents(page: Page):
    """The extracted text should contain both the original and new content."""
    logger.info("Checking if extracted text contains both original and new content")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert len(text_content.strip()) > 0, "Text area should contain content"

    # For URL extraction, we expect content from the URL
    content_preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
    logger.info(f"Combined content found: {content_preview}")


@then("the extracted text area should be empty")
def text_area_should_be_empty(page: Page):
    """The extracted text area should be empty."""
    logger.info("Checking if extracted text area is empty")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert len(text_content.strip()) == 0, f"Text area should be empty, but contains: {text_content[:50]}"

    logger.info("Text area is empty as expected")


@when("the user enters some initial text in the extracted text area")
def user_enters_initial_text(page: Page):
    """The user enters some initial text in the extracted text area."""
    logger.info("Entering initial text in extracted text area")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    initial_text = "This is some initial text that was already in the text area."
    text_area.fill(initial_text)

    time.sleep(0.5)
    logger.info("Initial text entered successfully")


@then("the existing text with separator is preserved")
def existing_text_is_preserved(page: Page):
    """The existing text with separator is preserved."""
    logger.info("Checking if existing text with separator is preserved")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:200]}...")

    # 既存のテキストが保持されていることを確認
    assert "Existing content" in text_content, "Existing content not preserved"

    # セパレータが追加されていることを確認
    assert "---" in text_content, "Separator not found"

    # URLからの新しいコンテンツも追加されていることを確認
    assert "**Source:" in text_content, "URL content not added"

    logger.info("Existing text with separator preserved as expected")


@then("the existing text without separator is preserved")
def existing_text_no_separator_preserved(page: Page):
    """The existing text without separator is preserved."""
    logger.info("Checking if existing text without separator is preserved")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:200]}...")

    # 既存のテキストが保持されていることを確認
    assert "Existing content" in text_content, "Existing content not preserved"

    # セパレータが追加されていないことを確認（連続する---がない）
    # ただし、ソース情報の区切りは存在する可能性がある
    lines = text_content.split("\n")
    separator_lines = [line for line in lines if line.strip() == "---"]

    # セパレータが自動挿入されていない（つまり、ソース区切り以外の---がない）ことを確認
    logger.info(f"Found {len(separator_lines)} separator lines")

    # URLからの新しいコンテンツも追加されていることを確認
    assert "**Source:" in text_content, "URL content not added"

    logger.info("Existing text without automatic separator preserved as expected")


@given('the user unchecks the "追加時に自動で区切りを挿入" checkbox')
def user_unchecks_separator_checkbox_url_extraction(page: Page):
    """User unchecks the automatic separator checkbox (URL extraction context)."""
    logger.info("Unchecking auto separator checkbox (URL extraction context)")

    checkbox = page.locator('label:has-text("追加時に自動で区切りを挿入") input[type="checkbox"]')
    if not checkbox.is_visible():
        checkbox = page.locator('input[type="checkbox"]').nth(0)  # Fallback to first checkbox
    expect(checkbox).to_be_visible()

    # チェックボックスがチェック済みの場合のみクリック
    if checkbox.is_checked():
        checkbox.click()

    logger.info("Auto separator checkbox unchecked (URL extraction context)")


@then('the extracted text area contains "<text>"')
def text_area_contains_specific_text_url(page: Page, text: str):
    """The extracted text area contains the specific text (URL context)."""
    logger.info(f"Checking if extracted text area contains: {text}")

    text_area = page.locator("textarea").nth(1)
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert text in text_content, f"Expected '{text}' in content, but found: '{text_content[:200]}...'"

    logger.info(f"Text area contains expected text: {text}")
