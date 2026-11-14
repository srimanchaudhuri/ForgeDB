"""Checkpoint 0 kata: a Playlist that behaves like a sequence
using only the data model. Implement it in scratch/playlist.py.
"""

import random

import pytest
from playlist import Playlist

SONGS = ["Intro", "Verse", "Chorus", "Bridge", "Outro"]


@pytest.fixture
def pl() -> Playlist:
    return Playlist(SONGS)


def test_len(pl):
    assert len(pl) == 5


def test_index(pl):
    assert pl[0] == "Intro"
    assert pl[-1] == "Outro"


def test_index_out_of_range(pl):
    with pytest.raises(IndexError):
        pl[5]


def test_slice(pl):
    assert list(pl[1:3]) == ["Verse", "Chorus"]
    assert list(pl[::-1]) == SONGS[::-1]


def test_contains(pl):
    assert "Chorus" in pl
    assert "Nope" not in pl


def test_iteration(pl):
    assert list(pl) == SONGS
    assert next(s.upper() for s in pl) == "INTRO"


def test_reversed(pl):
    assert list(reversed(pl)) == SONGS[::-1]


def test_random_choice(pl):
    assert random.choice(pl) in SONGS


def test_bool():
    assert bool(Playlist(["a"])) is True
    assert bool(Playlist([])) is False


def test_repr_is_informative(pl):
    assert "Playlist" in repr(pl)
    assert "Intro" in repr(pl)


def test_does_not_inherit_from_anything():
    assert Playlist.__mro__ == (Playlist, object)


def test_does_not_alias_input():
    songs = ["a", "b"]
    p = Playlist(songs)
    songs.append("c")
    assert len(p) == 2
