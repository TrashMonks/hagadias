from hagadias.qudobject_props import strip_qud_color_codes


def test_strip_qud_color_codes():
    assert strip_qud_color_codes('&yfloating&G &Yglowsphere') == 'floating glowsphere'


# Properties
def test_chargeused(qindex):
    obj = qindex['Geomagnetic Disc']
    assert obj.chargeused == '400'
