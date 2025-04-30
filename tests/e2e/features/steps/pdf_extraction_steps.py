"""
File extraction steps for paper podcast e2e tests
"""

from pathlib import Path

import pytest
from playwright.sync_api import Page
from pytest_bdd import given, then, when

from tests.utils.logger import test_logger as logger

from .common_steps import TEST_PDF_PATH, TEST_TEXT_PATH


@when("the user uploads a file")
def upload_file(page_with_server: Page):
    """Upload a file (PDF or text)"""
    page = page_with_server

    try:
        # デフォルトではPDFをアップロード
        test_file_path = TEST_PDF_PATH
        logger.info(f"Uploading file from: {test_file_path}")
        logger.debug(f"File exists: {Path(test_file_path).exists()}")
        logger.debug(f"File size: {Path(test_file_path).stat().st_size} bytes")

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
        file_input.set_input_files(test_file_path)
        logger.info("File uploaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to upload file: {e}")


@when("the user uploads a PDF file")
def upload_pdf_file(page_with_server: Page):
    """Upload PDF file - 後方互換性のために残す"""
    upload_file(page_with_server)


@when("the user uploads a text file")
def upload_text_file(page_with_server: Page):
    """Upload text file"""
    page = page_with_server

    try:
        logger.info(f"Uploading text file from: {TEST_TEXT_PATH}")
        logger.debug(f"File exists: {Path(TEST_TEXT_PATH).exists()}")
        logger.debug(f"File size: {Path(TEST_TEXT_PATH).stat().st_size} bytes")

        file_input = page.locator("input[type='file']").first
        file_input.set_input_files(TEST_TEXT_PATH)
        logger.info("Text file uploaded successfully")
    except Exception as e:
        pytest.fail(f"Failed to upload text file: {e}")


@when("the user clicks the extract text button")
def click_extract_text_button(page_with_server: Page):
    """Click the extract text button"""
    page = page_with_server

    try:
        # ID属性がない場合、テキストコンテンツで検索
        extract_button = page.get_by_role("button", name="テキストを抽出")
        extract_button.click()
        logger.info("Extract text button clicked")

        # テキスト抽出が完了するまで待機
        # extracted_textが表示されるまで待機する代わりに、ボタンクリック後に待機
        page.wait_for_timeout(2000)  # 2秒待機
    except Exception as e:
        pytest.fail(f"Failed to click extract text button: {e}")


@then("the extracted text is displayed")
def verify_extracted_text(page_with_server: Page):
    """Verify extracted text is displayed"""
    page = page_with_server

    try:
        logger.info("Verifying extracted text...")

        # テキストエリアの内容を取得
        # CSSセレクタでテキストエリアを特定
        extracted_text = ""

        # textareaエレメントを探す
        textarea_locators = [
            "textarea",
            '[data-testid="textbox"]',
            '[placeholder*="テキスト"]',
            '[placeholder*="text"]',
        ]

        for selector in textarea_locators:
            try:
                all_textareas = page.locator(selector).all()
                if len(all_textareas) == 0:
                    continue

                # 最初のテキストエリアまたは特定の条件に合うテキストエリアを選択
                for textarea in all_textareas:
                    # 値を取得して確認
                    content = textarea.input_value()
                    if content and len(content) > 10:  # 有意な内容があるかチェック
                        extracted_text = content
                        logger.debug(
                            f"Found text area with content: {content[:100]}..."
                        )
                        break

                if extracted_text:
                    break
            except Exception as e:
                logger.debug(f"Error finding text area with selector {selector}: {e}")
                continue

        # それでも見つからない場合はJavaScriptで確認
        if not extracted_text or len(extracted_text) < 100:
            extracted_text = page.evaluate(
                """
            () => {
                const textareas = document.querySelectorAll('textarea');
                // 各textareaをチェックして内容らしきテキストを探す
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
        ), "The extracted text is too short to be meaningful"

        logger.info(
            f"Extracted text verified (length: {len(extracted_text)}, sample: {extracted_text[:100]}...)"
        )

    except Exception as e:
        pytest.fail(f"Failed to verify extracted text: {e}")


@given("text has been extracted from a file")
def file_text_extracted(page_with_server: Page):
    """Text has been extracted from a file"""
    # Upload file
    upload_file(page_with_server)

    # Extract text
    click_extract_text_button(page_with_server)

    # Verify text was extracted
    verify_extracted_text(page_with_server)


@given("text has been extracted from a PDF")
def pdf_text_extracted(page_with_server: Page):
    """Text has been extracted from a PDF - 後方互換性のために残す"""
    file_text_extracted(page_with_server)


@when("the user edits the extracted text")
def edit_extracted_text(page_with_server: Page):
    """ユーザーが抽出されたテキストを編集する"""
    page = page_with_server

    try:
        logger.info("Editing the extracted text...")

        # 抽出テキストのテキストエリアを見つける - 無効なテキストエリアをスキップ
        textarea = None

        # まず最も長いテキストを含むtextareaを探す（それが抽出されたテキストの可能性が高い）
        textarea_content = page.evaluate(
            """
            () => {
                const textareas = document.querySelectorAll('textarea');
                let longestText = '';
                let longestIndex = -1;

                for (let i = 0; i < textareas.length; i++) {
                    // 無効なtextareaはスキップ
                    if (textareas[i].disabled) {
                        continue;
                    }

                    const text = textareas[i].value;
                    if (text && text.length > longestText.length) {
                        longestText = text;
                        longestIndex = i;
                    }
                }

                return {
                    text: longestText,
                    index: longestIndex,
                    count: textareas.length
                };
            }
            """
        )

        logger.info(
            f"Found {textarea_content['count']} textareas, longest at index {textarea_content['index']}"
        )

        if textarea_content["index"] < 0:
            pytest.fail("Could not find any enabled textarea with content")

        # インデックスに基づいてtextareaを選択
        all_textareas = page.locator("textarea").all()
        textarea = all_textareas[textarea_content["index"]]

        # テキストを編集 - 冒頭に編集されたことを示すテキストを追加
        edited_text = "【編集済み】\n" + textarea_content["text"]

        # テキストエリアに直接入力
        textarea.fill(edited_text)

        # 編集されたことを確認
        updated_text = textarea.input_value()
        assert "【編集済み】" in updated_text, "Text was not edited correctly"
        logger.info("Successfully edited the extracted text")

    except Exception as e:
        logger.error(f"Error editing extracted text: {e}")
        pytest.fail(f"Failed to edit extracted text: {e}")
