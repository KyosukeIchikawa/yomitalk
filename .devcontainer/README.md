# Yomitalk Development Container

This directory contains the development container configuration for Yomitalk, enabling a consistent and reproducible development environment using VS Code Dev Containers.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Getting Started

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd yomitalk
   ```

2. **Open in VS Code:**
   ```bash
   code .
   ```

3. **Open in Dev Container:**
   - Press `F1` and select "Dev Containers: Reopen in Container"
   - Or click the popup notification to reopen in container
   - Wait for the container to build and setup to complete

4. **Start developing:**
   - The environment will be automatically configured
   - VOICEVOX Core will be downloaded and installed
   - All Python dependencies will be installed
   - Pre-commit hooks will be configured

## Development Workflow

### Running the Application

```bash
# Run the Yomitalk web application
python app.py

# Or use VS Code task (Ctrl+Shift+P -> "Tasks: Run Task" -> "Run Yomitalk App")
```

The application will be available at `http://localhost:7860`

### Testing

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run E2E tests only
E2E_TEST_MODE=true pytest tests/e2e/

# Use VS Code tasks for better integration
```

### Code Quality

```bash
# Format code
black . && isort .

# Run linting
flake8 . && mypy .

# Run pre-commit hooks
pre-commit run --all-files
```

### Common Commands

| Task | Command | VS Code Task |
|------|---------|-------------|
| Run app | `python app.py` | "Run Yomitalk App" |
| All tests | `pytest tests/` | "Run All Tests" |
| Unit tests | `pytest tests/unit/` | "Run Unit Tests" |
| E2E tests | `E2E_TEST_MODE=true pytest tests/e2e/` | "Run E2E Tests" |
| Format | `black . && isort .` | "Format Code" |
| Lint | `flake8 . && mypy .` | "Run Linting" |
| Pre-commit | `pre-commit run --all-files` | "Run Pre-commit" |

## Container Architecture

### Base Image
- **Python 3.11 slim**: Official Python image for consistent Python environment
- **System packages**: FFmpeg, build tools, and browser dependencies for Playwright

### Development Features
- **Non-root user**: `vscode` user for security and VS Code integration
- **Persistent volumes**: Separate volumes for data and VOICEVOX models
- **Port forwarding**: Automatic port 7860 forwarding for web access
- **Extensions**: Pre-configured VS Code extensions for Python development

### File Structure

```
.devcontainer/
├── devcontainer.json    # Main configuration file
├── docker-compose.yml   # Multi-service container setup
├── Dockerfile          # Development container image
├── setup.sh            # Post-creation setup script
└── README.md           # This file
```

## Customization

### Adding Extensions

Edit `.devcontainer/devcontainer.json`:

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "existing-extensions...",
        "new.extension.id"
      ]
    }
  }
}
```

### Environment Variables

Add to `containerEnv` in `devcontainer.json`:

```json
{
  "containerEnv": {
    "NEW_VAR": "value"
  }
}
```

### System Packages

Edit `.devcontainer/Dockerfile` and add to the `RUN apt-get install` command.

## Troubleshooting

### Container Build Issues

1. **Clean rebuild:**
   ```bash
   # Remove container and rebuild
   # In VS Code: "Dev Containers: Rebuild Container"
   ```

2. **VOICEVOX download fails:**
   ```bash
   # Manually run setup in container terminal
   bash .devcontainer/setup.sh
   ```

3. **Permission issues:**
   ```bash
   # Fix ownership (run in container terminal)
   sudo chown -R vscode:vscode /workspace
   ```

### Performance Issues

1. **Slow file access:**
   - Ensure using volume mounts for large directories (data, voicevox_core)
   - Check Docker Desktop resource allocation

2. **Memory issues:**
   - Increase Docker Desktop memory limit
   - VOICEVOX and ML models require significant RAM

### Network Issues

1. **Port forwarding not working:**
   - Check VS Code port forwarding tab
   - Ensure application binds to `0.0.0.0:7860`, not `localhost:7860`

2. **Internet access for downloads:**
   - Check Docker network configuration
   - Verify proxy settings if behind corporate firewall

## Migration from Makefile/venv

### Key Changes

- **No virtual environment**: Python packages installed globally in container
- **No make commands**: Use VS Code tasks or direct commands
- **Persistent data**: Data and models stored in Docker volumes
- **Integrated tools**: Linting, formatting, and testing integrated with VS Code

### Old vs New Commands

| Old (Makefile) | New (Devcontainer) |
|----------------|-------------------|
| `make setup` | Automatic via `postCreateCommand` |
| `make run` | `python app.py` or VS Code task |
| `make test` | `pytest tests/` or VS Code task |
| `make lint` | `flake8 . && mypy .` or VS Code task |
| `make format` | `black . && isort .` or VS Code task |
| `make clean` | "Dev Containers: Rebuild Container" |

## Benefits

### Developer Experience
- **Zero setup**: One-click development environment
- **Consistency**: Same environment across all developers
- **Isolation**: No conflicts with host system packages
- **Integration**: Deep VS Code integration with debugging, testing, and formatting

### CI/CD Alignment
- **Same base**: Development and production environments share base image
- **Reproducible**: Exact same dependencies and versions
- **Testable**: E2E tests run in similar environment to production
