"""Tests for the GameRoot class in gameroot.py.

The 'gameroot' pytest fixture is supplied by tests/conftest.py."""

from hagadias.gameroot import GameRoot


def test_gameroot(gameroot):
    assert isinstance(gameroot, GameRoot)


def test_get_character_codes(gameroot):
    """Test retrieving the character code map.

    This may already have been loaded into cache by a pytest fixture."""
    gamecodes = gameroot.get_character_codes()
    assert "Horticulturist" in gamecodes["class_bonuses"]
    assert "Horticulturist" in gamecodes["class_skills"]
    assert "Horticulturist" in gamecodes["class_tiles"]


def test_get_object_tree(gameroot):
    """Test retrieving the root of the object tree and the name->object map index.

    This may already have been loaded into cache by a pytest fixture."""
    qud_object_root, qindex = gameroot.get_object_tree()
    assert len(qindex) > 1000


def test_get_anatomies(gameroot):
    anatomies = gameroot.get_anatomies()
    assert "Humanoid" in anatomies
    assert len(anatomies) > 50


def test_get_colors(gameroot):
    colors = gameroot.get_colors()
    assert "solidcolors" in colors
    assert "shaders" in colors
    assert colors["shaders"]["snakeskin"]["colors"] == "g-c-C-G"


def test_get_genders(gameroot):
    genders = gameroot.get_genders()
    assert "plural" in genders
    assert len(genders) >= 3  # the biden parameter
    assert genders["neuter"]["Subjective"] == "it"
    assert genders["elverson"]["FormalAddressTerm"] == "friend"


def test_gamever(gameroot):
    """Retrieve the game version.

    Game versions are strings like '2.0.194.1'."""
    ver = gameroot.gamever
    assert isinstance(ver, str)
    assert len(ver) > 4
    assert ver[0].isdigit()
    assert "." in ver
