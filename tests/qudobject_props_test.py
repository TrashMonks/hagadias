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
    assert obj.chargeused == 400


def test_displayname(qindex):
    testcases = {
        "Tam": "Tam, dromad merchant",
        "High Priest Eschelstadt": "Eschelstadt II, High Priest of the Stilt",
        "Lulihart": "Lulihart, hindren pariah",
        "Tszappur": "Tszappur, disciple of the Coiled Lamb",
        "Oboroqoru": "Oboroqoru, Ape God",
        "Skybear": "Saad Amus, the Sky-Bear",
        "Phinae Hoshaiah": "Phinae Hoshaiah, High Priest of the Rock",
        "Asphodel": "Asphodel, Earl of Omonporch",
        "Hamilcrab": "Hamilcrab, cyclopean merchant",
        "AoygNoLonger": "Aoyg-No-Longer, servant of Ptoh in the Cosmic Wood",
        "Troll King 1": "Jotun, Who Parts Limbs",
        "Troll King 2": "Fjorn-Kosef, Who Knits The Icy Lattice",
        "Troll King 3": "Haggabah, Who Plies The Umbral Path",
        "ElderBob": "Elder Irudad",
        "Warden Esthers": "Wardens Esther",
        "Barathrum": "Barathrum the Old",
        "Neelahind": "Warden Neelahind",
        "Mayor Nuntu": "Mayor Nuntu",
        "Warden Indrix": "Warden Indrix, Goatfolk Pariah",
        "GolgothaSlog": "Slog of the Cloaca",
        "Haddas": "Mayor Haddas",
        "Warden 1-FF": "Warden 1-FF, reprogrammed conservator",
        "Zothom": "Zothom the Penitent",
        "Rainwater Shomer": "Rainwater Shomer",
        "Une": "Warden Une",
        "Agolgot": "Girsh Agolgot",
        "Bethsaida": "Girsh Bethsaida",
        "Rermadon": "Girsh Rermadon",
        "Qas": "Girsh Qas",
        "Qon": "Girsh Qon",
        "Shugruith": "Girsh Shug'ruith the Burrower",
        "Erah": "Ciderer Erah",
        "Warden Yrame": "Warden Yrame",
        "Ehalcodon": "Starformed Ehalcodon",
    }

    for id, expected in testcases.items():
        assert qindex[id].displayname == expected

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
