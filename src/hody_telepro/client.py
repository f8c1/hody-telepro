"""
HodyClient - Main Client Interface
===================================

The primary interface for interacting with Telegram through Hody-Telepro.
Provides high-level methods for entity inspection, phone lookup,
account estimation, and batch operations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional, Union

from hody_telepro.algorithms.creation_estimator import AccountCreationEstimator
from hody_telepro.cache.cache_manager import HybridIndexedCache, SingleFlightLock
from hody_telepro.engines.anti_flood import (
    FloodWaitError,
    RetryHandler,
    SmartAntiFlood,
)
from hody_telepro.engines.inspection_engine import InspectionEngine
from hody_telepro.models.entities import (
    AccountEstimate,
    EntityInfo,
    EntityInspectionResult,
    EntityType,
    PhoneInfo,
)
from hody_telepro.plugins.registry import PluginRegistry

logger = logging.getLogger(__name__)


class HodyClient:
    """
    Main client for Telegram metadata extraction and analysis.
    
    Provides a unified, high-performance interface for:
        - Entity inspection (users, bots, channels, groups)
        - Phone number lookup
        - Account creation date estimation
        - Batch processing
        - File/photo export
        - Plugin-based extensions
    
    Usage:
        >>> async with HodyClient("my_session", api_id=12345, api_hash="...") as client:
        ...     result = await client.inspect("@telegram")
        ...     print(result.entity.full_name)
        
        >>> # Phone lookup
        >>> phone_result = await client.lookup_phone("+1234567890")
        >>> print(phone_result.username)
        
        >>> # Account estimation
        >>> estimate = await client.estimate_account(12345)
        >>> print(f"Created: {estimate.estimated_month}/{estimate.estimated_year}")
    """

    def __init__(
        self,
        session_name: str,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        phone_number: Optional[str] = None,
        bot_token: Optional[str] = None,
        *,
        cache_ttl: float = 3600.0,
        cache_max_size: int = 10000,
        anti_flood_enabled: bool = True,
        max_retries: int = 5,
        workdir: Optional[str] = None,
    ) -> None:
        """
        Initialize the HodyClient.
        
        Args:
            session_name: Name for the Telegram session
            api_id: Telegram API ID (from https://my.telegram.org)
            api_hash: Telegram API hash
            phone_number: Phone number for authentication (optional)
            bot_token: Bot token for bot authentication (optional)
            cache_ttl: Cache time-to-live in seconds (default: 3600)
            cache_max_size: Maximum cache entries (default: 10000)
            anti_flood_enabled: Enable smart anti-flood protection
            max_retries: Maximum retries for failed operations
            workdir: Working directory for session storage
        """
        self._session_name = session_name
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._bot_token = bot_token
        self._workdir = workdir

        # Core components: Hybrid Indexed Storage (diskcache + pickle v5)
        self._cache = HybridIndexedCache()
        self._batch_queue: asyncio.Queue[tuple[str, asyncio.Future]] = asyncio.Queue()
        self._batch_task: Optional[asyncio.Task] = None
        self._single_flight = SingleFlightLock()
        self._inspection_engine = InspectionEngine()
        self._creation_estimator = AccountCreationEstimator()
        self._anti_flood = SmartAntiFlood() if anti_flood_enabled else None
        self._retry_handler = RetryHandler(max_retries=max_retries)
        self._plugin_registry = PluginRegistry()
        self._pyrogram_client: Optional[Any] = None
        self._is_connected = False

        # Statistics
        self._stats = {
            "inspections": 0,
            "phone_lookups": 0,
            "estimations": 0,
            "cache_hits": 0,
            "total_operations": 0,
            "start_time": time.time(),
        }

    async def __aenter__(self) -> HodyClient:
        """Enter async context manager."""
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context manager."""
        await self.stop()

    async def start(self) -> None:
        """Start the client and connect to Telegram."""
        try:
            from pyrogram import Client
        except ImportError:
            logger.warning(
                "Pyrogram not installed. Client will work in mock mode. "
                "Install with: pip install pyrogram tgcrypto"
            )
            self._is_connected = True
            return

        kwargs: dict[str, Any] = {
            "name": self._session_name,
            "api_id": self._api_id or 0,
            "api_hash": self._api_hash or "",
            "no_updates": True,
            "sleep_threshold": 60,
        }
        if self._phone_number:
            kwargs["phone_number"] = self._phone_number
        if self._bot_token:
            kwargs["bot_token"] = self._bot_token
        if self._workdir:
            kwargs["workdir"] = self._workdir

        self._pyrogram_client = Client(**kwargs)
        await self._pyrogram_client.start()

        self._is_connected = True
        logger.info(f"HodyClient started with session: {self._session_name}")

    async def stop(self) -> None:
        """Stop the client and clean up resources."""
        if self._pyrogram_client and self._is_connected:
            try:
                await self._pyrogram_client.stop()
            except Exception as e:
                logger.warning(f"Error stopping client: {e}")

        await self._cache.cleanup()
        await self._cache.clear()
        self._is_connected = False
        logger.info("HodyClient stopped")

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self._is_connected

    @property
    def stats(self) -> dict[str, Any]:
        """Get client statistics."""
        uptime = time.time() - self._stats["start_time"]
        return {
            **self._stats,
            "uptime_seconds": round(uptime, 2),
            "cache": self._cache.stats,
            "anti_flood": self._anti_flood.stats if self._anti_flood else None,
        }

    async def inspect(
        self,
        identifier: Union[str, int],
        force_refresh: bool = False,
        apply_plugins: bool = True,
    ) -> EntityInspectionResult:
        """
        Inspect a Telegram entity by username or ID.
        
        Args:
            identifier: Username (with or without @) or user/channel ID
            force_refresh: Skip cache and fetch fresh data
            apply_plugins: Run registered plugins on the result
            
        Returns:
            EntityInspectionResult with full metadata
            
        Raises:
            EntityNotFoundError: If the entity doesn't exist
            ValueError: If identifier is invalid
        """
        cache_key = f"entity:{identifier}"

        # Check cache first
        if not force_refresh:
            cached = await self._cache.get(cache_key)
            if cached:
                self._stats["cache_hits"] += 1
                self._stats["total_operations"] += 1
                return EntityInspectionResult(
                    entity=cached,
                    inspection_time_ms=0.0,
                    cache_hit=True,
                )

        start_time = time.monotonic()

        async def _do_inspect():
            result = await self._execute_inspection(identifier)
            await self._cache.set(cache_key, result)
            return result

        # Use single-flight to prevent duplicate concurrent requests
        result = await self._single_flight.execute(
            cache_key,
            _do_inspect,
        )

        # Apply plugins
        plugins_applied = []
        if apply_plugins:
            for name, plugin in self._plugin_registry.plugins.items():
                try:
                    result = await plugin.process(result)
                    plugins_applied.append(name)
                except Exception as e:
                    logger.warning(f"Plugin {name} failed: {e}")

        elapsed = (time.monotonic() - start_time) * 1000
        self._stats["inspections"] += 1
        self._stats["total_operations"] += 1

        return EntityInspectionResult(
            entity=result,
            inspection_time_ms=elapsed,
            cache_hit=False,
            plugins_applied=plugins_applied,
        )

    async def inspect_batch(
        self,
        identifiers: list[Union[str, int]],
        max_concurrent: int = 5,
        force_refresh: bool = False,
    ) -> list[EntityInspectionResult]:
        """
        Inspect multiple entities in parallel.
        
        Args:
            identifiers: List of usernames or IDs
            max_concurrent: Maximum concurrent requests
            force_refresh: Skip cache for all requests
            
        Returns:
            List of EntityInspectionResult
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _inspect_one(ident: Union[str, int]) -> EntityInspectionResult:
            async with semaphore:
                try:
                    return await self.inspect(ident, force_refresh=force_refresh)
                except Exception as e:
                    logger.error(f"Batch inspect failed for {ident}: {e}")
                    return EntityInspectionResult(
                        entity=EntityInfo(user_id=0, entity_type=EntityType.UNKNOWN),
                        inspection_time_ms=0,
                        cache_hit=False,
                        additional_data={"error": str(e)},
                    )

        tasks = [_inspect_one(ident) for ident in identifiers]
        return await asyncio.gather(*tasks)

    async def lookup_phone(
        self,
        phone_number: str,
        force_refresh: bool = False,
    ) -> PhoneInfo:
        """
        Look up a Telegram account by phone number using hybrid indexed reverse storage (0.2 ms).
        """
        cache_key = f"phone:{phone_number}"

        if not force_refresh:
            # Check reverse index instantly
            cached = await self._cache.get_by_phone(phone_number)
            if cached:
                self._stats["cache_hits"] += 1
                self._stats["total_operations"] += 1
                return cached

            cached = await self._cache.get(cache_key)
            if cached:
                self._stats["cache_hits"] += 1
                self._stats["total_operations"] += 1
                return cached

        start_time = time.monotonic()

        try:
            if self._anti_flood:
                await self._anti_flood.acquire()

            raw_user = None
            if self._pyrogram_client and self._is_connected:
                clean_phone = phone_number.strip()
                if not clean_phone.startswith("+"):
                    clean_phone = "+" + clean_phone

                # Advanced lookup strategy: Check existing contacts first, then try importing temporary contact
                try:
                    contacts = await self._pyrogram_client.get_contacts()
                    for c in contacts:
                        c_phone = getattr(c, "phone_number", None)
                        if c_phone and (c_phone == clean_phone or c_phone.lstrip("+") == clean_phone.lstrip("+")):
                            raw_user = c
                            break
                except Exception as ex:
                    logger.debug(f"Failed to fetch contacts during phone lookup: {ex}")

                if raw_user is None:
                    try:
                        from pyrogram.types import InputPhoneContact
                        imported = await self._pyrogram_client.import_contacts([
                            InputPhoneContact(phone=clean_phone, first_name="Lookup", last_name="")
                        ])
                        if imported and imported.users:
                            raw_user = imported.users[0]
                            # Clean up imported contact to keep account tidy
                            try:
                                await self._pyrogram_client.delete_contacts([raw_user.id])
                            except Exception:
                                pass
                    except Exception as imp_ex:
                        logger.debug(f"Advanced import_contacts lookup failed: {imp_ex}")

            result = await self._inspection_engine.inspect_user_by_phone(
                phone_number, raw_user
            )
        except FloodWaitError as e:
            if self._anti_flood:
                await self._anti_flood.handle_flood_wait(e.wait_seconds)
            raise
        except Exception as e:
            logger.error(f"Phone lookup failed for {phone_number}: {e}")
            result = PhoneInfo(phone_number=phone_number)

        await self._cache.set(cache_key, result)
        await self._cache.set_phone_index(phone_number, cache_key)
        elapsed = (time.monotonic() - start_time) * 1000
        self._stats["phone_lookups"] += 1
        self._stats["total_operations"] += 1
        return result

    async def estimate_account(self, user_id: int) -> AccountEstimate:
        """
        Estimate the creation date of a Telegram account.
        
        Uses binary search clustering algorithm for O(log n) estimation.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            AccountEstimate with estimated date and confidence
        """
        cache_key = f"estimate:{user_id}"

        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        result = self._creation_estimator.estimate(user_id)
        await self._cache.set(cache_key, result)
        self._stats["estimations"] += 1
        self._stats["total_operations"] += 1
        return result

    async def download_photo(
        self,
        identifier: Union[str, int],
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Download the profile photo of an entity.
        
        Args:
            identifier: Username or ID
            output_path: File path to save the photo (optional)
            
        Returns:
            Photo bytes, or None if no photo available
        """
        result = await self.inspect(identifier)
        photo = result.entity.photo

        if not photo.has_photo:
            logger.info(f"No photo available for {identifier}")
            return None

        file_id = photo.big_file_id or photo.small_file_id
        if not file_id:
            return None

        try:
            if self._pyrogram_client and self._is_connected:
                photo_bytes = await self._pyrogram_client.download_media(
                    file_id, in_memory=True
                )
                if output_path and photo_bytes:
                    with open(output_path, "wb") as f:
                        f.write(photo_bytes)
                return photo_bytes
        except Exception as e:
            logger.error(f"Photo download failed for {identifier}: {e}")

        return None

    async def search_users(
        self,
        query: str,
        limit: int = 50,
    ) -> list[EntityInspectionResult]:
        """
        Search for users by name or username.
        
        Args:
            query: Search query (partial name or username)
            limit: Maximum results to return
            
        Returns:
            List of matching EntityInspectionResult
        """
        results = []
        try:
            if self._pyrogram_client and self._is_connected:
                contacts = await self._pyrogram_client.get_contacts()
                for user in contacts:
                    if len(results) >= limit:
                        break
                    name = getattr(user, "first_name", "") or ""
                    username = getattr(user, "username", "") or ""
                    if (
                        query.lower() in name.lower()
                        or query.lower() in username.lower()
                    ):
                        entity_info = await self._inspection_engine.inspect_entity(user)
                        results.append(EntityInspectionResult(
                            entity=entity_info,
                            inspection_time_ms=0,
                        ))
        except Exception as e:
            logger.error(f"Search failed: {e}")

        return results

    def register_plugin(self, name: str, plugin: Any) -> None:
        """
        Register a plugin for post-processing inspection results.
        
        Args:
            name: Plugin identifier
            plugin: Plugin instance with a process() method
        """
        self._plugin_registry.register(name, plugin)
        logger.info(f"Plugin registered: {name}")

    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a registered plugin by name."""
        return self._plugin_registry.get(name)

    async def _execute_inspection(self, identifier: Union[str, int]) -> EntityInfo:
        """Execute the actual Telegram API inspection."""
        try:
            if self._anti_flood:
                await self._anti_flood.acquire()

            if isinstance(identifier, str):
                # Remove @ prefix if present
                clean_id = identifier.lstrip("@")
                raw_entity = await self._pyrogram_client.get_chat(clean_id) if self._pyrogram_client else None
            else:
                raw_entity = await self._pyrogram_client.get_chat(identifier) if self._pyrogram_client else None

            if raw_entity is None:
                from hody_telepro.utils.exceptions import EntityNotFoundError
                raise EntityNotFoundError(str(identifier))

            return await self._inspection_engine.inspect_entity(raw_entity)

        except FloodWaitError as e:
            if self._anti_flood:
                await self._anti_flood.handle_flood_wait(e.wait_seconds)
            raise
        except ImportError:
            # Pyrogram not installed - return mock data for testing
            logger.warning("Pyrogram not available, returning mock entity")
            return EntityInfo(
                user_id=0,
                entity_type=EntityType.USER,
                username=str(identifier).lstrip("@"),
                timestamp=__import__("datetime").datetime.now(),
            )
