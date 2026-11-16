import itertools
from collections import deque


class RList:
    def __init__(self, values=()) -> None:
        self._queue = deque(values)

    def lpush(self, *values) -> int:
        for value in values:
            self._queue.appendleft(value)
        return len(self._queue)

    def rpush(self, *values) -> int:
        for value in values:
            self._queue.append(value)
        return len(self._queue)

    def lpop(self):
        if self._queue:
            return self._queue.popleft()
        return None

    def rpop(self):
        if self._queue:
            return self._queue.pop()
        return None

    def llen(self) -> int:
        return len(self._queue)

    def lrange(self, start: int, stop: int) -> list:
        start, stop = self._bounds(start, stop)
        if start > stop:
            return []
        return list(itertools.islice(self._queue, start, stop + 1))

    def ltrim(self, start: int, stop: int) -> None:
        start, stop = self._bounds(start, stop)
        if start > stop:
            self._queue.clear()
        else:
            self._queue = deque(itertools.islice(self._queue, start, stop + 1))

    def _bounds(self, start: int, stop: int) -> tuple[int, int]:
        """returns (start, stop), stop inclusive, Redis-style"""

        if start < 0:
            start += len(self._queue)
        if stop < 0:
            stop += len(self._queue)
        return max(0, start), min(len(self._queue), stop)

    def __len__(self) -> int:
        return len(self._queue)

    def __iter__(self):
        return iter(self._queue)

    def __repr__(self) -> str:
        return f"RList({list(self._queue)})"
