#!/usr/bin/env python3
"""
テンプレートディレクトリ整理スクリプト

このスクリプトは、プロジェクト内のテンプレートディレクトリを整理します。
ルートディレクトリの templates/prompts/ 内のテンプレートを
app/templates/prompts/ に移動し、重複を解決します。
"""

import os
import shutil
import sys
from typing import List, Tuple

from app.utils.logger import logger


def setup_paths() -> Tuple[str, str, str]:
    """パスを設定します。"""
    # プロジェクトルートディレクトリを取得
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 各テンプレートディレクトリのパスを設定
    old_templates_dir = os.path.join(root_dir, "templates", "prompts")
    app_templates_dir = os.path.join(root_dir, "app", "templates", "prompts")
    test_templates_dir = os.path.join(root_dir, "tests", "test_templates", "prompts")

    return old_templates_dir, app_templates_dir, test_templates_dir


def list_templates(directory: str) -> List[str]:
    """ディレクトリ内のテンプレートファイル一覧を取得します。"""
    if not os.path.exists(directory):
        return []

    return [f for f in os.listdir(directory) if f.endswith(".j2")]


def backup_old_templates(old_templates_dir: str) -> str:
    """古いテンプレートディレクトリをバックアップします。"""
    if not os.path.exists(old_templates_dir):
        logger.info(f"古いテンプレートディレクトリが存在しません: {old_templates_dir}")
        return ""

    backup_dir = f"{old_templates_dir}_backup"
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)

    shutil.copytree(old_templates_dir, backup_dir)
    logger.info(f"古いテンプレートをバックアップしました: {backup_dir}")
    return backup_dir


def move_templates(
    old_templates_dir: str, app_templates_dir: str, test_templates_dir: str
) -> None:
    """テンプレートを適切なディレクトリに移動します。"""
    if not os.path.exists(old_templates_dir):
        logger.info(f"古いテンプレートディレクトリが存在しません: {old_templates_dir}")
        return

    # ディレクトリが存在することを確認
    os.makedirs(app_templates_dir, exist_ok=True)
    os.makedirs(test_templates_dir, exist_ok=True)

    old_templates = list_templates(old_templates_dir)

    # 既存のテンプレートと新規テンプレートを分類
    for template in old_templates:
        src_path = os.path.join(old_templates_dir, template)

        # テスト用テンプレートはテストディレクトリに移動
        if template.startswith("test_"):
            dst_path = os.path.join(test_templates_dir, template)
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
                logger.info(f"テストテンプレートをコピーしました: {template} -> {test_templates_dir}")
        else:
            # 通常のテンプレートはアプリディレクトリに移動（存在しない場合のみ）
            dst_path = os.path.join(app_templates_dir, template)
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
                logger.info(f"通常テンプレートをコピーしました: {template} -> {app_templates_dir}")
            else:
                logger.info(f"テンプレートは既に存在します: {dst_path}")


def cleanup_old_templates(old_templates_dir: str) -> None:
    """古いテンプレートディレクトリを削除します。"""
    if not os.path.exists(old_templates_dir):
        return

    # テンプレートディレクトリを削除
    parent_dir = os.path.dirname(old_templates_dir)
    if len(os.listdir(old_templates_dir)) == 0:
        os.rmdir(old_templates_dir)
        logger.info(f"空のテンプレートディレクトリを削除しました: {old_templates_dir}")

        # 親ディレクトリも空なら削除
        if os.path.exists(parent_dir) and len(os.listdir(parent_dir)) == 0:
            os.rmdir(parent_dir)
            logger.info(f"空の親ディレクトリを削除しました: {parent_dir}")


def main() -> int:
    """メイン処理"""
    logger.info("テンプレートディレクトリ整理スクリプトを実行します...")

    # パスの設定
    old_templates_dir, app_templates_dir, test_templates_dir = setup_paths()

    # 古いテンプレートのバックアップ
    backup_dir = backup_old_templates(old_templates_dir)
    if not backup_dir:
        logger.error("バックアップ作成に失敗しました。処理を中止します。")
        return 1

    # テンプレートの移動
    move_templates(old_templates_dir, app_templates_dir, test_templates_dir)

    # 古いテンプレートディレクトリの削除
    cleanup_old_templates(old_templates_dir)

    logger.info("テンプレートディレクトリの整理が完了しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
