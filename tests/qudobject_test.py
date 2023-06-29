"""pytest tests to test functions in qudobject.py.

The qindex fixture is supplied by tests/conftest.py.
"""


def test_ui_inheritance_path(qindex: dict):
    """Check the inheritance path string provided for UI tools."""
    obj = qindex["Snapjaw Scavenger"]
    want = "Object➜PhysicalObject➜Creature➜Humanoid➜BaseHumanoid➜Snapjaw➜Snapjaw Scavenger"
    assert obj.ui_inheritance_path() == want


def test_inherits_from(qindex: dict):
    """Check that blueprint inheritance is properly calculated."""
    obj = qindex["Stopsvaalinn"]
    assert obj.inherits_from("BaseShield")
    assert obj.inherits_from("Item")
    assert obj.inherits_from("InorganicObject")
    assert obj.inherits_from("PhysicalObject")
    assert obj.inherits_from("Object")
    assert not obj.inherits_from("Widget")
    obj = qindex["Object"]
    assert obj.inherits_from("Object")


def test_is_specified(qindex: dict):
    """Test the is_specified method for whether parts are explicitly given (not inherited)."""
    obj = qindex["Stopsvaalinn"]
    assert obj.is_specified("part_Commerce_Value")
    assert not obj.is_specified("fart_Commerce_Value")
