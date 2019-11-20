"""Helper functions for Qud Blueprint Explorer."""

import os

# load and store the Code Page 437 to Unicode translation
import pefile

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
