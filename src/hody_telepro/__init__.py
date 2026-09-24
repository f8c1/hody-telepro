"""
Hody-Telepro
============

An ultra-fast, asynchronous, enterprise-grade Python library for Telegram
metadata extraction, entity inspection, and phone number lookup.

Core Features:
    - Entity Inspection: Retrieve full metadata for any Telegram entity
    - Phone Lookup: Extract account details from phone numbers
    - Account Creation Estimation: Estimate Telegram join dates
    - Smart Anti-Flood: Built-in rate limiting with single-flight protection
    - Async Persistent Sessions: SQLite-backed session management
    - Plugin System: Extensible architecture for custom functionality

Quick Start:
    >>> from hody_telepro import HodyClient
    >>>
    >>> async with HodyClient("session_name", api_id=12345, api_hash="...") as client:
    ...     user = await client.inspect("@telegram")
    ...     print(user.full_name)

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Hody"
__license__ = "MIT"

from hody_telepro.client import HodyClient
from hody_telepro.exporters import (
    CSVExporter,
    HTMLReporter,
    JSONExporter,
    SQLiteExporter,
)
from hody_telepro.models.entities import (
    AccountEstimate,
    EntityInfo,
    PhoneInfo,
    TelegramBot,
    TelegramChannel,
    TelegramGroup,
    TelegramUser,
)
from hody_telepro.models.entities import (
    EntityInfo as TelegramEntity,
)
from hody_telepro.plugins import Plugin, PluginRegistry

__all__ = [
    "AccountEstimate",
    "CSVExporter",
    "EntityInfo",
    "HTMLReporter",
    "HodyClient",
    "JSONExporter",
    "PhoneInfo",
    "Plugin",
    "PluginRegistry",
    "SQLiteExporter",
    "TelegramBot",
    "TelegramChannel",
    "TelegramEntity",
    "TelegramGroup",
    "TelegramUser",
    "__author__",
    "__license__",
    "__version__",
]
