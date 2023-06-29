"""Pytest file for classes in dicebag.py."""

import pytest

from hagadias.dicebag import DiceBag


def test_input_filtering():
    """Test range checks on user input."""
    with pytest.raises(ValueError, match="5001 is too many dice to roll"):
        DiceBag("-5001d1")  # too many dice
    with pytest.raises(ValueError, match="5001 is too many dice to roll"):
        DiceBag("5001d1")  # too many dice
    with pytest.raises(ValueError, match="0.0 is too low for the number of sides on a die"):
        DiceBag("3d0")
    with pytest.raises(ValueError, match="1001.0 is too high for the number of sides on a die"):
        DiceBag("1d1001")


def test_roll_average():
    """Tests for the roll_average function."""
    assert DiceBag("3d2-1").average() == 3.5
    assert DiceBag("7+1d3+3d2-1+1").average() == 13.5
    assert DiceBag("3d2+3d2").average() == 9.0
