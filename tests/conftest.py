"""pytest設定ファイル。

マーカーの定義などpytestの設定を行います。
"""


# マーカーの定義
def pytest_configure(config):
    """
    pytestの設定

    Args:
        config: pytestの設定オブジェクト
    """
    config.addinivalue_line("markers", "slow: 実行に時間がかかるテストをマーク")
    config.addinivalue_line("markers", "api: 外部APIを使用するテストをマーク")
    config.addinivalue_line("markers", "voicevox: VOICEVOXを使用するテストをマーク")
