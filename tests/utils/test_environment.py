"""
Test environment manager for handling application process and port.
"""

import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

import requests

from tests.utils.logger import test_logger as logger


class TestEnvironment:
    """
    Manages the test environment including application process and port.
    """

    def __init__(self):
        """Initialize the test environment state."""
        self._app_process: Optional[subprocess.Popen] = None
        self._app_port: Optional[int] = None

    @property
    def app_port(self):
        """Get the application port."""
        return self._app_port

    @property
    def app_url(self):
        """Get the application URL."""
        if not self._app_port:
            return None
        return f"http://localhost:{self._app_port}"

    @property
    def is_running(self):
        """Check if the application is running."""
        if not self._app_process:
            return False
        return self._app_process.poll() is None

    def find_free_port(self):
        """
        Find an available port.

        Returns:
            int: Available port number
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def setup(self):
        """
        Set up the test environment.

        Returns:
            str: Application URL
        """
        if self.is_running:
            logger.info(f"Application already running on port {self._app_port}")
            return self.app_url

        # Find an available port
        self._app_port = self.find_free_port()

        # Set environment variables
        env = os.environ.copy()
        env["PORT"] = str(self._app_port)
        env["E2E_TEST_MODE"] = "true"

        # Get project root path
        project_root = Path(__file__).parent.parent.parent.absolute()

        # Set virtual environment Python path
        venv_path = os.environ.get("VENV_PATH", "./venv")
        python_executable = os.path.join(venv_path, "bin", "python")

        # Use default Python if virtual environment Python does not exist
        if not os.path.exists(python_executable):
            python_executable = "python"
            logger.warning(
                f"Virtual environment Python not found at {python_executable}, using system Python"
            )
        else:
            logger.info(f"Using Python from virtual environment: {python_executable}")

        # Launch application as a subprocess
        self._app_process = subprocess.Popen(
            [python_executable, "-m", "yomitalk.app"],
            env=env,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Initial wait for application startup
        logger.info(f"Starting application on port {self._app_port}...")
        time.sleep(3)  # Initial longer wait

        # Wait for application to start with retry logic
        self._wait_for_application_start()

        return self.app_url

    def _wait_for_application_start(self):
        """Wait for application to start with retry logic."""
        max_retries = 20
        retry_interval = 1.5

        for i in range(max_retries):
            try:
                response = requests.get(self.app_url, timeout=2)
                if response.status_code == 200:
                    logger.info(
                        f"✓ Application started successfully on port {self._app_port}"
                    )

                    # Check if process is running
                    if self._app_process and self._app_process.poll() is None:
                        logger.info("Application is running normally")
                        return True
                    else:
                        if self._app_process:
                            raise Exception(
                                f"Application process terminated unexpectedly with code {self._app_process.returncode}"
                            )
                        else:
                            raise Exception("Application process not found")
            except (requests.ConnectionError, requests.Timeout) as e:
                # Log error details
                error_msg = str(e)
                if self._app_process and self._app_process.poll() is not None:
                    # Process has terminated
                    stdout, stderr = self._app_process.communicate()
                    logger.error(
                        f"Application process exited with code {self._app_process.returncode}"
                    )
                    logger.error(f"stdout: {stdout.decode('utf-8', errors='ignore')}")
                    logger.error(f"stderr: {stderr.decode('utf-8', errors='ignore')}")
                    raise Exception(
                        f"Application process exited prematurely with code {self._app_process.returncode}"
                    )

                logger.info(
                    f"Waiting for application to start (attempt {i+1}/{max_retries}): {error_msg[:100]}..."
                )
                time.sleep(retry_interval)

        # Final failure
        if not self._app_process:
            logger.error("No application process found")
        elif self._app_process.poll() is None:
            # Process is still running but not responding
            logger.error(
                "Application is still running but not responding to HTTP requests."
            )
        else:
            # Process has terminated
            stdout, stderr = self._app_process.communicate()
            logger.error(
                f"Application process exited with code {self._app_process.returncode}"
            )
            logger.error(f"stdout: {stdout.decode('utf-8', errors='ignore')}")
            logger.error(f"stderr: {stderr.decode('utf-8', errors='ignore')}")

        raise Exception("Failed to start application after multiple retries")

    def teardown(self):
        """
        Tear down the test environment.
        """
        if not self._app_process:
            logger.info("No application process to terminate")
            return

        logger.info(f"Terminating application process on port {self._app_port}...")

        try:
            # Try graceful termination first
            self._app_process.terminate()
            try:
                # Wait for termination (short timeout)
                self._app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force termination
                logger.warning(
                    "Application did not terminate gracefully, killing process..."
                )
                self._app_process.kill()
                self._app_process.wait(timeout=2)
        except Exception as e:
            logger.error(f"Error during application process termination: {e}")

        # Check status
        if self._app_process.poll() is None:
            logger.warning("WARNING: Application process could not be terminated")
        else:
            logger.info(
                f"Application process terminated with code {self._app_process.returncode}"
            )

        # Clear resources
        self._app_process = None
        self._app_port = None
