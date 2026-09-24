# Contributing

Thank you for helping improve Hody-Telepro.

## Before opening an issue

Please search existing issues and include the Python version, package version, operating system, a minimal reproduction, and the expected versus actual behavior. Never include Telegram API credentials, session files, phone numbers, private exports, or personal data.

## Development

```bash
PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10 python -m pip install --break-system-packages --retries 10 --timeout 120 --index-url https://pypi.org/simple -e '.[dev]'
pytest -q
ruff check src tests
mypy src/hody_telepro
```

Keep public APIs documented, add regression tests for behavior changes, and keep commits focused.
