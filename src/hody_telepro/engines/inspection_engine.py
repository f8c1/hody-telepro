"""
Entity Inspection Engine
=========================

Core engine for extracting and analyzing Telegram entity metadata.
Handles resolution of usernames, IDs, and raw API responses into
structured data models.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional, Union

from hody_telepro.models.entities import (
    AccountEstimate,
    EntityInfo,
    EntityPhoto,
    EntityStatus,
    EntityType,
    PhoneInfo,
    TelegramBot,
    TelegramChannel,
    TelegramGroup,
    TelegramUser,
)

logger = logging.getLogger(__name__)


class InspectionEngine:
    """
    Engine for inspecting and classifying Telegram entities.
    
    Converts raw Telegram API responses into structured entity models
    with full metadata extraction.
    """

    def __init__(self) -> None:
        self._creation_estimator = None

    def _get_creation_estimator(self):
        """Lazy-load the creation estimator."""
        if self._creation_estimator is None:
            from hody_telepro.algorithms.creation_estimator import AccountCreationEstimator
            self._creation_estimator = AccountCreationEstimator()
        return self._creation_estimator

    async def inspect_entity(self, raw_entity: Any) -> EntityInfo:
        """
        Inspect a raw Telegram entity and return structured metadata.
        
        Args:
            raw_entity: Raw Pyrogram User, Channel, or Chat object
            
        Returns:
            EntityInfo with full metadata
        """
        entity_type = self._classify_entity(raw_entity)

        if entity_type in (EntityType.USER, EntityType.BOT):
            return self._process_user(raw_entity)
        elif entity_type in (EntityType.CHANNEL,):
            return self._process_channel(raw_entity)
        elif entity_type in (EntityType.GROUP, EntityType.SUPPERGROUP):
            return self._process_group(raw_entity)
        else:
            return EntityInfo(
                user_id=getattr(raw_entity, "id", 0),
                entity_type=EntityType.UNKNOWN,
                raw_data=self._raw_to_dict(raw_entity),
                timestamp=datetime.now(),
            )

    async def inspect_user_by_phone(self, phone_number: str, raw_user: Any) -> PhoneInfo:
        """
        Inspect a user found via phone number lookup.
        
        Args:
            phone_number: The phone number used for lookup
            raw_user: Raw Pyrogram User object
            
        Returns:
            PhoneInfo with extracted details
        """
        if raw_user is None:
            return PhoneInfo(phone_number=phone_number, is_deleted=True)

        status = EntityStatus.DELETED if getattr(raw_user, "is_deleted", False) else EntityStatus.ACTIVE

        photo_available = bool(getattr(raw_user, "photo", None))

        return PhoneInfo(
            phone_number=phone_number,
            user_id=getattr(raw_user, "id", None),
            username=getattr(raw_user, "username", None),
            first_name=getattr(raw_user, "first_name", None),
            last_name=getattr(raw_user, "last_name", None),
            is_bot=getattr(raw_user, "is_bot", False),
            is_deleted=getattr(raw_user, "is_deleted", False),
            photo_available=photo_available,
            bio=getattr(raw_user, "about", None),
            status=status,
        )

    async def estimate_creation(self, user_id: int) -> AccountEstimate:
        """
        Estimate the creation date for a user ID.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            AccountEstimate with estimated date and confidence
        """
        estimator = self._get_creation_estimator()
        return estimator.estimate(user_id)

    def _classify_entity(self, raw_entity: Any) -> EntityType:
        """Classify a raw entity into its type."""
        raw_type = getattr(raw_entity, "type", "")
        if hasattr(raw_type, "value"):
            entity_type_str = str(raw_type.value).lower()
        else:
            entity_type_str = str(raw_type).lower()

        if entity_type_str == "channel":
            return EntityType.CHANNEL
        elif entity_type_str == "supergroup":
            return EntityType.SUPPERGROUP
        elif entity_type_str == "group":
            return EntityType.GROUP

        if getattr(raw_entity, "is_bot", False):
            return EntityType.BOT

        return EntityType.USER

    def _process_user(self, raw: Any) -> TelegramUser:
        """Process a raw User entity."""
        user_id = getattr(raw, "id", 0)
        username = getattr(raw, "username", None)
        first_name = getattr(raw, "first_name", None)
        last_name = getattr(raw, "last_name", None)
        is_bot = getattr(raw, "is_bot", False)
        is_premium = getattr(raw, "is_premium", False)
        is_verified = getattr(raw, "is_verified", False)
        is_scam = getattr(raw, "is_scam", False)
        is_fake = getattr(raw, "is_fake", False)
        is_restricted = getattr(raw, "is_restricted", False)
        is_deleted = getattr(raw, "is_deleted", False)
        is_support = getattr(raw, "is_support", False)
        language_code = getattr(raw, "language_code", None)
        phone_number = getattr(raw, "phone_number", None)
        bio = getattr(raw, "about", None)
        common_chats_count = getattr(raw, "common_chats_count", None)

        entity_type = EntityType.BOT if is_bot else EntityType.USER

        # Photo info
        photo = EntityPhoto()
        raw_photo = getattr(raw, "photo", None)
        if raw_photo:
            photo = EntityPhoto(
                small_file_id=getattr(raw_photo, "small_file_id", None),
                big_file_id=getattr(raw_photo, "big_file_id", None),
                has_photo=True,
                dc_id=getattr(raw_photo, "dc_id", None),
            )

        # Estimate creation date
        estimate = None
        try:
            estimate = self._get_creation_estimator().estimate(user_id)
        except Exception as e:
            logger.debug(f"Could not estimate creation for user_id={user_id}: {e}")

        if entity_type == EntityType.BOT:
            bot_info = getattr(raw, "bot_info", None)
            return TelegramUser(
                user_id=user_id,
                entity_type=EntityType.BOT,
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_bot=True,
                is_premium=is_premium,
                is_verified=is_verified,
                is_scam=is_scam,
                is_fake=is_fake,
                is_restricted=is_restricted,
                is_deleted=is_deleted,
                photo=photo,
                bio=bio,
                account_estimate=estimate,
                raw_data=self._raw_to_dict(raw),
                timestamp=datetime.now(),
            )

        return TelegramUser(
            user_id=user_id,
            entity_type=EntityType.USER,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_bot=is_bot,
            is_premium=is_premium,
            is_verified=is_verified,
            is_scam=is_scam,
            is_fake=is_fake,
            is_restricted=is_restricted,
            is_deleted=is_deleted,
            is_support=is_support,
            language_code=language_code,
            phone_number=phone_number,
            photo=photo,
            bio=bio,
            common_chats_count=common_chats_count,
            account_estimate=estimate,
            raw_data=self._raw_to_dict(raw),
            timestamp=datetime.now(),
        )

    def _process_channel(self, raw: Any) -> TelegramChannel:
        """Process a raw Channel entity."""
        return TelegramChannel(
            user_id=getattr(raw, "id", 0),
            entity_type=EntityType.CHANNEL,
            username=getattr(raw, "username", None),
            title=getattr(raw, "title", None),
            description=getattr(raw, "description", None),
            members_count=getattr(raw, "members_count", None),
            subscribers_count=getattr(raw, "subscribers_count", None),
            linked_chat_id=getattr(raw, "linked_chat_id", None),
            is_broadcast=getattr(raw, "is_broadcast", True),
            photo=self._extract_photo(raw),
            raw_data=self._raw_to_dict(raw),
            timestamp=datetime.now(),
        )

    def _process_group(self, raw: Any) -> TelegramGroup:
        """Process a raw Group/Supergroup entity."""
        return TelegramGroup(
            user_id=getattr(raw, "id", 0),
            entity_type=EntityType.SUPPERGROUP,
            username=getattr(raw, "username", None),
            title=getattr(raw, "title", None),
            description=getattr(raw, "description", None),
            members_count=getattr(raw, "members_count", None),
            is_supergroup=True,
            is_public=bool(getattr(raw, "username", None)),
            invite_link=getattr(raw, "invite_link", None),
            slow_mode_delay=getattr(raw, "slow_mode_delay", None),
            photo=self._extract_photo(raw),
            raw_data=self._raw_to_dict(raw),
            timestamp=datetime.now(),
        )

    def _extract_photo(self, raw: Any) -> EntityPhoto:
        """Extract photo info from any entity."""
        photo = getattr(raw, "photo", None)
        if photo:
            return EntityPhoto(
                small_file_id=getattr(photo, "small_file_id", None),
                big_file_id=getattr(photo, "big_file_id", None),
                has_photo=True,
                dc_id=getattr(photo, "dc_id", None),
            )
        return EntityPhoto()

    @staticmethod
    def _raw_to_dict(raw: Any) -> Optional[dict[str, Any]]:
        """Safely convert raw entity to dictionary."""
        try:
            if hasattr(raw, "__dict__"):
                return {
                    k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                    for k, v in raw.__dict__.items()
                    if not k.startswith("_")
                }
        except Exception:
            pass
        return None
