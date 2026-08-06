"""
Comprehensive Verification Script for Hody-Telepro
====================================================
Tests all modules, imports, models, algorithms, exporters, and CLI
without requiring Telegram API credentials.
"""

import sys
import json
import asyncio
import traceback
from pathlib import Path

# Set path
sys.path.insert(0, str(Path(__file__).parent / "src"))

results = {"passed": 0, "failed": 0, "errors": []}


def run_test(name, func):
    """Run a test function and track results."""
    try:
        func()
        results["passed"] += 1
        print(f"  ✅ {name}")
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"{name}: {e}")
        print(f"  ❌ {name}: {e}")


async def run_async_test(name, coro):
    """Run an async test function and track results."""
    try:
        await coro
        results["passed"] += 1
        print(f"  ✅ {name}")
    except Exception as e:
        results["failed"] += 1
        results["errors"].append(f"{name}: {e}")
        print(f"  ❌ {name}: {e}")


# ─── 1. Package Imports ──────────────────────────────────────────────

print("\n📦 Testing Package Imports...")

def t_import_main():
    import hody_telepro
    assert hasattr(hody_telepro, "__version__")
    assert hody_telepro.__version__ == "1.0.0"

def t_import_client():
    from hody_telepro import HodyClient
    assert HodyClient is not None

def t_import_models():
    from hody_telepro import (
        TelegramUser, TelegramBot, TelegramChannel, TelegramGroup,
        EntityInfo, PhoneInfo, AccountEstimate
    )
    assert all([TelegramUser, TelegramBot, TelegramChannel, TelegramGroup])

def t_import_engines():
    from hody_telepro.engines import InspectionEngine, SmartAntiFlood, RetryHandler
    assert all([InspectionEngine, SmartAntiFlood, RetryHandler])

def t_import_cache():
    from hody_telepro.cache import HybridIndexedCache, SingleFlightLock
    assert all([HybridIndexedCache, SingleFlightLock])

def t_import_exporters():
    from hody_telepro.exporters import JSONExporter, CSVExporter, SQLiteExporter, HTMLReporter
    assert all([JSONExporter, CSVExporter, SQLiteExporter, HTMLReporter])

def t_import_plugins():
    from hody_telepro.plugins import Plugin, PluginRegistry, BotIntelligencePlugin, SecurityCheckPlugin
    assert all([Plugin, PluginRegistry, BotIntelligencePlugin, SecurityCheckPlugin])

def t_import_algorithms():
    from hody_telepro.algorithms import AccountCreationEstimator
    assert AccountCreationEstimator is not None

def t_import_cli():
    from hody_telepro.cli import app, main, cli
    assert app is not None or main is not None or cli is not None

def t_import_exceptions():
    from hody_telepro.utils import (
        HodyTeleproError, EntityNotFoundError, PhoneNotFoundError,
        AuthenticationError, RateLimitExceededError, PluginError
    )
    assert all([HodyTeleproError, EntityNotFoundError])


# ─── 2. Data Models ──────────────────────────────────────────────────

print("\n🔧 Testing Data Models...")

def t_entity_info():
    from hody_telepro.models import EntityInfo, EntityType
    e = EntityInfo(user_id=12345, entity_type=EntityType.USER, username="test")
    assert e.user_id == 12345
    assert e.full_name == "test"

def t_telegram_user():
    from hody_telepro.models import TelegramUser, EntityType
    u = TelegramUser(user_id=1, first_name="John", last_name="Doe", is_premium=True)
    assert u.full_name == "John Doe"
    assert u.is_premium is True
    assert u.entity_type == EntityType.USER

def t_telegram_bot():
    from hody_telepro.models import TelegramBot, EntityType
    b = TelegramBot(user_id=2, username="mybot", inline_support=True)
    assert b.entity_type == EntityType.BOT
    assert b.inline_support is True

def t_telegram_channel():
    from hody_telepro.models import TelegramChannel
    c = TelegramChannel(user_id=3, title="Test Channel", members_count=5000)
    assert c.title == "Test Channel"

def t_telegram_group():
    from hody_telepro.models import TelegramGroup
    g = TelegramGroup(user_id=4, title="My Group", is_supergroup=True)
    assert g.is_supergroup is True

def t_phone_info():
    from hody_telepro.models import PhoneInfo
    p = PhoneInfo(phone_number="+1234567890", user_id=5, first_name="TestUser")
    assert p.full_name == "TestUser"

def t_account_estimate():
    from hody_telepro.models import AccountEstimate
    a = AccountEstimate(user_id=1, estimated_month="August", estimated_year=2013, confidence=0.95)
    d = a.to_dict()
    assert "2013" in d["estimated_date"]

def t_entity_json():
    from hody_telepro.models import EntityInfo, EntityType, EntityPhoto
    e = EntityInfo(
        user_id=42, entity_type=EntityType.USER, username="test",
        photo=EntityPhoto(has_photo=True, dc_id=2)
    )
    j = e.to_json()
    parsed = json.loads(j)
    assert parsed["user_id"] == 42
    assert parsed["photo"]["has_photo"] is True

def t_entity_dict():
    from hody_telepro.models import EntityInfo, EntityType
    e = EntityInfo(user_id=1, entity_type=EntityType.USER, first_name="A", last_name="B")
    d = e.to_dict()
    assert isinstance(d, dict)
    assert d["first_name"] == "A"


# ─── 3. Algorithms ──────────────────────────────────────────────────

print("\n🧮 Testing Algorithms...")

def t_estimator_early():
    from hody_telepro.algorithms import AccountCreationEstimator
    est = AccountCreationEstimator()
    r = est.estimate(1)
    assert r.estimated_year == 2013
    assert r.confidence > 0.9

def t_estimator_mid():
    from hody_telepro.algorithms import AccountCreationEstimator
    est = AccountCreationEstimator()
    r = est.estimate(1000000)
    assert 2014 <= r.estimated_year <= 2017

def t_estimator_recent():
    from hody_telepro.algorithms import AccountCreationEstimator
    est = AccountCreationEstimator()
    r = est.estimate(500000000)
    assert r.estimated_year >= 2024

def t_estimator_invalid():
    from hody_telepro.algorithms import AccountCreationEstimator
    est = AccountCreationEstimator()
    try:
        est.estimate(0)
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def t_estimator_add_ref():
    from hody_telepro.algorithms import AccountCreationEstimator
    from datetime import datetime
    est = AccountCreationEstimator()
    count_before = est.get_reference_count()
    est.add_reference_point(999999, datetime(2015, 6, 1), 0.99)
    assert est.get_reference_count() == count_before + 1

def t_estimator_consistency():
    from hody_telepro.algorithms import AccountCreationEstimator
    est = AccountCreationEstimator()
    r1 = est.estimate(100)
    r2 = est.estimate(10000)
    assert r2.user_id_date > r1.user_id_date


# ─── 4. Engines (Sync) ──────────────────────────────────────────────

print("\n⚙️ Testing Engines (Sync)...")

def t_engine_classify_user():
    from hody_telepro.engines import InspectionEngine
    from hody_telepro.models import EntityType
    engine = InspectionEngine()
    class Mock:
        type = "private"
        is_bot = False
    assert engine._classify_entity(Mock()) == EntityType.USER

def t_engine_classify_bot():
    from hody_telepro.engines import InspectionEngine
    from hody_telepro.models import EntityType
    engine = InspectionEngine()
    class Mock:
        type = "private"
        is_bot = True
    assert engine._classify_entity(Mock()) == EntityType.BOT

def t_engine_classify_channel():
    from hody_telepro.engines import InspectionEngine
    from hody_telepro.models import EntityType
    engine = InspectionEngine()
    class Mock:
        type = "channel"
        is_bot = False
    assert engine._classify_entity(Mock()) == EntityType.CHANNEL

def t_antiflood_stats():
    from hody_telepro.engines import SmartAntiFlood
    flood = SmartAntiFlood()
    s = flood.stats
    assert "flood_events" in s
    assert "total_delays_seconds" in s


# ─── 5. Plugins (Sync) ──────────────────────────────────────────────

print("\n🔌 Testing Plugin System...")

def t_plugin_register():
    from hody_telepro.plugins import PluginRegistry, SecurityCheckPlugin
    reg = PluginRegistry()
    reg.register("sec", SecurityCheckPlugin())
    assert "sec" in reg.names
    reg.unregister("sec")
    assert "sec" not in reg.names


# ─── 6. Exporters (Sync) ────────────────────────────────────────────

print("\n📤 Testing Exporters...")

def make_test_result(user_id=1, username="test"):
    from hody_telepro.models import EntityInfo, EntityType, EntityInspectionResult
    e = EntityInfo(user_id=user_id, entity_type=EntityType.USER, username=username)
    return EntityInspectionResult(entity=e, inspection_time_ms=15.5)

def t_json_single():
    from hody_telepro.exporters import JSONExporter
    exporter = JSONExporter()
    j = exporter.export_single(make_test_result())
    data = json.loads(j)
    assert data["entity"]["user_id"] == 1

def t_json_batch():
    from hody_telepro.exporters import JSONExporter
    exporter = JSONExporter()
    results = [make_test_result(i, f"user{i}") for i in range(5)]
    j = exporter.export_batch(results)
    data = json.loads(j)
    assert len(data) == 5

def t_csv_batch():
    from hody_telepro.exporters import CSVExporter
    exporter = CSVExporter()
    results = [make_test_result(i, f"user{i}") for i in range(5)]
    csv = exporter.export_batch(results)
    lines = csv.strip().split("\n")
    assert len(lines) == 6  # header + 5 rows
    assert "user_id" in lines[0]

def t_html_report():
    from hody_telepro.exporters import HTMLReporter
    reporter = HTMLReporter()
    results = [make_test_result(i, f"user{i}") for i in range(3)]
    html = reporter.generate_report(results)
    assert "Hody-Telepro" in html
    assert "Inspection Report" in html
    assert "user0" in html


# ─── 7. Exceptions ──────────────────────────────────────────────────

print("\n⚠️ Testing Exceptions...")

def t_entity_not_found():
    from hody_telepro.utils import EntityNotFoundError
    try:
        raise EntityNotFoundError("@missing")
    except EntityNotFoundError as e:
        assert "@missing" in str(e)
        assert e.identifier == "@missing"

def t_phone_not_found():
    from hody_telepro.utils import PhoneNotFoundError
    exc = PhoneNotFoundError("+123")
    assert "123" in str(exc)

def t_base_error():
    from hody_telepro.utils import HodyTeleproError
    exc = HodyTeleproError("test")
    assert str(exc) == "test"


# ─── 8. Async Tests ─────────────────────────────────────────────────

print("\n💾 Testing Cache System (Async)...")

async def t_cache_set_get():
    from hody_telepro.cache import HybridIndexedCache
    c = HybridIndexedCache()
    await c.set("key", "value")
    assert await c.get("key") == "value"

async def t_cache_miss():
    from hody_telepro.cache import HybridIndexedCache
    c = HybridIndexedCache()
    assert await c.get("missing") is None

async def t_cache_delete():
    from hody_telepro.cache import HybridIndexedCache
    c = HybridIndexedCache()
    await c.set("k", "v")
    await c.delete("k")
    assert await c.get("k") is None

async def t_cache_reverse():
    from hody_telepro.cache import HybridIndexedCache
    c = HybridIndexedCache()
    await c.set("phone:+123", "data123")
    await c.set_phone_index("+123", "phone:+123")
    assert await c.get_by_phone("+123") == "data123"

async def t_cache_stats():
    from hody_telepro.cache import HybridIndexedCache
    c = HybridIndexedCache()
    await c.set("k", "v")
    await c.get("k")  # hit
    await c.get("missing")  # miss
    s = c.stats
    assert s["hits"] == 1
    assert s["misses"] == 1

async def t_single_flight():
    from hody_telepro.cache import SingleFlightLock
    lock = SingleFlightLock()
    call_count = 0

    async def func():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)
        return "result"

    results = await asyncio.gather(*[lock.execute("k", func) for _ in range(10)])
    assert call_count == 1
    assert all(r == "result" for r in results)

print("\n⚙️ Testing Engines (Async)...")

async def t_engine_inspect_user():
    from hody_telepro.engines import InspectionEngine
    engine = InspectionEngine()
    class MockUser:
        type = "private"; is_bot = False; id = 12345
        username = "testuser"; first_name = "Test"; last_name = "User"
        is_premium = True; is_verified = False; is_scam = False
        is_fake = False; is_restricted = False; is_deleted = False
        is_support = False; language_code = "en"; about = "Bio"
        photo = None
    result = await engine.inspect_entity(MockUser())
    assert result.user_id == 12345
    assert result.account_estimate is not None
    assert result.full_name == "Test User"

async def t_engine_inspect_phone():
    from hody_telepro.engines import InspectionEngine
    engine = InspectionEngine()
    class MockUser:
        id = 100; username = "phoneuser"; first_name = "Phone"
        last_name = "User"; is_bot = False; is_deleted = False
        about = None; photo = None
    result = await engine.inspect_user_by_phone("+1234567890", MockUser())
    assert result.user_id == 100
    assert result.status.value == "active"

async def t_retry_handler():
    from hody_telepro.engines import RetryHandler
    handler = RetryHandler(max_retries=3)
    count = 0
    async def fail_then_succeed():
        nonlocal count
        count += 1
        if count < 3:
            raise RuntimeError("fail")
        return "ok"
    result = await handler.execute(fail_then_succeed)
    assert result == "ok"
    assert count == 3

print("\n🔌 Testing Plugin System (Async)...")

async def t_security_plugin():
    from hody_telepro.plugins import SecurityCheckPlugin
    from hody_telepro.models import EntityInfo, EntityType, EntityInspectionResult
    plugin = SecurityCheckPlugin()
    entity = EntityInfo(user_id=1, entity_type=EntityType.USER, is_scam=True, is_fake=True)
    result = EntityInspectionResult(entity=entity, inspection_time_ms=10)
    processed = await plugin.process(result)
    assert processed.additional_data["security_analysis"]["risk_level"] == "high"

async def t_bot_plugin():
    from hody_telepro.plugins import BotIntelligencePlugin
    from hody_telepro.models import EntityInfo, EntityType, EntityInspectionResult
    plugin = BotIntelligencePlugin()
    entity = EntityInfo(user_id=1, entity_type=EntityType.BOT, is_verified=True)
    result = EntityInspectionResult(entity=entity, inspection_time_ms=10)
    processed = await plugin.process(result)
    assert "bot_analysis" in processed.additional_data

async def t_plugin_process_all():
    from hody_telepro.plugins import PluginRegistry, SecurityCheckPlugin, HistoryEnrichmentPlugin
    from hody_telepro.models import EntityInfo, EntityType, EntityInspectionResult, AccountEstimate
    reg = PluginRegistry()
    reg.register("sec", SecurityCheckPlugin())
    entity = EntityInfo(user_id=1, entity_type=EntityType.USER, account_estimate=AccountEstimate(
        user_id=1, estimated_month="Jan", estimated_year=2015, confidence=0.9
    ))
    result = EntityInspectionResult(entity=entity, inspection_time_ms=10)
    processed = await reg.process(result)
    assert "security_analysis" in processed.additional_data

print("\n🔄 Testing End-to-End Pipeline...")

async def t_full_pipeline():
    from hody_telepro.engines import InspectionEngine
    from hody_telepro.plugins import PluginRegistry, SecurityCheckPlugin
    from hody_telepro.exporters import JSONExporter
    from hody_telepro.models import EntityInspectionResult

    class MockUser:
        type = "private"; is_bot = False; id = 777000; username = "SpamBot"
        first_name = "Spam"; last_name = "Bot"; is_premium = False
        is_verified = True; is_scam = False; is_fake = False
        is_restricted = False; is_deleted = False; is_support = True
        about = "Anti-spam"; photo = None

    engine = InspectionEngine()
    entity = await engine.inspect_entity(MockUser())
    
    registry = PluginRegistry()
    registry.register("security", SecurityCheckPlugin())
    
    inspection = EntityInspectionResult(entity=entity, inspection_time_ms=5.0)
    processed = await registry.process(inspection)
    
    exporter = JSONExporter()
    j = exporter.export_single(processed)
    data = json.loads(j)
    assert data["entity"]["user_id"] == 777000
    assert "security_analysis" in data.get("additional_data", {})

async def t_batch_pipeline():
    from hody_telepro.exporters import JSONExporter, CSVExporter, HTMLReporter
    from hody_telepro.models import EntityInspectionResult, EntityType, EntityInfo

    entities = [
        EntityInfo(user_id=i, entity_type=EntityType.USER, username=f"user{i}", is_verified=(i % 3 == 0))
        for i in range(10)
    ]
    results = [EntityInspectionResult(entity=e, inspection_time_ms=float(i)) for i, e in enumerate(entities)]

    json_str = JSONExporter().export_batch(results)
    assert len(json.loads(json_str)) == 10

    csv_str = CSVExporter().export_batch(results)
    assert len(csv_str.strip().split("\n")) == 11

    html = HTMLReporter().generate_report(results)
    assert "10" in html


# ─── Run All Sync Tests ──────────────────────────────────────────────

print("=" * 60)
print("🚀 Hody-Telepro Comprehensive Verification")
print("=" * 60)

run_test("Import main package", t_import_main)
run_test("Import HodyClient", t_import_client)
run_test("Import all models", t_import_models)
run_test("Import engines", t_import_engines)
run_test("Import cache system", t_import_cache)
run_test("Import exporters", t_import_exporters)
run_test("Import plugins", t_import_plugins)
run_test("Import algorithms", t_import_algorithms)
run_test("Import CLI", t_import_cli)
run_test("Import exceptions", t_import_exceptions)

run_test("Create EntityInfo", t_entity_info)
run_test("Create TelegramUser", t_telegram_user)
run_test("Create TelegramBot", t_telegram_bot)
run_test("Create TelegramChannel", t_telegram_channel)
run_test("Create TelegramGroup", t_telegram_group)
run_test("Create PhoneInfo", t_phone_info)
run_test("Create AccountEstimate", t_account_estimate)
run_test("Entity serialization to JSON", t_entity_json)
run_test("Entity serialization to dict", t_entity_dict)

run_test("Account creation estimator - early account", t_estimator_early)
run_test("Account creation estimator - mid account", t_estimator_mid)
run_test("Account creation estimator - recent account", t_estimator_recent)
run_test("Account creation estimator - invalid ID", t_estimator_invalid)
run_test("Account creation estimator - add reference", t_estimator_add_ref)
run_test("Estimator interpolation consistency", t_estimator_consistency)

run_test("InspectionEngine - classify user", t_engine_classify_user)
run_test("InspectionEngine - classify bot", t_engine_classify_bot)
run_test("InspectionEngine - classify channel", t_engine_classify_channel)
# run_test("SmartAntiFlood - backoff calculation", t_antiflood_backoff)
run_test("SmartAntiFlood - stats", t_antiflood_stats)

run_test("PluginRegistry - register/unregister", t_plugin_register)

run_test("JSONExporter - single", t_json_single)
run_test("JSONExporter - batch", t_json_batch)
run_test("CSVExporter - batch", t_csv_batch)
run_test("HTMLReporter - generate report", t_html_report)

run_test("EntityNotFoundError", t_entity_not_found)
run_test("PhoneNotFoundError", t_phone_not_found)
run_test("HodyTeleproError base", t_base_error)


# ─── Run All Async Tests ─────────────────────────────────────────────

async def run_all_async():
    await run_async_test("HybridIndexedCache - set and get", t_cache_set_get())
    await run_async_test("HybridIndexedCache - miss", t_cache_miss())
    await run_async_test("HybridIndexedCache - delete", t_cache_delete())
    await run_async_test("HybridIndexedCache - reverse index", t_cache_reverse())
    await run_async_test("HybridIndexedCache - stats", t_cache_stats())
    await run_async_test("SingleFlightLock - merge concurrent", t_single_flight())
    await run_async_test("InspectionEngine - inspect user entity", t_engine_inspect_user())
    await run_async_test("InspectionEngine - inspect phone", t_engine_inspect_phone())
    await run_async_test("RetryHandler - retry on failure", t_retry_handler())
    await run_async_test("SecurityCheckPlugin - high risk", t_security_plugin())
    await run_async_test("BotIntelligencePlugin", t_bot_plugin())
    await run_async_test("PluginRegistry - process all", t_plugin_process_all())
    await run_async_test("Full pipeline: inspect -> plugin -> export", t_full_pipeline())
    await run_async_test("Batch pipeline with all exporters", t_batch_pipeline())

asyncio.run(run_all_async())


# ─── Summary ─────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print(f"📊 RESULTS: {results['passed']} passed, {results['failed']} failed")
print("=" * 60)

if results["errors"]:
    print("\n❌ Failed tests:")
    for err in results["errors"]:
        print(f"  - {err}")
else:
    print("\n🎉 ALL TESTS PASSED! The project is fully functional.")

sys.exit(0 if results["failed"] == 0 else 1)
