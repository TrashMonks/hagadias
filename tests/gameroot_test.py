"""Tests for the GameRoot class.

The gameroot fixture is supplied by tests/conftest.py."""

from hagadias.gameroot import GameRoot


def test_gameroot(gameroot):
    assert isinstance(gameroot, GameRoot)
