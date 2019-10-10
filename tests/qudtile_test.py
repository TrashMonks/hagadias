"""Tests for the QudTile class.

The qindex fixture is supplied by tests/conftest.py."""

import os
from pathlib import Path


def test_renders(qindex):
    test_pairs = {'Portable Beehive': 'portable_beehive.png',
                  'Holographic Ivory': 'holographic_ivory.png',
                  }
    test_tile_path = Path(os.getcwd()) / 'tests' / 'test_tiles'
    for name, file in test_pairs.items():
        qud_object = qindex[name]
        with open(test_tile_path / file, 'rb') as f:
            assert qud_object.tile.get_bytes() == f.read()
