# Development container for Yomitalk
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    make \
    build-essential \
    ffmpeg \
    sudo \
    # For playwright browsers
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    # For VS Code development
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Create vscode user for development
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid vscode --shell /bin/bash --create-home vscode \
    && echo 'vscode ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Set up working directory
WORKDIR /workspace

# Install Python development tools globally (no venv needed in container)
COPY requirements.in requirements-lint.txt ./
RUN pip install --upgrade pip && \
    pip install --timeout 600 --retries 5 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --timeout 300 --retries 3 -r requirements-lint.txt

# Install pip-tools for requirements management
RUN pip install pip-tools

# Switch to vscode user
USER vscode

# Set environment variables for development
ENV PYTHONPATH=/workspace
ENV VOICEVOX_ACCEPT_AGREEMENT=true
ENV PAGER=cat
ENV LESSCHARSET=utf-8

# Default command (will be overridden by devcontainer)
CMD ["sleep", "infinity"]
