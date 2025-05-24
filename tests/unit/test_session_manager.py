"""Unit tests for SessionManager class."""
from pathlib import Path
from unittest.mock import patch

from yomitalk.utils.session_manager import SessionManager


class TestSessionManager:
    """Test class for SessionManager."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        # Create a patch for time.time() to return a fixed timestamp
        self.time_patch = patch("time.time", return_value=1600000000)
        self.time_patch.start()

    def teardown_method(self):
        """Tear down test fixtures after each test method is run."""
        self.time_patch.stop()

    def test_initialization(self):
        """Test that SessionManager initializes correctly."""
        session_manager = SessionManager()

        # Check that a session ID was created
        assert hasattr(session_manager, "session_id")
        assert session_manager.session_id is not None
        assert isinstance(session_manager.session_id, str)

        # Check that the timestamp and unique ID were used
        assert "1600000000" in session_manager.session_id

    def test_get_session_id(self):
        """Test getting the session ID."""
        session_manager = SessionManager()
        session_id = session_manager.get_session_id()

        # Check that the returned session ID matches the internal one
        assert session_id == session_manager.session_id

    def test_get_output_dir(self):
        """Test getting the output directory path."""
        session_manager = SessionManager()
        output_dir = session_manager.get_output_dir()

        # Check that the output directory path is correct
        assert isinstance(output_dir, Path)
        assert "data/output" in str(output_dir)
        assert session_manager.session_id in str(output_dir)

    def test_get_temp_dir(self):
        """Test getting the temporary directory path."""
        session_manager = SessionManager()
        temp_dir = session_manager.get_temp_dir()

        # Check that the temporary directory path is correct
        assert isinstance(temp_dir, Path)
        assert "data/temp" in str(temp_dir)
        assert session_manager.session_id in str(temp_dir)

    def test_get_talk_temp_dir(self):
        """Test getting the talk temporary directory path."""
        session_manager = SessionManager()
        temp_dir = session_manager.get_talk_temp_dir()

        # Check that the temporary directory path is correct
        assert isinstance(temp_dir, Path)
        assert "data/temp" in str(temp_dir)
        assert "talks" in str(temp_dir)
        assert session_manager.session_id in str(temp_dir)

    @patch("pathlib.Path.mkdir")
    def test_directory_creation(self, mock_mkdir):
        """Test directory creation in the manager."""
        session_manager = SessionManager()

        # Reset the mock call count (since initialization already happened)
        mock_mkdir.reset_mock()

        # Get directories which should trigger mkdir
        session_manager.get_output_dir()
        session_manager.get_temp_dir()
        session_manager.get_talk_temp_dir()

        # Check that mkdir was called
        assert mock_mkdir.call_count >= 3

        # Check mkdir parameters
        for call in mock_mkdir.call_args_list:
            kwargs = call[1]
            assert kwargs.get("parents", False) is True
            assert kwargs.get("exist_ok", False) is True
