#!/usr/bin/env python3
import os
import re
import sys
from typing import List, Optional, Pattern


def get_token_patterns() -> List[Pattern]:
    """
    カスタムトークンパターンの正規表現リストを返します
    必要に応じてここにパターンを追加してください
    """
    return [
        # 40文字以上の英数字とダッシュ/アンダースコア（一般的なAPIキーやトークン）
        # コードコメントやインポートパスなど一般的な文字列を除外
        re.compile(r"(?<![a-zA-Z0-9/_.-])[a-zA-Z0-9_-]{40,}(?![a-zA-Z0-9/_.-])"),
        # 引用符で囲まれた30文字以上の英数字（変数に格納されたトークン）
        # コンポーネントパスやインポートパスを除外
        re.compile(
            r'["\'](?!(?:app\.component|tests\/|app\.model|dict\/open|[-_a-zA-Z0-9\/\.]{0,20}\/[-_a-zA-Z0-9\/\.]{0,20}|libvoicevox_onnxruntime\.so\.|sk-test))[a-zA-Z0-9_\-\.=+/]{30,}["\']'
        ),
        # 環境変数風のトークン
        re.compile(
            r'(?:api_key|token|secret|password|credential|auth)[\s]*=[\s]*["\']?(?!test|sk-test)[a-zA-Z0-9_\-\.=+/]{16,}["\']?',
            re.IGNORECASE,
        ),
        # JWTトークン
        re.compile(r"eyJ[a-zA-Z0-9_-]{5,}\.eyJ[a-zA-Z0-9_-]{5,}\.[a-zA-Z0-9_-]{5,}"),
        # Base64のような文字列（終わりに=が0-2個ある）
        # 行区切りやコメント区切りなどのパターンを除外
        re.compile(
            r"(?<![- _=])(?<!-{10})(?!sk-test)[a-zA-Z0-9+/]{30,}={0,2}(?![-_=])"
        ),
        # ハッシュ値らしき文字列（MD5, SHA等）
        re.compile(r"(?<![a-zA-Z0-9-])([a-f0-9]{32})(?![a-zA-Z0-9-])"),  # MD5
        re.compile(r"(?<![a-zA-Z0-9-])([a-f0-9]{40})(?![a-zA-Z0-9-])"),  # SHA-1
        re.compile(r"(?<![a-zA-Z0-9-])([a-f0-9]{64})(?![a-zA-Z0-9-])"),  # SHA-256
        # 特定のサービスのパターン（依存はしないが知っていれば検出）
        # テストキーは除外
        re.compile(r"sk-(?!test)[a-zA-Z0-9]{20,}"),  # OpenAI（テストキーを除外）
        re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS
    ]


def is_excluded_path(file_path: str) -> bool:
    """
    特定のパスを検査から除外するかどうかを判断します
    """
    # バイナリファイルは処理できないので除外
    excluded_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".pdf",
        ".bin",
        ".exe",
        ".dll",
        ".so",
        ".pyc",
        ".pyo",
        ".class",
        ".jar",
        ".zip",
        ".tar",
        ".gz",
    ]

    # 除外するパス
    excluded_paths = [
        # 自身のテストファイル
        "tests/unit/test_detect_custom_tokens.py",
        # このスクリプト自体
        "detect_custom_tokens.py",
    ]

    # ファイル名
    filename = os.path.basename(file_path)

    # バイナリファイルを除外
    if any(filename.lower().endswith(ext) for ext in excluded_extensions):
        return True

    # 特定のパスを除外
    normalized_path = os.path.normpath(file_path)
    for excluded_path in excluded_paths:
        if excluded_path in normalized_path:
            return True

    return False


def check_file(file_path: str) -> bool:
    """
    指定されたファイルをチェックし、トークンパターンが見つかったらTrueを返します
    """
    # 除外パスのチェック
    if is_excluded_path(file_path):
        return False

    patterns = get_token_patterns()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        for i, pattern in enumerate(patterns):
            matches = pattern.findall(content)
            if matches:
                # テストデータやサンプルデータの検出を避ける
                is_test_data = False

                # シンプルな文字列の場合はリストまたは文字列として返される
                match_str = matches[0]
                if isinstance(match_str, tuple) and len(match_str) > 0:
                    match_str = match_str[0]

                # テストデータの一般的なパターン
                test_patterns = ["test", "example", "sample", "dummy", "sk-test"]
                if any(test in str(match_str).lower() for test in test_patterns):
                    is_test_data = True

                # ハイフンまたはアンダースコアが連続するパターン (区切り線)
                if re.search(r"[-_]{10,}", str(match_str)):
                    is_test_data = True

                # ライブラリパスとバージョン番号
                if "libvoicevox_onnxruntime.so" in str(match_str):
                    is_test_data = True

                # 特定のパターンのトークン（テスト用）
                if "123456789" in str(match_str) and file_path.endswith(
                    "paper_podcast_steps.py"
                ):
                    is_test_data = True

                if not is_test_data:
                    print(f"ERROR: Found potential token in {file_path}")
                    print(f"Pattern #{i+1} matched: {str(match_str)[:10]}...")
                    return True

        return False
    except UnicodeDecodeError:
        # バイナリファイルなどはスキップ
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print("No files to check")
        return 0

    found_tokens = False
    for file_path in argv:
        if check_file(file_path):
            found_tokens = True

    return 1 if found_tokens else 0


if __name__ == "__main__":
    sys.exit(main())
