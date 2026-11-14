from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Entry:
    value: Any
    expires_at: float | None
    created_at: float

    def __post_init__(self):
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")


class Store:
    def __init__(self, clock: Callable[[], float]):
        self._clock = clock
        self._entries: dict[str, Entry] = {}

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        if ttl is not None and ttl <= 0:
            raise ValueError("ttl must be positive")
        current_time = self._clock()
        expires_at = None if ttl is None else current_time + ttl
        entry = Entry(value=value, expires_at=expires_at, created_at=current_time)
        self._entries[key] = entry

    def exists(self, key: str) -> bool:
        entry = self._entries.get(key)
        if entry is None:
            return False
        if entry.expires_at is not None and entry.expires_at <= self._clock():
            del self._entries[key]
            return False
        return True
