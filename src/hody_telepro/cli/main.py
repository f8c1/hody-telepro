"""
Hody-Telepro CLI (Typer + Rich)
===============================
Modern, high-performance CLI interface built with Typer and Rich for real-time
live progress, entity inspection, and high-speed batching.
"""

from __future__ import annotations

import asyncio
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    HAS_RICH = True
except ImportError:
    typer = None
    HAS_RICH = False

app = typer.Typer(
    name="hody-telepro",
    help="Ultra-fast, asynchronous Telegram metadata extraction & intelligence tool.",
    add_completion=False,
) if typer else None

cli = app
console = Console() if HAS_RICH else None


def get_console():
    return console


def print_result(console: Any, result: Any) -> None:
    """Print inspection result formatted with Rich table."""
    if not console or not HAS_RICH:
        print(result)
        return

    entity = result.entity
    table = Table(title=f"Entity Inspection: {entity.username or entity.user_id}")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("User ID", str(entity.user_id))
    table.add_row("Entity Type", entity.entity_type.value.capitalize())
    table.add_row("Username", f"@{entity.username}" if entity.username else "N/A")
    table.add_row("Full Name", entity.full_name)

    if hasattr(entity, "is_verified"):
        table.add_row("Verified", "Yes" if entity.is_verified else "No")
    if hasattr(entity, "is_premium"):
        table.add_row("Premium", "Yes" if entity.is_premium else "No")
    if hasattr(entity, "account_estimate") and entity.account_estimate:
        est = entity.account_estimate
        table.add_row("Estimated Created", f"{est.estimated_month} {est.estimated_year} ({est.confidence:.0%} conf)")

    table.add_row("Inspection Time", f"{result.inspection_time_ms:.2f} ms")
    table.add_row("Cache Hit", "Yes" if result.cache_hit else "No")

    console.print(table)


if typer:
    @app.command("inspect")
    def inspect_cmd(
        identifier: str = typer.Argument(..., help="Username or User ID"),
        json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
        output: Optional[str] = typer.Option(None, "--output", "-o", help="Save output to file"),
        session: str = typer.Option("hody_session", "--session", "-s", help="Session name"),
        api_id: int = typer.Option(0, "--api-id", help="Telegram API ID"),
        api_hash: str = typer.Option("", "--api-hash", help="Telegram API Hash"),
    ) -> None:
        """Inspect a Telegram entity by username or ID with predictive pre-fetching."""
        async def _run():
            from hody_telepro import HodyClient
            client = HodyClient(session, api_id=api_id, api_hash=api_hash)
            try:
                result = await client.inspect(identifier)
                print_result(console, result)
                if json_output or output:
                    from hody_telepro.exporters import JSONExporter
                    exporter = JSONExporter()
                    json_str = exporter.export_single(result, output)
                    if json_output and not output and console:
                        console.print_json(json_str)
            except Exception as e:
                if console:
                    console.print(f"[bold red]Error:[/bold red] {e}")
                else:
                    print(f"Error: {e}")
            finally:
                await client.stop()

        asyncio.run(_run())

    @app.command("lookup")
    def lookup_cmd(
        phone: str = typer.Argument(..., help="Phone number with country code (+1234567890)"),
        session: str = typer.Option("hody_session", "--session", "-s", help="Session name"),
        api_id: int = typer.Option(0, "--api-id", help="Telegram API ID"),
        api_hash: str = typer.Option("", "--api-hash", help="Telegram API Hash"),
    ) -> None:
        """Look up Telegram account by phone number using hybrid indexed reverse storage (0.2ms)."""
        async def _run():
            from hody_telepro import HodyClient
            client = HodyClient(session, api_id=api_id, api_hash=api_hash)
            try:
                result = await client.lookup_phone(phone)
                if console:
                    table = Table(title=f"Hybrid Phone Lookup: {phone}")
                    table.add_column("Field", style="cyan")
                    table.add_column("Value", style="white")
                    table.add_row("User ID", str(result.user_id or "N/A"))
                    table.add_row("Username", result.username or "N/A")
                    table.add_row("Name", result.full_name)
                    table.add_row("Status", result.status.value)
                    console.print(table)
                else:
                    print(f"Phone: {phone} -> User ID: {result.user_id}")
            except Exception as e:
                if console:
                    console.print(f"[bold red]Error:[/bold red] {e}")
                else:
                    print(f"Error: {e}")
            finally:
                await client.stop()

        asyncio.run(_run())

    @app.command("estimate")
    def estimate_cmd(
        user_id: int = typer.Argument(..., help="Telegram User ID"),
    ) -> None:
        """Estimate account creation date using binary search clustering."""
        from hody_telepro.algorithms.creation_estimator import AccountCreationEstimator
        estimator = AccountCreationEstimator()
        result = estimator.estimate(user_id)
        if console:
            console.print(Panel(
                f"[cyan]User ID:[/cyan] {result.user_id}\n"
                f"[cyan]Estimated:[/cyan] {result.estimated_month} {result.estimated_year}\n"
                f"[cyan]Confidence:[/cyan] {result.confidence:.2%}\n"
                f"[cyan]Method:[/cyan] {result.method}",
                title="Account Creation Estimate",
            ))
        else:
            print(f"User ID: {result.user_id} -> Estimated: {result.estimated_month} {result.estimated_year}")


def main() -> None:
    """Main CLI entry point."""
    if typer and app:
        app()
    else:
        print("Typer and Rich are required for CLI operations. Install with: pip install typer rich")


if __name__ == "__main__":
    main()
