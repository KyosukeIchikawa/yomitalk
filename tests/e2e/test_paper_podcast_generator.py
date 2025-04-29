"""
Test runner for paper podcast generator features
"""

import os

from pytest_bdd import scenarios

from tests.e2e.features.steps.audio_generation_steps import *  # noqa

# Import steps from all step modules
from tests.e2e.features.steps.common_steps import *  # noqa
from tests.e2e.features.steps.pdf_extraction_steps import *  # noqa
from tests.e2e.features.steps.settings_steps import *  # noqa
from tests.e2e.features.steps.text_generation_steps import *  # noqa

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))
feature_path = os.path.join(current_dir, "features", "paper_podcast.feature")

# Register scenarios with absolute path
scenarios(feature_path)
