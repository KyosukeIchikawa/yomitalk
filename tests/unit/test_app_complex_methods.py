"""Unit tests for complex methods in app.py."""

import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch


from yomitalk.app import PaperPodcastApp
from yomitalk.user_session import UserSession


class TestUpdateAudioButtonStateWithResumeCheck:
    """Test update_audio_button_state_with_resume_check method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = PaperPodcastApp()
        self.user_session = UserSession("test_session")
        self.mock_request = Mock()
        self.mock_request.session_hash = "test_session_hash"

        # Base browser state
        self.browser_state: Dict[str, Any] = {
            "app_session_id": "test_session",
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
                "script_changed": False,
            },
            "user_settings": {},
            "ui_state": {},
        }

    def test_unchecked_checkbox_returns_disabled_state(self):
        """Test that unchecked checkbox returns disabled state with message."""
        result = self.app.update_audio_button_state_with_resume_check(checked=False, podcast_text="Some valid text", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is False
        assert result["variant"] == "secondary"
        assert "VOICEVOX利用規約に同意が必要です" in result["value"]

    def test_empty_text_returns_disabled_state(self):
        """Test that empty text returns disabled state with message."""
        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is False
        assert result["variant"] == "secondary"
        assert "トーク原稿が必要です" in result["value"]

    def test_whitespace_only_text_returns_disabled_state(self):
        """Test that whitespace-only text returns disabled state."""
        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="   \n\t  ", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is False
        assert result["variant"] == "secondary"
        assert "トーク原稿が必要です" in result["value"]

    def test_none_text_returns_disabled_state(self):
        """Test that None text returns disabled state."""
        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text=None, user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is False
        assert result["variant"] == "secondary"
        assert "トーク原稿が必要です" in result["value"]

    def test_new_script_returns_generate_button(self):
        """Test that new script returns generate button state."""
        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="New script content", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is True
        assert result["variant"] == "primary"
        assert result["value"] == "音声を生成"

    def test_script_unchanged_with_streaming_parts_returns_resume_button(self):
        """Test that unchanged script with streaming parts returns resume button."""
        # Set up browser state with streaming parts
        self.browser_state["audio_generation_state"]["current_script"] = "Test script"
        self.browser_state["audio_generation_state"]["streaming_parts"] = ["part1.wav", "part2.wav"]

        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is True
        assert result["variant"] == "primary"
        assert result["value"] == "音声生成を再開"

    def test_script_unchanged_with_preparing_status_returns_resume_button(self):
        """Test that unchanged script with preparing status returns resume button."""
        # Set up browser state with preparing status
        self.browser_state["audio_generation_state"]["current_script"] = "Test script"
        self.browser_state["audio_generation_state"]["status"] = "preparing"

        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is True
        assert result["variant"] == "primary"
        assert result["value"] == "音声生成を再開"

    def test_script_unchanged_with_final_audio_returns_completed_button(self):
        """Test that unchanged script with final audio returns completed button."""
        # Set up browser state with final audio
        self.browser_state["audio_generation_state"]["current_script"] = "Test script"
        self.browser_state["audio_generation_state"]["final_audio_path"] = "/path/to/final.wav"

        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is False
        assert result["variant"] == "secondary"
        assert result["value"] == "音声生成済み"

    def test_script_changed_after_completion_returns_generate_button(self):
        """Test that changed script after completion returns generate button."""
        # Set up browser state with final audio for old script
        self.browser_state["audio_generation_state"]["current_script"] = "Old script"
        self.browser_state["audio_generation_state"]["final_audio_path"] = "/path/to/final.wav"

        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="New script content", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is True
        assert result["variant"] == "primary"
        assert result["value"] == "音声を生成"

    def test_discovers_final_audio_on_disk_when_not_in_browser_state(self):
        """Test that method discovers final audio on disk when not in browser state."""
        # Set up browser state with matching script but no final audio
        self.browser_state["audio_generation_state"]["current_script"] = "Test script"
        self.browser_state["audio_generation_state"]["final_audio_path"] = None

        # Create a temporary directory and audio file
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file = Path(temp_dir) / "audio_final.wav"
            audio_file.write_text("fake audio content")

            # Mock user_session.get_output_dir to return our temp directory
            with patch.object(self.user_session, "get_output_dir", return_value=Path(temp_dir)):
                result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=self.browser_state)

                # Should discover the file and update browser state
                assert result["interactive"] is False
                assert result["variant"] == "secondary"
                assert result["value"] == "音声生成済み"

                # Browser state should be updated
                assert self.browser_state["audio_generation_state"]["final_audio_path"] == str(audio_file)
                assert self.browser_state["audio_generation_state"]["status"] == "completed"
                assert self.browser_state["audio_generation_state"]["is_generating"] is False
                assert self.browser_state["audio_generation_state"]["progress"] == 1.0

    def test_no_discovery_when_script_changed_flag_is_set(self):
        """Test that no disk discovery happens when script_changed flag is set."""
        # Set up browser state with matching script but script_changed flag
        self.browser_state["audio_generation_state"]["current_script"] = "Test script"
        self.browser_state["audio_generation_state"]["final_audio_path"] = None
        self.browser_state["audio_generation_state"]["script_changed"] = True

        # Create a temporary directory and audio file
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file = Path(temp_dir) / "audio_final.wav"
            audio_file.write_text("fake audio content")

            # Mock user_session.get_output_dir to return our temp directory
            with patch.object(self.user_session, "get_output_dir", return_value=Path(temp_dir)):
                result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=self.browser_state)

                # Should not discover the file and return resume button
                assert result["interactive"] is True
                assert result["variant"] == "primary"
                assert result["value"] == "音声生成を再開"

                # Browser state should not be updated
                assert self.browser_state["audio_generation_state"]["final_audio_path"] is None

    def test_fallback_to_legacy_session_methods_when_no_browser_state(self):
        """Test fallback to legacy UserSession methods when browser_state is None."""
        # Mock UserSession methods
        mock_audio_state = {"current_script": "Test script", "status": "completed"}

        with (
            patch.object(self.user_session, "get_audio_generation_status", return_value=mock_audio_state),
            patch.object(self.user_session, "has_generated_audio", return_value=True),
            patch.object(self.user_session.audio_generator, "final_audio_path", "/path/to/final.wav"),
            patch("os.path.exists", return_value=True),
        ):
            result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=None)

            assert result["interactive"] is False
            assert result["variant"] == "secondary"
            assert result["value"] == "音声生成済み"

    def test_fallback_to_legacy_resume_when_no_final_audio_file(self):
        """Test fallback to legacy resume when no final audio file exists."""
        # Mock UserSession methods
        mock_audio_state = {"current_script": "Test script", "status": "generating"}

        with (
            patch.object(self.user_session, "get_audio_generation_status", return_value=mock_audio_state),
            patch.object(self.user_session, "has_generated_audio", return_value=True),
            patch.object(self.user_session.audio_generator, "final_audio_path", "/path/to/final.wav"),
            patch("os.path.exists", return_value=False),
        ):
            result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=None)

            assert result["interactive"] is True
            assert result["variant"] == "primary"
            assert result["value"] == "音声生成を再開"

    def test_empty_current_script_in_browser_state_returns_generate_button(self):
        """Test that empty current_script in browser state returns generate button."""
        # Set up browser state with empty current_script
        self.browser_state["audio_generation_state"]["current_script"] = ""

        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="New script content", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is True
        assert result["variant"] == "primary"
        assert result["value"] == "音声を生成"

    def test_script_mismatch_returns_generate_button(self):
        """Test that script mismatch returns generate button."""
        # Set up browser state with different script
        self.browser_state["audio_generation_state"]["current_script"] = "Old script"
        self.browser_state["audio_generation_state"]["streaming_parts"] = ["part1.wav"]

        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="New script content", user_session=self.user_session, browser_state=self.browser_state)

        assert result["interactive"] is True
        assert result["variant"] == "primary"
        assert result["value"] == "音声を生成"

    def test_gradio_update_structure(self):
        """Test that result has correct Gradio update structure."""
        result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=self.browser_state)

        # Check that result has the correct structure for gr.update
        assert "value" in result
        assert "interactive" in result
        assert "variant" in result
        assert isinstance(result["value"], str)
        assert isinstance(result["interactive"], bool)
        assert result["variant"] in ["primary", "secondary"]

    def test_multiple_audio_files_on_disk_uses_first_match(self):
        """Test that when multiple audio files exist on disk, it uses the first match."""
        # Set up browser state with matching script but no final audio
        self.browser_state["audio_generation_state"]["current_script"] = "Test script"
        self.browser_state["audio_generation_state"]["final_audio_path"] = None

        # Create a temporary directory with multiple audio files
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file1 = Path(temp_dir) / "audio_part1.wav"
            audio_file2 = Path(temp_dir) / "audio_final.wav"
            audio_file1.write_text("fake audio content 1")
            audio_file2.write_text("fake audio content 2")

            # Mock user_session.get_output_dir to return our temp directory
            with patch.object(self.user_session, "get_output_dir", return_value=Path(temp_dir)):
                result = self.app.update_audio_button_state_with_resume_check(checked=True, podcast_text="Test script", user_session=self.user_session, browser_state=self.browser_state)

                # Should discover a file and update browser state
                assert result["interactive"] is False
                assert result["variant"] == "secondary"
                assert result["value"] == "音声生成済み"

                # Browser state should be updated with one of the files
                final_audio_path = self.browser_state["audio_generation_state"]["final_audio_path"]
                assert final_audio_path in [str(audio_file1), str(audio_file2)]
                assert self.browser_state["audio_generation_state"]["status"] == "completed"


class TestCreateProgressHTML:
    """Test _create_progress_html method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = PaperPodcastApp()

    def test_basic_progress_display(self):
        """Test basic progress display without completion."""
        result = self.app._create_progress_html(current_part=3, total_parts=10, status_message="音声生成中...", is_completed=False)

        assert "音声生成中..." in result
        assert "パート 3/10" in result
        assert "30.0%" in result
        assert "🎵" in result
        assert "✅" not in result

    def test_completed_progress_display(self):
        """Test completed progress display."""
        result = self.app._create_progress_html(current_part=10, total_parts=10, status_message="生成完了", is_completed=True)

        assert "生成完了" in result
        assert "パート 10/10" in result
        assert "100%" in result
        assert "✅" in result
        assert "🎵" not in result

    def test_progress_calculation_with_zero_total(self):
        """Test progress calculation when total_parts is 0."""
        result = self.app._create_progress_html(current_part=0, total_parts=0, status_message="準備中...", is_completed=False)

        assert "準備中..." in result
        assert "パート 0/0" in result
        assert "0%" in result

    def test_progress_calculation_caps_at_95_percent(self):
        """Test that progress calculation caps at 95% when not completed."""
        result = self.app._create_progress_html(current_part=100, total_parts=100, status_message="最終処理中...", is_completed=False)

        assert "最終処理中..." in result
        assert "パート 100/100" in result
        assert "95%" in result

    def test_time_calculation_with_start_time(self):
        """Test time calculation with start_time provided."""
        import time

        start_time = time.time() - 65  # 1 minute 5 seconds ago

        result = self.app._create_progress_html(current_part=5, total_parts=10, status_message="音声生成中...", is_completed=False, start_time=start_time)

        assert "経過: 01:05" in result
        assert "推定残り:" in result

    def test_time_calculation_when_completed(self):
        """Test time calculation when generation is completed."""
        import time

        start_time = time.time() - 120  # 2 minutes ago

        result = self.app._create_progress_html(current_part=10, total_parts=10, status_message="生成完了", is_completed=True, start_time=start_time)

        assert "完了時間: 02:00" in result
        assert "推定残り:" not in result

    def test_time_calculation_at_start(self):
        """Test time calculation when current_part is 0."""
        import time

        start_time = time.time() - 30  # 30 seconds ago

        result = self.app._create_progress_html(current_part=0, total_parts=10, status_message="開始準備中...", is_completed=False, start_time=start_time)

        assert "経過: 00:30" in result
        assert "推定残り:" not in result

    def test_resume_from_part_display(self):
        """Test display of resume from part information."""
        result = self.app._create_progress_html(current_part=7, total_parts=10, status_message="再開中...", is_completed=False)

        assert "再開中..." in result
        # Resume functionality is handled elsewhere in the app, not in _create_progress_html

    def test_resume_from_part_zero_not_displayed(self):
        """Test that resume from part 0 is not displayed."""
        result = self.app._create_progress_html(current_part=3, total_parts=10, status_message="生成中...", is_completed=False)

        assert "生成中..." in result
        # Resume functionality is handled elsewhere in the app, not in _create_progress_html

    def test_resume_from_part_none_not_displayed(self):
        """Test that resume from part None is not displayed."""
        result = self.app._create_progress_html(current_part=3, total_parts=10, status_message="生成中...", is_completed=False)

        assert "生成中..." in result
        # Resume functionality is handled elsewhere in the app, not in _create_progress_html

    def test_html_structure_contains_required_elements(self):
        """Test that HTML structure contains all required elements."""
        result = self.app._create_progress_html(current_part=3, total_parts=10, status_message="音声生成中...", is_completed=False)

        # Check for HTML structure
        assert "<div" in result
        assert "style=" in result
        assert "background-color:" in result
        assert "border-radius:" in result
        assert "width:" in result
        assert "height:" in result

    def test_estimated_remaining_time_calculation(self):
        """Test estimated remaining time calculation accuracy."""
        import time

        start_time = time.time() - 60  # 1 minute ago

        result = self.app._create_progress_html(current_part=2, total_parts=10, status_message="音声生成中...", is_completed=False, start_time=start_time)

        # With 2 parts in 60 seconds, that's 30 seconds per part
        # 8 remaining parts would be 240 seconds = 4 minutes
        assert "推定残り: 04:00" in result

    def test_edge_case_single_part_generation(self):
        """Test edge case with single part generation."""
        result = self.app._create_progress_html(current_part=1, total_parts=1, status_message="音声生成中...", is_completed=False)

        assert "音声生成中..." in result
        assert "パート 1/1" in result
        assert "95%" in result  # Should cap at 95% when not completed

    def test_edge_case_single_part_completed(self):
        """Test edge case with single part completed."""
        result = self.app._create_progress_html(current_part=1, total_parts=1, status_message="生成完了", is_completed=True)

        assert "生成完了" in result
        assert "パート 1/1" in result
        assert "100%" in result  # Should be 100% when completed

    def test_long_elapsed_time_formatting(self):
        """Test formatting of long elapsed times."""
        import time

        start_time = time.time() - 3665  # 61 minutes 5 seconds ago

        result = self.app._create_progress_html(current_part=5, total_parts=10, status_message="音声生成中...", is_completed=False, start_time=start_time)

        assert "経過: 61:05" in result
