"""
PDF extraction steps for paper podcast e2e tests
"""

from pathlib import Path

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, then, when

from tests.utils.logger import test_logger as logger

from .common_steps import TEST_PDF_PATH


@when("the user uploads a PDF file")
def upload_pdf_file(page_with_server: Page):
    """Upload PDF file"""
    page = page_with_server

    try:
        logger.info(f"Uploading PDF from: {TEST_PDF_PATH}")
        logger.debug(f"File exists: {Path(TEST_PDF_PATH).exists()}")
        logger.debug(f"File size: {Path(TEST_PDF_PATH).stat().st_size} bytes")

        # HTML要素をデバッグ
        upload_elements = page.evaluate(
            """
        () => {
            const inputs = document.querySelectorAll('input[type="file"]');
            return Array.from(inputs).map(el => ({
                id: el.id,
                name: el.name,
                class: el.className,
                isVisible: el.offsetParent !== null
            }));
        }
        """
        )
        logger.debug(f"File inputs on page: {upload_elements}")

        file_input = page.locator("input[type='file']").first
        file_input.set_input_files(TEST_PDF_PATH)
        logger.info("File uploaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to upload PDF file: {e}")


@when("the user clicks the extract text button")
def click_extract_text_button(page_with_server: Page):
    """Click extract text button"""
    page = page_with_server

    try:
        # ボタン要素をデバッグ
        button_elements = page.evaluate(
            """
        () => {
            const buttons = Array.from(document.querySelectorAll('button'));
            return buttons.map(btn => ({
                text: btn.textContent,
                isVisible: btn.offsetParent !== null
            }));
        }
        """
        )
        logger.debug(f"Buttons on page: {button_elements}")

        # 柔軟にボタンを検索する
        extract_button = None
        for button in page.locator("button").all():
            text = button.text_content().strip()
            if "テキスト" in text and ("抽出" in text or "Extract" in text):
                extract_button = button
                break

        if extract_button:
            extract_button.click(timeout=2000)  # Reduced from 3000
            logger.info("Extract Text button clicked")
        else:
            raise Exception("Extract button not found")

    except Exception as e:
        logger.error(f"First attempt failed: {e}")
        try:
            # Click directly via JavaScript
            clicked = page.evaluate(
                """
            () => {
                const buttons = Array.from(document.querySelectorAll('button'));
                // より緩やかな検索条件
                const extractButton = buttons.find(
                    b => (b.textContent && (
                          b.textContent.includes('テキスト') ||
                          b.textContent.includes('抽出') ||
                          b.textContent.includes('Extract')
                    ))
                );
                if (extractButton) {
                    extractButton.click();
                    console.log("Button clicked via JS");
                    return true;
                }
                return false;
            }
            """
            )
            if not clicked:
                pytest.fail("テキスト抽出ボタンが見つかりません。ボタンテキストが変更された可能性があります。")
            else:
                logger.info("Extract Text button clicked via JS")
        except Exception as js_e:
            pytest.fail(
                f"Failed to click text extraction button: {e}, JS error: {js_e}"
            )

    # Wait for text extraction to process - reduced wait time
    page.wait_for_timeout(3000)  # Reduced from 5000


@then("the extracted text is displayed")
def verify_extracted_text(page_with_server: Page):
    """Verify extracted text is displayed"""
    page = page_with_server

    # textarea要素をデバッグ
    text_elements = page.evaluate(
        """
    () => {
        const textareas = Array.from(document.querySelectorAll('textarea'));
        return textareas.map(el => ({
            id: el.id,
            value: el.value.substring(0, 100) + (el.value.length > 100 ? "..." : ""),
            length: el.value.length,
            isVisible: el.offsetParent !== null
        }));
    }
    """
    )
    logger.debug(f"Textareas on page: {text_elements}")

    # Get content from textarea
    textareas = page.locator("textarea").all()
    logger.debug(f"Number of textareas found: {len(textareas)}")

    extracted_text = ""

    # デバッグ出力からテキストが2番目のtextarea (index 1)に含まれていることが分かる
    if len(textareas) >= 2:
        extracted_text = textareas[1].input_value()
        logger.debug(f"Second textarea content length: {len(extracted_text)}")
        if extracted_text:
            logger.debug(f"Content preview: {extracted_text[:100]}...")

    # 2番目で見つからなかった場合、すべてのtextareaをチェック
    if not extracted_text:
        for i, textarea in enumerate(textareas):
            content = textarea.input_value()
            if content and len(content) > 100:  # 長いテキストを探す
                extracted_text = content
                logger.debug(
                    f"Found text in textarea {i}, length: {len(extracted_text)}"
                )
                break

    # それでも見つからない場合はJavaScriptで確認
    if not extracted_text or len(extracted_text) < 100:
        extracted_text = page.evaluate(
            """
        () => {
            const textareas = document.querySelectorAll('textarea');
            // 各textareaをチェックして論文内容らしきテキストを探す
            for (let i = 0; i < textareas.length; i++) {
                const text = textareas[i].value;
                if (text && text.length > 100) {
                    return text;
                }
            }
            // 見つからなければ一番長いテキストを返す
            let longestText = '';
            for (let i = 0; i < textareas.length; i++) {
                if (textareas[i].value.length > longestText.length) {
                    longestText = textareas[i].value;
                }
            }
            return longestText;
        }
        """
        )
        logger.debug(f"Extracted via JS, content length: {len(extracted_text)}")

    # Check the text extraction result
    assert extracted_text, "No text was extracted"
    assert (
        len(extracted_text) > 100
    ), "The extracted text is too short to be from the PDF"


@given("text has been extracted from a PDF")
def pdf_text_extracted(page_with_server: Page):
    """Text has been extracted from a PDF"""
    # Upload PDF file
    upload_pdf_file(page_with_server)

    # Extract text
    click_extract_text_button(page_with_server)

    # Verify text was extracted
    verify_extracted_text(page_with_server)
