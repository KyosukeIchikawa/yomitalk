"""
Test runner for template management features
"""

import os

from pytest_bdd import scenarios

# Import steps from all required step modules
from tests.e2e.features.steps.common_steps import *  # noqa
from tests.e2e.features.steps.pdf_extraction_steps import *  # noqa
from tests.e2e.features.steps.settings_steps import *  # noqa
from tests.e2e.features.steps.template_steps import *  # noqa
from tests.e2e.features.steps.text_generation_steps import *  # noqa

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))
feature_path = os.path.join(current_dir, "features", "file_extraction.feature")

# Register scenarios with absolute path
scenarios(feature_path)
