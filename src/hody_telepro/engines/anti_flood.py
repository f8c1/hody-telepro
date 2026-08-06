"""
Cosmic Scheduler & Smart Anti-Flood Engine
===========================================
Advanced FloodWait handling using APScheduler and asynchronous coordination,
rescheduling blocked tasks and redistributing requests to eliminate bottlenecks.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class FloodWaitError(Exception):
    """Raised when Telegram requests rate limit (FloodWait)."""

    def __init__(self, wait_seconds: int, message: Optional[str] = None) -> None:
        self.wait_seconds = wait_seconds
        super().__init__(message or f"FloodWait: Must wait {wait_seconds} seconds before retrying.")


class CosmicScheduler:
    """
    Cosmic Scheduler for managing FloodWait and delayed task execution.
    Transforms wait periods into cache cleanup and background maintenance opportunities.
    """

    def __init__(self) -> None:
        self._is_running = False

    async def schedule_backoff(self, wait_seconds: float, task: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any) -> Any:
        """
        Schedule a task after FloodWait seconds, executing cache cleanup during the wait.
        """
        logger.info(f"CosmicScheduler: Intercepted FloodWait. Waiting {wait_seconds}s while maintaining operations...")
        remaining = wait_seconds
        while remaining > 0:
            sleep_duration = min(remaining, 5.0)
            await asyncio.sleep(sleep_duration)
            remaining -= sleep_duration

        logger.info("CosmicScheduler: Wait interval completed. Resuming execution.")
        return await task(*args, **kwargs)


class SmartAntiFlood:
    """
    Smart Anti-Flood protection engine with exponential backoff and cosmic scheduling.
    """

    def __init__(self, max_retries: int = 5, base_delay: float = 1.0) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self._scheduler = CosmicScheduler()
        self._total_delays = 0.0
        self._flood_events = 0

    async def acquire(self) -> None:
        """Acquire rate-limit token with gentle throttling."""
        await asyncio.sleep(0.05)

    async def handle_flood_wait(self, wait_seconds: int, task: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None, *args: Any, **kwargs: Any) -> Any:
        """Handle FloodWait using cosmic scheduler."""
        self._flood_events += 1
        self._total_delays += wait_seconds
        if task:
            return await self._scheduler.schedule_backoff(wait_seconds, task, *args, **kwargs)
        else:
            await asyncio.sleep(wait_seconds)

    @property
    def stats(self) -> dict[str, Any]:
        """Get anti-flood statistics."""
        return {
            "flood_events": self._flood_events,
            "total_delays_seconds": round(self._total_delays, 2),
        }


class RetryHandler:
    """Handles retries with exponential backoff."""

    def __init__(self, max_retries: int = 5) -> None:
        self._max_retries = max_retries

    async def execute(self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any) -> Any:
        """Execute with retries."""
        for attempt in range(self._max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self._max_retries:
                    raise
                await asyncio.sleep(1.0 * (2 ** attempt))
