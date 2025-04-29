"""
Test runner for paper podcast generator features
"""

import os

from pytest_bdd import scenarios

# Import steps
from tests.e2e.features.steps.paper_podcast_steps import *  # noqa

# Get the directory of this file
current_dir = os.path.dirname(os.path.abspath(__file__))
feature_path = os.path.join(current_dir, "features", "paper_podcast.feature")

# Register scenarios with absolute path
scenarios(feature_path)
