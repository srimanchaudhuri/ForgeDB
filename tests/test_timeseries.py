"""Checkpoint 2, part 2: TimeSeries on array.array('d').

Implement in src/forgedb/types/timeseries.py.

Contract
    TimeSeries()
    add(timestamp, value) -> None     timestamps must be strictly increasing;
                                      otherwise ValueError (keeps the
                                      timestamp array sorted, so bisect works)
    range(start, end) -> list[tuple[float, float]]
                                      (timestamp, value) pairs with
                                      start <= timestamp <= end   (BOTH ends
                                      inclusive, like Redis TS.RANGE)
    avg(start, end) -> float | None   mean of values in range, None if empty
    window(start, end) -> memoryview  read-only, zero-copy view of the values
                                      in range (format 'd')
    __len__

Storage: timestamps and values each live in an array.array('d').
Use bisect to find the range boundaries (no linear scans).
"""

import array
import statistics

import pytest
from hypothesis import given
from hypothesis import strategies as st

from forgedb.types.timeseries import TimeSeries


def make(points):
    ts = TimeSeries()
    for t, v in points:
        ts.add(t, v)
    return ts


POINTS = [(10, 1.0), (20, 2.0), (30, 3.0), (40, 4.0), (50, 5.0)]


# -------------------------------------------------------------------- add


def test_len():
    assert len(TimeSeries()) == 0
    assert len(make(POINTS)) == 5


def test_add_rejects_non_increasing_timestamps():
    ts = make(POINTS)
    with pytest.raises(ValueError):
        ts.add(50, 9.0)  # equal to last
    with pytest.raises(ValueError):
        ts.add(5, 9.0)  # older than last
    assert len(ts) == 5


# ------------------------------------------------------------------ range


def test_range_is_inclusive_on_both_ends():
    assert make(POINTS).range(20, 40) == [(20, 2.0), (30, 3.0), (40, 4.0)]


def test_range_between_samples():
    assert make(POINTS).range(15, 35) == [(20, 2.0), (30, 3.0)]


def test_range_outside_data_is_empty():
    ts = make(POINTS)
    assert ts.range(100, 200) == []
    assert ts.range(0, 5) == []


def test_range_wider_than_data_returns_everything():
    assert make(POINTS).range(-1000, 1000) == POINTS


def test_range_start_after_end_is_empty():
    assert make(POINTS).range(40, 20) == []


def test_range_on_empty_series():
    assert TimeSeries().range(0, 100) == []


# -------------------------------------------------------------------- avg


def test_avg():
    assert make(POINTS).avg(20, 40) == pytest.approx(3.0)


def test_avg_of_empty_range_is_none():
    assert make(POINTS).avg(100, 200) is None
    assert TimeSeries().avg(0, 1) is None


# ----------------------------------------------------------------- window


def test_window_is_a_readonly_memoryview_of_doubles():
    w = make(POINTS).window(20, 40)
    assert isinstance(w, memoryview)
    assert w.format == "d"
    assert w.readonly
    assert w.tolist() == [2.0, 3.0, 4.0]


def test_window_is_zero_copy():
    """The view must point at the series' own array, not at a copy."""
    w = make(POINTS).window(20, 40)
    assert isinstance(w.obj, array.array)
    assert len(w.obj) == 5  # the whole backing array, we only see a slice


def test_window_of_empty_range_is_empty():
    assert make(POINTS).window(100, 200).tolist() == []


def test_add_works_again_after_window_is_released():
    """While a memoryview of an array exists, the array cannot be resized.
    Find out what happens, then make sure releasing the view fixes it."""
    ts = make(POINTS)
    w = ts.window(20, 40)
    w.release()
    ts.add(60, 6.0)
    assert len(ts) == 6


# --------------------------------------------------- property-based tests

stamps = st.lists(st.integers(0, 1000), unique=True, max_size=40).map(sorted)
bounds = st.integers(-50, 1050)


@given(stamps=stamps, start=bounds, end=bounds)
def test_range_matches_linear_filter(stamps, start, end):
    points = [(t, float(t) * 1.5) for t in stamps]
    expected = [(t, v) for t, v in points if start <= t <= end]
    assert make(points).range(start, end) == expected


@given(stamps=stamps, start=bounds, end=bounds)
def test_avg_matches_statistics(stamps, start, end):
    points = [(t, float(t) * 1.5) for t in stamps]
    values = [v for t, v in points if start <= t <= end]
    result = make(points).avg(start, end)
    if values:
        assert result == pytest.approx(statistics.fmean(values))
    else:
        assert result is None


@given(stamps=stamps, start=bounds, end=bounds)
def test_window_matches_range_values(stamps, start, end):
    points = [(t, float(t) * 1.5) for t in stamps]
    ts = make(points)
    assert ts.window(start, end).tolist() == [v for _, v in ts.range(start, end)]
