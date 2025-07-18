.PHONY: setup venv install setup-lint clean run test test-unit test-e2e test-staged create-sample-pdf help lint format pre-commit-install pre-commit-run download-voicevox-core install-voicevox-core-module install-system-deps install-python-packages install-python-packages-lint requirements

#--------------------------------------------------------------
# Variables and Configuration
#--------------------------------------------------------------
# Python related
PYTHON = python
VENV_DIR = venv
VENV_PYTHON = $(VENV_DIR)/bin/python
VENV_PIP = $(VENV_DIR)/bin/pip
VENV_PRECOMMIT = $(VENV_DIR)/bin/pre-commit

# VOICEVOX related
VOICEVOX_VERSION = 0.16.0
VOICEVOX_SKIP_IF_EXISTS ?= true
VOICEVOX_ACCEPT_AGREEMENT ?= false
VOICEVOX_DIR = voicevox_core
VOICEVOX_CHECK_MODULE = $(VENV_PYTHON) -c "import voicevox_core" 2>/dev/null

# Source code related
SRC_DIRS = yomitalk tests app.py
CACHE_DIRS = __pycache__ app/__pycache__ app/components/__pycache__ app/utils/__pycache__ \
             tests/__pycache__ tests/unit/__pycache__ tests/e2e/__pycache__ tests/data/__pycache__ \
             .pytest_cache
DATA_DIRS = data/temp/* data/output/*

# Default target
.DEFAULT_GOAL := help

#--------------------------------------------------------------
# Help and Basic Setup
#--------------------------------------------------------------
# Help message
help:
	@echo "Paper Podcast Generator Makefile"
	@echo ""
	@echo "Usage:"
	@echo "【Setup】"
	@echo "  make setup        - Setup virtual environment and install packages"
	@echo "  make venv         - Setup virtual environment only"
	@echo "  make install      - Install dependency packages only"
	@echo "  make setup-lint   - Install linting packages only"
	@echo "【Development】"
	@echo "  make run          - Run the application"
	@echo "  make lint         - Run static code analysis (ruff check, mypy)"
	@echo "  make format       - Auto-format and fix code issues (ruff format, ruff check --fix)"
	@echo "  make pre-commit-install - Install pre-commit hooks"
	@echo "  make pre-commit-run    - Run pre-commit hooks manually"
	@echo "【Testing】"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-e2e     - Run E2E tests only"
	@echo "  make test-staged  - Run unit tests for staged files only"
	@echo "【VOICEVOX】"
	@echo "  make download-voicevox-core - Download and setup VOICEVOX Core"
	@echo "  make install-voicevox-core-module - Install VOICEVOX Core Python module"
	@echo "  VOICEVOX_ACCEPT_AGREEMENT=true - Set to auto-accept VOICEVOX license agreement"
	@echo "【Cleanup】"
	@echo "  make clean        - Remove virtual environment and generated files"
	@echo ""

install-system-deps:
	@echo "Installing system dependencies..."
	sudo apt-get update
	$(MAKE) download-voicevox-core
	@echo "System dependencies installation completed!"

venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Setting up virtual environment..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "Virtual environment created at $(VENV_DIR)"; \
	else \
		echo "Virtual environment already exists at $(VENV_DIR)"; \
	fi

install-python-packages: venv
	@echo "Installing python packages..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements.txt
	$(MAKE) install-voicevox-core-module
	@echo "Python packages installed"

install-python-packages-lint: venv
	@echo "Installing linting packages..."
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r requirements-lint.txt
	@echo "Linting packages installed"

setup-lint: venv install-python-packages-lint
	@echo "Setup lint completed!"

setup: install-system-deps venv install-python-packages-lint install-python-packages pre-commit-install
	@echo "Setup completed!"

#--------------------------------------------------------------
# VOICEVOX Related
#--------------------------------------------------------------
# Download and setup VOICEVOX Core
download-voicevox-core: venv
	@echo "Running VOICEVOX Core download script..."
	@scripts/download_voicevox.sh \
		--version $(VOICEVOX_VERSION) \
		--dir $(VOICEVOX_DIR) \
		$(if $(filter true, $(VOICEVOX_SKIP_IF_EXISTS)), --skip-if-exists) \
		$(if $(filter true, $(VOICEVOX_ACCEPT_AGREEMENT)), --accept-agreement)
	@if [ $$? -ne 0 ]; then \
		echo "Error: Failed to download VOICEVOX Core. Check logs for details."; \
		exit 1; \
	fi

# Install VOICEVOX Core Python module
install-voicevox-core-module: venv
	@echo "Installing VOICEVOX Core Python module..."
	@OS_TYPE="manylinux_2_34_x86_64"; \
	WHEEL_URL="https://github.com/VOICEVOX/voicevox_core/releases/download/$(VOICEVOX_VERSION)/voicevox_core-$(VOICEVOX_VERSION)-cp310-abi3-$$OS_TYPE.whl"; \
	$(VENV_PIP) install $$WHEEL_URL || echo "Failed to install wheel for $$OS_TYPE. Check available wheels at https://github.com/VOICEVOX/voicevox_core/releases/tag/$(VOICEVOX_VERSION)"
	@echo "VOICEVOX Core Python module installed!"

#--------------------------------------------------------------
# Development Tools
#--------------------------------------------------------------
# Run the application
run: venv
	@echo "Running application..."
	$(VENV_PYTHON) app.py

# Run static analysis (lint)
lint: setup-lint
	@echo "Running static code analysis..."
	$(VENV_DIR)/bin/ruff check $(SRC_DIRS)
	$(VENV_DIR)/bin/mypy $(SRC_DIRS)
	@echo "Static analysis completed"

# Format code
format: setup-lint
	@echo "Running code formatting and issue fixes..."
	$(VENV_DIR)/bin/ruff check --fix $(SRC_DIRS)
	$(VENV_DIR)/bin/ruff format $(SRC_DIRS)
	@echo "Formatting completed"

# Install pre-commit hooks
pre-commit-install: setup-lint
	@echo "Installing pre-commit hooks..."
	$(VENV_PRECOMMIT) install
	@echo "Pre-commit hooks installed"

# Run pre-commit hooks
pre-commit-run: setup-lint
	@echo "Running pre-commit hooks..."
	$(VENV_PRECOMMIT) run --all-files
	@echo "Pre-commit hooks execution completed"

# Run linting checks for CI (check only, no modifications)
lint-ci: setup-lint
	@echo "Running linting checks for CI (check only)..."
	@echo "Ruff version: $$($(VENV_DIR)/bin/ruff --version)"
	@echo "Current directory: $$(pwd)"
	@echo "Python version: $$($(VENV_DIR)/bin/python --version)"
	$(VENV_DIR)/bin/ruff check --ignore I001 $(SRC_DIRS)
	$(VENV_DIR)/bin/ruff format --check $(SRC_DIRS)
	@echo "Linting checks completed"

#--------------------------------------------------------------
# Testing
#--------------------------------------------------------------
# Run all tests
test: venv
	@echo "Running tests..."
	$(VENV_PYTHON) -m pytest tests/ --durations=10

# Run unit tests only
test-unit: venv
	@echo "Running unit tests..."
	$(VENV_PYTHON) -m pytest tests/unit/ --durations=10

# Run E2E tests only
test-e2e: venv
	@echo "Running E2E tests..."
	E2E_TEST_MODE=true $(VENV_PYTHON) -m pytest tests/e2e/ --durations=10

# Run tests for staged files only
test-staged: venv
	@echo "Running tests for staged files..."
	$(VENV_DIR)/bin/python .pre-commit-hooks/run_staged_tests.py

#--------------------------------------------------------------
# Cleanup
#--------------------------------------------------------------
# Clean up generated files
clean:
	@echo "Removing generated files..."
	rm -rf $(VENV_DIR)
	rm -rf $(DATA_DIRS)
	rm -rf $(CACHE_DIRS)
	@echo "Cleanup completed"

requirements:
	pip-compile -v requirements.in > requirements.txt
