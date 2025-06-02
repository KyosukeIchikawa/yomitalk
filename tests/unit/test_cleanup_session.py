"""Unit tests for session cleanup functionality."""

import shutil

from yomitalk.app import UserSession


class TestSessionCleanup:
    """Tests for session cleanup functionality."""

    def test_cleanup_session_data(self):
        """Test that cleanup_session_data properly removes session directories."""
        # セットアップ: UserSessionインスタンスを作成し、ディレクトリ構造を構築
        user_session = UserSession("test_session_cleanup")

        # テスト用のディレクトリを作成
        temp_dir = user_session.get_temp_dir()
        output_dir = user_session.get_output_dir()
        talk_dir = user_session.get_talk_temp_dir()

        # ファイルを作成してディレクトリが空でないようにする
        test_file1 = temp_dir / "test.txt"
        test_file2 = output_dir / "output.wav"
        test_file3 = talk_dir / "talk.wav"

        with open(test_file1, "w") as f:
            f.write("test")
        with open(test_file2, "w") as f:
            f.write("test output")
        with open(test_file3, "w") as f:
            f.write("test talk")

        # 全てのディレクトリとファイルが作成されたことを検証
        assert temp_dir.exists()
        assert output_dir.exists()
        assert talk_dir.exists()
        assert test_file1.exists()
        assert test_file2.exists()
        assert test_file3.exists()

        # 実行: クリーンアップメソッドを呼び出す
        success = user_session.cleanup_session_data()

        # 検証: ディレクトリが正常に削除されたことを確認
        assert success is True
        assert not temp_dir.exists()
        assert not output_dir.exists()

    def test_cleanup_nonexistent_directories(self):
        """Test that cleanup handles non-existent directories gracefully."""
        # セットアップ: UserSessionインスタンスを作成
        user_session = UserSession("test_session_nonexistent")
        temp_dir = user_session.get_temp_dir()
        output_dir = user_session.get_output_dir()

        # 事前にディレクトリを削除
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(output_dir, ignore_errors=True)

        # 存在しないことを確認
        assert not temp_dir.exists()
        assert not output_dir.exists()

        # 実行: クリーンアップメソッドを呼び出す
        success = user_session.cleanup_session_data()

        # 検証: エラーなしで完了していること
        assert success is True
