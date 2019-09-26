"""Tests for the GameRoot class."""

from hagadias.gameroot import GameRoot


def test_gameroot(gameroot):
    assert isinstance(gameroot, GameRoot)
