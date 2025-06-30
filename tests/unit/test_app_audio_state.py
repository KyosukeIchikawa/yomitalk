"""Unit tests for app audio state management functionality."""

from yomitalk.app import UserSession


class TestUserSessionAudioState:
    """Test class for UserSession audio state management."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        self.session_id = "test_session"
        self.user_session = UserSession(self.session_id)
        # Create test browser state
        self.browser_state = {
            "app_session_id": self.session_id,
            "audio_generation_state": {
                "is_generating": False,
                "progress": 0.0,
                "status": "idle",
                "current_script": "",
                "generated_parts": [],
                "final_audio_path": None,
                "streaming_parts": [],
                "generation_id": None,
                "start_time": None,
                "estimated_total_parts": 1,
            },
            "user_settings": {},
            "ui_state": {},
        }

    def test_initial_audio_state(self):
        """Test initial audio generation state."""
        state = self.user_session.get_audio_generation_status(self.browser_state)

        assert state["is_generating"] is False
        assert state["progress"] == 0.0
        assert state["status"] == "idle"
        assert state["current_script"] == ""
        assert state["generated_parts"] == []
        assert state["final_audio_path"] is None
        assert state["streaming_parts"] == []
        assert state["generation_id"] is None

    def test_update_audio_generation_state(self):
        """Test updating audio generation state."""
        test_id = "test_generation_id"
        test_script = "Test script content"

        updated_browser_state = self.user_session.update_audio_generation_state(
            self.browser_state,
            is_generating=True,
            status="generating",
            current_script=test_script,
            generation_id=test_id,
            progress=0.5,
        )

        state = self.user_session.get_audio_generation_status(updated_browser_state)
        assert state["is_generating"] is True
        assert state["status"] == "generating"
        assert state["current_script"] == test_script
        assert state["generation_id"] == test_id
        assert state["progress"] == 0.5
        assert state["last_update"] is not None

    def test_reset_audio_generation_state(self):
        """Test resetting audio generation state."""
        # First update state
        updated_browser_state = self.user_session.update_audio_generation_state(self.browser_state, is_generating=True, status="generating", progress=0.5)

        # Reset state
        reset_browser_state = self.user_session.reset_audio_generation_state(updated_browser_state)

        state = self.user_session.get_audio_generation_status(reset_browser_state)
        assert state["is_generating"] is False
        assert state["status"] == "idle"
        assert state["progress"] == 0.0
        assert state["current_script"] == ""

    def test_is_audio_generation_active(self):
        """Test checking if audio generation is active."""
        # Initially not active
        assert self.user_session.is_audio_generation_active(self.browser_state) is False

        # Set to generating but wrong status
        updated_state = self.user_session.update_audio_generation_state(self.browser_state, is_generating=True, status="idle")
        assert self.user_session.is_audio_generation_active(updated_state) is False

        # Set to correct status
        updated_state = self.user_session.update_audio_generation_state(self.browser_state, is_generating=True, status="generating")
        assert self.user_session.is_audio_generation_active(updated_state) is True

        # Complete generation
        updated_state = self.user_session.update_audio_generation_state(self.browser_state, is_generating=False, status="completed")
        assert self.user_session.is_audio_generation_active(updated_state) is False

    def test_has_generated_audio(self):
        """Test checking if audio has been generated."""
        # Initially no audio
        assert self.user_session.has_generated_audio(self.browser_state) is False

        # Add streaming parts
        updated_state = self.user_session.update_audio_generation_state(self.browser_state, streaming_parts=["part1.wav", "part2.wav"])
        assert self.user_session.has_generated_audio(updated_state) is True

        # Reset and add final audio
        reset_state = self.user_session.reset_audio_generation_state(self.browser_state)
        updated_state = self.user_session.update_audio_generation_state(reset_state, final_audio_path="final_audio.wav")
        assert self.user_session.has_generated_audio(updated_state) is True
