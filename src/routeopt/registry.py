"""Generic name -> factory registry (Factory + Registry pattern)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])


class Registry(Generic[T]):
    def __init__(self) -> None:
        self._factories: dict[str, Callable[..., T]] = {}

    def register(self, name: str) -> Callable[[F], F]:
        """Decorator that registers a class or factory function under ``name``."""

        def decorator(factory: F) -> F:
            if name in self._factories:
                raise ValueError(f"{name!r} already registered")
            self._factories[name] = factory
            return factory

        return decorator

    def create(self, name: str, **kwargs: Any) -> T:
        try:
            factory = self._factories[name]
        except KeyError:
            raise KeyError(f"unknown name {name!r}; choose from {self.names()}") from None
        return factory(**kwargs)

    def names(self) -> list[str]:
        return sorted(self._factories)
