"""Tests for SessionManager module."""

from yomitalk.utils.session_manager import SessionManager


def test_session_manager_initialization():
    """Test that SessionManager is initialized properly."""
    session_manager = SessionManager()
    assert session_manager.session_id is not None
    assert isinstance(session_manager.session_id, str)
    assert len(session_manager.session_id) > 0

    # セッションIDのフォーマットを確認
    assert session_manager.session_id.startswith("session_")


def test_session_dirs_creation():
    """Test that SessionManager creates session-specific directories."""
    session_manager = SessionManager()

    # テンポラリディレクトリのテスト
    temp_dir = session_manager.get_temp_dir()
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    assert session_manager.session_id in str(temp_dir)

    # 出力ディレクトリのテスト
    output_dir = session_manager.get_output_dir()
    assert output_dir.exists()
    assert output_dir.is_dir()
    assert session_manager.session_id in str(output_dir)

    # トーク一時ディレクトリのテスト
    talk_temp_dir = session_manager.get_talk_temp_dir()
    assert talk_temp_dir.exists()
    assert talk_temp_dir.is_dir()
    assert session_manager.session_id in str(talk_temp_dir)
    assert "talks" in str(talk_temp_dir)


def test_unique_session_ids():
    """Test that consecutive session managers get different session IDs."""
    session1 = SessionManager()
    session2 = SessionManager()
    assert session1.session_id != session2.session_id
