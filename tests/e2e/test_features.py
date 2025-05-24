"""Test module for E2E tests discovery.

This file ensures that pytest-bdd can properly discover and run feature files.
"""
from pytest_bdd import scenarios

# Import all step definitions to make them available for pytest-bdd
from tests.e2e.steps.audio_generation_steps import *  # noqa: F401, F403
from tests.e2e.steps.common_steps import *  # noqa: F401, F403
from tests.e2e.steps.file_upload_steps import *  # noqa: F401, F403
from tests.e2e.steps.script_generation_steps import *  # noqa: F401, F403

# Register feature scenarios
scenarios(".")
