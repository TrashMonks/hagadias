"""pytest file to test functions in svalue.py."""

from hagadias.svalue import sValue


def test_creation():
    """Test making an instance of sValue."""
    _ = sValue("16,1d3,(t-1)d2")
    assert _.__repr__() == "sValue 16,1d3,(t-1)d2"


def test_simple():
    """Test the case where the svalue is an integer."""
    _ = sValue("16")
    assert _.low == 16
    assert _.high == 16


def test_range():
    """Test adding together dice rolls of different types."""
    _ = sValue("16,1d3,(t-1)d2")
    assert _.low == 17
    assert _.high == 19
    _ = sValue("16,1d3,(t-1)d2", level=5)
    assert _.low == 18
    assert _.high == 21


def test_modifier():
    """Test adding scalars to die rolls."""
    _ = sValue("1+1")
    assert _.low == 2
    assert _.high == 2
    _ = sValue("1d4+4,(t+1),3+2")
    assert _.low == 12
    assert _.high == 15


def test_iteration():
    """Test cases where more than one die is given."""
    _ = sValue("1d5,1d5")
    assert _.low == 2
    assert _.high == 10
    assert min(_) == 2
    assert max(_) == 10
    _ = sValue("5")
    assert len(_) == 1
    _ = sValue("(t)d100")
    assert min(_) == 1
    assert max(_) == 100
    assert len(_) == 100
