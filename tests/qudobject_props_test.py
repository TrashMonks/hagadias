"""pytest tests to test qudobject_props.py.

The QudObjectProps class inherits from QudObject and provides most of the properties methods.

The qindex fixture is supplied by tests/conftest.py.
"""


def test_av(qindex: dict):
    """Check calculated AV."""
    assert qindex["Chain Mail"].av == 3
    assert qindex["Stopsvaalinn"].av == 3
    assert qindex["Basalt"].av == 10
    assert qindex["Asphodel"].av == 11  # natural 8 + clay pot


def test_lv(qindex: dict):
    """Check level."""
    assert qindex["Asphodel"].lv == "30"


def test_hp(qindex: dict):
    """Check hitpoints."""
    assert qindex["Asphodel"].hp == "500"


def test_chargeused(qindex: dict):
    """Check calculated charge cost."""
    obj = qindex["Geomagnetic Disc"]
    assert obj.chargeused == 400


def test_displayname(qindex: dict):
    """Check display names."""
    assert qindex["ElderBob"].displayname == "Elder Irudad"
    assert qindex["Cudgel6"].displayname == "crysteel mace"


def test_dv(qindex: dict):
    """Check calculated DV."""
    assert qindex["Chain Mail"].dv == -1
    assert qindex["Stopsvaalinn"].dv == 0
    assert qindex["Basalt"].dv == -10


def test_mentalshield(qindex: dict):
    """Check calculated mental armor value."""
    assert qindex["Sawhander"].ma == 10
    assert qindex["Lurking Beth"].ma is None


def test_extrainfo(qindex: dict):
    """Check that extrainfo is correctly provided."""
    assert qindex["Ctesiphus"].pettable is True
    assert qindex["Lurking Beth"].hidden == 18
    assert qindex["Prayer Rod"].energycellrequired is True


def test_tier(qindex: dict):
    """Check tier of a few objects."""
    assert qindex["Tattoo Gun"].tier == 3
    assert qindex["HandENuke"].tier == 8
    assert qindex["Glowfish"].tier == 0
