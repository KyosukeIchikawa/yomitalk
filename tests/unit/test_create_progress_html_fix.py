"""
Test to verify that the _create_progress_html bug has been fixed.
This tests that None values are handled gracefully.
"""

import time
from yomitalk.app import PaperPodcastApp


class TestCreateProgressHtmlFix:
    """Test cases to verify the fix for _create_progress_html with None values."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = PaperPodcastApp()

    def test_create_progress_html_with_none_total_parts_fixed(self):
        """
        Test that _create_progress_html handles None total_parts gracefully after the fix.
        """
        # This should no longer raise a TypeError
        result = self.app._create_progress_html(
            current_part=5,
            total_parts=None,  # None should be handled gracefully
            status_message="Test status",
            is_completed=False,
            start_time=time.time(),
        )

        # Verify we get a valid HTML string
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test status" in result
        assert "🎵" in result  # Should show the progress emoji

    def test_create_progress_html_with_none_current_part(self):
        """
        Test that _create_progress_html handles None current_part gracefully.
        """
        result = self.app._create_progress_html(
            current_part=None,  # None should be handled gracefully
            total_parts=10,
            status_message="Test with None current_part",
            is_completed=False,
            start_time=time.time(),
        )

        assert isinstance(result, str)
        assert "Test with None current_part" in result

    def test_create_progress_html_with_both_none(self):
        """
        Test that _create_progress_html handles both None values gracefully.
        """
        result = self.app._create_progress_html(current_part=None, total_parts=None, status_message="Both None", is_completed=False, start_time=time.time())

        assert isinstance(result, str)
        assert "Both None" in result

    def test_create_progress_html_completed_with_none_values(self):
        """
        Test that completed status works even with None values.
        """
        result = self.app._create_progress_html(
            current_part=None,
            total_parts=None,
            status_message="Completed test",
            is_completed=True,  # Completed should bypass progress calculation
            start_time=time.time(),
        )

        assert isinstance(result, str)
        assert "Completed test" in result
        assert "✅" in result  # Should show completion emoji

    def test_normal_operation_still_works(self):
        """
        Test that normal operation with valid integers still works correctly.
        """
        result = self.app._create_progress_html(current_part=3, total_parts=10, status_message="Normal operation", is_completed=False, start_time=time.time())

        assert isinstance(result, str)
        assert "Normal operation" in result
        # Should calculate 30% progress (but capped at 95%)
        assert "🎵" in result

    def test_progress_percentage_calculation_with_valid_values(self):
        """
        Test that progress percentage is calculated correctly with valid values.
        """
        result = self.app._create_progress_html(current_part=2, total_parts=4, status_message="Half done", is_completed=False)

        # 2/4 = 50% progress
        assert "50%" in result or "50 %" in result

    def test_zero_division_protection(self):
        """
        Test that zero total_parts doesn't cause division by zero.
        """
        result = self.app._create_progress_html(
            current_part=5,
            total_parts=0,  # This should be handled without division error
            status_message="Zero total",
            is_completed=False,
        )

        assert isinstance(result, str)
        assert "Zero total" in result
