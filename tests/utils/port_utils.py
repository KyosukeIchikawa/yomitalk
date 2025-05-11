import socket
from contextlib import closing


def find_free_port(base_port=8000, max_attempts=100):
    """空いているTCPポートを見つける。

    Args:
        base_port (int, optional): 検索を始めるポート番号. デフォルトは8000.
        max_attempts (int, optional): 試行する最大回数. デフォルトは100.

    Returns:
        int: 利用可能なポート番号
    """
    port = base_port
    attempts = 0

    while attempts < max_attempts:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            try:
                sock.bind(("localhost", port))
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return port
            except OSError:
                # ポートが使用中の場合
                port += 1
                attempts += 1

    # 空きポートが見つからない場合
    raise RuntimeError(
        f"利用可能なポートが見つかりませんでした (試行: {base_port}〜{base_port+max_attempts-1})"
    )
