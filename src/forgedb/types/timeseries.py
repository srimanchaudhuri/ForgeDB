import array
import itertools
from bisect import bisect_left, bisect_right


class TimeSeries:
    def __init__(self):
        self._timestamps = array.array("d")
        self._values = array.array("d")

    def add(self, timestamp, value):
        if self._timestamps and timestamp <= self._timestamps[-1]:
            raise ValueError("Timestamps must be strictly increasing.")
        self._timestamps.append(timestamp)
        self._values.append(value)

    def range(self, start, end) -> list[tuple[float, float]]:
        left, right = self._bounds(start, end)
        return [
            (t, v)
            for t, v in zip(
                itertools.islice(self._timestamps, left, right),
                self.window(start, end),
            )
        ]

    def avg(self, start, end) -> float | None:
        values = self.window(start, end)
        if not values:
            return None
        return sum(values) / len(values)

    def window(self, start, end) -> memoryview:
        """Release the window before adding"""
        m_values = memoryview(self._values)
        left, right = self._bounds(start, end)
        return m_values[left:right].toreadonly()

    def _bounds(self, start, end):
        left = bisect_left(self._timestamps, start)
        right = bisect_right(self._timestamps, end)
        return left, right

    def __len__(self):
        return len(self._timestamps)
