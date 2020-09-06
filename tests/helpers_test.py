from hagadias.helpers import parse_qud_colors, iter_qud_colors, \
    strip_oldstyle_qud_colors, strip_newstyle_qud_colors


def test_parse_qud_colors():
    assert parse_qud_colors('test') == [('test', None)]
    assert parse_qud_colors('{{y|raw beetle meat}}') == [('raw beetle meat', 'y')]
    assert parse_qud_colors('{{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}') ==\
        [('La', 'r'), (' ', None), ('Jeunesse', 'r-R-R-W-W-w-w sequence')]
    assert parse_qud_colors('{{K|{{crysteel|crysteel}} mace}}') ==\
        [('crysteel', 'crysteel'), (' mace', 'K')]
    assert parse_qud_colors('{{O|persistent {{G-W-o sequence|papaya}}}}') ==\
        [('persistent ', 'O'), ('papaya', 'G-W-o sequence')]


def test_iter_qud_colors(gameroot):
    colors = gameroot.get_colors()
    i = iter_qud_colors('test', colors)
    assert next(i) == ('t', None)
    i = iter_qud_colors('{{y|raw beetle meat}}', colors)
    assert next(i) == ('r', 'y')
    i = iter_qud_colors('{{cider|cider}}', colors)
    assert(list(i)) == [('c', 'r'), ('i', 'r'), ('d', 'r'), ('e', 'r'), ('r', 'r')]
    i = iter_qud_colors('{{g-g-G sequence|abcdef}}', colors)
    assert list(i) == [('a', 'g'), ('b', 'g'), ('c', 'G'), ('d', 'g'), ('e', 'g'), ('f', 'G')]
    i = iter_qud_colors('{{leafy|abcdef}}', colors)
    assert list(i) == [('a', 'g'), ('b', 'g'), ('c', 'G'), ('d', 'g'), ('e', 'g'), ('f', 'G')]
    i = iter_qud_colors('{{r-R alternation|abcd', colors)
    assert list(i) == [('a', 'r'), ('b', 'r'), ('c', 'R'), ('d', 'R')]
    i = iter_qud_colors('{{gaslight|gaslight}}', colors)
    assert list(i) == [('g', 'g'), ('a', 'g'), ('s', 'g'), ('l', 'w'), ('i', 'W'), ('g', 'w'),
                       ('h', 'g'), ('t', 'g')]
    i = iter_qud_colors('{{y-Y alternation|the', colors)
    assert list(i) == [('t', 'y'), ('h', 'y'), ('e', 'Y')]
    i = iter_qud_colors('{{y-W bordered|horned}}', colors)
    assert list(i) == [('h', 'W'), ('o', 'y'), ('r', 'y'), ('n', 'y'), ('e', 'y'), ('d', 'W')]
    i = iter_qud_colors('{{horned|horned}}', colors)
    assert list(i) == [('h', 'W'), ('o', 'y'), ('r', 'y'), ('n', 'y'), ('e', 'y'), ('d', 'W')]


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
