"""
依存関係のインストール状態を確認するテスト。
CIでの依存関係インストールの問題を検出するために使用します。
"""

import importlib
import sys
from typing import List, Tuple


def test_critical_dependencies():
    """
    重要な依存関係がインストールされていることを確認します。
    これらはアプリケーションの実行に必要不可欠なモジュールです。
    """
    critical_modules = [
        "gradio",
        "numpy",
        "torch",
        "transformers",
        "huggingface_hub",
        "httpx",
        "openai",
        "ffmpeg_python",
        "onnxruntime",
    ]

    missing_modules: List[str] = []
    error_modules: List[Tuple[str, Exception]] = []

    for module_name in critical_modules:
        try:
            importlib.import_module(module_name)
            # 正常にインポートできた場合はバージョンを表示
            module = sys.modules[module_name]
            version = getattr(module, "__version__", "不明")
            print(f"✓ {module_name} (version: {version})")
        except ImportError as e:
            missing_modules.append(module_name)
            error_modules.append((module_name, e))
            print(f"✗ {module_name} - インポートできませんでした")
        except Exception as e:
            error_modules.append((module_name, e))
            print(f"! {module_name} - エラーが発生しました: {e}")

    # エラーメッセージの表示
    if missing_modules:
        missing_list = ", ".join(missing_modules)
        error_details = "\n".join([f"{m}: {str(e)}" for m, e in error_modules])

        error_message = f"""
        以下のモジュールがインストールされていないか、インポート中にエラーが発生しました:
        {missing_list}

        エラーの詳細:
        {error_details}

        解決策:
        1. 仮想環境がアクティブであることを確認してください
        2. `pip install -r requirements.txt` を実行して依存関係をインストールしてください
        3. 特定のモジュールで問題が続く場合は、個別に `pip install <module_name>` を試してください
        """
        assert not missing_modules, error_message
