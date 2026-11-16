# ForgeDB Progress

## Current
- Checkpoint: 3 — Hashes, Sets, Config & Stats
- Status: not started (Ch 3 reading + summary first)
- Next step: summarize Ch 3 (dict/set mechanics, ChainMap, Counter, UserDict, MappingProxyType), then tests get written before any implementation

## Completed
| # | Date | What I learned (2 lines) |
|---|------|--------------------------|
| 0 | 2026-11-15 | Special methods are called by the interpreter via the data model, not by you: `len()` is a function (fast C-struct path for built-ins, "practicality beats purity"). Missing `__iter__` falls back to `__getitem__(0..)` until `IndexError`, which also powers `in`. |
|   |            | `__bool__` then `__len__`; `__repr__` is the one to define first because `str()` falls back to it but not the reverse. Playlist kata passed (composition, no inheritance), uv/pytest/ruff/mypy set up. |
| 1 | 2026-11-15 | Frozen dataclass `Entry`: change means build a new one (`expire`), which makes sharing one `Entry` between keys safe (`copy`); `deepcopy` needs a new `Entry` for the new value. Injected clock keeps expiry testable; `_live()` is the single place that decides expiry. |
|   |            | Dict views are live, not snapshots (iterate `list(...)` when mutating). `int`/`str`/`list`/`dict` have no `__weakref__` slot, so the hot-key `WeakValueDictionary` caches the `Entry`, not the value; CPython drops dead entries by refcount. |
| 2 | 2026-11-17 | Redis `LRANGE` is end-inclusive with `-1` = last; Python slices are end-exclusive. `slice.indices` clamps and fits Python semantics, not Redis's, so a small hand-written `_bounds` helper was the right tool. `deque` trades slicing and O(1) middle indexing for O(1) at both ends. |
|   |            | `array('d')` + `bisect` give 16 bytes/point and O(log n) range lookup; `memoryview` gives zero-copy windows but pins the array (`BufferError` on resize). Property tests catch the unexpected, hand examples pin the Redis special cases. `[[]] * 3` shares one inner list. |

## Benchmarks & Measurements
(slots memory, deque vs list, thread vs process, etc.)

### Checkpoint 2 (`bench/bench_checkpoint2.py`, run 2026-11-17)
| Experiment | Result | Why |
|---|---|---|
| Left-push 50,000 items | `list.insert(0, x)` 347 ms vs `deque.appendleft` 1.9 ms (~180x) | `insert(0)` shifts every existing element one slot, O(n) per push, O(n^2) total; `deque` adds at either end without moving anything |
| Memory, 1M floats | `list[float]` 32.4 MB vs `array('d')` 8.2 MB (~4x) | list = 8-byte pointer + separate 24-byte float object = 32 B/item; array stores raw 8-byte doubles |
| 2-item window, deque of 1M | full copy 12.5 ms; `islice` at start 0.7 us; `islice` near end 6.0 ms | `islice` doesn't copy but must step past every skipped item, so cost follows the window's start position; deque has no slicing or O(1) middle indexing |
| `memoryview` over `array` | `array.append` raises `BufferError` while a view exists | exported buffer pins the array's size; `TimeSeries.window` documents "release before adding" |

## Open Questions
- Playlist slicing returns a `list`, not a `Playlist`. Revisit in Ch 12 (slice-aware `__getitem__`).
- `Store.__repr__` is O(n) (copies all items) and truncates silently; polish in Checkpoint 16 (`itertools.islice`, show a count).
- Checkpoint 6: `@dataclass(slots=True)` removes `__weakref__`; `tests/test_hot_cache.py::test_entry_supports_weakref` guards this (use `weakref_slot=True`).
- Python 3.14 defers annotation evaluation; `requires-python` is `>=3.12`, so check annotations against 3.12 semantics.
