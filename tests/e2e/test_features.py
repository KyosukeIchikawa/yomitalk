"""Test module for E2E tests discovery.

This file ensures that pytest-bdd can properly discover and run feature files.
"""

import os

from pytest_bdd import scenarios

# Import all step definitions to make them available for pytest-bdd
from tests.e2e.steps.audio_generation_steps import *  # noqa: F401, F403
from tests.e2e.steps.browser_state_steps import *  # noqa: F401, F403
from tests.e2e.steps.common_steps import *  # noqa: F401, F403
from tests.e2e.steps.file_upload_steps import *  # noqa: F401, F403
from tests.e2e.steps.script_generation_steps import *  # noqa: F401, F403
from tests.e2e.steps.session_recovery_steps import *  # noqa: F401, F403
from tests.e2e.steps.text_management_steps import *  # noqa: F401, F403
from tests.e2e.steps.url_extraction_steps import *  # noqa: F401, F403
from tests.e2e.steps.voicevox_sharing_steps import *  # noqa: F401, F403

# Get the absolute path to features directory
feature_dir = os.path.join(os.path.dirname(__file__), "features")

# Register feature scenarios with absolute path
scenarios(feature_dir)

# Register specific scenarios for audio recovery
scenarios(os.path.join(feature_dir, "audio_recovery.feature"))
