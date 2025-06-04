"""Unit tests for app audio state management functionality."""

from yomitalk.app import PaperPodcastApp, UserSession


class TestUserSessionAudioState:
    """Test class for UserSession audio state management."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        self.session_id = "test_session"
        self.user_session = UserSession(self.session_id)

    def test_initial_audio_state(self):
        """Test initial audio generation state."""
        state = self.user_session.get_audio_generation_status()

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

        self.user_session.update_audio_generation_state(
            is_generating=True,
            status="generating",
            current_script=test_script,
            generation_id=test_id,
            progress=0.5,
        )

        state = self.user_session.get_audio_generation_status()
        assert state["is_generating"] is True
        assert state["status"] == "generating"
        assert state["current_script"] == test_script
        assert state["generation_id"] == test_id
        assert state["progress"] == 0.5
        assert state["last_update"] is not None

    def test_reset_audio_generation_state(self):
        """Test resetting audio generation state."""
        # First update state
        self.user_session.update_audio_generation_state(
            is_generating=True, status="generating", progress=0.8
        )

        # Then reset
        self.user_session.reset_audio_generation_state()

        state = self.user_session.get_audio_generation_status()
        assert state["is_generating"] is False
        assert state["progress"] == 0.0
        assert state["status"] == "idle"
        assert state["current_script"] == ""

    def test_is_audio_generation_active(self):
        """Test checking if audio generation is active."""
        # Initially not active
        assert self.user_session.is_audio_generation_active() is False

        # Set to generating but wrong status
        self.user_session.update_audio_generation_state(
            is_generating=True, status="idle"
        )
        assert self.user_session.is_audio_generation_active() is False

        # Set to correct status
        self.user_session.update_audio_generation_state(
            is_generating=True, status="generating"
        )
        assert self.user_session.is_audio_generation_active() is True

        # Complete generation
        self.user_session.update_audio_generation_state(
            is_generating=False, status="completed"
        )
        assert self.user_session.is_audio_generation_active() is False

    def test_has_generated_audio(self):
        """Test checking if audio has been generated."""
        # Initially no audio
        assert self.user_session.has_generated_audio() is False

        # Add streaming parts
        self.user_session.update_audio_generation_state(
            streaming_parts=["part1.wav", "part2.wav"]
        )
        assert self.user_session.has_generated_audio() is True

        # Reset and add final audio
        self.user_session.reset_audio_generation_state()
        self.user_session.update_audio_generation_state(
            final_audio_path="final_audio.wav"
        )
        assert self.user_session.has_generated_audio() is True


class TestPaperPodcastAppAudioRecovery:
    """Test class for PaperPodcastApp audio recovery functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method is run."""
        self.app = PaperPodcastApp()
        self.session_id = "test_session"
        self.user_session = UserSession(self.session_id)

    def test_check_and_restore_audio_generation_no_audio(self):
        """Test audio restoration when no audio exists."""
        streaming_audio, final_audio, status = (
            self.app.check_and_restore_audio_generation(self.user_session)
        )

        assert streaming_audio is None
        assert final_audio is None
        assert status == ""

    def test_check_and_restore_audio_generation_completed(self):
        """Test audio restoration when audio is completed."""
        # Set up completed audio state
        self.user_session.update_audio_generation_state(
            status="completed",
            is_generating=False,
            streaming_parts=["part1.wav", "part2.wav"],
            final_audio_path="final_audio.wav",
        )

        streaming_audio, final_audio, status = (
            self.app.check_and_restore_audio_generation(self.user_session)
        )

        assert streaming_audio == "part2.wav"  # Latest streaming part
        assert final_audio == "final_audio.wav"
        assert "復帰" in status

    def test_check_and_restore_audio_generation_active(self):
        """Test audio restoration when generation is active."""
        # Set up active generation state
        self.user_session.update_audio_generation_state(
            is_generating=True,
            status="generating",
            progress=0.6,
            streaming_parts=["part1.wav"],
        )

        streaming_audio, final_audio, status = (
            self.app.check_and_restore_audio_generation(self.user_session)
        )

        assert streaming_audio == "part1.wav"
        assert final_audio is None
        assert "60%" in status
        assert "復帰" in status

    def test_check_and_restore_audio_generation_integration(self):
        """Test that audio restoration is properly integrated into connection recovery."""
        # Set up completed audio state
        self.user_session.update_audio_generation_state(
            status="completed",
            is_generating=False,
            streaming_parts=["part1.wav", "part2.wav"],
            final_audio_path="final_audio.wav",
        )

        # Test direct audio restoration
        streaming_audio, final_audio, status = (
            self.app.check_and_restore_audio_generation(self.user_session)
        )

        assert streaming_audio == "part2.wav"
        assert final_audio == "final_audio.wav"
        assert "復帰" in status

        # Test connection recovery integration
        streaming_audio_recovery, final_audio_recovery, button_state = (
            self.app.handle_connection_recovery(
                self.user_session, terms_agreed=True, podcast_text="Test script"
            )
        )

        # Both should return the same audio content
        assert streaming_audio_recovery == streaming_audio
        assert final_audio_recovery == final_audio
        assert button_state["interactive"] is True

    def test_handle_connection_recovery_no_audio(self):
        """Test connection recovery when no audio exists."""
        streaming_audio, final_audio, button_state = (
            self.app.handle_connection_recovery(
                self.user_session, terms_agreed=True, podcast_text="Test script"
            )
        )

        assert streaming_audio is None
        assert final_audio is None
        assert button_state["interactive"] is True
        assert button_state["value"] == "音声を生成"

    def test_handle_connection_recovery_with_completed_audio(self):
        """Test connection recovery when audio is completed."""
        # Set up completed audio state
        self.user_session.update_audio_generation_state(
            status="completed",
            is_generating=False,
            streaming_parts=["part1.wav", "part2.wav"],
            final_audio_path="final_audio.wav",
        )

        streaming_audio, final_audio, button_state = (
            self.app.handle_connection_recovery(
                self.user_session, terms_agreed=True, podcast_text="Test script"
            )
        )

        assert streaming_audio == "part2.wav"
        assert final_audio == "final_audio.wav"
        assert button_state["interactive"] is True

    def test_handle_connection_recovery_with_active_generation(self):
        """Test connection recovery when generation is active."""
        # Set up active generation state
        self.user_session.update_audio_generation_state(
            is_generating=True,
            status="generating",
            progress=0.6,
            streaming_parts=["part1.wav"],
        )

        streaming_audio, final_audio, button_state = (
            self.app.handle_connection_recovery(
                self.user_session, terms_agreed=True, podcast_text="Test script"
            )
        )

        # During active generation, audio components should return gr.update() to avoid race conditions
        import gradio as gr

        assert isinstance(streaming_audio, gr.update().__class__)
        assert isinstance(final_audio, gr.update().__class__)
        assert button_state["interactive"] is False

    def test_handle_connection_recovery_terms_not_agreed(self):
        """Test connection recovery when terms are not agreed."""
        # Set up completed audio state
        self.user_session.update_audio_generation_state(
            status="completed",
            is_generating=False,
            streaming_parts=["part1.wav"],
            final_audio_path="final_audio.wav",
        )

        streaming_audio, final_audio, button_state = (
            self.app.handle_connection_recovery(
                self.user_session, terms_agreed=False, podcast_text="Test script"
            )
        )

        assert streaming_audio == "part1.wav"
        assert final_audio == "final_audio.wav"
        assert button_state["interactive"] is False
        assert "VOICEVOX利用規約に同意が必要です" in button_state["value"]

    def test_reset_audio_state_and_components(self):
        """Test resetting audio state and components."""
        # Set up some state first
        self.user_session.update_audio_generation_state(
            is_generating=True, status="generating", progress=0.7
        )

        # Reset
        streaming_clear, audio_clear = self.app.reset_audio_state_and_components(
            self.user_session
        )

        # Check components are cleared
        assert streaming_clear is None
        assert audio_clear is None

        # Check state is reset
        state = self.user_session.get_audio_generation_status()
        assert state["is_generating"] is False
        assert state["progress"] == 0.0
        assert state["status"] == "idle"

    def test_enable_generate_button_both_conditions_met(self):
        """Test enable button when both conditions are met."""
        button_state = self.app.enable_generate_button(
            terms_agreed=True, podcast_text="Test script content"
        )

        assert button_state["interactive"] is True
        assert button_state["value"] == "音声を生成"

    def test_enable_generate_button_terms_not_agreed(self):
        """Test enable button when terms are not agreed."""
        button_state = self.app.enable_generate_button(
            terms_agreed=False, podcast_text="Test script content"
        )

        assert button_state["interactive"] is False
        assert button_state["value"] == "音声を生成（VOICEVOX利用規約に同意が必要です）"

    def test_enable_generate_button_no_text(self):
        """Test enable button when no text is provided."""
        button_state = self.app.enable_generate_button(
            terms_agreed=True, podcast_text=""
        )

        assert button_state["interactive"] is False
        assert button_state["value"] == "音声を生成（トーク原稿が必要です）"

    def test_enable_generate_button_neither_condition_met(self):
        """Test enable button when neither condition is met."""
        button_state = self.app.enable_generate_button(
            terms_agreed=False, podcast_text=""
        )

        assert button_state["interactive"] is False
        assert button_state["value"] == "音声を生成（VOICEVOX利用規約に同意が必要です）"

    def test_enable_generate_button_whitespace_text(self):
        """Test enable button with whitespace-only text."""
        button_state = self.app.enable_generate_button(
            terms_agreed=True, podcast_text="   \n\t   "
        )

        assert button_state["interactive"] is False
        assert button_state["value"] == "音声を生成（トーク原稿が必要です）"
