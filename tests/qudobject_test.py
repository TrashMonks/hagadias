"""pytest tests to test functions in qudobject.py.

The qindex fixture is supplied by tests/conftest.py."""

from hagadias.qudtile import QudTile


def test_tile(qindex):
    obj = qindex['Svenlainard']
    assert isinstance(obj.tile, QudTile)


def test_ui_inheritance_path(qindex):
    obj = qindex['Snapjaw Scavenger']
    want = 'Object➜PhysicalObject➜Creature➜Humanoid➜BaseHumanoid➜Snapjaw➜Snapjaw Scavenger'
    assert obj.ui_inheritance_path() == want


def test_inherits_from(qindex):
    obj = qindex['Stopsvaalinn']
    assert obj.inherits_from('BaseShield')
    assert obj.inherits_from('Item')
    assert obj.inherits_from('InorganicObject')
    assert obj.inherits_from('PhysicalObject')
    assert obj.inherits_from('Object')
    assert not obj.inherits_from('Widget')
    obj = qindex['Object']
    assert obj.inherits_from('Object')


def test_is_specified(qindex):
    obj = qindex['Stopsvaalinn']
    assert obj.is_specified('part_Commerce_Value')
    assert not obj.is_specified('fart_Commerce_Value')


def test_properties(qindex):
    obj = qindex['Asphodel']
    assert obj.lv == '30'
    assert obj.hp == '500'
    assert obj.av == 11  # natural 8 + clay pot
    # assert obj.dv == '12'  # base 6 plus (28 - 16) / 2
