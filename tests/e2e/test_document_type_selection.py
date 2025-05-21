"""E2E tests for document type and podcast mode selection."""
import os

import pytest
import pytest_bdd

from tests.e2e.features.steps.common_steps import *  # noqa: F401, F403
from tests.e2e.features.steps.document_type_steps import *  # noqa: F401, F403

# Get the directory of this file and resolve the feature path
current_dir = os.path.dirname(os.path.abspath(__file__))
feature_path = os.path.join(current_dir, "features", "document_type_selection.feature")


# Apply E2E marker to all scenarios in the feature file
@pytest.mark.e2e
def test_all_document_type_selection_scenarios():
    """Container for all document type selection scenarios."""


# Load all scenarios from the feature file
pytest_bdd.scenarios(feature_path)
