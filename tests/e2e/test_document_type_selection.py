"""E2E tests for document type and podcast mode selection."""

import pytest
from pytest_bdd import scenario

from tests.e2e.features.steps.document_type_steps import (  # noqa
    check_available_document_types,
    check_available_podcast_modes,
    check_document_type_changed,
    check_podcast_mode_changed,
    select_document_type,
    select_podcast_mode,
)


@pytest.mark.e2e
@scenario(
    "features/document_type_selection.feature",
    "Default document type and mode selection",
)
def test_default_document_type_and_mode():
    """Test that default document type and mode are correctly selected."""


@pytest.mark.e2e
@scenario("features/document_type_selection.feature", "Changing document type")
def test_changing_document_type():
    """Test changing the document type."""


@pytest.mark.e2e
@scenario("features/document_type_selection.feature", "Changing podcast mode")
def test_changing_podcast_mode():
    """Test changing the podcast mode."""


@pytest.mark.e2e
@scenario(
    "features/document_type_selection.feature",
    "Changing both document type and podcast mode",
)
def test_changing_both_document_type_and_podcast_mode():
    """Test changing both document type and podcast mode."""


@pytest.mark.e2e
@scenario(
    "features/document_type_selection.feature", "All document types are available"
)
def test_all_document_types_are_available():
    """Test that all expected document types are available."""


@pytest.mark.e2e
@scenario("features/document_type_selection.feature", "All podcast modes are available")
def test_all_podcast_modes_are_available():
    """Test that all expected podcast modes are available."""
