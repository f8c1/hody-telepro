"""
Custom Exceptions for Hody-Telepro
===================================
"""

from __future__ import annotations

from typing import Optional


class HodyTeleproError(Exception):
    """Base exception for all Hody-Telepro errors."""


class EntityNotFoundError(HodyTeleproError):
    """Raised when a Telegram entity is not found."""

    def __init__(self, identifier: str, message: Optional[str] = None) -> None:
        self.identifier = identifier
        self.message = message or f"Entity not found: {identifier}"
        super().__init__(self.message)


class PhoneNotFoundError(HodyTeleproError):
    """Raised when no Telegram account is linked to a phone number."""

    def __init__(self, phone_number: str, message: Optional[str] = None) -> None:
        self.phone_number = phone_number
        self.message = message or f"No Telegram account found for: {phone_number}"
        super().__init__(self.message)


class AuthenticationError(HodyTeleproError):
    """Raised when authentication with Telegram fails."""

    def __init__(self, reason: str = "") -> None:
        self.message = f"Authentication failed: {reason}" if reason else "Authentication failed"
        super().__init__(self.message)


class RateLimitExceededError(HodyTeleproError):
    """Raised when rate limits are exceeded."""

    def __init__(self, retry_after: float = 0.0) -> None:
        self.retry_after = retry_after
        self.message = f"Rate limit exceeded. Retry after {retry_after}s"
        super().__init__(self.message)


class PluginError(HodyTeleproError):
    """Raised when a plugin operation fails."""

    def __init__(self, plugin_name: str, reason: str = "") -> None:
        self.plugin_name = plugin_name
        self.message = f"Plugin '{plugin_name}' error: {reason}" if reason else f"Plugin '{plugin_name}' error"
        super().__init__(self.message)


class InvalidIdentifierError(HodyTeleproError):
    """Raised when an invalid identifier is provided."""

    def __init__(self, identifier: str, expected_format: str = "") -> None:
        self.identifier = identifier
        fmt = f". Expected format: {expected_format}" if expected_format else ""
        self.message = f"Invalid identifier: {identifier}{fmt}"
        super().__init__(self.message)
