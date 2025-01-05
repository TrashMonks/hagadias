"""pytest tests to test qudobject_props.py.

The qindex fixture is supplied by tests/conftest.py."""

from hagadias.helpers import strip_oldstyle_qud_colors


def test_strip_qud_color_codes():
    assert strip_oldstyle_qud_colors("&yfloating&G &Yglowsphere") == "floating glowsphere"


# Properties
def test_av(qindex):
    assert qindex["Chain Mail"].av == 3
    assert qindex["Stopsvaalinn"].av == 3
    assert qindex["Basalt"].av == 10


def test_chargeused(qindex):
    obj = qindex["Geomagnetic Disc"]
    assert obj.chargeused == 100


def test_displayname(qindex):
    assert qindex["ElderBob"].displayname == "Irudad"
    assert qindex["Cudgel6"].displayname == "crysteel mace"


def test_dv(qindex):
    assert qindex["Chain Mail"].dv == -1
    assert qindex["Stopsvaalinn"].dv == 0
    assert qindex["Basalt"].dv == -10


def test_mentalshield(qindex):
    assert qindex["Sawhander"].ma == 10
    assert qindex["Lurking Beth"].ma is None


def test_extrainfo(qindex):
    assert qindex["Ctesiphus"].pettable is True
    assert qindex["Lurking Beth"].hidden == 18
    assert qindex["Prayer Rod"].energycellrequired is True


def test_tier(qindex):
    assert qindex["Tattoo Gun"].tier == 3
    assert qindex["HandENuke"].tier == 8
    assert qindex["Glowfish"].tier == 0
