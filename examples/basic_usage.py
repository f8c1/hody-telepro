"""
Hody-Telepro - Basic Usage Examples
=====================================

This file demonstrates the core functionality of Hody-Telepro.
"""

import asyncio
from hody_telepro import HodyClient
from hody_telepro.plugins import BotIntelligencePlugin, SecurityCheckPlugin
from hody_telepro.exporters import JSONExporter, HTMLReporter


async def basic_inspection():
    """Basic entity inspection example."""
    async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
        # Inspect a user
        result = await client.inspect("@telegram")
        print(f"Name: {result.entity.full_name}")
        print(f"Type: {result.entity.entity_type.value}")
        print(f"Verified: {result.entity.is_verified}")
        print(f"Inspection Time: {result.inspection_time_ms:.2f}ms")


async def batch_inspection():
    """Batch inspection example."""
    identifiers = ["@telegram", "@durov", "12345"]

    async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
        results = await client.inspect_batch(identifiers, max_concurrent=3)

        for result in results:
            print(f"  {result.entity.full_name} ({result.entity.entity_type.value})")


async def phone_lookup():
    """Phone number lookup example."""
    async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
        result = await client.lookup_phone("+1234567890")
        print(f"Username: {result.username}")
        print(f"Name: {result.full_name}")
        print(f"Status: {result.status.value}")


async def account_estimation():
    """Account creation estimation example."""
    async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
        estimate = await client.estimate_account(12345)
        print(f"Created: {estimate.estimated_month} {estimate.estimated_year}")
        print(f"Confidence: {estimate.confidence:.2%}")


async def with_plugins():
    """Example with plugins enabled."""
    async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
        # Register built-in plugins
        client.register_plugin("bot_intel", BotIntelligencePlugin())
        client.register_plugin("security", SecurityCheckPlugin())

        result = await client.inspect("@botfather")
        print(f"Security Risk: {result.additional_data.get('security_analysis', {}).get('risk_level')}")


async def export_results():
    """Export results to different formats."""
    async with HodyClient("my_session", api_id=12345, api_hash="your_hash") as client:
        results = await client.inspect_batch(["@telegram", "@durov"])

        # Export to JSON
        JSONExporter().export_batch(results, "results.json")

        # Export to HTML report
        HTMLReporter().generate_report(results, "report.html")

        print("Results exported successfully!")


if __name__ == "__main__":
    # Uncomment the example you want to run:
    # asyncio.run(basic_inspection())
    # asyncio.run(batch_inspection())
    # asyncio.run(phone_lookup())
    # asyncio.run(account_estimation())
    # asyncio.run(with_plugins())
    # asyncio.run(export_results())
    print("Run an example by uncommenting it in __main__")
