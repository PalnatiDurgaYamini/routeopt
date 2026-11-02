"""Concurrency helpers, chosen by workload type.

CPU-bound (route optimisation)  -> processes  (bypasses the GIL)
I/O-bound (loading order files) -> asyncio / threads (GIL is released while waiting)
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import TypeVar

from routeopt.fileio import merge_orders, read_orders_csv
from routeopt.models import Order

T = TypeVar("T")
R = TypeVar("R")


def parallel_map(fn: Callable[[T], R], items: Sequence[T], workers: int) -> list[R]:
    """CPU-bound map. ``fn`` must be a picklable top-level function.

    Falls back to a plain loop for one worker or one item, because starting
    processes costs more than it saves on tiny workloads.
    """
    if workers <= 1 or len(items) <= 1:
        return [fn(item) for item in items]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, items, chunksize=1))


def thread_map(fn: Callable[[T], R], items: Sequence[T], workers: int) -> list[R]:
    """I/O-bound map using threads."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(fn, items))


async def fetch_orders(
    sources: Sequence[Path], *, concurrency: int = 8, latency: float = 0.0
) -> list[Order]:
    """Load several order files concurrently and merge them.

    ``latency`` simulates a slow remote source (seconds per source).
    A semaphore bounds how many loads run at once.
    """
    gate = asyncio.Semaphore(concurrency)

    async def load(path: Path) -> list[Order]:
        async with gate:
            if latency:
                await asyncio.sleep(latency)
            return await asyncio.to_thread(lambda: list(read_orders_csv(path)))

    batches = await asyncio.gather(*(load(p) for p in sources))
    return merge_orders(batches)
