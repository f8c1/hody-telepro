# Hody-Telepro

[![CI](https://github.com/f8c1/hody-telepro/actions/workflows/ci.yml/badge.svg)](https://github.com/f8c1/hody-telepro/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT- green)](LICENSE)

An asynchronous Python toolkit for **authorized Telegram entity inspection**, CLI workflows, caching, plugins, and structured exports.

> Use this project only with accounts, data, and Telegram access that you are authorized to inspect. Results can be incomplete or estimated; they are not an official source of identity or account history.

## Why this project exists

Telegram automation projects often repeat the same concerns: asynchronous entity access, safe retry behavior, local caching, structured models, and useful exports. Hody-Telepro packages these concerns behind a small async API and a command-line interface that can be adapted to legitimate internal tools and research workflows.

## Features

- Asynchronous entity inspection for users, bots, channels, and groups
- Configurable retry and FloodWait-aware backoff helpers
- Persistent local session and cache support
- Plugin hooks for domain-specific enrichment
- JSON, CSV, SQLite, and HTML export paths
- Batch inspection with bounded concurrency
- Typed public models and custom exceptions
- CLI commands for inspection, batch workflows, estimation, and statistics

## Installation

```bash
python -m pip install hody-telepro
```

Optional development and reporting dependencies:

```bash
python -m pip install 'hody-telepro[dev]'
python -m pip install 'hody-telepro[full]'
```

## Quick start

Set the Telegram credentials in your shell or a local `.env` file that is never committed:

```bash
export TELEGRAM_API_ID=12345
export TELEGRAM_API_HASH='replace-with-your-api-hash'
```

Then use the async client:

```python
import asyncio
from hody_telepro import HodyClient


async def main() -> None:
    async with HodyClient(
        'demo_session',
        api_id=12345,
        api_hash='replace-with-your-api-hash',
    ) as client:
        result = await client.inspect('@telegram')
        print(result.entity.full_name)


if __name__ == '__main__':
    asyncio.run(main())
```

## CLI examples

```bash
hody-telepro --help
hody-telepro --api-id "$TELEGRAM_API_ID" --api-hash "$TELEGRAM_API_HASH" inspect @telegram
hody-telepro estimate 12345
hody-telepro stats
```

Do not place API credentials, session files, phone numbers, or private exports in a public repository.

## Architecture

```text
src/hody_telepro/
├── client.py                 Public async client
├── models/                   Typed entity and result models
├── engines/                  Inspection and retry helpers
├── cache/                    Persistent cache and single-flight support
├── exporters/                JSON, CSV, SQLite, and HTML exporters
├── algorithms/               Account-estimation utilities
├── plugins/                  Extension points and built-in plugins
├── cli/                      Command-line interface
└── utils/                    Exceptions and shared utilities
```

## Development

```bash
git clone https://github.com/f8c1/hody-telepro.git
cd hody-telepro
PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10 python -m pip install --break-system-packages --retries 10 --timeout 120 --index-url https://pypi.org/simple -e '.[dev]'
pytest -q
ruff check src tests
mypy src/hody_telepro
```

## Privacy and responsible use

This software is intended for authorized development, testing, research, and automation. Do not use it to harass, identify, profile, or monitor people without a lawful basis and appropriate permission. Review Telegram's terms and the laws applicable to your use case. Treat phone numbers, session files, exported metadata, and logs as sensitive data. The account-creation estimator is a heuristic and must not be presented as an official Telegram record.

## Limitations

Network behavior, Telegram API permissions, rate limits, entity visibility, and library compatibility can affect results. The project does not guarantee completeness, accuracy, availability, or uninterrupted access. Validate behavior in a controlled environment before using it in production.

## Contributing

Issues and pull requests are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and avoid including credentials, session files, personal data, or private Telegram exports in reports.

## Security

Please read [SECURITY.md](SECURITY.md) for responsible disclosure guidance.

## License

MIT License. See [LICENSE](LICENSE).
