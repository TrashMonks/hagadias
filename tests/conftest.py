"""Fixtures for pytest."""
import logging
from pathlib import Path

import pytest

from hagadias.gameroot import GameRoot
from hagadias.qudobject import QudObject

log = logging.getLogger(__name__)

try:
    with open("game_location_for_tests") as f:
        game_loc = f.read().strip()
        GAME_ROOT_LOC = Path(game_loc)
except FileNotFoundError:
    log.error('Tests require a game installation path to be in the file "game_location_for_tests".')
    raise

_root = GameRoot(game_loc)
_qud_object_root, _qindex = _root.get_object_tree()


@pytest.fixture(scope="session")
def gameroot() -> GameRoot:
    """Return the gameroot object"""
    return _root


@pytest.fixture(scope="session")
def character_codes() -> dict:
    """Return the character codes"""
    return _root.get_character_codes()


@pytest.fixture(scope="session")
def qud_object_root() -> QudObject:
    """Return the root QudObject"""
    return _qud_object_root


@pytest.fixture(scope="session")
def qindex() -> dict:
    """Return the dictionary mapping object IDs to QudObjects"""
    return _qindex
