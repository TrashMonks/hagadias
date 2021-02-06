"""Tests for the QudTile class.

The qindex fixture is supplied by tests/conftest.py."""


def test_renders(qindex):
    test_objects = ['Portable Beehive', 'Holographic Ivory']
    for name in test_objects:
        qud_object = qindex[name]
        assert len(qud_object.tile.get_bytes()) > 10
