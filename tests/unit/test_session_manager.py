"""Unit tests for UserSession class."""
from pathlib import Path
from unittest.mock import patch

from yomitalk.app import UserSession


class TestUserSession:
    """Test class for UserSession."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        # Create a patch for time.time() to return a fixed timestamp
        self.time_patch = patch("time.time", return_value=1600000000)
        self.time_patch.start()

    def teardown_method(self):
        """Tear down test fixtures after each test method is run."""
        self.time_patch.stop()

    def test_initialization(self):
        """Test that UserSession initializes correctly."""
        user_session = UserSession("test_session_123")

        # Check that a session ID was set
        assert hasattr(user_session, "session_id")
        assert user_session.session_id is not None
        assert isinstance(user_session.session_id, str)
        assert user_session.session_id == "test_session_123"

    def test_get_output_dir(self):
        """Test getting the output directory path."""
        user_session = UserSession("test_session_123")
        output_dir = user_session.get_output_dir()

        # Check that the output directory path is correct
        assert isinstance(output_dir, Path)
        assert "data/output" in str(output_dir)
        assert "test_session_123" in str(output_dir)

    def test_get_temp_dir(self):
        """Test getting the temporary directory path."""
        user_session = UserSession("test_session_123")
        temp_dir = user_session.get_temp_dir()

        # Check that the temporary directory path is correct
        assert isinstance(temp_dir, Path)
        assert "data/temp" in str(temp_dir)
        assert "test_session_123" in str(temp_dir)

    def test_get_talk_temp_dir(self):
        """Test getting the talk temporary directory path."""
        user_session = UserSession("test_session_123")
        temp_dir = user_session.get_talk_temp_dir()

        # Check that the temporary directory path is correct
        assert isinstance(temp_dir, Path)
        assert "data/temp" in str(temp_dir)
        assert "talks" in str(temp_dir)
        assert "test_session_123" in str(temp_dir)

    @patch("pathlib.Path.mkdir")
    def test_directory_creation(self, mock_mkdir):
        """Test directory creation in the manager."""
        user_session = UserSession("test_session_123")

        # Reset the mock call count (since initialization already happened)
        mock_mkdir.reset_mock()

        # Get directories which should trigger mkdir
        user_session.get_output_dir()
        user_session.get_temp_dir()
        user_session.get_talk_temp_dir()

        # Check that mkdir was called
        assert mock_mkdir.call_count >= 3

        # Check mkdir parameters
        for call in mock_mkdir.call_args_list:
            kwargs = call[1]
            assert kwargs.get("parents", False) is True
            assert kwargs.get("exist_ok", False) is True
