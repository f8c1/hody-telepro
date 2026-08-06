# Hody-Telepro

> An ultra-fast, asynchronous, enterprise-grade Python library for Telegram metadata extraction, entity inspection, and phone number lookup.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)
![Tests](https://img.shields.io/badge/tests-64%2F64%20passing-brightgreen.svg)

---

## Overview

**Hody-Telepro** is the most advanced and fastest Python library designed for Telegram metadata extraction and deep account analysis. Built with enterprise-grade architecture, it provides developers with a unified, simple API for inspecting accounts, bots, channels, and groups with maximum precision and minimal resource consumption.

## Core Features

### Entity Inspection
Pass any identifier (`@username` or ID) to automatically retrieve the full metadata of any Telegram entity (user, bot, channel, or group) with comprehensive details and photo references.

### Phone Lookup
Enter a phone number to retrieve the complete associated account (username, ID, profile photo, bio).

### Account Creation Estimation
Accurately estimate the creation date of any Telegram account using a binary search clustering algorithm — no external connections required.

### Smart Anti-Flood Protection
Built-in rate limiting with single-flight pattern, exponential backoff, and priority queue management to prevent Telegram API bans.

### Async Persistent Sessions
SQLite-backed session storage for instant resumption and direct SQL queries.

### Plugin System
Extensible architecture allowing custom functionality without modifying core code.

### Multi-Format Export
Export results to JSON, CSV, SQLite, or generate styled HTML reports.

---

## Architecture

Hody-Telepro is built according to the highest standards of Clean Architecture using cutting-edge technologies:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Core Engine** | Pyrogram v2 + TgCrypto (C) | 3-5x faster than traditional libraries via MTProto 2.0 |
| **Data Modeling** | msgspec (Rust) | 4x faster than Pydantic, minimal memory footprint |
| **Concurrency** | asyncio + aiocache | Single-flight pattern prevents FloodWait errors |
| **Algorithms** | Binary Search O(log n) | Precise account creation date estimation |
| **Storage** | aiosqlite | Persistent async sessions and cache |
| **CLI** | Click + Rich | Colorful terminal output with progress bars |
| **Package** | PEP 621 + uv | Ultra-fast builds and PyPI publishing |

---

## Installation

```bash
# Basic installation
pip install hody-telepro

# With full features (pandas, HTML reports)
pip install hody-telepro[full]

# Development installation
pip install hody-telepro[dev]
```

---

## Quick Start

### Basic Inspection

```python
import asyncio
from hody_telepro import HodyClient

async def main():
    async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
        # Inspect a user
        result = await client.inspect("@telegram")
        print(f"Name: {result.entity.full_name}")
        print(f"Type: {result.entity.entity_type.value}")
        print(f"Verified: {result.entity.is_verified}")
        print(f"Time: {result.inspection_time_ms:.2f}ms")

asyncio.run(main())
```

### Phone Lookup

```python
async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
    result = await client.lookup_phone("+1234567890")
    print(f"Username: {result.username}")
    print(f"Name: {result.full_name}")
```

### Account Creation Estimation

```python
from hody_telepro.algorithms import AccountCreationEstimator

estimator = AccountCreationEstimator()
result = estimator.estimate(12345)

print(f"Created: {result.estimated_month} {result.estimated_year}")
print(f"Confidence: {result.confidence:.2%}")
```

### Batch Processing

```python
async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
    results = await client.inspect_batch(
        ["@telegram", "@durov", "@BotFather"],
        max_concurrent=5
    )
    for r in results:
        print(f"{r.entity.full_name} ({r.entity.entity_type.value})")
```

### With Plugins

```python
from hody_telepro.plugins import BotIntelligencePlugin, SecurityCheckPlugin

async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
    client.register_plugin("bot_intel", BotIntelligencePlugin())
    client.register_plugin("security", SecurityCheckPlugin())

    result = await client.inspect("@BotFather")
    print(f"Risk Level: {result.additional_data.get('security_analysis', {}).get('risk_level')}")
```

### Export Results

```python
from hody_telepro.exporters import JSONExporter, CSVExporter, HTMLReporter

# Export to JSON
JSONExporter().export_batch(results, "output.json")

# Export to CSV
CSVExporter().export_batch(results, "output.csv")

# Generate HTML Report
HTMLReporter().generate_report(results, "report.html")
```

---

## CLI Usage

```bash
# Install CLI tool
pip install hody-telepro

# Inspect an entity
hody-telepro --api-id 12345 --api-hash "hash" inspect @telegram

# Phone lookup
hody-telepro lookup +1234567890

# Estimate account creation
hody-telepro estimate 12345

# Batch inspection
hody-telepro batch @telegram @durov -f html -o report.html

# View stats
hody-telepro stats
```

---

## Plugin System

### Creating a Custom Plugin

```python
from hody_telepro.plugins import Plugin
from hody_telepro.models.entities import EntityInspectionResult

class MyPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "My custom analysis plugin"

    async def process(self, result: EntityInspectionResult) -> EntityInspectionResult:
        # Add custom analysis
        result.additional_data["custom_field"] = "analyzed_value"
        return result

# Register with client
client.register_plugin("my_plugin", MyPlugin())
```

### Built-in Plugins

| Plugin | Description |
|--------|-------------|
| `BotIntelligencePlugin` | Analyzes bot capabilities and behavior patterns |
| `SecurityCheckPlugin` | Performs security risk assessment |
| `HistoryEnrichmentPlugin` | Enriches data with historical context |

---

## Built-in Anti-Flood System

Hody-Telepro includes a sophisticated anti-flood system:

- **Single-Flight Pattern**: Merges concurrent identical requests into one
- **Exponential Backoff**: Automatically adjusts delays on FloodWait
- **Priority Queue**: Critical requests processed before batch operations
- **Adaptive Rate Limiting**: Dynamically adjusts based on server responses
- **Retry Handler**: Configurable retries with jitter

---

## Project Structure

```
hody-telepro/
├── src/
│   └── hody_telepro/
│       ├── __init__.py              # Public API
│       ├── client.py                # Main client
│       ├── models/
│       │   └── entities.py          # Data models (msgspec)
│       ├── engines/
│       │   ├── inspection_engine.py # Entity inspection
│       │   └── anti_flood.py        # Rate limiting
│       ├── cache/
│       │   └── cache_manager.py     # Async cache + single-flight
│       ├── exporters/
│       │   └── exporters.py         # JSON, CSV, SQLite, HTML
│       ├── algorithms/
│       │   └── creation_estimator.py # Binary search clustering
│       ├── cli/
│       │   └── main.py              # CLI interface
│       ├── plugins/
│       │   └── registry.py          # Plugin system
│       └── utils/
│           └── exceptions.py        # Custom exceptions
├── tests/
│   └── test_hody_telepro.py         # 64 tests
├── examples/
│   └── basic_usage.py               # Usage examples
├── pyproject.toml                   # Package configuration
└── README.md                        # Documentation
```

---

## Configuration

### Environment Variables

```bash
export TELEGRAM_API_ID=12345
export TELEGRAM_API_HASH="your_api_hash"
```

### Client Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session_name` | str | Required | Telegram session identifier |
| `api_id` | int | Required | Telegram API ID |
| `api_hash` | str | Required | Telegram API hash |
| `cache_ttl` | float | 3600 | Cache time-to-live in seconds |
| `cache_max_size` | int | 10000 | Maximum cache entries |
| `anti_flood_enabled` | bool | True | Enable flood protection |
| `max_retries` | int | 5 | Maximum operation retries |
| `workdir` | str | None | Session storage directory |

---

## Development

```bash
# Clone repository
git clone https://github.com/hody/hody-telepro.git
cd hody-telepro

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=hody_telepro --cov-report=html

# Linting
ruff check src/

# Type checking
mypy src/hody_telepro/
```

---

## Publishing to PyPI

```bash
# Build package
python -m build

# Upload to PyPI
twine upload dist/*

# Or use uv (recommended)
uv build
uv publish
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

- **Pyrogram** — Telegram MTProto client library
- **msgspec** — Fast serialization library (Rust)
- **aiocache** — Async caching framework
- **Click** — Command-line interface creation
- **Rich** — Terminal formatting library

---

<div align="center">

**Built with ❤️ by Hody**

[Report Bug](https://github.com/hody/hody-telepro/issues) | [Request Feature](https://github.com/hody/hody-telepro/issues)

</div>
