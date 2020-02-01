"""Helper functions for hagadias."""

import os
import re

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
