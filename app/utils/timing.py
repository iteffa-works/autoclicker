"""High-resolution timers for scheduling (Windows user-space)."""

from __future__ import annotations

import time
from typing import Callable


def monotonic_now() -> float:
    return time.perf_counter()


def sleep_until_deadline(deadline: float) -> None:
    """Sleep until perf_counter() reaches deadline; busy-waits briefly if near."""
    while True:
        now = time.perf_counter()
        if now >= deadline:
            return
        remaining = deadline - now
        if remaining > 0.002:
            time.sleep(remaining - 0.001)
        else:
            while time.perf_counter() < deadline:
                pass


def schedule_next_interval(
    interval_ms: float,
    jitter_ms: float,
    rng,
) -> float:
    """Return delay in seconds until next tick (with optional jitter)."""
    base = max(0.0, float(interval_ms))
    j = float(jitter_ms)
    if j > 0:
        base -= j
        span = 2.0 * j
        base += rng.uniform(0.0, span) if span > 0 else 0.0
    return max(0.0, base) / 1000.0
