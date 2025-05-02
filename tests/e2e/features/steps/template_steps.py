"""
Template management test steps
"""

import re
import time

from playwright.sync_api import Page, expect
from pytest_bdd import given, then, when

from tests.utils.logger import test_logger as logger

# テンプレート設定領域のセレクタ
TEMPLATE_SETTINGS_BUTTON = "#templatesettings-button"
TEMPLATE_SETTINGS_PANEL = "#templatesettings-panel"
TEMPLATE_DROPDOWN = "#template-dropdown"
CUSTOM_TEMPLATE_TEXTAREA = "#custom-template-textarea"
SAVE_TEMPLATE_BUTTON = "#save-template-button"
RESET_TEMPLATE_BUTTON = "#reset-template-button"
TEMPLATE_ERROR_MESSAGE = "#template-error-message"

# テストで使用するカスタムテンプレート
CUSTOM_TEMPLATE = """
Character1: こんにちは、今日は「{{ paper_text }}」について話します。
Character2: わかりました、詳しく説明しましょう。
"""

# 無効なテンプレート（Jinja2構文エラーを含む）
INVALID_TEMPLATE = """
Character1: こんにちは、今日は「{{ paper_text }」について話します。
Character2: わかりました、詳しく説明しましょう。
"""


@when("the user opens the template settings")
def open_template_settings(page: Page):
    """テンプレート設定を開く"""
    logger.info("テンプレート設定を開きます")

    # テンプレート設定ボタンの存在を確認
    expect(page.locator(TEMPLATE_SETTINGS_BUTTON)).to_be_visible(timeout=10000)

    # テンプレート設定ボタンをクリック
    page.click(TEMPLATE_SETTINGS_BUTTON)

    # テンプレート設定パネルが表示されるまで待機
    expect(page.locator(TEMPLATE_SETTINGS_PANEL)).to_be_visible(timeout=5000)


@when('the user selects the "{template_name}" template')
def select_template(page: Page, template_name: str):
    """指定されたテンプレートを選択する"""
    logger.info(f"テンプレート '{template_name}' を選択します")

    # テンプレートドロップダウンを開く
    page.click(TEMPLATE_DROPDOWN)

    # 指定されたテンプレートを選択
    page.select_option(TEMPLATE_DROPDOWN, template_name)

    # 正しく選択されていることを確認
    expect(page.locator(f"{TEMPLATE_DROPDOWN} option:checked")).to_have_text(
        template_name
    )


@when("the user enters a custom template")
def enter_custom_template(page: Page):
    """カスタムテンプレートを入力する"""
    logger.info("カスタムテンプレートを入力します")

    # カスタムテンプレートテキストエリアが表示されるまで待機
    expect(page.locator(CUSTOM_TEMPLATE_TEXTAREA)).to_be_visible(timeout=5000)

    # カスタムテンプレートテキストエリアをクリア
    page.click(CUSTOM_TEMPLATE_TEXTAREA)
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")

    # カスタムテンプレートを入力
    page.fill(CUSTOM_TEMPLATE_TEXTAREA, CUSTOM_TEMPLATE)

    # 入力されていることを確認
    expect(page.locator(CUSTOM_TEMPLATE_TEXTAREA)).to_have_value(CUSTOM_TEMPLATE)


@when("the user enters an invalid template")
def enter_invalid_template(page: Page):
    """無効なテンプレートを入力する"""
    logger.info("無効なテンプレートを入力します")

    # カスタムテンプレートテキストエリアをクリア
    page.click(CUSTOM_TEMPLATE_TEXTAREA)
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")

    # 無効なテンプレートを入力
    page.fill(CUSTOM_TEMPLATE_TEXTAREA, INVALID_TEMPLATE)

    # 入力されていることを確認
    expect(page.locator(CUSTOM_TEMPLATE_TEXTAREA)).to_have_value(INVALID_TEMPLATE)


@when("the user saves the template settings")
def save_template_settings(page: Page):
    """テンプレート設定を保存する"""
    logger.info("テンプレート設定を保存します")

    # 保存ボタンをクリック
    page.click(SAVE_TEMPLATE_BUTTON)

    # 保存後に少し待機
    time.sleep(1)


@when("the user tries to save the template settings")
def try_save_template_settings(page: Page):
    """テンプレート設定の保存を試みる"""
    logger.info("テンプレート設定の保存を試みます")

    # 保存ボタンをクリック
    page.click(SAVE_TEMPLATE_BUTTON)

    # エラーメッセージが表示されるまで待機
    time.sleep(1)


@when("the user clicks the reset template button")
def click_reset_template(page: Page):
    """テンプレートリセットボタンをクリックする"""
    logger.info("テンプレートをリセットします")

    # リセットボタンをクリック
    page.click(RESET_TEMPLATE_BUTTON)

    # リセット後に少し待機
    time.sleep(1)


@given("a custom template has been applied")
def custom_template_applied(page: Page):
    """カスタムテンプレートが適用された状態にする"""
    # テンプレート設定を開く
    open_template_settings(page)

    # カスタムテンプレートを入力
    enter_custom_template(page)

    # テンプレート設定を保存
    save_template_settings(page)

    logger.info("カスタムテンプレートが適用されました")


@given("the user has a custom template")
def user_has_custom_template(page: Page):
    """ユーザーがカスタムテンプレートを持っている状態にする"""
    # カスタムテンプレートを入力
    enter_custom_template(page)

    # 入力されていることを確認
    expect(page.locator(CUSTOM_TEMPLATE_TEXTAREA)).to_have_value(CUSTOM_TEMPLATE)

    logger.info("ユーザーがカスタムテンプレートを持っています")


@then("the selected template is applied")
def template_is_applied(page: Page):
    """選択したテンプレートが適用されていることを確認する"""
    logger.info("選択したテンプレートが適用されていることを確認します")

    # テンプレート設定が適用されているかを確認するため、
    # テンプレート設定パネルを開き直す
    time.sleep(1)
    if not page.is_visible(TEMPLATE_SETTINGS_PANEL):
        page.click(TEMPLATE_SETTINGS_BUTTON)

    # 選択したテンプレートがドロップダウンで選択されていることを確認
    selected_option = page.locator(f"{TEMPLATE_DROPDOWN} option:checked").text_content()
    assert (
        selected_option == "technical.j2"
    ), f"期待値: technical.j2, 実際: {selected_option}"

    logger.info("テンプレートが正しく適用されています")


@then("the custom template is applied")
def custom_template_is_applied(page: Page):
    """カスタムテンプレートが適用されていることを確認する"""
    logger.info("カスタムテンプレートが適用されていることを確認します")

    # テンプレート設定が適用されているかを確認するため、
    # テンプレート設定パネルを開き直す
    time.sleep(1)
    if not page.is_visible(TEMPLATE_SETTINGS_PANEL):
        page.click(TEMPLATE_SETTINGS_BUTTON)

    # カスタムテンプレートがテキストエリアに表示されていることを確認
    textarea_content = page.locator(CUSTOM_TEMPLATE_TEXTAREA).input_value()
    assert (
        CUSTOM_TEMPLATE in textarea_content
    ), f"期待値: {CUSTOM_TEMPLATE}, 実際: {textarea_content}"

    logger.info("カスタムテンプレートが正しく適用されています")


@then("podcast-style text is generated using the custom template")
def podcast_text_with_custom_template(page: Page):
    """カスタムテンプレートを使用してポッドキャストテキストが生成されていることを確認する"""
    # ポッドキャストテキストが生成されていることを確認
    output_area = page.locator("#podcast-output-textarea").input_value()
    assert len(output_area) > 0, "ポッドキャストテキストが生成されていません"

    # カスタムテンプレートのパターンが含まれていることを確認
    character1_pattern = r"(Character1|ずんだもん)[:：]"
    character2_pattern = r"(Character2|四国めたん)[:：]"

    assert (
        re.search(character1_pattern, output_area) is not None
    ), "Character1のパターンが見つかりません"
    assert (
        re.search(character2_pattern, output_area) is not None
    ), "Character2のパターンが見つかりません"

    logger.info("カスタムテンプレートを使用してポッドキャストテキストが生成されました")


@then("the default template is restored")
def default_template_restored(page: Page):
    """デフォルトテンプレートが復元されていることを確認する"""
    logger.info("デフォルトテンプレートが復元されていることを確認します")

    # テンプレート設定が適用されているかを確認するため、
    # テンプレート設定パネルを開き直す
    time.sleep(1)
    if not page.is_visible(TEMPLATE_SETTINGS_PANEL):
        page.click(TEMPLATE_SETTINGS_BUTTON)

    # デフォルトテンプレートが選択されていることを確認
    selected_option = page.locator(f"{TEMPLATE_DROPDOWN} option:checked").text_content()
    assert selected_option == "default.j2", f"期待値: default.j2, 実際: {selected_option}"

    # カスタムテンプレートがクリアされていることを確認
    textarea_content = page.locator(CUSTOM_TEMPLATE_TEXTAREA).input_value()
    assert (
        CUSTOM_TEMPLATE not in textarea_content
    ), f"カスタムテンプレートがクリアされていません: {textarea_content}"

    logger.info("デフォルトテンプレートが正しく復元されています")


@then("an error message about invalid template is displayed")
def error_message_displayed(page: Page):
    """無効なテンプレートに関するエラーメッセージが表示されていることを確認する"""
    logger.info("エラーメッセージが表示されていることを確認します")

    # エラーメッセージが表示されていることを確認
    expect(page.locator(TEMPLATE_ERROR_MESSAGE)).to_be_visible(timeout=5000)

    error_text = page.locator(TEMPLATE_ERROR_MESSAGE).text_content() or ""
    assert (
        "error" in error_text.lower() or "エラー" in error_text
    ), f"エラーメッセージが正しくありません: {error_text}"

    logger.info(f"エラーメッセージが表示されています: {error_text}")
