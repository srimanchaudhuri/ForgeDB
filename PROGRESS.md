# ForgeDB Progress

## Current
- Checkpoint: 1 — Core Store & Entries
- Status: not started (Ch 5 and Ch 6 reading + summary first)
- Next step: summarize Ch 5 (dataclasses) and Ch 6 (identity, copies, weakref) in 1-2 sentences each, then tests get written before any implementation

## Completed
| # | Date | What I learned (2 lines) |
|---|------|--------------------------|
| 0 | 2026-11-15 | Special methods are called by the interpreter via the data model, not by you: `len()` is a function (fast C-struct path for built-ins, "practicality beats purity"). Missing `__iter__` falls back to `__getitem__(0..)` until `IndexError`, which also powers `in`. |
|   |            | `__bool__` then `__len__`; `__repr__` is the one to define first because `str()` falls back to it but not the reverse. Playlist kata passed (composition, no inheritance), uv/pytest/ruff/mypy set up. |

## Benchmarks & Measurements
(slots memory, deque vs list, thread vs process, etc.)

## Open Questions
- Playlist slicing returns a `list`, not a `Playlist`. Revisit in Ch 12 (slice-aware `__getitem__`).
