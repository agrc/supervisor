# GitHub Copilot Instructions for Supervisor

## Project Overview

Supervisor is a Python module for monitoring scheduled processes, catching errors, and sending notifications through multiple channels (email, SendGrid, console, etc.). It's designed to work with Windows' Task Scheduler but can be used with any scheduled script environment.

## Key Architecture

### Core Components

1. **Supervisor** (`models.py`): Main orchestrator that:
   - Optionally replaces `sys.excepthook` to catch all uncaught exceptions
   - Manages a list of message handlers
   - Sends notifications through all registered handlers
   - Can attach a logger for additional logging capabilities

2. **MessageHandler** (`message_handlers.py`): Abstract base class for notification handlers
   - `EmailHandler`: SMTP email support
   - `SendGridHandler`: SendGrid API email support
   - `ConsoleHandler`: Print to console
   - `SlackHandler`: Placeholder for future Slack support

3. **MessageDetails** (`models.py`): Data structure for messages with:
   - `message`: The text content
   - `subject`: Message subject
   - `attachments`: File path(s) to attach (supports single path or list; automatically gzipped or zipped)

## Code Style and Conventions

### Python Style
- Line length: 120 characters (configured in ruff)
- Indentation: 4 spaces for Python files
- Use type hints where appropriate (e.g., `handler: MessageHandler`)
- Follow PEP 8 conventions
- Use pylint disable comments sparingly and only when necessary (e.g., `# pylint: disable=invalid-name`)

### Documentation
- Use docstrings for all classes and public methods
- Follow NumPy/SciPy docstring format with sections:
  - Brief description
  - `Attributes` for class attributes
  - `Parameters` for method parameters
  - `Returns` for return values
  - `Methods` for public methods in class docstrings

### Error Handling
- Use warnings for non-critical issues that shouldn't stop execution
- Gracefully handle missing configuration (e.g., `warnings.warn()` and return early)
- Catch specific exceptions and handle them appropriately
- Log errors through the provided logger when available

## Development Workflow

### Environment Setup
- Python environment typically cloned from `arcgispro-py3`
- Install in development mode: `pip install -e ".[tests]"`

### Dependencies
- **Core**: `sendgrid==6.*`
- **Testing**: pytest suite with coverage, mocking, and instant failure reporting
- **Linting**: ruff for code quality

### Testing
- Tests located in `tests/` directory
- Use pytest with coverage tracking
- Run tests with: `pytest`
- Test coverage configured in `pyproject.toml` with branch coverage enabled
- Mock external dependencies (SMTP, SendGrid API calls)

### Common Patterns

1. **Adding a new MessageHandler**:
   - Inherit from `MessageHandler` abstract base class
   - Implement `send_message(message_details)` method
   - Handle configuration validation gracefully
   - Use warnings for missing/invalid configuration

2. **File Attachments**:
   - EmailHandler: gzips files individually
   - SendGridHandler: zips files (directories are zipped recursively)
   - Always verify paths exist before processing

3. **Configuration**:
   - Use dictionaries for handler settings
   - Include `from_address`, `to_addresses` (can be str or list)
   - Optional `prefix` for subject line prefixes
   - Handle missing keys with try/except and warnings

## Important Considerations

### Error Handling Philosophy
- Supervisor should never crash the client script due to notification failures
- Use `warnings.warn()` instead of raising exceptions for configuration issues
- Return early from `send_message()` if settings are invalid

### Version Reporting
- Handlers can report client project name and version in messages
- Use `client_name` and `client_version` parameters in handler constructors

### Backwards Compatibility
- This is a published PyPI package (`ugrc-supervisor`)
- Maintain backwards compatibility when modifying public APIs
- Update version in `src/supervisor/version.py` for releases

### File Operations
- Prefer `pathlib.Path` for internal file operations
- **Always** support both string paths and Path objects as input for backwards compatibility
- Convert string inputs to Path objects when needed: `Path(attachment)`
- Check if files/directories exist before processing attachments
- Use context managers for file operations

## Testing Guidelines

- Mock external services (SMTP servers, SendGrid API)
- Test both success and failure paths
- Verify warning messages for invalid configurations
- Test with various input types (strings, lists, Path objects)
- Ensure attachments are properly processed (gzipped/zipped)

## Code Quality

- Run `ruff` for linting before committing
- Maintain test coverage (tracked via codecov)
- Follow existing patterns in the codebase
- Keep methods focused and single-purpose
- Use static methods when methods don't need instance state
