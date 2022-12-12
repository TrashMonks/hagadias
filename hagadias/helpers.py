"""Helper functions for hagadias."""

import itertools
import random
import re
from math import gcd
from pathlib import Path
from typing import Iterator, List, Tuple, Optional

import pefile

from hagadias.constants import QUD_COLORS

PALETTE = list(QUD_COLORS)
PALETTE.remove("transparent")
PALETTE.remove("o")  # extradimensional color
PALETTE.remove("O")  # extradimensional color

# load and store the Code Page 437 to Unicode translation
ASSETS = Path(__file__).parent / "assets"
cp437_conv = {}
with open(ASSETS / "IBMGRAPH.TXT") as f:
    for line in f.readlines():
        if not line.startswith("#"):
            unicode, cp437, *_ = line.split()
            cp437_conv[int(cp437, base=16)] = chr(int(unicode, base=16))


def cp437_to_unicode(val: int):
    """Convert an IBM Code Page 437 code point to its Unicode equivalent.

    See https://stackoverflow.com/questions/46942721/is-cp437-decoding-broken-for-control-characters
    """
    if val > 0x1F:
        # no control characters, just ascii and "upper ascii"
        hex_val = hex(val)[2:]
        if len(hex_val) == 1:
            hex_val = "0" + hex_val
        byte = bytes.fromhex(hex_val)
        glyph = byte.decode(encoding="cp437")
    else:
        # control character - must be loaded from table
        glyph = cp437_conv[val]
    return glyph


# From https://stackoverflow.com/questions/580924/python-windows-file-version-attribute:
def get_dll_version_string(path, throwaway):
    """Return the version information from a PE file (exe or dll)."""
    pe = pefile.PE(path)
    if hasattr(pe, "VS_VERSIONINFO"):
        for idx in range(len(pe.VS_VERSIONINFO)):
            if hasattr(pe, "FileInfo") and len(pe.FileInfo) > idx:
                for entry in pe.FileInfo[idx]:
                    if hasattr(entry, "StringTable"):
                        for st_entry in entry.StringTable:
                            for str_entry in sorted(list(st_entry.entries.items())):
                                key = str_entry[0].decode("utf-8", "backslashreplace")
                                val = str_entry[1].decode("utf-8", "backslashreplace")
                                if key == "ProductVersion":
                                    return val
    raise ValueError


def int_or_default(value, default=0) -> int:
    """Return the result of int(value), or else a default if value is None or is not an int."""
    if value is None:
        return default
    try:
        value = int(value)
    except ValueError:
        return default
    return value


def int_or_none(value) -> int | None:
    """Return the result of int(value), or else None if value is None or is not an int."""
    if value is not None:
        try:
            value = int(value)
        except ValueError:
            return None
        return value


def float_or_default(value, default=0.0) -> float:
    """Return the result of float(value), or else a default if value is None or is not a float."""
    if value is None:
        return default
    try:
        value = float(value)
    except ValueError:
        return default
    return value


def float_or_none(value) -> float | None:
    """Return the result of float(value), or else None if value is None or is not a float."""
    if value is not None:
        try:
            value = float(value)
        except ValueError:
            return None
        return value


def str_or_default(value, default) -> str:
    """Return the result of str(value), or else a default if value is None or an empty string."""
    if value is None:
        return default
    value = str(value)
    return value if value else default


def bool_or_default(value, default=False) -> bool:
    """Returns value if value is a bool.
    Returns true if value is a string equal to 'yes' or 'true' (case insensitive).
    Returns false if value is a string equal to 'no' or 'false' (case insensitive).
    Otherwise, returns the default."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.lower().strip()
        if value == "yes" or value == "true":
            return True
        if value == "no" or value == "false":
            return False
    return default


def repair_invalid_linebreaks(contents):
    """Return a version of an XML file with invalid line breaks replaced with XML line breaks.

    Used to stitch together lines in ObjectBlueprints.xml.
    """
    pat_linebreaks = r"^\s*<[^!][^>]*\n.*?>"
    match = re.search(pat_linebreaks, contents, re.MULTILINE)
    while match:
        before = match.string[: match.start()]
        fixed = match.string[match.start() : match.end()].replace("\n", "&#10;")
        after = match.string[match.end() :]
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
    contents = re.sub(ch_re, "♂", contents)
    ch_re = re.compile("&#15;")
    contents = re.sub(ch_re, "☼", contents)
    ch_re = re.compile("&#27;")
    contents = re.sub(ch_re, "←", contents)
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
    new_shader_name = ""
    coloredchars = []  # tuples of character, current shader
    for char in phrase:
        if state == READING_TEXT:
            if char == "{":
                state = ONE_LEFT_BRACE
            elif char == "}":
                state = ONE_RIGHT_BRACE
            else:
                coloredchars.append((char, shader_stack[-1]))
        elif state == ONE_LEFT_BRACE:
            if char == "{":
                state = READING_SHADER
            else:
                state = READING_TEXT
                coloredchars.append(("{", shader_stack[-1]))  # include the { that we didn't write
                coloredchars.append((char, shader_stack[-1]))
        elif state == READING_SHADER:
            if char == "|":
                state = READING_TEXT
                shader_stack.append(new_shader_name)
                new_shader_name = ""
            else:
                new_shader_name += char
        elif state == ONE_RIGHT_BRACE:
            state = READING_TEXT
            if char == "}":
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
    current_fragment = ""
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


def iter_qud_colors(phrase: str, colors) -> Iterator[Tuple]:
    """Builds on parse_qud_colors to return one character with its color code at a time,
    instead of a longer string with its color code. This also interprets shader
    color codes properly.

    Where parse_qud_colors('{{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}') would return
    [("la", "r"), (" ", None), ("Jeunesse", "r-R-R-W-W-w-w sequence"],
    iter_qud_colors('{{r|La}} {{r-R-R-W-W-w-w sequence|Jeunesse}}') returns instead
    [('l', 'r'), ('a', 'r'), (' ', None), ('J', 'r'), ('e', 'R'), ('u', 'R'), ('n', 'W') ...]

    :param phrase:
    :param colors: a colors dictionary from a game install obtained by calling GameRoot.get_colors()
    """
    for text, code in parse_qud_colors(phrase):
        if code is None:
            # no shader
            for char in text:
                yield char, None
        elif code in QUD_COLORS:
            # the basic built-in color codes like 'y'
            for char in text:
                yield char, code
        elif code in colors["solidcolors"]:
            # the short name color codes that map to the basic color codes
            for char in text:
                yield char, colors["solidcolors"][code]
        elif code in colors["shaders"] and colors["shaders"][code]["type"] == "solid":
            # solid shaders
            for char in text:
                yield char, colors["shaders"][code]["colors"]
        # predefined complex shaders
        elif (
            code.endswith(" sequence")
            or code in colors["shaders"]
            and colors["shaders"][code]["type"] == "sequence"
        ):
            # sequence: one color at a time from the list, starting at the beginning when done
            if code.endswith(" sequence"):
                sequence = code[:-9].split("-")
            else:
                sequence = colors["shaders"][code]["colors"].split("-")
            for char, color in zip(text, itertools.cycle(sequence)):
                yield char, color
        elif (
            code.endswith(" alternation")
            or code in colors["shaders"]
            and colors["shaders"][code]["type"] == "alternation"
        ):
            # alternate: If the phrase is longer than the list of colors, stretch the colors across
            # the length of the phrase. If the phrase is shorter, render the same as sequence type.
            if code.endswith(" alternation"):
                alternation = code[:-12].split("-")
            else:
                alternation = colors["shaders"][code]["colors"].split("-")
            for index, char in enumerate(text):
                yield char, alternation[int(index / len(text) * len(alternation))]
        elif (
            code.endswith(" bordered")
            or code in colors["shaders"]
            and colors["shaders"][code]["type"] == "bordered"
        ):
            # bordered: first code is for the main text, second code is for the first and last
            # characters
            if code.endswith(" bordered"):
                bordered = code[:-9].split("-")
            else:
                bordered = colors["shaders"][code]["colors"].split("-")
            for index, char in enumerate(text):
                if index == 0 or index == len(text) - 1:
                    yield char, bordered[1]
                else:
                    yield char, bordered[0]
        elif (
            code.endswith(" distribution")
            or code in colors["shaders"]
            and colors["shaders"][code]["type"] == "distribution"
        ):
            # distribution: the color list specifies colors to be sampled from
            if code.endswith(" distribution"):
                distribution = code[:-13].split("-")
            else:
                distribution = colors["shaders"][code]["colors"].split("-")
            for char in text:
                yield char, random.choice(distribution)
        elif code == "chaotic":
            # each character is different
            for char in text:
                yield char, random.choice(PALETTE)
        elif code == "random":
            # random solid color
            color = random.choice(PALETTE)
            for char in text:
                yield char, color


def strip_newstyle_qud_colors(phrase: str) -> str:
    """Strip the new-style Qud color templates from a string, returning the plain text only.

    Example:
        "{{y|raw beetle meat}}"
    becomes
        "raw beetle meat"
    """
    parsed = parse_qud_colors(phrase)
    return "".join(text for text, shader in parsed)


def strip_oldstyle_qud_colors(text: str) -> str:
    """Remove the old-style Qud color codes from a string, returning the plain text only.

    Example:
        "&Yraw beetle meat"
    becomes
        "raw beetle meat"
    """
    return re.sub("&[rRwWcCbBgGmMyYkKoO]", "", text)


def extract_color(colorstr: str, prefix_symbol: str) -> str | None:
    """Generic function to extract a color codes and its prefixing symbol."""
    c = None
    if colorstr is not None and prefix_symbol in colorstr:
        val = colorstr.split(prefix_symbol)[1]
        if len(val) >= 1 and (val[0] in QUD_COLORS):
            c = f"{prefix_symbol}{val[0]}"
    return c


def extract_background_color(colorstr: str, default: Optional[str] = None) -> str | None:
    """Extracts background (^) color from a colorstring, including both caret and color char."""
    bg = extract_color(colorstr, "^")
    return default if bg is None else bg


def extract_background_char(colorstr: str, default: Optional[str] = None) -> str | None:
    """Extracts background (^) color from a colorstring, returning only the color char."""
    bg = extract_background_color(colorstr)
    return default if bg is None else bg[1]


def extract_foreground_color(colorstr: str, default: Optional[str] = None) -> str | None:
    """Extracts foreground (&) color from a colorstring, including both ampersand and color char."""
    fg = extract_color(colorstr, "&")
    return default if fg is None else fg


def extract_foreground_char(colorstr: str, default: Optional[str] = None) -> str | None:
    """Extracts foreground (&) color from a colorstring, returning only the color char."""
    fg = extract_foreground_color(colorstr, f"&{default}")
    return None if fg is None else fg[1]


def pos_or_neg(num: int) -> str:
    """Returns a + or - symbol depending on the positivity or negativity of the provided integer."""
    if int(num) >= 0:
        return "+"
    return "-"


def lowest_common_multiple(a, b) -> int:
    """Returns the lowest common multiple (LCM) of two integers."""
    return abs(a * b) // gcd(a, b)


def parse_comma_equals_str_into_dict(values: str, output: dict):
    """Consumes a string in the format '1=baa,2=boo,3=bop' and inserts key/value pairs into the
    provided dictionary."""
    if values is not None and len(values) > 0:
        for entry in values.split(","):
            info = entry.split("=")
            val = int_or_none(info[0])
            if val is not None and len(info) == 2:
                output[val] = info[1]


def make_list_from_words(wds: List[str]) -> str:
    """Converts a python list into a grammatical string list."""
    if wds is None or len(wds) == 0:
        return ""
    if len(wds) == 1:
        return wds[0]
    if len(wds) == 2:
        return f"{wds[0]} and {wds[1]}"
    else:
        last_wd = wds.pop()
        return f'{", ".join(wds)}, and {last_wd}'


def obj_has_any_part(qudobject, parts: List[str]) -> bool:
    """Returns True if the QudObject has any of the specified parts"""
    if parts is not None and len(parts) > 0:
        for part in parts:
            if getattr(qudobject, f"part_{part}", None) is not None:
                return True
    return False
