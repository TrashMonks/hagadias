"""Functionality for loading the Qud game data from various game files."""

import sys
import time
from pathlib import Path
# Force Python XML parser:
sys.modules['_elementtree'] = None
from xml.etree import ElementTree as ET  # noqa E402

from hagadias.character_codes import read_gamedata  # noqa E402
from hagadias.helpers import get_dll_version_string, repair_invalid_linebreaks, \
    repair_invalid_chars  # noqa E402
from hagadias.qudobject_props import QudObjectProps  # noqa E402


class LineNumberingParser(ET.XMLParser):
    """An alternate parser for ElementTree that captures information about the source from the
    underlying expat parser."""

    def _start(self, *args, **kwargs):
        # Here we assume the default XML parser which is expat
        # and copy its element position attributes into output Elements
        element = super(self.__class__, self)._start(*args, **kwargs)
        element._start_line_number = self.parser.CurrentLineNumber
        element._start_column_number = self.parser.CurrentColumnNumber
        element._start_byte_index = self.parser.CurrentByteIndex
        return element

    def _end(self, *args, **kwargs):
        element = super(self.__class__, self)._end(*args, **kwargs)
        element._end_line_number = self.parser.CurrentLineNumber
        element._end_column_number = self.parser.CurrentColumnNumber
        element._end_byte_index = self.parser.CurrentByteIndex
        return element


class GameRoot:
    """Gather together the various data sources provided in a Caves of Qud game root.

    The game root should be the root folder containing the Caves of Qud executable. On Steam this
    should be something like
        Steam/steamapps/common/Caves of Qud/
    which on Linux might be located in ~/.local/share/ ,
    or on Mac OS might be located in ~/Library/Application Support/ .

    This class doesn't load all data when instantiated, instead loading components on demand since
    some of the tasks are compute-heavy (loading the Qud object tree from ObjectBlueprints.xml for
    example).
    """

    def __init__(self, root: str):
        """Load the various assets under the given game root and export them as attributes."""
        root_path = Path(root)
        if not Path.exists(root_path / 'CoQ_Data'):
            raise FileNotFoundError(f'The given game root {root} does not seem to be a Caves of Qud'
                                    ' game directory.')
        self._root = root_path
        self._xmlroot = root_path / 'CoQ_Data' / 'StreamingAssets' / 'Base'
        self.pathstr = str(root_path)
        assembly_path = root_path / 'CoQ_Data' / 'Managed' / 'Assembly-CSharp.dll'
        try:
            self.gamever = get_dll_version_string(str(assembly_path), "FileVersion")
        except NameError:
            # FIXME: temporary workaround for inability to use windll on Linux
            self.gamever = 'unknown'

        # set up cache for multiple calls, so we don't have to parse XML every time
        self.character_codes = None
        self.qud_object_root = None
        self.qindex = None
        self.anatomies = None

    def get_character_codes(self) -> dict:
        """Load and return a dictionary containing all the Qud character code pieces.

        Also includes associated data like callings and castes with stat bonuses that are required
        to calculate complete build codes."""
        if self.character_codes is None:
            self.character_codes = read_gamedata(self._xmlroot)
        return self.character_codes

    def get_object_tree(self, cls=QudObjectProps):
        """Create a tree of the Caves of Qud hierarchy of objects from ObjectBlueprints.xml and
        return a tuple containing:
         - the root object ('Object'),
         - a dictionary mapping the string name of each Qud object to the Python object
           representing it.

        Parameters:
            cls: the QudObject class, or optionally, a subclass of QudObject to represent the game
            objects. Implemented to allow a tree of QudObjectWiki for the Qud Blueprint Explorer
            app.
        """
        if self.qud_object_root is not None:
            return self.qud_object_root, self.qindex
        path = self._xmlroot / 'ObjectBlueprints.xml'
        with path.open('r', encoding='utf-8') as f:
            contents = f.read()
        # Do some repair of invalid XML specifically for ObjectBlueprints.xml:
        # First, replace some invalid control characters intended for CP437 with their Unicode equiv
        start = time.time()
        print("Repairing invalid XML characters... ", end='')
        contents = repair_invalid_chars(contents)
        print(f"done in {time.time() - start:.2f} seconds")
        # Second, replace line breaks inside attributes with proper XML line breaks
        start = time.time()
        print("Repairing invalid XML line breaks... ", end='')
        contents = repair_invalid_linebreaks(contents)
        print(f"done in {time.time() - start:.2f} seconds")
        contents_b = contents.encode('utf-8')  # start/stop markers are in bytes, not characters
        raw = ET.fromstring(contents, parser=LineNumberingParser())
        print("Building Qud object hierarchy and adding tiles...")
        # Build the Qud object hierarchy from the XML data
        last_stop = 0
        # Objects must receive the qindex and add themselves, rather than doing it here, because
        # they need access to their parent by name lookup during creation for inheritance
        # calculations.
        qindex = {}  # fast lookup of name->QudObject

        # first pass - load xml data into dictionary structure
        for element in raw:
            # parsing 'ends' at the close tag, so add 9 bytes to include '</object>'
            start, stop = element._start_byte_index, element._end_byte_index + 9
            source = contents_b[start:stop].decode('utf-8')
            # capture comments, etc. before start tag for later saving
            full_source = contents_b[last_stop:stop].decode('utf-8')
            last_stop = stop
            if element.tag != 'object':
                continue
            obj = cls(element, source, full_source, qindex)
        tail = contents_b[last_stop:].decode('utf-8')
        obj.source = source + tail  # add tail of file to the XML source of last object loaded

        # second pass - resolve object inheritance
        for object_id, qud_object in qindex.items():
            qud_object.resolve_inheritance()

        qud_object_root = qindex['Object']
        self.qud_object_root = qud_object_root
        self.qindex = qindex
        return qud_object_root, qindex

    def get_anatomies(self) -> dict:
        """Return the available body plans.

        Returns a dictionary containing all available creature anatomies.
        Each anatomy is given as a list of tuples of body parts.
        The tuples are the body part name and what they are a variant of (if applicable), like
        ("Support Strut", "Arm"). If the body part name is not a variant, it will be given like
        ("Arm", "Arm").
        """
        if self.anatomies is not None:
            return self.anatomies
        path = self._xmlroot / 'Bodies.xml'
        tree = ET.parse(path)
        # Walk the body part type variants first, to map out the part synonyms
        variants = {}
        tag_variants = tree.find('bodyparttypevariants')
        for tag_variant in tag_variants:
            variants[tag_variant.attrib['Type']] = tag_variant.attrib['VariantOf']
        # Now walk the anatomies and collect their parts
        anatomies = {}
        tag_anatomies = tree.find('anatomies')
        for tag_anatomy in tag_anatomies:
            parts = []
            name = tag_anatomy.attrib['Name']
            # .// XPath syntax means select all <part> tags under this element, even if nested
            found_tag_part = tag_anatomy.findall('.//part')
            for tag_part in found_tag_part:
                part = tag_part.attrib['Type']
                if 'Laterality' in tag_part.attrib:
                    part_full = f"{tag_part.attrib['Laterality']} {part}"
                else:
                    part_full = part
                variant_of = variants[part] if part in variants else part
                parts.append({'name': part_full, 'type': variant_of})
            anatomies[name] = parts
        self.anatomies = anatomies
        return anatomies

    def get_colors(self) -> dict:
        """Return the color codes and shaders.

        Returns a nested dictionary mirroring the XML file structure.
        Format:
            {"solidcolors": {"black":"K"},
             ...
             "shaders": {"arctic camouflage": {"type": "sequence",
                                               "colors": "y-y-Y-y-K-y-y-Y-Y-K"}
            }
        """
        colors = {'solidcolors': {}, 'shaders': {}}
        path = self._xmlroot / 'Colors.xml'
        tree = ET.parse(path)
        for solidcolor in tree.find('solidcolors'):
            name = solidcolor.attrib['Name']
            colors['solidcolors'][name] = solidcolor.attrib['Color']
        for shader in tree.find('shaders'):
            name = shader.attrib['Name']
            colors['shaders'][name] = {'type': shader.attrib['Type'],
                                       'colors': shader.attrib['Colors']}
        return colors
