"""pytest tests to test functions in qudobject.py.

The qindex fixture is supplied by tests/conftest.py."""


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
    assert obj.av == '11'  # natural 8 + clay pot
    # assert obj.dv == '12'  # base 6 plus (28 - 16) / 2
