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
from hody_telepro.models.entities import (
    TelegramUser,
    TelegramBot,
    TelegramChannel,
    TelegramGroup,
    EntityInfo as TelegramEntity,
    EntityInfo,
    PhoneInfo,
    AccountEstimate,
)
from hody_telepro.plugins import Plugin, PluginRegistry
from hody_telepro.exporters import (
    JSONExporter,
    CSVExporter,
    SQLiteExporter,
    HTMLReporter,
)

__all__ = [
    "HodyClient",
    "TelegramUser",
    "TelegramBot",
    "TelegramChannel",
    "TelegramGroup",
    "TelegramEntity",
    "EntityInfo",
    "PhoneInfo",
    "AccountEstimate",
    "Plugin",
    "PluginRegistry",
    "JSONExporter",
    "CSVExporter",
    "SQLiteExporter",
    "HTMLReporter",
    "__version__",
    "__author__",
    "__license__",
]
