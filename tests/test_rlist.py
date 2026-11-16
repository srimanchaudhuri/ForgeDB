"""Checkpoint 2, part 1: RList (Redis-style list on collections.deque).

Implement in src/forgedb/types/rlist.py  (create src/forgedb/types/__init__.py too).

Contract
    RList(values=())                      initial items, left to right
    lpush(*values) -> int                 pushes one at a time to the left, so
                                          lpush(1, 2, 3) leaves [3, 2, 1].
                                          Returns the new length.
    rpush(*values) -> int                 appends on the right, returns length
    lpop() -> object | None               None when empty
    rpop() -> object | None
    llen() -> int
    lrange(start, stop) -> list           Redis semantics: stop is INCLUSIVE,
                                          negative indexes count from the end
                                          (-1 is the last item), out-of-range
                                          indexes are clamped, never an error.
    ltrim(start, stop) -> None            keep only lrange(start, stop)
    Dunders: __len__, __iter__ (left to right), __repr__

Redis LRANGE reminders (n = number of items):
    LRANGE k 0 -1   -> everything
    LRANGE k 0 2    -> three items (indexes 0, 1, 2)
    start > stop    -> []
    start >= n      -> []
"""

from forgedb.types.rlist import RList
from hypothesis import given
from hypothesis import strategies as st


def reference_lrange(items: list[int], start: int, stop: int) -> list[int]:
    """Independent, deliberately boring model of Redis LRANGE."""
    n = len(items)
    if start < 0:
        start = max(n + start, 0)
    if stop < 0:
        stop = n + stop
    if start > stop or start >= n:
        return []
    stop = min(stop, n - 1)
    return items[start : stop + 1]


# ------------------------------------------------------------- push / pop


def test_rpush_and_rpop():
    r = RList()
    assert r.rpush(1, 2, 3) == 3
    assert r.rpop() == 3
    assert r.llen() == 2


def test_lpush_pushes_one_at_a_time():
    r = RList()
    assert r.lpush(1, 2, 3) == 3
    assert list(r) == [3, 2, 1]


def test_lpop_and_rpop_order():
    r = RList([1, 2, 3, 4])
    assert r.lpop() == 1
    assert r.rpop() == 4
    assert list(r) == [2, 3]


def test_pop_from_empty_returns_none():
    r = RList()
    assert r.lpop() is None
    assert r.rpop() is None
    assert r.llen() == 0


def test_dunders():
    r = RList([1, 2])
    assert len(r) == 2
    assert list(r) == [1, 2]
    assert "RList" in repr(r)


# ----------------------------------------------------------------- lrange


def test_lrange_whole_list():
    assert RList([1, 2, 3, 4, 5]).lrange(0, -1) == [1, 2, 3, 4, 5]


def test_lrange_stop_is_inclusive():
    assert RList([1, 2, 3, 4, 5]).lrange(0, 2) == [1, 2, 3]
    assert RList([1, 2, 3, 4, 5]).lrange(1, 1) == [2]


def test_lrange_negative_indexes():
    r = RList([1, 2, 3, 4, 5])
    assert r.lrange(-3, -1) == [3, 4, 5]
    assert r.lrange(0, -2) == [1, 2, 3, 4]
    assert r.lrange(-2, -2) == [4]


def test_lrange_out_of_range_is_clamped():
    r = RList([1, 2, 3])
    assert r.lrange(0, 100) == [1, 2, 3]
    assert r.lrange(-100, 1) == [1, 2]
    assert r.lrange(5, 10) == []
    assert r.lrange(-100, -50) == []


def test_lrange_start_after_stop_is_empty():
    assert RList([1, 2, 3]).lrange(2, 1) == []


def test_lrange_on_empty_list():
    assert RList().lrange(0, -1) == []


def test_lrange_does_not_mutate():
    r = RList([1, 2, 3])
    r.lrange(0, 1)
    assert list(r) == [1, 2, 3]


# ------------------------------------------------------------------ ltrim


def test_ltrim_keeps_range():
    r = RList([1, 2, 3, 4, 5])
    r.ltrim(1, -2)
    assert list(r) == [2, 3, 4]


def test_ltrim_with_empty_range_empties_list():
    r = RList([1, 2, 3])
    r.ltrim(2, 1)
    assert list(r) == []
    assert r.llen() == 0


def test_ltrim_out_of_range_is_clamped():
    r = RList([1, 2, 3])
    r.ltrim(0, 100)
    assert list(r) == [1, 2, 3]


# --------------------------------------------------- property-based tests

ints = st.lists(st.integers(), max_size=30)
indexes = st.integers(min_value=-40, max_value=40)


@given(items=ints, start=indexes, stop=indexes)
def test_lrange_matches_reference(items, start, stop):
    assert RList(items).lrange(start, stop) == reference_lrange(items, start, stop)


@given(items=ints, start=indexes, stop=indexes)
def test_ltrim_matches_reference(items, start, stop):
    r = RList(items)
    r.ltrim(start, stop)
    assert list(r) == reference_lrange(items, start, stop)


@given(
    items=ints,
    ops=st.lists(st.sampled_from(["lpop", "rpop", "lpush", "rpush"]), max_size=30),
)
def test_push_pop_matches_list_model(items, ops):
    r = RList(items)
    model = list(items)
    for i, op in enumerate(ops):
        if op == "lpush":
            r.lpush(i)
            model.insert(0, i)
        elif op == "rpush":
            r.rpush(i)
            model.append(i)
        elif op == "lpop":
            assert r.lpop() == (model.pop(0) if model else None)
        else:
            assert r.rpop() == (model.pop() if model else None)
    assert list(r) == model
    assert r.llen() == len(model)
