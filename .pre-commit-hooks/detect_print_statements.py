#!/usr/bin/env python3
"""
Pre-commit hook that detects print statements in Python files.
"""

import ast
import logging
import os
import sys
from typing import List, Optional, Tuple

# 簡単なロガーを設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("detect_print")


def is_excluded_path(file_path: str) -> bool:
    """
    Check if a file should be excluded from print statement detection.

    Args:
        file_path (str): Path to the file to check

    Returns:
        bool: True if the file should be excluded, False otherwise
    """
    # 除外するパス
    excluded_paths = [
        # このスクリプト自体
        "detect_print_statements.py",
        # テスト用のprintが含まれるファイル
        "tests/fixtures/",
        # サードパーティライブラリ
        "venv/",
        # テスト用の特定のファイル
        "tests/conftest.py",
    ]

    # ファイル名
    normalized_path = os.path.normpath(file_path)

    # 特定のパスを除外
    return any(excluded_path in normalized_path for excluded_path in excluded_paths)


class PrintFinder(ast.NodeVisitor):
    """AST visitor to find print statements in Python code."""

    def __init__(self):
        self.print_calls: List[Tuple[int, str]] = []

    def visit_Call(self, node):
        """Visit a call node and check if it's a print call."""
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            lineno = getattr(node, "lineno", 0)

            # 可能であれば、print呼び出しの引数を取得
            call_args = []
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    call_args.append(repr(arg.value))
                else:
                    call_args.append("...")

            call_desc = f"print({', '.join(call_args)})"
            self.print_calls.append((lineno, call_desc))

        # Continue visiting child nodes
        self.generic_visit(node)


def check_file(file_path: str) -> List[Tuple[int, str]]:
    """
    Check a Python file for print statements.

    Args:
        file_path (str): Path to the Python file to check

    Returns:
        List[Tuple[int, str]]: List of (line_number, print_call) tuples
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        visitor = PrintFinder()
        visitor.visit(tree)
        return visitor.print_calls

    except SyntaxError:
        logger.error(f"Syntax error in {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return []


def get_python_files(directory: str) -> List[str]:
    """
    再帰的にディレクトリをスキャンしてPythonファイルを見つける

    Args:
        directory (str): スキャンするディレクトリパス

    Returns:
        List[str]: 見つかったPythonファイルのリスト
    """
    python_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if not is_excluded_path(file_path):
                    python_files.append(file_path)

    return python_files


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main function for the pre-commit hook.

    Args:
        argv: Command line arguments (file paths to check)

    Returns:
        int: 0 if no print statements were found, 1 otherwise
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        logger.info("No files to check")
        return 0

    # 処理するファイルのリスト
    files_to_check = []

    # 引数からファイルとディレクトリを処理
    for path in argv:
        if os.path.isdir(path):
            # ディレクトリの場合、再帰的にPythonファイルを検索
            files_to_check.extend(get_python_files(path))
        elif path.endswith(".py") and not is_excluded_path(path):
            # 単一のPythonファイルの場合
            files_to_check.append(path)

    found_prints = False
    for file_path in files_to_check:
        print_calls = check_file(file_path)
        if print_calls:
            found_prints = True
            logger.error(f"Found {len(print_calls)} print statement(s) in {file_path}:")
            for lineno, call_desc in print_calls:
                logger.error(f"  Line {lineno}: {call_desc}")
            logger.error(f"Please use logger instead of print in {file_path}")

    return 1 if found_prints else 0


if __name__ == "__main__":
    sys.exit(main())
