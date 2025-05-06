"""E2E tests for the paper podcast generator."""

import os

import pytest_bdd

# Import step implementations
from tests.e2e.features.steps.audio_generation_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.common_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.max_tokens_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.pdf_extraction_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.podcast_generation_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.podcast_mode_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.settings_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.text_generation_steps import *  # noqa: F401, F403

# Get the directory of this file and resolve the feature path
current_dir = os.path.dirname(os.path.abspath(__file__))
feature_path = os.path.join(current_dir, "features", "paper_podcast.feature")

# Features and scenarios are defined in feature files in the features/ directory.
pytest_bdd.scenarios(feature_path)
