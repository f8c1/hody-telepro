"""Utility modules for Hody-Telepro."""

from hody_telepro.utils.exceptions import (
    AuthenticationError,
    EntityNotFoundError,
    HodyTeleproError,
    InvalidIdentifierError,
    PhoneNotFoundError,
    PluginError,
    RateLimitExceededError,
)

__all__ = [
    "AuthenticationError",
    "EntityNotFoundError",
    "HodyTeleproError",
    "InvalidIdentifierError",
    "PhoneNotFoundError",
    "PluginError",
    "RateLimitExceededError",
]
