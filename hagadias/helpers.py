"""Helper functions for hagadias."""

import os
import re
from typing import List, Tuple, Union

import pefile


# load and store the Code Page 437 to Unicode translation
CP437_MAP_FILE = os.path.join(os.path.dirname(__file__), 'IBMGRAPH.TXT')
cp437_conv = {}
with open(CP437_MAP_FILE) as f:
    for line in f.readlines():
        if not line.startswith('#'):
            unicode, cp437, *_ = line.split()
            cp437_conv[int(cp437, base=16)] = chr(int(unicode, base=16))


def cp437_to_unicode(val: int):
    """Convert an IBM Code Page 437 code point to its Unicode equivalent.

    See https://stackoverflow.com/questions/46942721/is-cp437-decoding-broken-for-control-characters
    """
    if val > 0x1f:
        # no control characters, just ascii and "upper ascii"
        hex_val = hex(val)[2:]
        if len(hex_val) == 1:
            hex_val = '0' + hex_val
        byte = bytes.fromhex(hex_val)
        glyph = byte.decode(encoding='cp437')
    else:
        # control character - must be loaded from table
        glyph = cp437_conv[val]
    return glyph


# From https://stackoverflow.com/questions/580924/python-windows-file-version-attribute:
def get_dll_version_string(path, throwaway):
    """Return the version information from a PE file (exe or dll)."""
    pe = pefile.PE(path)
    if hasattr(pe, 'VS_VERSIONINFO'):
        for idx in range(len(pe.VS_VERSIONINFO)):
            if hasattr(pe, 'FileInfo') and len(pe.FileInfo) > idx:
                for entry in pe.FileInfo[idx]:
                    if hasattr(entry, 'StringTable'):
                        for st_entry in entry.StringTable:
                            for str_entry in sorted(list(st_entry.entries.items())):
                                key = str_entry[0].decode('utf-8', 'backslashreplace')
                                val = str_entry[1].decode('utf-8', 'backslashreplace')
                                if key == 'ProductVersion':
                                    return val
    raise ValueError


def int_or_none(value) -> Union[int, None]:
    """Return the result of int(value), or None if value is None."""
    if value is not None:
        return int(value)


def repair_invalid_linebreaks(contents):
    """Return a version of an XML file with invalid line breaks replaced with XML line breaks.

    Used to stitch together lines in ObjectBlueprints.xml.
    """
    pat_linebreaks = r"^\s*<[^!][^>]*\n.*?>"
    match = re.search(pat_linebreaks, contents, re.MULTILINE)
    while match:
        before = match.string[:match.start()]
        fixed = match.string[match.start():match.end()].replace('\n', '&#10;')
        after = match.string[match.end():]
        contents = before + fixed + after
        match = re.search(pat_linebreaks, contents, re.MULTILINE)
    return contents


def repair_invalid_chars(contents):
    """Return a version of an XML file with certain invalid control characters substituted.

    Used for various characters in ObjectBlueprints.xml. The invalid codes are decimal references
    into IBM Code Page 437
    https://en.wikipedia.org/wiki/Code_page_437#/media/File:Codepage-437.png
    so we can substitute them with their Unicode equivalents.
    """
    ch_re = re.compile("&#11;")
    contents = re.sub(ch_re, '♂', contents)
    ch_re = re.compile("&#15;")
    contents = re.sub(ch_re, '☼', contents)
    ch_re = re.compile("&#27;")
    contents = re.sub(ch_re, '←', contents)
    return contents


def parse_qud_colors(phrase: str) -> List[Tuple]:
    """Convert display names from the new color templating format to a list
    of tuples.

    The tuples are like ('text', 'shader') where 'text' is the raw text to be
    colored, and 'shader' is the name of the coloring that should be applied to
    that segment of the text.

    For example, this function will take the input text
        {{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}
    and return
        [("la", "r"), (" ", None), ("Jeunesse", "r-R-R-W-W-w-w sequence"]

    As another example,
        {{K|{{crysteel|crysteel}} mace}}
    becomes
        [('crysteel', 'crysteel'), (' mace', 'K')]

    More examples of display names in game format:
    Game displayname: {{c-C-Y-W alternation|maghammer}}
    Game displayname: {{R-r-K-y-Y sequence|Stopsvalinn}}
    Game displayname: {{y|raw beetle meat}}
    Game displayname: {{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}
    """
    # Parser states:
    READING_TEXT = 1
    ONE_LEFT_BRACE = 2
    READING_SHADER = 3
    ONE_RIGHT_BRACE = 4
    state = READING_TEXT
    shader_stack = [None]  # default white
    new_shader_name = ''
    coloredchars = []  # tuples of character, current shader
    for char in phrase:
        if state == READING_TEXT:
            if char == '{':
                state = ONE_LEFT_BRACE
            elif char == '}':
                state = ONE_RIGHT_BRACE
            else:
                coloredchars.append((char, shader_stack[-1]))
        elif state == ONE_LEFT_BRACE:
            if char == '{':
                state = READING_SHADER
            else:
                state = READING_TEXT
                coloredchars.append(('{', shader_stack[-1]))  # include the { that we didn't write
                coloredchars.append((char, shader_stack[-1]))
        elif state == READING_SHADER:
            if char == '|':
                state = READING_TEXT
                shader_stack.append(new_shader_name)
                new_shader_name = ''
            else:
                new_shader_name += char
        elif state == ONE_RIGHT_BRACE:
            state = READING_TEXT
            if char == '}':
                if len(shader_stack) == 1:
                    error = f"Unexpected }} occurred while parsing {phrase}"
                    raise ValueError(error)
                else:
                    shader_stack.pop()
            else:
                coloredchars.append((char, shader_stack[-1]))
    # we've parsed all printable chars:
    # now, conflate sequential chars with the same shader
    output = []
    current_shader = None
    current_fragment = ''
    for character, shader in coloredchars:
        if shader == current_shader:
            current_fragment += character
        else:
            if len(current_fragment) > 0:
                output.append((current_fragment, current_shader))
            current_fragment = character
            current_shader = shader
    if len(current_fragment) > 0:
        output.append((current_fragment, current_shader))
    return output


def strip_newstyle_qud_colors(phrase: str) -> str:
    """Strip the new-style Qud color templates from a string, returning the plain text only.

    Example:
        "{{y|raw beetle meat}}"
    becomes
        "raw beetle meat"
    """
    parsed = parse_qud_colors(phrase)
    return ''.join(text for text, shader in parsed)


def strip_oldstyle_qud_colors(text: str) -> str:
    """Remove the old-style Qud color codes from a string, returning the plain text only.

    Example:
        "&Yraw beetle meat"
    becomes
        "raw beetle meat"
    """
    return re.sub('&[rRwWcCbBgGmMyYkKoO]', '', text)

def pos_or_neg(num: int) -> str:
    if int(num) >= 0:
        return '+'
    return "-"
