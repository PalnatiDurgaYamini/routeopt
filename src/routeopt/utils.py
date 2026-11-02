"""Small cross-cutting helpers: a context manager, a decorator, a generator."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable, Iterator
from functools import wraps
from types import TracebackType
from typing import ParamSpec, TypeVar

log = logging.getLogger("routeopt")

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T")


class Timer:
    """Context manager measuring wall-clock time: ``with Timer() as t: ...; t.elapsed``."""

    def __init__(self) -> None:
        self.elapsed = 0.0
        self._start = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.elapsed = time.perf_counter() - self._start


def timed(fn: Callable[P, R]) -> Callable[P, R]:
    """Decorator: log how long the wrapped call took (DEBUG level)."""

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        with Timer() as t:
            result = fn(*args, **kwargs)
        log.debug("%s took %.4fs", fn.__qualname__, t.elapsed)
        return result

    return wrapper


def batched(items: Iterable[T], size: int) -> Iterator[tuple[T, ...]]:
    """Lazily yield tuples of up to ``size`` items (generator; O(size) memory)."""
    if size < 1:
        raise ValueError("size must be >= 1")
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield tuple(batch)
            batch = []
    if batch:
        yield tuple(batch)
