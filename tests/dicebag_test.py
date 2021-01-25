"""Pytest file for functions in helpers.py"""

from hagadias.dicebag import DiceBag
from pytest import raises


def test_DiceBag():
    with raises(ValueError):
        DiceBag('-1001d1')  # too many dice
        DiceBag('1001d1')   # too many dice
        DiceBag('3d0')      # die too small
        DiceBag('1d1001')   # die too large


def test_roll_average():
    """Tests for the roll_average function."""
    assert DiceBag('3d2-1').average() == 3.5
    assert DiceBag('7+1d3+3d2-1+1').average() == 13.5
    assert DiceBag('3d2+3d2').average() == 9.0
