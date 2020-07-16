from hagadias.helpers import parse_qud_colors, strip_oldstyle_qud_colors, strip_newstyle_qud_colors


def test_parse_qud_colors():
    assert parse_qud_colors('test') == [('test', None)]
    assert parse_qud_colors('{{y|raw beetle meat}}') == [('raw beetle meat', 'y')]
    assert parse_qud_colors('{{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}') ==\
        [('La', 'r'), (' ', None), ('Jeunesse', 'r-R-R-W-W-w-w sequence')]
    assert parse_qud_colors('{{K|{{crysteel|crysteel}} mace}}') ==\
        [('crysteel', 'crysteel'), (' mace', 'K')]
    assert parse_qud_colors('{{O|persistent {{G-W-o sequence|papaya}}}}') ==\
        [('persistent ', 'O'), ('papaya', 'G-W-o sequence')]


def test_strip_oldstyle_qud_colors():
    assert strip_oldstyle_qud_colors('&Otest &ytest') == 'test test'


def test_strip_newstyle_qud_colors():
    assert strip_newstyle_qud_colors('test') == 'test'
    assert strip_newstyle_qud_colors('{{y|raw beetle meat}}') == 'raw beetle meat'
    assert strip_newstyle_qud_colors('{{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}') ==\
        'La Jeunesse'
    assert strip_newstyle_qud_colors('{{K|{{crysteel|crysteel}} mace}}') ==\
        'crysteel mace'
    assert strip_newstyle_qud_colors('{{O|persistent {{G-W-o sequence|papaya}}}}') ==\
        'persistent papaya'
