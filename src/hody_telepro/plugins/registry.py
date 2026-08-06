"""
Plugin System for Hody-Telepro
===============================

Provides an extensible plugin architecture that allows users to add
custom functionality to the inspection pipeline without modifying
the core library code.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from hody_telepro.models.entities import EntityInspectionResult

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """
    Base class for all Hody-Telepro plugins.
    
    Plugins can process inspection results to add additional analysis,
    validation, or data enrichment.
    
    Example:
        class MyPlugin(Plugin):
            async def process(self, result: EntityInspectionResult) -> EntityInspectionResult:
                result.additional_data["my_field"] = "custom_value"
                return result
    """

    name: str = "unnamed_plugin"
    version: str = "1.0.0"
    description: str = ""

    @abstractmethod
    async def process(self, result: EntityInspectionResult) -> EntityInspectionResult:
        """
        Process an inspection result.
        
        Args:
            result: The entity inspection result to process
            
        Returns:
            Modified inspection result
        """
        ...

    async def on_init(self, client: Any) -> None:
        """Called when the plugin is initialized with a client."""
        pass

    async def on_inspection_start(self, identifier: str) -> None:
        """Called before an inspection begins."""
        pass

    async def on_inspection_complete(self, result: EntityInspectionResult) -> None:
        """Called after an inspection completes."""
        pass


class PluginRegistry:
    """
    Registry for managing and executing plugins.
    
    Features:
        - Register/unregister plugins by name
        - Execute plugins in order
        - Plugin lifecycle management
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, name: str, plugin: Plugin) -> None:
        """
        Register a plugin.
        
        Args:
            name: Unique plugin identifier
            plugin: Plugin instance
        """
        if name in self._plugins:
            logger.warning(f"Plugin '{name}' already registered, replacing")
        self._plugins[name] = plugin
        plugin.name = name
        logger.info(f"Plugin registered: {name} v{plugin.version}")

    def unregister(self, name: str) -> Optional[Plugin]:
        """Unregister a plugin by name."""
        plugin = self._plugins.pop(name, None)
        if plugin:
            logger.info(f"Plugin unregistered: {name}")
        return plugin

    def get(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)

    @property
    def plugins(self) -> dict[str, Plugin]:
        """Get all registered plugins."""
        return dict(self._plugins)

    @property
    def names(self) -> list[str]:
        """Get all plugin names."""
        return list(self._plugins.keys())

    async def process(self, result: EntityInspectionResult) -> EntityInspectionResult:
        """
        Process a result through all registered plugins.
        
        Args:
            result: Inspection result to process
            
        Returns:
            Result after plugin processing
        """
        for name, plugin in self._plugins.items():
            try:
                result = await plugin.process(result)
            except Exception as e:
                logger.error(f"Plugin '{name}' error during processing: {e}")
        return result

    async def init_all(self, client: Any) -> None:
        """Initialize all plugins with the client."""
        for name, plugin in self._plugins.items():
            try:
                await plugin.on_init(client)
            except Exception as e:
                logger.error(f"Plugin '{name}' init error: {e}")

    async def notify_start(self, identifier: str) -> None:
        """Notify all plugins that inspection is starting."""
        for name, plugin in self._plugins.items():
            try:
                await plugin.on_inspection_start(identifier)
            except Exception as e:
                logger.error(f"Plugin '{name}' start notification error: {e}")

    async def notify_complete(self, result: EntityInspectionResult) -> None:
        """Notify all plugins that inspection is complete."""
        for name, plugin in self._plugins.items():
            try:
                await plugin.on_inspection_complete(result)
            except Exception as e:
                logger.error(f"Plugin '{name}' complete notification error: {e}")


# ─── Built-in Plugins ───────────────────────────────────────────────

class BotIntelligencePlugin(Plugin):
    """
    Plugin that analyzes bot behavior patterns.
    
    Determines if an account is a real bot or a disguised user,
    and analyzes bot capabilities.
    """

    name = "bot_intelligence"
    version = "1.0.0"
    description = "Analyzes bot behavior patterns and capabilities"

    async def process(self, result: EntityInspectionResult) -> EntityInspectionResult:
        from hody_telepro.models.entities import EntityType

        if result.entity_type != EntityType.BOT:
            return result

        entity = result.entity
        raw = entity.raw_data or {}

        # Analyze bot capabilities
        capabilities = []
        if raw.get("bot_info"):
            bot_info = raw.get("bot_info", {})
            if getattr(bot_info, "description", None):
                capabilities.append("has_description")
            if getattr(bot_info, "inline_placeholder", None):
                capabilities.append("inline_support")

        result.additional_data["bot_capabilities"] = capabilities
        result.additional_data["bot_analysis"] = {
            "is_verified_bot": bool(entity.is_verified),
            "has_inline": bool(getattr(entity, "inline_support", False)),
            "has_description": bool(getattr(entity, "bot_description", None)),
            "can_join_groups": getattr(entity, "can_join_groups", None),
        }

        return result


class HistoryEnrichmentPlugin(Plugin):
    """
    Plugin that enriches entity data with historical context.
    """

    name = "history_enrichment"
    version = "1.0.0"
    description = "Enriches entity data with historical context"

    async def process(self, result: EntityInspectionResult) -> EntityInspectionResult:
        if result.entity.account_estimate:
            result.additional_data["account_age_info"] = {
                "estimated": result.entity.account_estimate.to_dict(),
            }
        return result


class SecurityCheckPlugin(Plugin):
    """
    Plugin that performs security analysis on entities.
    """

    name = "security_check"
    version = "1.0.0"
    description = "Performs security analysis on entities"

    async def process(self, result: EntityInspectionResult) -> EntityInspectionResult:
        flags = []
        risk_score = 0

        if result.entity.is_scam:
            flags.append("scam_flagged")
            risk_score += 40
        if result.entity.is_fake:
            flags.append("fake_flagged")
            risk_score += 50
        if result.entity.is_restricted:
            flags.append("restricted")
            risk_score += 30

        result.additional_data["security_analysis"] = {
            "risk_score": risk_score,
            "risk_level": "high" if risk_score >= 70 else "medium" if risk_score >= 30 else "low",
            "flags": flags,
        }

        return result
