"""
Tests for Hody-Telepro
======================
Comprehensive test suite covering models, algorithms, inspection engines,
hybrid indexed cache, cosmic scheduler, plugins, exporters, and CLI.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from hody_telepro.algorithms.creation_estimator import AccountCreationEstimator
from hody_telepro.cache.cache_manager import HybridIndexedCache, SingleFlightLock
from hody_telepro.engines.anti_flood import RetryHandler, SmartAntiFlood
from hody_telepro.engines.inspection_engine import InspectionEngine
from hody_telepro.exporters.exporters import CSVExporter, HTMLReporter, JSONExporter
from hody_telepro.models.entities import (
    AccountEstimate,
    EntityInfo,
    EntityInspectionResult,
    EntityPhoto,
    EntityStatus,
    EntityType,
    PhoneInfo,
    TelegramChannel,
    TelegramGroup,
    TelegramUser,
)
from hody_telepro.plugins import BotIntelligencePlugin, SecurityCheckPlugin
from hody_telepro.plugins.registry import PluginRegistry
from hody_telepro.utils.exceptions import EntityNotFoundError, PhoneNotFoundError


class TestDataModels:
    """Test data models and serialization."""

    def test_entity_info_defaults(self):
        info = EntityInfo(user_id=12345, entity_type=EntityType.USER)
        assert info.user_id == 12345
        assert info.entity_type == EntityType.USER
        assert info.full_name == "12345"

    def test_telegram_user_full_name(self):
        user = TelegramUser(
            user_id=1,
            entity_type=EntityType.USER,
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"

    def test_telegram_channel_title(self):
        channel = TelegramChannel(
            user_id=2,
            entity_type=EntityType.CHANNEL,
            title="Tech News",
        )
        assert channel.title == "Tech News"

    def test_telegram_group_title(self):
        group = TelegramGroup(
            user_id=3,
            entity_type=EntityType.SUPPERGROUP,
            title="Python Devs",
        )
        assert group.title == "Python Devs"

    def test_entity_photo(self):
        photo = EntityPhoto(
            small_file_id="abc",
            big_file_id="def",
            has_photo=True,
            dc_id=2,
        )
        assert photo.has_photo is True
        assert photo.big_file_id == "def"

    def test_phone_info(self):
        phone = PhoneInfo(
            phone_number="+1234567890",
            user_id=100,
            username="user",
            first_name="Test",
        )
        assert phone.full_name == "Test"
        assert phone.phone_number == "+1234567890"

    def test_phone_info_deleted(self):
        phone = PhoneInfo(phone_number="+1234567890", is_deleted=True)
        assert phone.is_deleted is True
        assert phone.status == EntityStatus.UNKNOWN

    def test_account_estimate(self):
        estimate = AccountEstimate(
            user_id=100,
            estimated_month="August",
            estimated_year=2013,
            confidence=0.95,
        )
        assert estimate.user_id == 100
        assert estimate.estimated_year == 2013


class TestCreationEstimator:
    """Test the account creation date estimation algorithm."""

    def setup_method(self):
        self.estimator = AccountCreationEstimator()

    def test_early_account_estimation(self):
        estimate = self.estimator.estimate(1000)
        assert estimate.estimated_year == 2013
        assert estimate.estimated_month in [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

    def test_mid_account_estimation(self):
        estimate = self.estimator.estimate(100000000)
        assert estimate.estimated_year >= 2015

    def test_recent_account_estimation(self):
        estimate = self.estimator.estimate(7000000000)
        assert estimate.estimated_year >= 2022

    def test_invalid_user_id(self):
        with pytest.raises(ValueError):
            self.estimator.estimate(0)

    def test_add_reference_point(self):
        from datetime import datetime, timezone
        self.estimator.add_reference_point(8000000000, datetime(2026, 1, 1, tzinfo=timezone.utc), 0.90)
        estimate = self.estimator.estimate(8000000000)
        assert estimate.estimated_year == 2026
        assert estimate.estimated_month == "January"


class TestHybridIndexedCache:
    """Test hybrid indexed storage with diskcache and pickle v5."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        cache = HybridIndexedCache()
        await cache.set("key1", {"data": "value1"})
        result = await cache.get("key1")
        assert result == {"data": "value1"}

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        cache = HybridIndexedCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_phone_reverse_index(self):
        cache = HybridIndexedCache()
        phone = "+1234567890"
        key = "phone:+1234567890"
        await cache.set(key, "phone_result_data")
        await cache.set_phone_index(phone, key)
        
        # Instant lookup via reverse index (0.2 ms)
        res = await cache.get_by_phone(phone)
        assert res == "phone_result_data"

    @pytest.mark.asyncio
    async def test_delete(self):
        cache = HybridIndexedCache()
        await cache.set("key1", "value1")
        await cache.delete("key1")
        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self):
        cache = HybridIndexedCache()
        await cache.set("key1", "value1")
        await cache.clear()
        assert await cache.get("key1") is None


class TestSingleFlightLock:
    """Test single-flight lock pattern."""

    @pytest.mark.asyncio
    async def test_single_execution(self):
        lock = SingleFlightLock()
        call_count = 0

        async def expensive_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return "result"

        results = await asyncio.gather(*[
            lock.execute("key1", expensive_func)
            for _ in range(10)
        ])

        assert call_count == 1
        assert all(r == "result" for r in results)


class TestInspectionEngine:
    """Test the inspection engine."""

    def setup_method(self):
        self.engine = InspectionEngine()

    def test_classify_user(self):
        class MockUser:
            type = "private"
            is_bot = False
        assert self.engine._classify_entity(MockUser()) == EntityType.USER

    def test_classify_bot(self):
        class MockBot:
            type = "private"
            is_bot = True
        assert self.engine._classify_entity(MockBot()) == EntityType.BOT

    def test_classify_channel(self):
        class MockChannel:
            type = "channel"
            is_bot = False
        assert self.engine._classify_entity(MockChannel()) == EntityType.CHANNEL

    @pytest.mark.asyncio
    async def test_inspect_user_entity(self):
        class MockUser:
            id = 123
            username = "testuser"
            first_name = "Test"
            last_name = "User"
            is_bot = False
            is_premium = True
            is_verified = False
            is_scam = False
            is_fake = False
            is_restricted = False
            is_deleted = False
            is_support = False
            language_code = "en"
            phone_number = "12345"
            about = "Hello"
            photo = None

        result = await self.engine.inspect_entity(MockUser())
        assert result.user_id == 123
        assert result.username == "testuser"
        assert result.is_premium is True

    @pytest.mark.asyncio
    async def test_inspect_phone_user(self):
        class MockUser:
            id = 100
            username = "phoneuser"
            first_name = "Phone"
            last_name = "User"
            is_bot = False
            is_deleted = False
            about = "Bio"
            photo = None

        result = await self.engine.inspect_user_by_phone("+1234567890", MockUser())
        assert result.user_id == 100
        assert result.phone_number == "+1234567890"

    @pytest.mark.asyncio
    async def test_inspect_phone_deleted(self):
        result = await self.engine.inspect_user_by_phone("+1234567890", None)
        assert result.is_deleted is True


class TestPluginSystem:
    """Test the plugin system."""

    def test_register_plugin(self):
        registry = PluginRegistry()
        plugin = SecurityCheckPlugin()
        registry.register("security", plugin)
        assert "security" in registry.names

    @pytest.mark.asyncio
    async def test_security_plugin(self):
        plugin = SecurityCheckPlugin()
        entity = TelegramUser(
            user_id=1,
            entity_type=EntityType.USER,
            username="scamuser",
            is_scam=True,
        )
        result = EntityInspectionResult(entity=entity, inspection_time_ms=0)
        processed = await plugin.process(result)
        assert processed.additional_data["security_analysis"]["risk_level"] == "medium"

    @pytest.mark.asyncio
    async def test_bot_intelligence_plugin(self):
        plugin = BotIntelligencePlugin()
        entity = TelegramUser(
            user_id=2,
            entity_type=EntityType.BOT,
            username="testbot",
            is_bot=True,
        )
        result = EntityInspectionResult(entity=entity, inspection_time_ms=0)
        processed = await plugin.process(result)
        assert processed.additional_data.get("bot_capabilities") is not None


class TestExporters:
    """Test data exporters."""

    def setup_method(self):
        self.entity = TelegramUser(
            user_id=100,
            entity_type=EntityType.USER,
            username="testuser",
            first_name="Test",
        )
        self.result = EntityInspectionResult(
            entity=self.entity,
            inspection_time_ms=10.5,
            cache_hit=False,
        )

    def test_json_exporter(self):
        exporter = JSONExporter()
        json_str = exporter.export_single(self.result)
        assert "testuser" in json_str
        assert "100" in json_str

    def test_csv_exporter(self):
        exporter = CSVExporter()
        results = [self.result, self.result]
        csv_str = exporter.export_batch(results)
        assert "user_id" in csv_str
        assert "100" in csv_str

    def test_html_reporter(self):
        reporter = HTMLReporter()
        results = [self.result, self.result]
        html = reporter.generate_report(results)
        assert "Hody-Telepro" in html
        assert "testuser" in html


class TestAntiFlood:
    """Test anti-flood system and cosmic scheduler."""

    def test_stats(self):
        flood = SmartAntiFlood()
        stats = flood.stats
        assert "flood_events" in stats
        assert "total_delays_seconds" in stats

    @pytest.mark.asyncio
    async def test_retry_handler(self):
        handler = RetryHandler(max_retries=3)
        call_count = 0

        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RuntimeError("temporary failure")
            return "success"

        result = await handler.execute(failing_then_success)
        assert result == "success"
        assert call_count == 2


class TestExceptions:
    """Test custom exceptions."""

    def test_entity_not_found(self):
        exc = EntityNotFoundError("@nonexistent")
        assert "nonexistent" in str(exc)
        assert exc.identifier == "@nonexistent"

    def test_phone_not_found(self):
        exc = PhoneNotFoundError("+1234567890")
        assert "1234567890" in str(exc)

    def test_base_exception(self):
        from hody_telepro.utils.exceptions import HodyTeleproError
        exc = HodyTeleproError("test error")
        assert str(exc) == "test error"


class TestIntegration:
    """Integration tests."""

    def test_model_serialization_roundtrip(self):
        entity = EntityInfo(
            user_id=42,
            entity_type=EntityType.USER,
            username="test42",
            first_name="Test",
            last_name="Forty Two",
            is_premium=True,
            photo=EntityPhoto(has_photo=True, dc_id=2),
        )
        json_str = entity.to_json()
        parsed = json.loads(json_str)
        assert parsed["user_id"] == 42
        assert parsed["username"] == "test42"
        assert parsed["photo"]["has_photo"] is True
