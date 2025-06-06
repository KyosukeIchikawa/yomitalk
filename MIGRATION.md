# Migration Guide: Makefile/venv → Dev Containers

This guide helps you migrate from the traditional Makefile/venv setup to the new Dev Container development environment.

## Why Migrate?

### Benefits of Dev Containers
- **Zero setup**: One-click development environment
- **Consistency**: Same environment across all developers and CI/CD
- **Isolation**: No conflicts with host system packages
- **VS Code integration**: Seamless debugging, testing, and development tools
- **Docker alignment**: Development environment matches production container

### Before (Makefile/venv)
```bash
make setup           # Manual setup required
source venv/bin/activate  # Manual activation
make run            # Run commands
```

### After (Dev Container)
```bash
# Just open in VS Code and reopen in container
# Everything is automatic!
python app.py       # Direct commands
```

## Migration Steps

### 1. Prerequisites

Install required tools:
- [Docker](https://docs.docker.com/get-docker/)
- [VS Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### 2. Clean Up Old Environment (Optional)

If you want to start fresh:

```bash
# Clean up old virtual environment and generated files
make clean

# Or manually:
rm -rf venv/
rm -rf data/temp/* data/output/*
rm -rf __pycache__ .pytest_cache
```

### 3. Open in Dev Container

1. **Open VS Code:**
   ```bash
   code .
   ```

2. **Reopen in Container:**
   - Press `F1`
   - Type "Dev Containers: Reopen in Container"
   - Select the command
   - Wait for container to build and setup to complete

3. **First-time setup:**
   - Container builds automatically (5-10 minutes first time)
   - VOICEVOX Core downloads automatically
   - All dependencies install automatically
   - Pre-commit hooks setup automatically

### 4. Verify Setup

Test that everything works:

```bash
# Run the application
python app.py

# Run tests
pytest tests/

# Check linting
flake8 . && mypy .
```

### 5. Update Your Workflow

#### Old Workflow
```bash
source venv/bin/activate  # Activate environment
make run                  # Run application
make test                 # Run tests
make lint                 # Run linting
make format               # Format code
deactivate               # Deactivate environment
```

#### New Workflow
```bash
# No activation needed - just use commands directly
python app.py            # Run application
pytest tests/            # Run tests
flake8 . && mypy .       # Run linting
black . && isort .       # Format code

# Or use VS Code tasks:
# Ctrl+Shift+P → "Tasks: Run Task" → Select task
```

## Command Mapping

| Old (Make) | New (Direct) | VS Code Task |
|------------|--------------|-------------|
| `make setup` | Automatic via devcontainer | N/A |
| `make run` | `python app.py` | "Run Yomitalk App" |
| `make test` | `pytest tests/` | "Run All Tests" |
| `make test-unit` | `pytest tests/unit/` | "Run Unit Tests" |
| `make test-e2e` | `E2E_TEST_MODE=true pytest tests/e2e/` | "Run E2E Tests" |
| `make lint` | `flake8 . && mypy .` | "Run Linting" |
| `make format` | `black . && isort .` | "Format Code" |
| `make pre-commit-run` | `pre-commit run --all-files` | "Run Pre-commit" |
| `make clean` | "Dev Containers: Rebuild Container" | N/A |

## VS Code Integration

### Tasks
Access via `Ctrl+Shift+P` → "Tasks: Run Task":
- Run Yomitalk App
- Run All Tests
- Run Unit Tests
- Run E2E Tests
- Format Code
- Run Linting
- Run Pre-commit

### Debugging
- **F5**: Debug current configuration
- **Ctrl+F5**: Run without debugging
- Configurations available for app, unit tests, E2E tests

### Extensions
Automatically installed and configured:
- Python
- Black Formatter
- isort
- Flake8
- MyPy Type Checker
- Jupyter
- Jinja
- Playwright

## Troubleshooting

### Container Won't Start
1. Ensure Docker is running
2. Check Docker Desktop has enough resources (4GB+ RAM recommended)
3. Try "Dev Containers: Rebuild Container"

### VOICEVOX Download Fails
```bash
# Run setup script manually in container terminal
bash .devcontainer/setup.sh
```

### Port 7860 Not Accessible
1. Check VS Code port forwarding tab
2. Ensure app binds to `0.0.0.0:7860`, not `localhost:7860`
3. Check firewall settings

### Slow Performance
1. Use Docker volumes for large directories (already configured)
2. Increase Docker Desktop resource allocation
3. Consider using WSL2 backend on Windows

### Permission Issues
```bash
# In container terminal
sudo chown -R vscode:vscode /workspace
```

## Keeping Both Approaches

You can use both approaches simultaneously:

### Dev Container (Recommended)
- Daily development
- Debugging and testing
- Code review and collaboration

### Makefile (Backup)
- CI/CD environments without container support
- Quick local testing
- Legacy system compatibility

The Makefile is still maintained and functional for those who prefer it or need it for specific scenarios.

## Getting Help

- **Dev Container Issues**: See `.devcontainer/README.md`
- **Application Issues**: See main `README.md`
- **Architecture Questions**: See `docs/design.md`
- **Development Guidelines**: See `CLAUDE.md`

## Benefits You'll Notice

### Immediate
- No more virtual environment management
- Consistent Python environment
- Pre-configured development tools
- Integrated VS Code experience

### Long-term
- Same environment across team members
- Easier onboarding for new developers
- Better CI/CD environment alignment
- Simplified Docker deployment
