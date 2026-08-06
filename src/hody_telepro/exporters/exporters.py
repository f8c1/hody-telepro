"""
Data Exporters for Hody-Telepro
================================

Provides multiple export formats for inspection results including
JSON, CSV, SQLite, and HTML report generation.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from hody_telepro.models.entities import EntityInspectionResult, EntityType

logger = logging.getLogger(__name__)


class JSONExporter:
    """
    Export inspection results to JSON format.
    
    Supports single results and batch exports with optional formatting.
    """

    def __init__(self, pretty: bool = True, indent: int = 2) -> None:
        self._pretty = pretty
        self._indent = indent

    def export_single(
        self,
        result: EntityInspectionResult,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Export a single inspection result to JSON.
        
        Args:
            result: Inspection result to export
            output_path: File path to save (optional, returns string if None)
            
        Returns:
            JSON string
        """
        data = result.to_dict()
        json_str = json.dumps(data, indent=self._indent if self._pretty else None, default=str)

        if output_path:
            Path(output_path).write_text(json_str, encoding="utf-8")
            logger.info(f"Exported to {output_path}")

        return json_str

    def export_batch(
        self,
        results: list[EntityInspectionResult],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Export multiple inspection results to a JSON array.
        
        Args:
            results: List of inspection results
            output_path: File path to save
            
        Returns:
            JSON string
        """
        data = [r.to_dict() for r in results]
        json_str = json.dumps(
            data,
            indent=self._indent if self._pretty else None,
            default=str,
        )

        if output_path:
            Path(output_path).write_text(json_str, encoding="utf-8")
            logger.info(f"Batch exported {len(results)} results to {output_path}")

        return json_str


class CSVExporter:
    """
    Export inspection results to CSV format.
    
    Generates a flat CSV with one row per entity.
    """

    COLUMNS = [
        "user_id",
        "entity_type",
        "username",
        "first_name",
        "last_name",
        "full_name",
        "is_bot",
        "is_premium",
        "is_verified",
        "is_scam",
        "is_fake",
        "bio",
        "has_photo",
        "account_estimate_month",
        "account_estimate_year",
        "inspection_time_ms",
        "cache_hit",
    ]

    def export_batch(
        self,
        results: list[EntityInspectionResult],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Export multiple results to CSV.
        
        Args:
            results: List of inspection results
            output_path: File path to save
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.COLUMNS)
        writer.writeheader()

        for result in results:
            entity = result.entity
            row = {
                "user_id": entity.user_id,
                "entity_type": entity.entity_type.value,
                "username": entity.username or "",
                "first_name": entity.first_name or "",
                "last_name": entity.last_name or "",
                "full_name": entity.full_name,
                "is_bot": entity.is_bot,
                "is_premium": entity.is_premium,
                "is_verified": entity.is_verified,
                "is_scam": entity.is_scam,
                "is_fake": entity.is_fake,
                "bio": entity.bio or "",
                "has_photo": entity.photo.has_photo,
                "account_estimate_month": (
                    entity.account_estimate.estimated_month
                    if entity.account_estimate else ""
                ),
                "account_estimate_year": (
                    entity.account_estimate.estimated_year
                    if entity.account_estimate else ""
                ),
                "inspection_time_ms": round(result.inspection_time_ms, 3),
                "cache_hit": result.cache_hit,
            }
            writer.writerow(row)

        csv_str = output.getvalue()

        if output_path:
            Path(output_path).write_text(csv_str, encoding="utf-8")
            logger.info(f"CSV exported {len(results)} results to {output_path}")

        return csv_str


class SQLiteExporter:
    """
    Export inspection results to SQLite database.
    
    Creates a structured database with indexes for fast querying.
    """

    def __init__(self, db_path: str = "hody_telepro_data.db") -> None:
        self._db_path = db_path

    async def export_batch(
        self,
        results: list[EntityInspectionResult],
    ) -> None:
        """
        Export multiple results to SQLite.
        
        Args:
            results: List of inspection results
        """
        import aiosqlite

        async with aiosqlite.connect(self._db_path) as db:
            # Create tables
            await db.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    user_id INTEGER PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    is_bot INTEGER,
                    is_premium INTEGER,
                    is_verified INTEGER,
                    is_scam INTEGER,
                    is_fake INTEGER,
                    is_restricted INTEGER,
                    bio TEXT,
                    has_photo INTEGER,
                    language_code TEXT,
                    estimate_month TEXT,
                    estimate_year INTEGER,
                    estimate_confidence REAL,
                    inspection_time_ms REAL,
                    cache_hit INTEGER,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_username ON entities(username)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)
            """)
            await db.commit()

            now = datetime.now().timestamp()
            for result in results:
                entity = result.entity
                await db.execute(
                    """INSERT OR REPLACE INTO entities
                       (user_id, entity_type, username, first_name, last_name,
                        is_bot, is_premium, is_verified, is_scam, is_fake,
                        is_restricted, bio, has_photo, language_code,
                        estimate_month, estimate_year, estimate_confidence,
                        inspection_time_ms, cache_hit, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        entity.user_id,
                        entity.entity_type.value,
                        entity.username,
                        entity.first_name,
                        entity.last_name,
                        entity.is_bot,
                        entity.is_premium,
                        entity.is_verified,
                        entity.is_scam,
                        entity.is_fake,
                        entity.is_restricted,
                        entity.bio,
                        entity.photo.has_photo,
                        entity.language_code,
                        entity.account_estimate.estimated_month if entity.account_estimate else None,
                        entity.account_estimate.estimated_year if entity.account_estimate else None,
                        entity.account_estimate.confidence if entity.account_estimate else None,
                        result.inspection_time_ms,
                        result.cache_hit,
                        now,
                        now,
                    ),
                )

            await db.commit()
            logger.info(f"Exported {len(results)} results to SQLite: {self._db_path}")

    async def query_entities(
        self,
        entity_type: Optional[EntityType] = None,
        username: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Query entities from the SQLite database.
        
        Args:
            entity_type: Filter by entity type
            username: Filter by username
            limit: Maximum results
            
        Returns:
            List of entity dictionaries
        """
        import aiosqlite

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM entities WHERE 1=1"
            params: list = []

            if entity_type:
                query += " AND entity_type = ?"
                params.append(entity_type.value)
            if username:
                query += " AND username LIKE ?"
                params.append(f"%{username}%")

            query += f" LIMIT {limit}"

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


class HTMLReporter:
    """
    Generate HTML reports from inspection results.
    
    Creates a styled HTML page with entity details, statistics,
    and visual summaries.
    """

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hody-Telepro Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f23;
            color: #e0e0e0;
            line-height: 1.6;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, #1a1a3e, #2d2d6b);
            border-radius: 12px;
            margin-bottom: 2rem;
        }}
        .header h1 {{ color: #00d4ff; font-size: 2rem; margin-bottom: 0.5rem; }}
        .header p {{ color: #a0a0c0; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: #1a1a3e;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid #2d2d6b;
        }}
        .stat-card .number {{ font-size: 2rem; color: #00d4ff; font-weight: bold; }}
        .stat-card .label {{ color: #a0a0c0; font-size: 0.9rem; }}
        .entity-card {{
            background: #1a1a3e;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            border: 1px solid #2d2d6b;
        }}
        .entity-card h3 {{ color: #00d4ff; margin-bottom: 0.5rem; }}
        .entity-meta {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
        .badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        .badge-user {{ background: #1e3a5f; color: #64b5f6; }}
        .badge-bot {{ background: #2d4a1e; color: #81c784; }}
        .badge-channel {{ background: #4a1e4a; color: #ce93d8; }}
        .badge-group {{ background: #4a3a1e; color: #ffb74d; }}
        .badge-danger {{ background: #5f1e1e; color: #ef5350; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #2d2d6b; }}
        th {{ color: #00d4ff; font-weight: 600; }}
        .footer {{ text-align: center; padding: 2rem; color: #666; margin-top: 2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Hody-Telepro Inspection Report</h1>
            <p>Generated on {timestamp}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="number">{total_entities}</div>
                <div class="label">Total Entities</div>
            </div>
            <div class="stat-card">
                <div class="number">{users_count}</div>
                <div class="label">Users</div>
            </div>
            <div class="stat-card">
                <div class="number">{bots_count}</div>
                <div class="label">Bots</div>
            </div>
            <div class="stat-card">
                <div class="number">{channels_count}</div>
                <div class="label">Channels</div>
            </div>
            <div class="stat-card">
                <div class="number">{groups_count}</div>
                <div class="label">Groups</div>
            </div>
            <div class="stat-card">
                <div class="number">{avg_time}ms</div>
                <div class="label">Avg Inspection Time</div>
            </div>
        </div>

        <h2 style="color: #00d4ff; margin-bottom: 1rem;">Entity Details</h2>
        {entity_cards}

        <div class="footer">
            <p>Generated by Hody-Telepro v{version}</p>
        </div>
    </div>
</body>
</html>"""

    ENTITY_CARD_TEMPLATE = """
    <div class="entity-card">
        <h3>{full_name}</h3>
        <div class="entity-meta">
            <span class="badge badge-{entity_type}">{entity_type_label}</span>
            <span>@{username}</span>
            <span>ID: {user_id}</span>
            {risk_badge}
        </div>
        <table>
            <tr><td>Verified</td><td>{is_verified}</td></tr>
            <tr><td>Premium</td><td>{is_premium}</td></tr>
            <tr><td>Bot</td><td>{is_bot}</td></tr>
            <tr><td>Has Photo</td><td>{has_photo}</td></tr>
            <tr><td>Est. Created</td><td>{estimate}</td></tr>
            <tr><td>Inspection Time</td><td>{inspection_time}ms</td></tr>
        </table>
    </div>
    """

    def generate_report(
        self,
        results: list[EntityInspectionResult],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate an HTML report from inspection results.
        
        Args:
            results: List of inspection results
            output_path: File path to save
            
        Returns:
            HTML string
        """
        from hody_telepro import __version__

        # Calculate statistics
        total = len(results)
        users = sum(1 for r in results if r.entity_type == EntityType.USER)
        bots = sum(1 for r in results if r.entity_type == EntityType.BOT)
        channels = sum(1 for r in results if r.entity_type == EntityType.CHANNEL)
        groups = sum(1 for r in results if r.entity_type in (EntityType.GROUP, EntityType.SUPPERGROUP))

        avg_time = sum(r.inspection_time_ms for r in results) / max(total, 1)

        # Generate entity cards
        entity_cards = ""
        for result in results:
            entity = result.entity
            risk = result.additional_data.get("security_analysis", {}).get("risk_level", "low")
            risk_badge = (
                f'<span class="badge badge-danger">Risk: {risk}</span>'
                if risk == "high" else ""
            )

            entity_cards += self.ENTITY_CARD_TEMPLATE.format(
                full_name=entity.full_name,
                entity_type=entity.entity_type.value,
                entity_type_label=entity.entity_type.value.capitalize(),
                username=entity.username or "N/A",
                user_id=entity.user_id,
                risk_badge=risk_badge,
                is_verified="Yes" if entity.is_verified else "No",
                is_premium="Yes" if entity.is_premium else "No",
                is_bot="Yes" if entity.is_bot else "No",
                has_photo="Yes" if entity.photo.has_photo else "No",
                estimate=(
                    f"{entity.account_estimate.estimated_month} {entity.account_estimate.estimated_year}"
                    if entity.account_estimate else "Unknown"
                ),
                inspection_time=round(result.inspection_time_ms, 2),
            )

        html = self.HTML_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_entities=total,
            users_count=users,
            bots_count=bots,
            channels_count=channels,
            groups_count=groups,
            avg_time=round(avg_time, 2),
            entity_cards=entity_cards,
            version=__version__,
        )

        if output_path:
            Path(output_path).write_text(html, encoding="utf-8")
            logger.info(f"HTML report saved to {output_path}")

        return html
