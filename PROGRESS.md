# ForgeDB Progress

## Current
- Checkpoint: 2 — Value Types: Lists & Time Series
- Status: not started (Ch 2 reading + summary first)
- Next step: summarize Ch 2 (slicing, deque vs list, array/memoryview), then tests get written before any implementation

## Completed
| # | Date | What I learned (2 lines) |
|---|------|--------------------------|
| 0 | 2026-11-15 | Special methods are called by the interpreter via the data model, not by you: `len()` is a function (fast C-struct path for built-ins, "practicality beats purity"). Missing `__iter__` falls back to `__getitem__(0..)` until `IndexError`, which also powers `in`. |
|   |            | `__bool__` then `__len__`; `__repr__` is the one to define first because `str()` falls back to it but not the reverse. Playlist kata passed (composition, no inheritance), uv/pytest/ruff/mypy set up. |
| 1 | 2026-11-15 | Frozen dataclass `Entry`: change means build a new one (`expire`), which makes sharing one `Entry` between keys safe (`copy`); `deepcopy` needs a new `Entry` for the new value. Injected clock keeps expiry testable; `_live()` is the single place that decides expiry. |
|   |            | Dict views are live, not snapshots (iterate `list(...)` when mutating). `int`/`str`/`list`/`dict` have no `__weakref__` slot, so the hot-key `WeakValueDictionary` caches the `Entry`, not the value; CPython drops dead entries by refcount. |

## Benchmarks & Measurements
(slots memory, deque vs list, thread vs process, etc.)

## Open Questions
- Playlist slicing returns a `list`, not a `Playlist`. Revisit in Ch 12 (slice-aware `__getitem__`).
- `Store.__repr__` is O(n) (copies all items) and truncates silently; polish in Checkpoint 16 (`itertools.islice`, show a count).
- Checkpoint 6: `@dataclass(slots=True)` removes `__weakref__`; `tests/test_hot_cache.py::test_entry_supports_weakref` guards this (use `weakref_slot=True`).
- Python 3.14 defers annotation evaluation; `requires-python` is `>=3.12`, so check annotations against 3.12 semantics.
