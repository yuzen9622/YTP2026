"""Event loop helpers for async drivers that require selector-based loops."""
from __future__ import annotations

import asyncio
import selectors
import sys
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


def selector_event_loop() -> asyncio.AbstractEventLoop:
    """Return a selector event loop compatible with psycopg async connections."""
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop(selectors.SelectSelector())
    return asyncio.SelectorEventLoop()


def run_with_selector_event_loop(main: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine with the same loop factory used by uvicorn scripts."""
    return asyncio.run(main, loop_factory=selector_event_loop)
