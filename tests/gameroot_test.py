"""Tests for the GameRoot class.

The gameroot fixture is supplied by tests/conftest.py."""

from hagadias.gameroot import GameRoot


def test_gameroot(gameroot):
    assert isinstance(gameroot, GameRoot)


def test_gamever(gameroot):
    # game versions are strings like '2.0.194.1'
    ver = gameroot.gamever
    assert isinstance(ver, str)
    assert len(ver) > 4
    assert ver[0] in '01234567890'
    assert '.' in ver


def test_colors(gameroot):
    colors = gameroot.get_colors()
    assert(colors['shaders']['snakeskin']['colors'] == 'g-c-C-G')


def test_genders(gameroot):
    genders = gameroot.get_genders()
    assert(genders['neuter']['Subjective'] == 'it')
    assert(genders['elverson']['FormalAddressTerm'] == 'friend')
