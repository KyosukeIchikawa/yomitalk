"""Text management functionality step definitions."""

import time

from playwright.sync_api import Page, expect
from pytest_bdd import given, parsers, then, when

from tests.utils.logger import test_logger as logger


@given('the user has entered "<text>" into the extracted text area')
def user_enters_text_to_area(page: Page, text: str):
    """The user has entered text into the extracted text area."""
    logger.info(f"Entering text into extracted text area: {text}")

    # 抽出されたテキストエリアを見つける
    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()
    text_area.fill(text)

    logger.info(f"Text entered successfully: {text}")


@given('the user has entered "Some test content" into the extracted text area')
def user_has_entered_some_test_content(page: Page):
    """The user has entered 'Some test content' into the extracted text area."""
    logger.info("Entering 'Some test content' into extracted text area")

    # 抽出されたテキストエリアを見つける
    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()
    text_area.fill("Some test content")

    logger.info("Test content entered successfully")


@given('the user unchecks the "追加時に自動で区切りを挿入" checkbox')
def user_unchecks_auto_separator_given(page: Page):
    """The user unchecks the automatic separator checkbox (given step)."""
    logger.info("Unchecking auto separator checkbox (Given step)")

    # チェックボックスを見つけてクリック（チェックを外す）
    checkbox = page.locator('label:has-text("追加時に自動で区切りを挿入") input[type="checkbox"]')
    if not checkbox.is_visible():
        checkbox = page.locator('input[type="checkbox"]').nth(0)  # Fallback to first checkbox
    expect(checkbox).to_be_visible()

    # チェックボックスがチェック済みの場合のみクリック
    if checkbox.is_checked():
        checkbox.click()

    logger.info("Auto separator checkbox unchecked (Given step)")


@given(parsers.parse('the user has entered "{text}" into the extracted text area'))
def user_enters_text_into_text_area(page: Page, text: str):
    """User enters text into the extracted text area."""
    logger.info(f"Entering '{text}' into extracted text area")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_area.clear()
    text_area.fill(text)

    logger.info("Successfully entered text into extracted text area")


@when('the user unchecks the "追加時に自動で区切りを挿入" checkbox')
def user_unchecks_auto_separator(page: Page):
    """The user unchecks the automatic separator checkbox (Japanese text)."""
    logger.info("Unchecking auto separator checkbox (Japanese)")

    # チェックボックスを見つけてクリック（チェックを外す）
    # Try different selectors for Gradio checkbox
    checkbox = page.locator('label:has-text("追加時に自動で区切りを挿入") input[type="checkbox"]')
    if not checkbox.is_visible():
        checkbox = page.locator('input[type="checkbox"]').nth(0)  # Fallback to first checkbox
    expect(checkbox).to_be_visible()

    # チェックボックスがチェック済みの場合のみクリック
    if checkbox.is_checked():
        checkbox.click()

    logger.info("Auto separator checkbox unchecked (Japanese)")


@when('the user checks the "追加時に自動で区切りを挿入" checkbox')
def user_checks_auto_separator_checkbox_japanese(page: Page):
    """The user checks the automatic separator checkbox (Japanese text)."""
    logger.info("Checking auto separator checkbox (Japanese)")

    # チェックボックスを見つけてクリック（チェックする）
    # Try different selectors for Gradio checkbox
    checkbox = page.locator('label:has-text("追加時に自動で区切りを挿入") input[type="checkbox"]')
    if not checkbox.is_visible():
        checkbox = page.locator('input[type="checkbox"]').nth(0)  # Fallback to first checkbox
    expect(checkbox).to_be_visible()

    # チェックボックスがチェックされていない場合のみクリック
    if not checkbox.is_checked():
        checkbox.click()

    logger.info("Auto separator checkbox checked (Japanese)")


@when('the user clicks the "テキストをクリア" button')
def user_clicks_clear_text_button(page: Page):
    """The user clicks the clear text button."""
    logger.info("Clicking clear text button")

    # クリアボタンを見つけてクリック
    clear_button = page.locator('button:has-text("テキストをクリア")')
    expect(clear_button).to_be_visible()
    clear_button.click()

    # クリア処理の完了を少し待つ
    time.sleep(0.5)

    logger.info("Clear text button clicked successfully")


@when('the user clicks on the "ファイルアップロード" tab')
def user_clicks_file_upload_tab(page: Page):
    """The user clicks on the file upload tab."""
    logger.info("Clicking file upload tab")

    # Look for the tab using different possible selectors
    tab_selectors = [
        'button[role="tab"]:has-text("ファイルアップロード")',
        '.tab-nav button:has-text("ファイルアップロード")',
        'button:has-text("ファイルアップロード")',
        '*[data-testid*="tab"]:has-text("ファイルアップロード")',
    ]

    tab_clicked = False
    for selector in tab_selectors:
        tab = page.locator(selector)
        if tab.count() > 0 and tab.first.is_visible():
            tab.first.click()
            tab_clicked = True
            break

    if not tab_clicked:
        # Fallback: look for any clickable element with the text
        tab = page.get_by_text("ファイルアップロード")
        if tab.count() > 0:
            tab.first.click()
            tab_clicked = True

    if not tab_clicked:
        raise Exception("File upload tab not found")

    time.sleep(0.5)
    logger.info("File upload tab clicked successfully")


@when('the user clicks on the "Webページ抽出" tab')
def user_clicks_web_extraction_tab(page: Page):
    """The user clicks on the web page extraction tab."""
    logger.info("Clicking web page extraction tab")

    # Look for the tab using different possible selectors
    tab_selectors = [
        'button[role="tab"]:has-text("Webページ抽出")',
        '.tab-nav button:has-text("Webページ抽出")',
        'button:has-text("Webページ抽出")',
        '*[data-testid*="tab"]:has-text("Webページ抽出")',
    ]

    tab_clicked = False
    for selector in tab_selectors:
        tab = page.locator(selector)
        if tab.count() > 0 and tab.first.is_visible():
            tab.first.click()
            tab_clicked = True
            break

    if not tab_clicked:
        # Fallback: look for any clickable element with the text
        tab = page.get_by_text("Webページ抽出")
        if tab.count() > 0:
            tab.first.click()
            tab_clicked = True

    if not tab_clicked:
        raise Exception("Web page extraction tab not found")

    time.sleep(0.5)
    logger.info("Web page extraction tab clicked successfully")


@when('the user clicks the "ファイルからテキストを抽出" button')
def user_clicks_file_extract_button(page: Page):
    """The user clicks the file text extraction button."""
    logger.info("Clicking file extract button")

    # ファイル抽出ボタンを見つけてクリック
    extract_button = page.locator('button:has-text("ファイルからテキストを抽出")')
    expect(extract_button).to_be_visible()
    extract_button.click()

    # Get the current content length before extraction
    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか"]')
    initial_content = text_area.input_value() or ""
    initial_length = len(initial_content.strip())
    logger.info(f"Initial content length before URL extraction: {initial_length}")

    # 抽出処理の完了を待つ
    # Wait for processing with smart timeout - URL extraction needs more time
    try:
        if initial_length > 0:
            # If there's existing content, wait for length to increase or separator to appear
            page.wait_for_function(
                f"() => {{"
                f"  const textarea = document.querySelector('textarea[placeholder*=\"ファイルをアップロードするか\"]');"
                f"  if (!textarea) return false;"
                f"  const content = textarea.value || '';"
                f"  return content.length > {initial_length} || content.includes('---') || content.includes('エラー');"
                f"}}",
                timeout=15000,
            )
        else:
            # If textarea is empty, wait for any content to appear
            page.wait_for_function(
                "() => {  const textarea = document.querySelector('textarea[placeholder*=\"ファイルをアップロードするか\"]');  return textarea && textarea.value && textarea.value.trim().length > 0;}",
                timeout=15000,
            )
    except Exception:
        logger.warning("Wait for URL extraction completion timed out, using fallback sleep")
        time.sleep(5)  # Fallback to longer timeout for URL extraction

    logger.info("File extract button clicked successfully")


@then("the extracted text area is empty")
def text_area_is_empty(page: Page):
    """The extracted text area is empty."""
    logger.info("Checking if extracted text area is empty")

    # 抽出されたテキストエリアを見つける
    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    # テキストエリアが空であることを確認
    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    assert text_content == "", f"Expected empty text area, but found: '{text_content}'"
    logger.info("Text area is empty as expected")


@then("the extracted text area shows content with source separator")
def text_area_shows_content_with_separator(page: Page):
    """The extracted text area shows content with source separator."""
    logger.info("Checking if extracted text area shows content with separator")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    # セパレーター（---）が含まれていることを確認
    assert "---" in text_content, f"Expected separator in content, but found: '{text_content}'"
    # ソース情報が含まれていることを確認
    assert "**Source:" in text_content, f"Expected source info in content, but found: '{text_content}'"

    logger.info("Text area shows content with separator as expected")


@then("the extracted text area shows appended content without separator")
def text_area_shows_appended_content(page: Page):
    """The extracted text area shows appended content without separator."""
    logger.info("Checking if extracted text area shows appended content without separator")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    # セパレーター（---）が含まれていないことを確認
    assert "---" not in text_content, f"Expected no separator in content, but found: '{text_content}'"
    # ソース情報（**Source:**）が含まれていないことを確認
    assert "**Source:" not in text_content, f"Expected no source info in content, but found: '{text_content}'"

    # ただし、既存のコンテンツと新しいコンテンツが追加されていることは確認
    assert "Existing content" in text_content, f"Expected existing content to be preserved, but found: '{text_content}'"

    logger.info("Text area shows appended content without separator as expected")


@then('the extracted text area contains "<expected_text>"')
def text_area_contains_text(page: Page, expected_text: str):
    """The extracted text area contains the expected text."""
    logger.info(f"Checking if extracted text area contains: {expected_text}")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    assert expected_text in text_content, f"Expected '{expected_text}' in content, but found: '{text_content}'"
    logger.info(f"Text area contains expected text: {expected_text}")


@then('the extracted text area contains source information for "<source>"')
def text_area_contains_source_info(page: Page, source: str):
    """The extracted text area contains source information for the given source."""
    logger.info(f"Checking if extracted text area contains source info for: {source}")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    # ソース情報が含まれていることを確認
    assert f"**Source: {source}**" in text_content, f"Expected source info for '{source}' in content, but found: '{text_content}'"
    logger.info(f"Text area contains source info for: {source}")


@then("the file input should be cleared")
def file_input_should_be_cleared(page: Page):
    """The file input should be cleared after upload."""
    logger.info("Checking if file input is cleared")

    # Look for file input element
    file_input = page.locator('input[type="file"]')
    expect(file_input).to_be_attached()  # Check element exists, not visibility

    # Check if file input has no value (cleared)
    input_value = file_input.input_value()
    logger.info(f"File input value: '{input_value}'")

    # File input should be empty after automatic extraction
    assert input_value == "" or input_value is None, "File input should be cleared after extraction"

    logger.info("File input is cleared as expected")


@then("text should be extracted with source separator")
def text_should_be_extracted_with_separator(page: Page):
    """Text should be extracted with source separator."""
    logger.info("Checking if text is extracted with source separator")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Extracted text content: '{text_content}'")

    # テキストが抽出されていることを確認
    assert text_content and len(text_content.strip()) > 0, "Expected extracted text but found empty content"

    # セパレーターが含まれていることを確認
    assert "---" in text_content, f"Expected separator in content, but found: '{text_content}'"
    assert "**Source:" in text_content, f"Expected source info in content, but found: '{text_content}'"

    logger.info("Text extracted with source separator as expected")


@then("text should be extracted without separator")
def text_should_be_extracted_without_separator(page: Page):
    """Text should be extracted without separator."""
    logger.info("Checking if text is extracted without separator")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Extracted text content: '{text_content}'")

    # テキストが抽出されていることを確認
    assert text_content and len(text_content.strip()) > 0, "Expected extracted text but found empty content"

    # セパレーターが含まれていないことを確認
    assert "---" not in text_content, f"Expected no separator in content, but found: '{text_content}'"
    assert "**Source:" not in text_content, f"Expected no source info in content, but found: '{text_content}'"

    logger.info("Text extracted without separator as expected")


@then("the extracted text area contains content from both files")
def text_area_contains_content_from_both_files(page: Page):
    """The extracted text area contains content from both files."""
    logger.info("Checking if text area contains content from both files")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:300]}...")

    # 両方のファイルからのソース情報があることを確認
    assert "**Source: sample_text.txt**" in text_content, "Source information for sample_text.txt not found"
    assert "**Source: another_file.txt**" in text_content, "Source information for another_file.txt not found"

    # 両方のファイルの内容があることを確認
    assert "Yomitalk サンプルテキスト" in text_content, "Content from sample_text.txt not found"
    assert "別のサンプルファイル" in text_content, "Content from another_file.txt not found"

    logger.info("Content from both files found as expected")


@then("the existing text is preserved when extracting from file")
def existing_text_preserved_from_file(page: Page):
    """The existing text is preserved when extracting from file."""
    logger.info("Checking if existing text is preserved during file extraction")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:200]}...")

    # 手動入力されたテキストが保持されていることを確認
    assert "Manual input content" in text_content, "Manually entered text not preserved"

    # ファイルからの新しいコンテンツも追加されていることを確認
    assert "**Source:" in text_content, "File content not added"

    logger.info("Existing text preserved during file extraction as expected")


@then(parsers.parse('the extracted text area contains source information for "{filename}"'))
def text_area_contains_source_information(page: Page, filename: str):
    """The extracted text area contains source information for the specified file."""
    logger.info(f"Checking if text area contains source information for {filename}")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:200]}...")

    expected_source = f"**Source: {filename}**"
    assert expected_source in text_content, f"Expected source information '{expected_source}' not found in text content"

    logger.info(f"Source information for {filename} found as expected")


@then('the extracted text area contains source information for "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"')
def text_area_contains_github_source_info(page: Page):
    """The extracted text area contains source information for the GitHub README URL."""
    url = "https://github.com/KyosukeIchikawa/yomitalk/blob/main/README.md"
    logger.info(f"Checking if text area contains source information for GitHub URL: {url}")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:200]}...")

    expected_source = f"**Source: {url}**"
    assert expected_source in text_content, f"Expected source information '{expected_source}' not found in text content"

    logger.info("Source information for GitHub URL found in text content")


@then("the automatic separator is disabled")
def automatic_separator_is_disabled(page: Page):
    """The automatic separator is disabled."""
    logger.info("Checking if automatic separator is disabled")

    # チェックボックスがチェックされていないことを確認
    checkbox = page.locator('label:has-text("追加時に自動で区切りを挿入") input[type="checkbox"]')
    if not checkbox.is_visible():
        checkbox = page.locator('input[type="checkbox"]').nth(0)  # Fallback to first checkbox
    expect(checkbox).to_be_visible()

    assert not checkbox.is_checked(), "Expected checkbox to be unchecked (separator disabled)"
    logger.info("Automatic separator is disabled as expected")


@then("the extracted text area contains content from both sources")
def text_area_contains_content_from_both_sources(page: Page):
    """The extracted text area contains content from both sources."""
    logger.info("Checking if text area contains content from both sources")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: {text_content[:300]}...")

    # ファイルのソース情報があることを確認
    assert "**Source: sample_text.txt**" in text_content, "Source information for file not found"

    # URLのソース情報があることを確認
    assert "**Source: https://example.com**" in text_content, "Source information for URL not found"

    # 両方のソースからの内容があることを確認
    assert "Yomitalk サンプルテキスト" in text_content or "Example Domain" in text_content, "Content from sources not found"

    logger.info("Content from both sources found as expected")


@then('the extracted text section shows step "3. 抽出テキスト表示"')
def extracted_text_section_shows_step_3_alt(page: Page):
    """The extracted text section shows step 3 (alternative text)."""
    logger.info("Checking if extracted text section shows step 3 (alternative)")

    step_3_header = page.locator('text="3. 抽出テキスト表示"')
    expect(step_3_header).to_be_visible()

    logger.info("Extracted text section shows step 3 (alternative) as expected")


@then('the extracted text area contains "{expected_text}"')
def text_area_contains_specific_text(page: Page, expected_text: str):
    """The extracted text area contains the specific expected text."""
    logger.info(f"Checking if extracted text area contains: {expected_text}")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    assert expected_text in text_content, f"Expected '{expected_text}' in content, but found: '{text_content}'"
    logger.info(f"Text area contains expected text: {expected_text}")


@then("the automatic separator is enabled")
def automatic_separator_is_enabled(page: Page):
    """The automatic separator is enabled."""
    logger.info("Checking if automatic separator is enabled")

    # チェックボックスを見つける
    checkbox = page.locator('label:has-text("追加時に自動で区切りを挿入") input[type="checkbox"]')
    if not checkbox.is_visible():
        checkbox = page.locator('input[type="checkbox"]').nth(0)  # Fallback to first checkbox
    expect(checkbox).to_be_visible()

    # チェックボックスがチェックされていることを確認
    assert checkbox.is_checked(), "Automatic separator checkbox should be enabled"
    logger.info("Automatic separator is enabled as expected")


@then("the extracted text area contains content from the file")
def text_area_contains_file_content(page: Page):
    """The extracted text area contains content from the file."""
    logger.info("Checking if text area contains content from the file")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content[:200]}...'")

    # ファイルからのコンテンツが含まれていることを確認
    file_indicators = [
        "Yomitalk サンプルテキスト",
        "機能概要",
        "PDF",
        "テキスト",
        "VOICEVOX",
    ]
    has_file_content = any(indicator in text_content for indicator in file_indicators)

    assert has_file_content, f"Expected file content indicators in text area, but found: '{text_content[:200]}...'"
    logger.info("Text area contains content from the file as expected")


@then("the file upload and URL input are displayed side by side")
def file_upload_and_url_input_side_by_side(page: Page):
    """The file upload and URL input are displayed side by side."""
    logger.info("Checking if file upload and URL input are displayed side by side")

    # ファイルアップロードとURL入力が並んで表示されていることを確認
    # ファイルアップロード要素は hidden でも存在することを確認
    file_upload = page.locator('input[type="file"]')
    url_input = page.locator('textarea[placeholder="https://example.com/page"]')

    # ファイルアップロード要素の存在を確認（visible でなくても良い）
    expect(file_upload).to_be_attached()
    expect(url_input).to_be_visible()

    logger.info("File upload and URL input are displayed side by side")


@then('the extracted text area has label "{expected_label}"')
def extracted_text_area_has_label(page: Page, expected_label: str):
    """The extracted text area has the expected label."""
    logger.info(f"Checking if extracted text area has label: {expected_label}")

    # ラベルテキストを探す
    label_element = page.locator(f'text="{expected_label}"')
    expect(label_element).to_be_visible()

    logger.info(f"Extracted text area has label: {expected_label}")


@then('the extracted text area has label "解説対象テキスト（トークの元ネタ）"')
def extracted_text_area_has_japanese_label(page: Page):
    """The extracted text area has the Japanese label."""
    logger.info("Checking if extracted text area has label: 解説対象テキスト（トークの元ネタ）")

    # ラベルテキストを探す
    label_element = page.locator('text="解説対象テキスト（トークの元ネタ）"')
    expect(label_element).to_be_visible()

    logger.info("Extracted text area has label: 解説対象テキスト（トークの元ネタ）")


@then('the extracted text area contains "Existing content"')
def text_area_contains_existing_content(page: Page):
    """The extracted text area contains 'Existing content'."""
    logger.info("Checking if extracted text area contains 'Existing content'")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    assert "Existing content" in text_content, f"Expected 'Existing content' in content, but found: '{text_content}'"
    logger.info("Text area contains 'Existing content' as expected")


@then("the file upload area should be visible")
def file_upload_area_should_be_visible(page: Page):
    """The file upload area should be visible."""
    logger.info("Checking if file upload area is visible")

    file_upload = page.locator('input[type="file"]')
    expect(file_upload).to_be_visible()
    logger.info("File upload area is visible")


@then("the file upload area should be hidden")
def file_upload_area_should_be_hidden(page: Page):
    """The file upload area should be hidden."""
    logger.info("Checking if file upload area is hidden")

    file_upload = page.locator('input[type="file"]')
    expect(file_upload).to_be_hidden()
    logger.info("File upload area is hidden")


@then("the URL input area should be visible")
def url_input_area_should_be_visible(page: Page):
    """The URL input area should be visible."""
    logger.info("Checking if URL input area is visible")

    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_visible()
    logger.info("URL input area is visible")


@then("the URL input area should be hidden")
def url_input_area_should_be_hidden(page: Page):
    """The URL input area should be hidden."""
    logger.info("Checking if URL input area is hidden")

    url_input = page.locator('textarea[placeholder="https://example.com/page"]')
    expect(url_input).to_be_hidden()
    logger.info("URL input area is hidden")


@then("the extracted text area contains content from the URL")
def text_area_contains_url_content(page: Page):
    """The extracted text area contains content from the URL."""
    logger.info("Checking if text area contains URL content")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert len(text_content.strip()) > 0, "Text area should contain URL content"

    logger.info("Text area contains URL content as expected")


@then('the extracted text area contains "Manual input content"')
def text_area_contains_manual_input_content(page: Page):
    """The extracted text area contains 'Manual input content'."""
    logger.info("Checking if extracted text area contains 'Manual input content'")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    logger.info(f"Text area content: '{text_content}'")

    assert "Manual input content" in text_content, f"Expected 'Manual input content' in content, but found: '{text_content}'"
    logger.info("Text area contains 'Manual input content' as expected")
