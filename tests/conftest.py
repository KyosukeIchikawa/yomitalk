"""
Pytestのconftest.pyファイル

このファイルはPytestの実行時に自動的にロードされ、
パスの設定などのグローバルな初期設定を行います。
"""

import os
import sys

import pytest

# プロジェクトのルートパスをPYTHONPATHに追加
# conftest.pyの場所から2階層上がルートディレクトリ
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)


@pytest.fixture
def test_templates_dir():
    """テスト用のテンプレートディレクトリのパスを返します。"""
    return os.path.join(root_dir, "tests", "test_templates")
