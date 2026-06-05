"""Scheduler stub — no background jobs currently configured."""
from loguru import logger


async def start_scheduler() -> None:
    logger.debug("[scheduler] No background jobs configured, scheduler not started")


async def stop_scheduler() -> None:
    logger.debug("[scheduler] Nothing to stop")
