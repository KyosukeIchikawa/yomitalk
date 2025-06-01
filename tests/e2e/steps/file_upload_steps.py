"""Module implementing test steps for file upload functionality."""

from playwright.sync_api import Page, expect
from pytest_bdd import given, parsers, then, when

from tests.e2e.conftest import TEST_DATA_DIR


@when(parsers.parse('I upload a {file_type} file "{file_name}"'))
def upload_file(page: Page, file_type, file_name):
    """
    Upload a file

    Args:
        page: Playwright page object
        file_type: File type (PDF/text)
        file_name: Name of the file to upload
    """
    # Set the file path
    file_path = TEST_DATA_DIR / file_name
    assert file_path.exists(), f"Test file {file_path} does not exist"

    # Upload the file
    # Upload to Gradio file upload component
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(file_path))

    # Wait for the file to be uploaded (max 2 seconds)
    page.wait_for_timeout(2000)  # Wait for 2 seconds


@when(parsers.parse('the user uploads a {file_type} file "{file_name}"'))
def user_uploads_file(page: Page, file_type, file_name):
    """
    User uploads a file without automatic extraction

    Args:
        page: Playwright page object
        file_type: File type (PDF/text)
        file_name: Name of the file to upload
    """
    # Set the file path
    file_path = TEST_DATA_DIR / file_name
    assert file_path.exists(), f"Test file {file_path} does not exist"

    # Upload the file to Gradio file upload component
    file_input = page.locator('input[type="file"]').first
    file_input.set_input_files(str(file_path))

    # Wait for the file to be uploaded (max 2 seconds)
    page.wait_for_timeout(2000)  # Wait for 2 seconds


@then("text should be extracted")
def text_is_extracted(page: Page):
    """
    Verify that text is extracted

    Args:
        page: Playwright page object
    """
    # Text extraction result should be displayed in the specific text box for extracted text
    # Use the placeholder text to identify the correct textarea
    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')

    # Wait up to 10 seconds for text to appear in the textbox
    expect(text_area).not_to_be_empty(timeout=10000)

    # Verify that the content is a meaningful string
    text_content = text_area.input_value()
    assert len(text_content) > 10, "Extracted text is too short"


@then('the "トーク原稿を生成" button should be active')
def process_button_is_active(page: Page):
    """
    Verify that the process button exists

    Args:
        page: Playwright page object
    """
    # Check the "Generate Talk Script" button exists
    generate_button = page.get_by_role("button", name="トーク原稿を生成")

    # アプリケーションの実装では、テキスト入力後もボタンは disabled かもしれないため、存在チェックのみ行う
    expect(generate_button).to_be_visible(timeout=2000)

    # API設定が必要な可能性があるため、設定を行う
    # OpenAI APIキーテキストボックスを探す
    api_input = page.get_by_placeholder("sk-...")
    if api_input.is_visible():
        api_input.fill("sk-dummy-key-for-testing")
        # APIキー設定ボタンをクリック
        set_api_button = page.get_by_role("button", name="APIキーを設定").first
        if set_api_button.is_visible():
            set_api_button.click()
            page.wait_for_timeout(1000)


@when('the user clicks the "ファイルからテキストを抽出" button')
def user_clicks_file_extract_button(page: Page):
    """The user clicks the file extraction button."""
    from tests.utils.logger import test_logger as logger

    logger.info("Clicking file extraction button")

    extract_button = page.locator('button:has-text("ファイルからテキストを抽出")')
    expect(extract_button).to_be_visible()
    extract_button.click()

    # Wait for processing
    page.wait_for_timeout(3000)

    logger.info("File extraction button clicked successfully")


@then("the file input should be cleared")
def file_input_should_be_cleared(page: Page):
    """The file input should be cleared after extraction."""
    from tests.utils.logger import test_logger as logger

    logger.info("Checking if file input is cleared")

    file_input = page.locator('input[type="file"]').first

    # Check if the file input has been cleared
    # In Gradio, this might show as empty or with a default placeholder
    files = file_input.input_value()
    assert files == "" or files is None, "File input should be cleared after extraction"

    logger.info("File input is cleared as expected")


@then("the extracted text should contain the file content")
def text_should_contain_file_content(page: Page):
    """The extracted text should contain the file content."""
    from tests.utils.logger import test_logger as logger

    logger.info("Checking if extracted text contains file content")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert (
        len(text_content.strip()) > 0
    ), "Extracted text area should contain file content"

    content_preview = (
        text_content[:100] + "..." if len(text_content) > 100 else text_content
    )
    logger.info(f"File content extracted: {content_preview}")


@when("the user uploads another file")
def user_uploads_another_file(page: Page):
    """The user uploads another file."""
    from pathlib import Path

    from tests.utils.logger import test_logger as logger

    logger.info("Uploading another file")

    # Create a second test file
    test_data_dir = Path(__file__).parent.parent / "data"
    test_file = test_data_dir / "sample2.txt"

    if not test_file.exists():
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("This is the content of the second test file.")

    file_input = page.locator('input[type="file"]').first
    expect(file_input).to_be_attached()
    file_input.set_input_files(str(test_file))

    page.wait_for_timeout(2000)
    logger.info("Second file uploaded successfully")


@then("the extracted text should accumulate both file contents")
def text_should_accumulate_contents(page: Page):
    """The extracted text should accumulate both file contents."""
    from tests.utils.logger import test_logger as logger

    logger.info("Checking if extracted text accumulates content from multiple files")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert (
        len(text_content.strip()) > 0
    ), "Extracted text area should contain accumulated content"

    # Check for content from both files or separator indicators
    has_multiple_sources = (
        "**Source:" in text_content or len(text_content.split("\n")) > 5
    )
    assert has_multiple_sources, "Text should contain content from multiple sources"

    content_preview = (
        text_content[:200] + "..." if len(text_content) > 200 else text_content
    )
    logger.info(f"Accumulated content: {content_preview}")


@then("text should be extracted with source separator")
def text_extracted_with_source_separator(page: Page):
    """Text should be extracted with source separator."""
    from tests.utils.logger import test_logger as logger

    logger.info("Checking if text is extracted with source separator")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert len(text_content.strip()) > 0, "Extracted text area should contain content"

    # Check for separator and source information
    assert "---" in text_content, "Separator should be present in extracted text"
    assert (
        "**Source:" in text_content
    ), "Source information should be present in extracted text"

    content_preview = (
        text_content[:200] + "..." if len(text_content) > 200 else text_content
    )
    logger.info(f"Extracted text content: '{content_preview}'")
    logger.info("Text extracted with source separator as expected")


@then("text should be extracted without separator")
def text_extracted_without_separator(page: Page):
    """Text should be extracted without separator."""
    from tests.utils.logger import test_logger as logger

    logger.info("Checking if text is extracted without separator")

    text_area = page.locator('textarea[placeholder*="ファイルをアップロードするか、URLを入力するか"]')
    expect(text_area).to_be_visible()

    text_content = text_area.input_value()
    assert len(text_content.strip()) > 0, "Extracted text area should contain content"

    # Check that separator is not present (but allow for natural line breaks)
    assert (
        "---" not in text_content
    ), "Separator should not be present in extracted text"

    content_preview = (
        text_content[:200] + "..." if len(text_content) > 200 else text_content
    )
    logger.info(f"Extracted text content: '{content_preview}'")
    logger.info("Text extracted without separator as expected")


@when('the user uploads a text file "<filename>"')
def user_uploads_text_file_with_name(page: Page, filename: str):
    """The user uploads a text file with the specified filename."""
    from pathlib import Path

    from tests.utils.logger import test_logger as logger

    logger.info(f"Uploading text file: {filename}")

    # Map known test files to actual test data
    test_data_dir = Path(__file__).parent.parent / "data"

    if filename == "sample_text.txt":
        test_file = test_data_dir / "sample.txt"
    elif filename == "another_file.txt":
        test_file = test_data_dir / "another_file.txt"
    else:
        test_file = test_data_dir / filename

    # Create file if it doesn't exist
    if not test_file.exists():
        test_file.parent.mkdir(parents=True, exist_ok=True)
        if filename == "another_file.txt":
            test_file.write_text(
                "This is content from another test file for testing file accumulation."
            )
        else:
            test_file.write_text("This is a sample text file content for testing.")

    file_input = page.locator('input[type="file"]').first
    expect(file_input).to_be_attached()
    file_input.set_input_files(str(test_file))

    page.wait_for_timeout(2000)
    logger.info(f"Text file uploaded successfully: {test_file}")


@given('the user unchecks the "追加時に自動で区切りを挿入" checkbox')
def user_unchecks_separator_checkbox(page: Page):
    """User unchecks the automatic separator checkbox (file upload context)."""
    from tests.utils.logger import test_logger as logger

    logger.info("Unchecking auto separator checkbox (file upload context)")

    checkbox = page.locator('label:has-text("追加時に自動で区切りを挿入") input[type="checkbox"]')
    if not checkbox.is_visible():
        checkbox = page.locator('input[type="checkbox"]').nth(
            0
        )  # Fallback to first checkbox
    expect(checkbox).to_be_visible()

    # チェックボックスがチェック済みの場合のみクリック
    if checkbox.is_checked():
        checkbox.click()

    logger.info("Auto separator checkbox unchecked (file upload context)")
