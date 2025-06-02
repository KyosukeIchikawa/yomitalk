"""
VOICEVOX sharing tests - Backend only execution.

This test module runs VOICEVOX sharing scenarios without requiring Playwright.
"""

import pytest
from pytest_bdd import scenarios

# Import VOICEVOX step definitions only
from tests.e2e.steps.voicevox_sharing_steps import *  # noqa: F401, F403

# Register only the VOICEVOX sharing feature
scenarios("voicevox_sharing.feature")


# Override browser-dependent fixtures for VOICEVOX tests
@pytest.fixture
def browser():
    """Dummy browser fixture for VOICEVOX tests."""
    return None


@pytest.fixture
def page():
    """Dummy page fixture for VOICEVOX tests."""
    return None


# Mark all VOICEVOX tests to not require Playwright
pytestmark = pytest.mark.no_playwright
