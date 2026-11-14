"""Checkpoint 1 tests: Entry and Store.

API contract (implement in src/forgedb/store.py):

Entry(value, expires_at, created_at)
    frozen dataclass. expires_at is None or an absolute timestamp.
    __post_init__ rejects expires_at <= created_at with ValueError.

Store(clock)
    clock is a zero-arg callable returning the current time (float).
    set(key, value, ttl=None) -> None      ttl in seconds; ttl <= 0 -> ValueError
                                           set() without ttl clears any old ttl
    get(key, default=None)                 lazy expiry on access
    delete(key) -> bool                    True if a live key was removed
    exists(key) -> bool
    expire(key, seconds) -> bool           False if key missing/expired
    ttl(key) -> float | int                -2 missing/expired, -1 no expiry,
                                           else seconds remaining
    keys() -> list[str]                    live keys only
    copy(src, dst) -> bool                 shallow; False if src missing
    deepcopy(src, dst) -> bool             deep;    False if src missing
    Dunders: [] (KeyError on missing/expired), []=, del, in, len (live keys
    only), iter (live keys), bool, repr.
"""

import dataclasses

import pytest
from forgedb.store import Entry, Store


class FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(clock: FakeClock) -> Store:
    return Store(clock)


# ---------------------------------------------------------------- Entry


def test_entry_is_frozen_dataclass():
    e = Entry(value="v", expires_at=None, created_at=1.0)
    assert dataclasses.is_dataclass(e)
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.value = "other"  # type: ignore[misc]


def test_entry_rejects_expiry_not_after_creation():
    with pytest.raises(ValueError):
        Entry(value="v", expires_at=5.0, created_at=5.0)
    with pytest.raises(ValueError):
        Entry(value="v", expires_at=4.0, created_at=5.0)


def test_entry_allows_no_expiry_and_future_expiry():
    Entry(value="v", expires_at=None, created_at=5.0)
    Entry(value="v", expires_at=6.0, created_at=5.0)


# -------------------------------------------------------- basic commands


def test_set_get(store):
    store.set("a", 1)
    assert store.get("a") == 1


def test_get_missing_returns_default(store):
    assert store.get("nope") is None
    assert store.get("nope", "d") == "d"


def test_delete(store):
    store.set("a", 1)
    assert store.delete("a") is True
    assert store.delete("a") is False
    assert store.exists("a") is False


def test_exists_and_keys(store):
    store.set("a", 1)
    store.set("b", 2)
    assert store.exists("a")
    assert sorted(store.keys()) == ["a", "b"]


def test_set_overwrites(store):
    store.set("a", 1)
    store.set("a", 2)
    assert store.get("a") == 2
    assert len(store) == 1


# ------------------------------------------------------------- expiry


def test_key_expires_after_ttl(store, clock):
    store.set("a", 1, ttl=10)
    clock.advance(9.9)
    assert store.get("a") == 1
    clock.advance(0.2)
    assert store.get("a") is None
    assert not store.exists("a")


def test_expired_key_is_excluded_everywhere(store, clock):
    store.set("a", 1, ttl=5)
    store.set("b", 2)
    clock.advance(6)
    assert store.keys() == ["b"]
    assert len(store) == 1
    assert "a" not in store
    assert list(store) == ["b"]
    with pytest.raises(KeyError):
        store["a"]


def test_set_without_ttl_clears_old_ttl(store, clock):
    store.set("a", 1, ttl=5)
    store.set("a", 2)
    clock.advance(100)
    assert store.get("a") == 2


def test_invalid_ttl_rejected(store):
    with pytest.raises(ValueError):
        store.set("a", 1, ttl=0)
    with pytest.raises(ValueError):
        store.set("a", 1, ttl=-3)


def test_expire_existing_and_missing(store, clock):
    store.set("a", 1)
    assert store.expire("a", 10) is True
    assert store.expire("nope", 10) is False
    clock.advance(11)
    assert store.get("a") is None
    assert store.expire("a", 10) is False


def test_ttl_values(store, clock):
    assert store.ttl("nope") == -2
    store.set("a", 1)
    assert store.ttl("a") == -1
    store.expire("a", 10)
    clock.advance(4)
    assert store.ttl("a") == pytest.approx(6)
    clock.advance(10)
    assert store.ttl("a") == -2


# ------------------------------------------------------ copy semantics


def test_shallow_copy_shares_inner_objects(store):
    store.set("src", [1, [2]])
    assert store.copy("src", "dst") is True
    store["dst"][1].append(3)
    assert store["src"] == [1, [2, 3]]
    assert store["dst"][1] is store["src"][1]


def test_deepcopy_is_independent(store):
    store.set("src", [1, [2]])
    assert store.deepcopy("src", "dst") is True
    store["dst"][1].append(3)
    assert store["src"] == [1, [2]]
    assert store["dst"] == [1, [2, 3]]


def test_copy_missing_source(store):
    assert store.copy("nope", "dst") is False
    assert store.deepcopy("nope", "dst") is False
    assert "dst" not in store


# --------------------------------------------------- dunder protocol


def test_getitem_setitem_delitem(store):
    store["a"] = 1
    assert store["a"] == 1
    del store["a"]
    with pytest.raises(KeyError):
        store["a"]
    with pytest.raises(KeyError):
        del store["a"]


def test_contains_and_len(store):
    assert len(store) == 0
    store["a"] = 1
    assert "a" in store
    assert "b" not in store
    assert len(store) == 1


def test_bool(store):
    assert not store
    store["a"] = 1
    assert store


def test_iter(store):
    store["a"] = 1
    store["b"] = 2
    assert sorted(store) == ["a", "b"]


def test_repr(store):
    store["a"] = 1
    assert "Store" in repr(store)


def test_store_has_no_wall_clock_dependency(clock):
    """Time must come only from the injected clock."""
    s = Store(clock)
    s.set("a", 1, ttl=1)
    clock.advance(2)
    assert "a" not in s
