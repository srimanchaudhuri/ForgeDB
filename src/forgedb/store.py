from collections.abc import Callable, Iterator
from copy import deepcopy
from dataclasses import dataclass
from typing import Any
from weakref import WeakValueDictionary


@dataclass(frozen=True)
class Entry:
    value: Any
    expires_at: float | None
    created_at: float

    def __post_init__(self) -> None:
        if self.expires_at is not None and self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")


class Store:
    def __init__(self, clock: Callable[[], float]) -> None:
        self._clock = clock
        self._entries: dict[str, Entry] = {}
        self._cache: WeakValueDictionary[str, Entry] = WeakValueDictionary()

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        if ttl is not None and ttl <= 0:
            raise ValueError("ttl must be positive")
        current_time = self._clock()
        expires_at = None if ttl is None else current_time + ttl
        entry = Entry(value=value, expires_at=expires_at, created_at=current_time)
        self._entries[key] = entry

    def exists(self, key: str) -> bool:
        return self._live(key) is not None

    def _live(self, key: str) -> Entry | None:
        entry = self._entries.get(key)
        if entry is None:
            return None

        if entry.expires_at is not None and entry.expires_at <= self._clock():
            del self._entries[key]
            return None
        return entry

    def get(self, key: str, default: Any = None) -> Any | None:
        entry = self._live(key)
        if entry is None:
            return default
        self._cache[key] = entry
        return entry.value

    def delete(self, key: str) -> bool:
        if self._live(key) is not None:
            del self._entries[key]
            return True
        return False

    def expire(self, key: str, seconds: float) -> bool:
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        entry = self._live(key)
        if entry is None:
            return False
        new_expires_at = self._clock() + seconds
        new_entry = Entry(
            value=entry.value, expires_at=new_expires_at, created_at=entry.created_at
        )
        self._entries[key] = new_entry
        return True

    def ttl(self, key: str) -> float:
        entry = self._live(key)
        if entry is None:
            return -2
        if entry.expires_at is None:
            return -1
        return entry.expires_at - self._clock()

    def keys(self) -> list[str]:
        keys = list(self._entries.keys())
        return [key for key in keys if self._live(key) is not None]

    def copy(self, src: str, dst: str) -> bool:
        entry = self._live(src)
        if entry is None:
            return False
        self._entries[dst] = entry
        return True

    def deepcopy(self, src: str, dst: str) -> bool:
        entry = self._live(src)
        if entry is None:
            return False
        new_entry = Entry(
            value=deepcopy(entry.value),
            expires_at=entry.expires_at,
            created_at=entry.created_at,
        )
        self._entries[dst] = new_entry
        return True

    def is_hot(self, key: str) -> bool:
        entry = self._live(key)
        if entry is None:
            return False
        return entry is self._cache.get(key)

    def __getitem__(self, key: str) -> Any:
        entry = self._live(key)
        if entry is None:
            raise KeyError(key)
        self._cache[key] = entry
        return entry.value

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        if self._live(key) is None:
            raise KeyError(key)
        del self._entries[key]

    def __contains__(self, key: str) -> bool:
        return self.exists(key)

    def __len__(self) -> int:
        return len(self.keys())

    def __iter__(self) -> Iterator[str]:
        keys = list(self._entries.keys())
        for key in keys:
            if self._live(key) is not None:
                yield key

    def __bool__(self) -> bool:
        keys = list(self._entries.keys())
        return any(self._live(key) is not None for key in keys)

    def __repr__(self) -> str:
        entries = list(self._entries.items())
        live_entries = {}
        for i in range(min(len(entries), 10)):
            key, entry = entries[i]
            if self._live(key) is not None:
                live_entries[key] = entry
        return f"Store({list(live_entries.keys())})"
