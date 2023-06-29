"""Tests for the QudTile class in qudtile.py.

The qindex fixture is supplied by tests/conftest.py.
"""
from hagadias import qudtile


def test_renders(qindex: dict):
    """Check a couple of items to ensure the png is not empty.

    Exercises the tile rendering code.

    Two textures from the main distribution are included in hagadias under
    Textures/ for this.
    """
    test_objects = ["Portable Beehive", "Holographic Ivory"]
    for name in test_objects:
        qud_object = qindex[name]
        assert len(qud_object.tile.get_bytes()) > 10


def test_tile(qindex: dict):
    """Ensure exceptions from missing files do not raise.

    This tile exists in the game but its texture file is not included with hagadias.
    """
    obj = qindex["Young Ivory"]
    assert isinstance(obj.tile, qudtile.QudTile)
    obj = qindex["Glowfish"]
    assert obj.tile.image is qudtile.blank_image
