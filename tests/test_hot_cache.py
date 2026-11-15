"""Checkpoint 1: hot-key cache built on weakref.WeakValueDictionary.

Contract (add to Store in src/forgedb/store.py):

    store.is_hot(key) -> bool

* Reading a live key with get() or store[key] marks it hot.
* A key that was never read, was deleted, overwritten, or has expired is
  not hot.
* The cache must never raise for values that cannot be weakly referenced
  (int, str, list, ...). Think about WHAT you can hold a weak reference to.
* The cache must not keep anything alive: it holds no strong references.
"""

import weakref

import pytest

from forgedb.store import Entry, Store


class FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(clock: FakeClock) -> Store:
    return Store(clock)


def test_entry_supports_weakref():
    """Guards against __slots__ without __weakref__ (Checkpoint 6 trap)."""
    e = Entry(value=1, expires_at=None, created_at=1.0)
    assert weakref.ref(e)() is e


def test_unread_key_is_not_hot(store):
    store.set("a", 1)
    assert store.is_hot("a") is False


def test_missing_key_is_not_hot(store):
    assert store.is_hot("nope") is False


@pytest.mark.parametrize("value", [1, "text", [1, 2], {"k": "v"}, (1, 2), None])
def test_reading_marks_hot_for_any_value_type(store, value):
    store.set("a", value)
    assert store.get("a") == value
    assert store.is_hot("a") is True


def test_getitem_marks_hot(store):
    store["a"] = 1
    store["a"]
    assert store.is_hot("a") is True


def test_delete_makes_key_not_hot(store):
    store.set("a", 1)
    store.get("a")
    store.delete("a")
    assert store.is_hot("a") is False


def test_overwrite_is_not_hot_and_never_serves_stale_value(store):
    store.set("a", 1)
    store.get("a")
    store.set("a", 2)
    assert store.is_hot("a") is False
    assert store.get("a") == 2
    assert store.is_hot("a") is True


def test_expired_key_is_not_hot_even_before_it_is_touched(store, clock):
    store.set("a", 1, ttl=5)
    store.get("a")
    clock.now += 10
    assert store.is_hot("a") is False


def test_cache_does_not_change_store_contents(store):
    store.set("a", 1)
    store.get("a")
    assert len(store) == 1
    assert list(store) == ["a"]
