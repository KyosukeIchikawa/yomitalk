# GitHub Copilot Instructions for Yomitalk

## 📖 **Project Documentation Reference**

**IMPORTANT**: For comprehensive project information, always refer to [`docs/design.md`](../docs/design.md) first.

This file provides GitHub Copilot-specific coding assistance patterns and quick references.

## Quick Project Overview

Yomitalk converts documents into podcast-style audio using VOICEVOX character voices with dual LLM support (OpenAI/Gemini).

**Architecture**: Session-based multi-user system with streaming audio generation and comprehensive progress tracking.

## Core Development Patterns

### Essential Imports
```python
from yomitalk.user_session import UserSession
from yomitalk.common import APIType
from yomitalk.components.audio_generator import initialize_global_voicevox_manager
```

### Session Management Pattern
```python
# Always work within UserSession context
user_session = UserSession(session_id)
user_session.auto_save()  # After state changes
```

## Code Quality Standards

### Language & Style
- **Code**: English (comments, logs, variable names)
- **UI**: Japanese (user-facing messages)
- **Documentation**: Japanese (design docs, README)
- **Style**: PEP 8 with black, isort, flake8, mypy

### Required Patterns
```python
# Error handling with user-friendly messages
try:
    result = some_operation()
except SpecificException as e:
    error_html = self._create_error_html(f"User-friendly message: {str(e)}")
    yield None, user_session, error_html, None

# Theme integration
style = """
    color: var(--body-text-color, #111827);
    background: var(--background-fill-secondary, #f8f9fa);
    border: none; box-shadow: none;
"""
```

## Testing Quick Reference

### BDD Feature Pattern
```gherkin
Scenario: Audio generation with progress display
  Given a podcast script has been generated
  When I click the "音声を生成" button
  Then audio generation progress should be visible
```

## File Structure Quick Reference

- `yomitalk/app.py`: Main Gradio application
- `yomitalk/user_session.py`: Session management
- `yomitalk/components/`: Core functionality
- `yomitalk/models/`: LLM integrations
- `yomitalk/templates/`: Jinja2 templates
- `tests/unit/`: Component tests
- `tests/e2e/`: BDD tests

## Security Guidelines

- **Never persist API keys** - memory only
- Use session directories: `data/{temp,output}/{session_id}/`
- Filter sensitive info from logs
- Validate session boundaries

## Common Gradio Patterns

```python
# Event chaining
event.then(fn=next_function, inputs=[...], outputs=[...])

# Queue configuration
concurrency_limit=1, concurrency_id="audio_queue"
```

## Development Commands

```bash
# Development
python app.py                    # Start application
pytest tests/                    # Run all tests
pytest tests/unit/               # Unit tests only
E2E_TEST_MODE=true pytest tests/e2e/  # E2E tests

# Code quality
flake8 . && mypy .              # Static analysis
black . && isort .              # Format code
```

## 🚫 Common Pitfalls to Avoid

- Don't persist API keys in session state
- Don't use hardcoded file paths
- Don't break session isolation
- Don't skip error handling in streaming functions
- Don't use `--no-verify` for git commits
- Don't create complex UI with redundant borders
