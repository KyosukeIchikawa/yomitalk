"""Module implementing common test steps shared across all scenarios."""
from playwright.sync_api import Page
from pytest_bdd import given

# Import setup function from conftest
from tests.e2e.steps.conftest import setup_test_environment


@given("the application is running")
def application_is_running(page: Page):
    """
    Set up the application for testing and navigate to it

    Args:
        page: Playwright page object
    """
    # Setup test environment and get app port
    app_port = setup_test_environment()

    # Navigate to the application
    app_url = f"http://localhost:{app_port}"
    page.goto(app_url)

    # Wait for the application to load
    page.wait_for_load_state("networkidle")

    # Verify that the application has loaded properly
    assert page.title() != "", "Application failed to load properly"
