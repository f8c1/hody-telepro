"""
Telegram Entity Models
======================

High-performance data models using msgspec (Rust-powered) for minimal
memory footprint and maximum serialization speed.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any, Optional

import msgspec


class EntityType(str, enum.Enum):
    """Enumeration of Telegram entity types."""
    USER = "user"
    BOT = "bot"
    CHANNEL = "channel"
    GROUP = "group"
    SUPPERGROUP = "supergroup"
    UNKNOWN = "unknown"


class EntityStatus(str, enum.Enum):
    """User/bot status enumeration."""
    ACTIVE = "active"
    DELETED = "deleted"
    RESTRICTED = "restricted"
    DEACTIVATED = "deactivated"
    UNKNOWN = "unknown"


class AccountEstimate(msgspec.Struct, kw_only=True):
    """Estimated account creation date based on user ID analysis."""
    user_id: int
    estimated_month: str
    estimated_year: int
    confidence: float = 0.85
    method: str = "binary_search_clustering"
    user_id_date: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "user_id": self.user_id,
            "estimated_date": f"{self.estimated_month}/{self.estimated_year}",
            "confidence": round(self.confidence, 4),
            "method": self.method,
        }


class PhoneInfo(msgspec.Struct, kw_only=True):
    """Phone number lookup result."""
    phone_number: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_bot: bool = False
    is_deleted: bool = False
    photo_available: bool = False
    bio: Optional[str] = None
    status: EntityStatus = EntityStatus.UNKNOWN

    @property
    def full_name(self) -> str:
        """Get the full name from first and last name."""
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else "Unknown"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return msgspec.structs.asdict(self)


class EntityPhoto(msgspec.Struct, kw_only=True):
    """Telegram entity photo information."""
    small_file_id: Optional[str] = None
    big_file_id: Optional[str] = None
    has_photo: bool = False
    dc_id: Optional[int] = None


class EntityInfo(msgspec.Struct, kw_only=True):
    """Core entity information shared across all entity types."""
    user_id: int
    entity_type: EntityType = EntityType.UNKNOWN
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    is_bot: bool = False
    is_premium: bool = False
    is_verified: bool = False
    is_scam: bool = False
    is_fake: bool = False
    is_restricted: bool = False
    is_deleted: bool = False
    is_support: bool = False
    photo: EntityPhoto = msgspec.field(default_factory=EntityPhoto)
    language_code: Optional[str] = None
    common_chats_count: Optional[int] = None
    account_estimate: Optional[AccountEstimate] = None
    raw_data: Optional[dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        """Get the full name from first and last name."""
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else self.username or str(self.user_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return msgspec.structs.asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return msgspec.json.encode(self).decode()


class TelegramUser(EntityInfo, kw_only=True):
    """Represents a Telegram user account."""
    entity_type: EntityType = EntityType.USER
    phone_number: Optional[str] = None
    online_status: Optional[str] = None
    last_online: Optional[datetime] = None
    mutual_contacts: bool = False


class TelegramBot(EntityInfo, kw_only=True):
    """Represents a Telegram bot."""
    entity_type: EntityType = EntityType.BOT
    bot_command: Optional[str] = None
    can_join_groups: Optional[bool] = None
    can_read_messages: Optional[bool] = None
    inline_support: bool = False
    bot_description: Optional[str] = None
    bot_about: Optional[str] = None


class TelegramChannel(EntityInfo, kw_only=True):
    """Represents a Telegram channel."""
    entity_type: EntityType = EntityType.CHANNEL
    title: Optional[str] = None
    description: Optional[str] = None
    members_count: Optional[int] = None
    subscribers_count: Optional[int] = None
    linked_chat_id: Optional[int] = None
    is_broadcast: bool = True


class TelegramGroup(EntityInfo, kw_only=True):
    """Represents a Telegram group or supergroup."""
    entity_type: EntityType = EntityType.SUPPERGROUP
    title: Optional[str] = None
    description: Optional[str] = None
    members_count: Optional[int] = None
    is_supergroup: bool = True
    is_public: bool = False
    invite_link: Optional[str] = None
    slow_mode_delay: Optional[int] = None


class EntityInspectionResult(msgspec.Struct, kw_only=True):
    """Complete inspection result for any entity."""
    entity: EntityInfo
    inspection_time_ms: float
    cache_hit: bool = False
    plugins_applied: list[str] = msgspec.field(default_factory=list)
    additional_data: dict[str, Any] = msgspec.field(default_factory=dict)

    @property
    def entity_type(self) -> EntityType:
        """Get the entity type."""
        return self.entity.entity_type

    @property
    def full_name(self) -> str:
        """Get the full name."""
        return self.entity.full_name

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity": self.entity.to_dict(),
            "inspection_time_ms": round(self.inspection_time_ms, 3),
            "cache_hit": self.cache_hit,
            "plugins_applied": self.plugins_applied,
            "additional_data": self.additional_data,
        }
