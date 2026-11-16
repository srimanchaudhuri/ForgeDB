"""Checkpoint 2 micro-benchmarks.

Run:  uv run python bench/bench_checkpoint2.py

Copy the numbers into PROGRESS.md under "Benchmarks & Measurements" and,
for each experiment, write ONE sentence explaining the result.
"""

import array
import sys
import tracemalloc
from collections import deque
from itertools import islice
from timeit import timeit

N = 50_000


def left_pushes_list(n: int) -> None:
    items: list[int] = []
    for i in range(n):
        items.insert(0, i)


def left_pushes_deque(n: int) -> None:
    items: deque[int] = deque()
    for i in range(n):
        items.appendleft(i)


def experiment_left_push() -> None:
    print(f"== left-push {N:,} items ==")
    for fn in (left_pushes_list, left_pushes_deque):
        secs = timeit(lambda fn=fn: fn(N), number=3) / 3
        print(f"  {fn.__name__:<20} {secs * 1000:9.2f} ms")


def measure(factory) -> int:
    """Peak bytes allocated while building the object (tracemalloc)."""
    tracemalloc.start()
    obj = factory()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    del obj
    return peak


def experiment_memory() -> None:
    count = 1_000_000
    print(f"== memory for {count:,} floats ==")
    as_list = measure(lambda: [float(i) for i in range(count)])
    as_array = measure(lambda: array.array("d", (float(i) for i in range(count))))
    print(f"  list[float]    {as_list / 1e6:8.1f} MB")
    print(f"  array('d')     {as_array / 1e6:8.1f} MB")
    print(f"  sys.getsizeof(float)={sys.getsizeof(1.0)} bytes, array item=8 bytes")


def experiment_lrange_window() -> None:
    size = 1_000_000
    d = deque(range(size))
    print(f"== deque window of 2 items out of {size:,} ==")
    cases = {
        "list(d)[0:2]": lambda: list(d)[0:2],
        "islice at start": lambda: list(islice(d, 0, 2)),
        "islice near end": lambda: list(islice(d, size - 100, size - 98)),
    }
    for name, fn in cases.items():
        secs = timeit(fn, number=20) / 20
        print(f"  {name:<18} {secs * 1e6:12.2f} us/call")


if __name__ == "__main__":
    experiment_left_push()
    experiment_memory()
    experiment_lrange_window()
