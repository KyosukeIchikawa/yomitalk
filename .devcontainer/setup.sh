#!/bin/bash

# Post-create setup script for Yomitalk devcontainer
set -e

echo "🚀 Setting up Yomitalk development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --timeout 300 --retries 3 -r requirements.txt

# Install VOICEVOX Core if not already present
if [ ! -d "voicevox_core" ] || [ -z "$(ls -A voicevox_core 2>/dev/null)" ]; then
    echo "🎤 Setting up VOICEVOX Core..."
    chmod +x scripts/download_voicevox.sh
    scripts/download_voicevox.sh \
        --core-version 0.16.1 \
        --models-version 0.16.0 \
        --dir voicevox_core \
        --skip-if-exists \
        --accept-agreement
fi

# Install VOICEVOX Core Python module
echo "🐍 Installing VOICEVOX Core Python module..."
OS_TYPE="manylinux_2_34_x86_64"
VOICEVOX_VERSION="0.16.1"
WHEEL_URL="https://github.com/VOICEVOX/voicevox_core/releases/download/${VOICEVOX_VERSION}/voicevox_core-${VOICEVOX_VERSION}-cp310-abi3-${OS_TYPE}.whl"
pip install "${WHEEL_URL}" || echo "⚠️  Warning: Failed to install VOICEVOX Core wheel. You may need to install it manually."

# Install playwright browsers for E2E testing
echo "🎭 Installing Playwright browsers for E2E testing..."
playwright install || echo "⚠️  Warning: Failed to install Playwright browsers."

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install || echo "⚠️  Warning: Failed to install pre-commit hooks."

# Create necessary directories with proper permissions
echo "📁 Creating data directories..."
mkdir -p data/temp data/output data/logs
chmod -R 755 data

# Ensure git configuration
echo "⚙️  Configuring git..."
git config --global --add safe.directory /app

echo "✅ Yomitalk development environment setup complete!"
echo ""
echo "🎯 Quick start commands:"
echo "  • Run app:           python app.py"
echo "  • Run tests:         pytest tests/"
echo "  • Run unit tests:    pytest tests/unit/"
echo "  • Run E2E tests:     E2E_TEST_MODE=true pytest tests/e2e/"
echo "  • Format code:       black . && isort ."
echo "  • Run linting:       flake8 . && mypy ."
echo "  • Run pre-commit:    pre-commit run --all-files"
echo ""
