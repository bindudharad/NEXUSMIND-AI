from __future__ import annotations

import copy
from threading import Lock
from time import monotonic
from typing import Callable, Generic, TypeVar


T = TypeVar("T")


class TTLResponseCache(Generic[T]):
    def __init__(self, ttl_seconds: float) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._expires_at = 0.0
        self._value: T | None = None

    def get_or_set(self, factory: Callable[[], T]) -> T:
        now = monotonic()
        with self._lock:
            if self._value is not None and now < self._expires_at:
                return self._clone(self._value)
            value = factory()
            self._value = self._clone(value)
            self._expires_at = monotonic() + self.ttl_seconds
            return value

    def seed(self, value: T, ttl_seconds: float | None = None) -> None:
        ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
        with self._lock:
            self._value = self._clone(value)
            self._expires_at = monotonic() + ttl

    def clear(self) -> None:
        with self._lock:
            self._value = None
            self._expires_at = 0.0

    @staticmethod
    def _clone(value: T) -> T:
        if hasattr(value, "model_copy"):
            return value.model_copy(deep=True)  # type: ignore[no-any-return, attr-defined]
        return copy.deepcopy(value)
