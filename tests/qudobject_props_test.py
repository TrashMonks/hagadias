"""pytest tests to test qudobject_props.py.

The qindex fixture is supplied by tests/conftest.py."""

from hagadias.qudobject_props import strip_qud_color_codes


def test_strip_qud_color_codes():
    assert strip_qud_color_codes('&yfloating&G &Yglowsphere') == 'floating glowsphere'


# Properties
def test_av(qindex):
    assert qindex['Chain Mail'].av == '3'
    assert qindex['Stopsvaalinn'].av == '3'
    assert qindex['Basalt'].av == '10'
    assert qindex['Q Girl'].av == '7'
    # 4 from quills, 1 from polyhedral rings, 0 from powered exoskeleton,
    # 1 from ulnar stimulator, 1 from plastifer sneakers
    assert qindex['Warden Ualraig'].av == '6'  # 2 from horn, 3 from chainmail, 1 from leather boots
    assert qindex['IrritableTortoise'].av == '4'


def test_chargeused(qindex):
    obj = qindex['Geomagnetic Disc']
    assert obj.chargeused == '400'


def test_dv(qindex):
    assert qindex['Chain Mail'].dv == '-1'
    assert qindex['Stopsvaalinn'].dv == '0'
    assert qindex['Basalt'].dv == '-10'
    assert qindex['Q Girl'].dv == '6'
    assert qindex['Warden Ualraig'].dv == '8'
    assert qindex['IrritableTortoise'].dv == '4'


def test_mentalshield(qindex):
    assert qindex['Sawhander'].ma is None
    assert qindex['Lurking Beth'].ma is None


def test_extrainfo(qindex):
    assert qindex['Ctesiphus'].pettable == 'yes'
    assert qindex['Lurking Beth'].hidden == '18'
    assert qindex['Prayer Rod'].energycellrequired == 'yes'


def test_tier(qindex):
    assert qindex['Tattoo Gun'].tier == '3'
    assert qindex['HandENuke'].tier == '8'
    assert qindex['Glowfish'].tier == '0'
