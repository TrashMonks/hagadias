"""pytest tests to test qudobject_props.py.

The qindex fixture is supplied by tests/conftest.py."""

from hagadias.qudobject_props import strip_qud_color_codes


def test_strip_qud_color_codes():
    assert strip_qud_color_codes('&yfloating&G &Yglowsphere') == 'floating glowsphere'


# Properties
def test_av(qindex):
    pairs = {'Chain Mail': '3',
             'Stopsvaalinn': '3',
             'Basalt': '10',
             'Q Girl': '7',  # 4 from quills, 1 from polyhedral rings, 0 from powered exoskeleton,
                             # 1 from ulnar stimulator, 1 from plastifer sneakers
             'Warden Ualraig': '6',  # 2 from horn, 3 from chainmail, 1 from leather boots
             'IrritableTortoise': '4'}
    for obj, av in pairs.items():
        assert qindex[obj].av == av


def test_chargeused(qindex):
    obj = qindex['Geomagnetic Disc']
    assert obj.chargeused == '400'


def test_dv(qindex):
    pairs = {'Chain Mail': '-1',
             'Stopsvaalinn': '0',
             'Basalt': '-10',
             'Q Girl': '6',
             'Warden Ualraig': '8',
             'IrritableTortoise': '4'}
    for obj, dv in pairs.items():
        assert qindex[obj].dv == dv
