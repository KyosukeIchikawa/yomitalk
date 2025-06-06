"""Test session cleanup functionality."""

import os
import shutil
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from yomitalk.user_session import UserSession


class TestSessionCleanup:
    """Test session cleanup functionality."""

    @pytest.fixture
    def setup_test_dirs(self):
        """Set up test directories."""
        # テスト用の一時ディレクトリを作成
        test_temp_dir = Path("tests/data/temp")
        test_output_dir = Path("tests/data/output")

        # テスト前に一度クリーンアップ
        if test_temp_dir.exists():
            shutil.rmtree(test_temp_dir)
        if test_output_dir.exists():
            shutil.rmtree(test_output_dir)

        # ディレクトリ作成
        test_temp_dir.mkdir(parents=True, exist_ok=True)
        test_output_dir.mkdir(parents=True, exist_ok=True)

        yield test_temp_dir, test_output_dir

        # テスト後のクリーンアップ
        if test_temp_dir.exists():
            shutil.rmtree(test_temp_dir)
        if test_output_dir.exists():
            shutil.rmtree(test_output_dir)

    def test_cleanup_old_sessions(self, setup_test_dirs):
        """Test cleanup_old_sessions method."""
        test_temp_dir, test_output_dir = setup_test_dirs

        # UserSessionのインスタンスを作成し、テスト用のディレクトリを設定
        user_session = UserSession("test_session_cleanup")

        # グローバル変数をパッチしてテスト用ディレクトリを使用
        with patch("yomitalk.session.BASE_TEMP_DIR", test_temp_dir), patch(
            "yomitalk.session.BASE_OUTPUT_DIR", test_output_dir
        ):
            # 現在の時刻を取得
            current_time = int(time.time())

            # テスト用のセッションディレクトリを作成
            # 1. セッションディレクトリ (更新日時を2日前に設定)
            old_session_id = "session_old_test1"
            old_temp_dir = test_temp_dir / old_session_id
            old_output_dir = test_output_dir / old_session_id
            old_temp_dir.mkdir(parents=True)
            old_output_dir.mkdir(parents=True)

            # 更新日時を2日前に設定
            two_days_ago = current_time - 172800
            os.utime(old_temp_dir, (two_days_ago, two_days_ago))
            os.utime(old_output_dir, (two_days_ago, two_days_ago))

            # 2. セッションディレクトリ (更新日時を12時間前に設定)
            semi_old_session_id = "session_semi_old_test2"
            semi_old_temp_dir = test_temp_dir / semi_old_session_id
            semi_old_output_dir = test_output_dir / semi_old_session_id
            semi_old_temp_dir.mkdir(parents=True)
            semi_old_output_dir.mkdir(parents=True)

            # 更新日時を12時間前に設定
            twelve_hours_ago = current_time - 43200
            os.utime(semi_old_temp_dir, (twelve_hours_ago, twelve_hours_ago))
            os.utime(semi_old_output_dir, (twelve_hours_ago, twelve_hours_ago))

            # 3. セッションディレクトリ (更新日時を1時間前に設定)
            recent_session_id = "session_recent_test3"
            recent_temp_dir = test_temp_dir / recent_session_id
            recent_output_dir = test_output_dir / recent_session_id
            recent_temp_dir.mkdir(parents=True)
            recent_output_dir.mkdir(parents=True)

            # 更新日時を1時間前に設定
            one_hour_ago = current_time - 3600
            os.utime(recent_temp_dir, (one_hour_ago, one_hour_ago))
            os.utime(recent_output_dir, (one_hour_ago, one_hour_ago))

            # 4. 無効な名前のディレクトリ (処理対象外)
            invalid_dir_name = "invalid_directory"
            invalid_temp_dir = test_temp_dir / invalid_dir_name
            invalid_output_dir = test_output_dir / invalid_dir_name
            invalid_temp_dir.mkdir(parents=True)
            invalid_output_dir.mkdir(parents=True)

            # 更新日時を2日前に設定 (セッションディレクトリではないので削除されない)
            os.utime(invalid_temp_dir, (two_days_ago, two_days_ago))
            os.utime(invalid_output_dir, (two_days_ago, two_days_ago))

            # 明示的にcleanupメソッドを呼び出す
            user_session.cleanup_old_sessions()

            # 残っているディレクトリを確認
            remaining_temp_dirs = [d.name for d in test_temp_dir.iterdir()]
            remaining_output_dirs = [d.name for d in test_output_dir.iterdir()]

            # 2日前のセッションが削除されていることを確認
            assert old_session_id not in remaining_temp_dirs
            assert old_session_id not in remaining_output_dirs

            # 12時間前のセッションも削除されていないことを確認（1日より新しいため）
            assert semi_old_session_id in remaining_temp_dirs
            assert semi_old_session_id in remaining_output_dirs

            # 1時間前のセッションは残っていることを確認
            assert recent_session_id in remaining_temp_dirs
            assert recent_session_id in remaining_output_dirs

            # 無効な名前のディレクトリは残っていることを確認（セッションディレクトリではないため）
            assert invalid_dir_name in remaining_temp_dirs
            assert invalid_dir_name in remaining_output_dirs

    def test_get_folder_modification_time(self):
        """Test _get_folder_modification_time method."""
        user_session = UserSession("test_session_modtime")

        # テスト用のディレクトリを作成
        test_dir = Path("tests/data/test_mod_time")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir(parents=True)

        try:
            # 現在の更新日時を取得
            mod_time = user_session._get_folder_modification_time(test_dir)
            assert mod_time > 0

            # 存在しないディレクトリの場合は0を返す
            assert (
                user_session._get_folder_modification_time(Path("non_existent_dir"))
                == 0
            )

        finally:
            # クリーンアップ
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_cleanup_directory(self):
        """Test _cleanup_directory method."""
        test_dir = Path("tests/data/temp_cleanup_test")
        if test_dir.exists():
            shutil.rmtree(test_dir)
        test_dir.mkdir(parents=True, exist_ok=True)

        try:
            user_session = UserSession("test_session_cleanup_dir")
            current_time = int(time.time())

            # テスト用のセッションディレクトリを作成
            # 1. 古いセッション (削除対象)
            old_session_id = "session_old_test"
            old_dir = test_dir / old_session_id
            old_dir.mkdir(parents=True)

            # 更新日時を2日前に設定
            two_days_ago = current_time - 172800
            os.utime(old_dir, (two_days_ago, two_days_ago))

            # 2. 現在のセッション (保持対象)
            current_session_id = "session_current_test"
            current_dir = test_dir / current_session_id
            current_dir.mkdir(parents=True)
            # 現在の時刻のままにしておく

            # 3. 無効なディレクトリ名 (処理対象外)
            invalid_dir_name = "invalid_directory"
            invalid_dir = test_dir / invalid_dir_name
            invalid_dir.mkdir(parents=True)

            # 更新日時を2日前に設定（セッション名でないので削除されないはず）
            os.utime(invalid_dir, (two_days_ago, two_days_ago))

            # クリーンアップを実行（1日以上前を削除）
            removed = user_session._cleanup_directory(test_dir, current_time, 86400)

            # 削除されるべきディレクトリ数を確認
            assert removed == 1

            # 残っているディレクトリを確認
            remaining_dirs = [d.name for d in test_dir.iterdir()]
            assert old_session_id not in remaining_dirs
            assert current_session_id in remaining_dirs
            assert invalid_dir_name in remaining_dirs

        finally:
            # クリーンアップ
            if test_dir.exists():
                shutil.rmtree(test_dir)
