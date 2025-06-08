# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📖 **Important**: Read the Design Document First
Before working on this codebase, **read [docs/design.md](docs/design.md)** for comprehensive architectural overview, including:
- Session management system design
- Component architecture and patterns
- Multi-user session isolation
- State persistence implementation
- Testing strategies and patterns

## Essential Commands

### Dev Container Setup (Recommended)

**Open in VS Code Dev Container:**
- Press `F1` → "Dev Containers: Reopen in Container"
- Automatic setup: dependencies, VOICEVOX Core, pre-commit hooks

**Development Commands:**
```bash
python app.py                    # Start the Gradio application on port 7860
pytest tests/                    # Run all tests (unit + E2E)
pytest tests/unit/               # Run unit tests only
E2E_TEST_MODE=true pytest tests/e2e/  # Run E2E tests
flake8 . && mypy .              # Run static analysis
black . && isort .              # Auto-format code
pre-commit run --all-files      # Run pre-commit hooks manually
```

**VS Code Integration:** Use `Ctrl+Shift+P` → "Tasks: Run Task" for GUI access to all commands

### Traditional Setup (Legacy)

<details>
<summary>Makefile/venv commands (still supported)</summary>

```bash
# Setup and Environment
make setup              # Complete setup: deps, VOICEVOX, lint tools, pre-commit
make venv              # Create virtual environment only
make install           # Install Python packages only
make download-voicevox-core  # Download VOICEVOX Core for audio generation

# Development
make run               # Start the Gradio application on port 7860
make lint              # Run flake8 and mypy static analysis
make format            # Auto-format code with black, isort, autoflake, autopep8

# Testing
make test              # Run all tests (unit + E2E)
make test-unit         # Run unit tests only
make test-e2e          # Run E2E tests (sets E2E_TEST_MODE=true)
make test-staged       # Run tests only for staged files

# Pre-commit Hooks
make pre-commit-install  # Install pre-commit hooks
make pre-commit-run     # Run pre-commit hooks manually
```

</details>

## Architecture Overview

**📋 For detailed architecture information, see [docs/design.md](docs/design.md)**

### Session-Based Multi-User Design
- **UserSession**: Each user gets isolated state with unique session directories
- **Global Resources**: VOICEVOX Core manager shared across users for performance
- **Session Cleanup**: Automatic cleanup of sessions older than 1 day
- **File Isolation**: Per-session temp/output directories under `data/{temp,output}/{session_id}/`
- **State Persistence**: Automatic save/restore of session state via JSON serialization

### Component Architecture
The codebase follows a clean component separation:

- **TextProcessor** (`yomitalk/components/text_processor.py`): LLM integration and script generation
- **AudioGenerator** (`yomitalk/components/audio_generator.py`): VOICEVOX integration and audio synthesis
- **ContentExtractor** (`yomitalk/components/content_extractor.py`): File/URL content extraction
- **PromptManager** (`yomitalk/prompt_manager.py`): Template-based prompt generation

### Dual LLM Support
- **Unified Interface**: Both OpenAI and Gemini models implement the same interface
- **Runtime Switching**: Users can switch between APIs during their session
- **Template System**: Jinja2 templates in `yomitalk/templates/` for different document types
- **Character Mapping**: Dynamic character assignment for dialogue generation

### Streaming Audio Pipeline
The audio generation follows a streaming pattern:
1. **Script Generation**: LLM creates character dialogue
2. **Character Extraction**: Parse dialogue into character-specific segments
3. **Streaming Synthesis**: VOICEVOX generates audio chunks yielded immediately
4. **Final Combination**: In-memory WAV combination for complete audio file

### Session Persistence System
- **Automatic Save/Restore**: All user settings persist across browser sessions
- **Security**: API keys excluded from persistence for security reasons
- **File Storage**: Session state saved to `data/temp/{session_id}/session_state.json`
- **Auto-Save Triggers**: Every setting change automatically saves session state
- **Restoration Info**: Methods to detect missing API keys and session status

### Key Design Patterns
- **Session Dependency Injection**: UserSession owns and manages component instances
- **Enum-Driven Configuration**: Type-safe configuration via Character, DocumentType, PodcastMode enums
- **Global Singleton**: VOICEVOX Core manager initialized once at startup
- **Template-Based Generation**: Jinja2 templates for flexible content generation

## Testing Structure

### Test Organization
- **Unit Tests** (`tests/unit/`): Component isolation with mocking
- **E2E Tests** (`tests/e2e/`): Full user workflows with BDD (Gherkin features)
- **Playwright Integration**: Browser automation for E2E testing
- **Test Data**: Isolated test data directories per test type

### BDD Features
Located in `tests/e2e/features/`, written in Gherkin syntax:
- `audio_generation.feature`
- `file_upload.feature`
- `script_generation.feature`
- `text_management.feature`
- `url_extraction.feature`
- `voicevox_sharing.feature`

## Important Implementation Notes

### VOICEVOX Integration
- **Global Manager**: One instance shared across all users (expensive to initialize)
- **Character Support**: Zundamon, Shikoku Metan, Kyushu Sora, Chugoku Usagi, Chubu Tsurugi
- **English Handling**: Automatic katakana conversion for technical terms
- **Natural Speech**: Smart word splitting to avoid robotic delivery

### Session Management
- **Isolation**: Each user gets completely isolated file system and state
- **Cleanup**: Automatic cleanup prevents disk space issues
- **State Persistence**: Audio generation state, LLM configuration maintained per session

### Error Handling Patterns
- **Graceful Degradation**: Components fail gracefully with user-friendly messages
- **Resource Cleanup**: Proper cleanup of session files and temporary data
- **API Resilience**: Handle LLM API failures and VOICEVOX errors appropriately

### Development Workflow
- **TDD Approach**: Write tests before implementation (per project rules)
- **Trunk-Based Development**: Direct commits to main branch
- **No --no-verify**: Pre-commit hooks must always run
- **English Comments**: Code comments and logs in English
- **Small Commits**: Frequent, small commits preferred

## Working with This Codebase

### When Adding Features
1. **Start with Tests**: Write unit tests first (TDD approach)
2. **Respect Session Boundaries**: Work within UserSession context
3. **Use Components**: Leverage existing TextProcessor, AudioGenerator, ContentExtractor
4. **Follow Templates**: Use PromptManager for any LLM interactions
5. **Handle Both APIs**: Ensure new features work with both OpenAI and Gemini
6. **Add Auto-Save**: If your feature modifies session state, add `user_session.auto_save()` calls

### When Debugging
1. **Check Session State**: User issues often relate to session-specific state
2. **Component Boundaries**: Verify component interactions work correctly
3. **VOICEVOX Status**: Audio issues usually relate to VOICEVOX Core availability
4. **Template Rendering**: Script generation issues often in Jinja2 templates

### Development Rules
- **NEVER use `--no-verify`**: All commits must pass pre-commit hooks
- **Fix issues properly**: Don't bypass linting, formatting, or type checking
- **Test before commit**: Ensure all tests pass before committing
- **Commit messages**: Do NOT include Claude as co-author in commit messages

### Performance Considerations
- **VOICEVOX Shared**: Don't reinitialize VOICEVOX Core per user
- **Session Cleanup**: Old sessions auto-cleanup, but manual cleanup may be needed
- **Memory Usage**: Audio generation can be memory-intensive with long content
- **Streaming**: Use streaming patterns for better user experience

### File Structure Key Points
- **Session Directories**: `data/temp/{session_id}/` and `data/output/{session_id}/`
- **Session State**: `data/temp/{session_id}/session_state.json` for persistence
- **Templates**: `yomitalk/templates/*.j2` for prompt generation
- **Components**: `yomitalk/components/` for core functionality
- **Models**: `yomitalk/models/` for LLM integrations
- **Common**: `yomitalk/common/` for enums and shared types
- **Session Management**: `yomitalk/user_session.py` for state persistence
