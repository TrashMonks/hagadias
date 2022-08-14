"""Functionality for loading the Qud game data from various game files."""
import logging
import time
from pathlib import Path

from lxml import etree as et

from hagadias.character_codes import read_gamedata
from hagadias.helpers import get_dll_version_string, repair_invalid_linebreaks, repair_invalid_chars
from hagadias.qudobject_props import QudObjectProps
from hagadias.qudpopulation import QudPopulation

log = logging.getLogger(__name__)


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
        if not Path.exists(root_path / "CoQ_Data"):
            raise FileNotFoundError(
                f"The given game root {root} does not seem to be a Caves of Qud" " game directory."
            )
        self._root = root_path
        self._xmlroot = root_path / "CoQ_Data" / "StreamingAssets" / "Base"
        self.pathstr = str(root_path)
        assembly_path = root_path / "CoQ_Data" / "Managed" / "Assembly-CSharp.dll"
        try:
            self.gamever = get_dll_version_string(str(assembly_path), "FileVersion")
        except NameError:
            # FIXME: temporary workaround for inability to use windll on Linux
            self.gamever = "unknown"

        # set up cache for multiple calls, so we don't have to parse XML every time
        self.character_codes = None
        self.qud_object_root = None
        self.qindex = None
        self.anatomies = None
        self.populations = None

    def get_character_codes(self) -> dict:
        """Load and return a dictionary containing all the Qud character code pieces.

        Also includes associated data like callings and castes with stat bonuses that are required
        to calculate complete build codes."""
        if self.character_codes is None:
            self.character_codes = read_gamedata(self._xmlroot)
        return self.character_codes

    def get_object_tree(self, cls=QudObjectProps):
        """Create a tree of the Caves of Qud hierarchy of objects from XML files in the
        ObjectBlueprints directory and
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
        path = self._xmlroot / "ObjectBlueprints"
        qindex = {}  # fast lookup of name->QudObject
        for blueprint_file in path.glob("*.xml"):
            log.info("Loading %s object blueprints:", blueprint_file.stem)
            with blueprint_file.open("r", encoding="utf-8") as f:
                contents = f.read()

            # Do some repair of invalid XML specifically for ObjectBlueprints files: First,
            # replace some invalid control characters intended for CP437 with their Unicode equiv
            start = time.time()
            log.debug("Repairing invalid XML characters... ")
            contents = repair_invalid_chars(contents)
            log.debug("done in %.2f seconds", time.time() - start)
            # Second, replace line breaks inside attributes with proper XML line breaks
            start = time.time()
            log.debug("Repairing invalid XML line breaks... ")
            contents = repair_invalid_linebreaks(contents)
            log.debug("done in %.2f seconds", time.time() - start)
            raw = et.fromstring(contents)
            # Objects must receive the qindex and add themselves, rather than doing it here, because
            # they need access to their parent by name lookup during creation for inheritance
            # calculations.

            # first pass - load xml data into dictionary structure
            for element in raw:
                if element.tag != "object":
                    continue
                cls(element, qindex, self)

        # second pass - resolve object inheritance
        log.debug("Resolving Qud object hierarchy and adding tiles...")
        for object_id, qud_object in qindex.items():
            qud_object.resolve_inheritance()

        qud_object_root = qindex["Object"]
        self.qud_object_root = qud_object_root
        self.qindex = qindex
        return qud_object_root, qindex

    def get_populations(self) -> dict[str, QudPopulation]:
        """Returns populations.

        Returns a nested dictionary mirroring the XML file structure."""
        if self.populations is not None:
            return self.populations
        path = self._xmlroot / "PopulationTables.xml"
        populations: dict[str, QudPopulation] = {}
        pop_tree = et.parse(path)
        for pop_entry in pop_tree.findall("population"):
            if pop_entry.tag != "population":
                pass  # shouldn't happen
            population = QudPopulation(pop_entry)
            if population is None:
                log.error("FIXME: unable to load a population entry")
            elif population.name is None or len(population.name) == 0:
                log.error("FIXME: tried to load a population that has no Name attribute?")
            elif population.name in populations and pop_entry.attrib.get("Load") == "Merge":
                log.error("FIXME: unsupported merge request for population %s", population.name)
            else:
                populations[population.name] = population
        self.populations = populations
        return populations

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
        path = self._xmlroot / "Bodies.xml"
        tree = et.parse(path)
        # Walk the body part type variants first, to map out the part synonyms
        variants = {}
        tag_variants = tree.find("bodyparttypevariants")
        for tag_variant in tag_variants:
            variants[tag_variant.attrib["Type"]] = tag_variant.attrib["VariantOf"]
        # Now walk the anatomies and collect their parts
        anatomies = {}
        tag_anatomies = tree.find("anatomies")
        for tag_anatomy in tag_anatomies:
            parts = []
            name = tag_anatomy.attrib["Name"]
            # .// XPath syntax means select all <part> tags under this element, even if nested
            found_tag_part = tag_anatomy.findall(".//part")
            for tag_part in found_tag_part:
                part = tag_part.attrib["Type"]
                if "Laterality" in tag_part.attrib:
                    part_full = f"{tag_part.attrib['Laterality']} {part}"
                else:
                    part_full = part
                variant_of = variants[part] if part in variants else part
                parts.append({"name": part_full, "type": variant_of})
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
        colors = {"solidcolors": {}, "shaders": {}}
        path = self._xmlroot / "Colors.xml"
        tree = et.parse(path)
        for solidcolor in tree.find("solidcolors"):
            name = solidcolor.attrib["Name"]
            colors["solidcolors"][name] = solidcolor.attrib["Color"]
        for shader in tree.find("shaders"):
            name = shader.attrib["Name"]
            colors["shaders"][name] = {
                "type": shader.attrib["Type"],
                "colors": shader.attrib["Colors"],
            }
        return colors

    def get_genders(self) -> dict:
        """Return the genders.

        Returns a nested dictionary mirroring the XML file structure."""
        genders = {}
        path = self._xmlroot / "Genders.xml"
        tree = et.parse(path)
        for gender in tree.findall("gender"):
            genders[gender.attrib["Name"]] = {}
            for attrib, val in gender.attrib.items():
                if attrib != "Name":
                    genders[gender.attrib["Name"]][attrib] = val
        return genders

    def get_pronouns(self) -> dict:
        """Returns pronouns.

        Returns a nested dictionary mirroring the XML file structure."""
        pronouns = {}
        path = self._xmlroot / "PronounSets.xml"
        tree = et.parse(path)
        for pronounset in tree.findall("pronounset"):
            pronounsetname = "/".join(
                [
                    pronounset.attrib["Subjective"],
                    pronounset.attrib["Objective"],
                    pronounset.attrib["PossessiveAdjective"],
                ]
            )
            pronouns[pronounsetname] = {}
            for attrib, val in pronounset.attrib.items():
                pronouns[pronounsetname][attrib] = val
        # add Oboroqoru's pronouns since they're defined in objectblueprints
        pronouns["He/Him/His/His/Himself/god/godling/lord/Son/Brother/Father"] = {
            "Subjective": "He",
            "Objective": "Him",
            "PossessiveAdjective": "His",
            "SubstantivePossessive": "His",
            "Reflexive": "Himself",
            "PersonTerm": "god",
            "ImmaturePersonTerm": "godling",
            "FormalAddressTerm": "lord",
            "OffspringTerm": "Son",
            "SiblingTerm": "Brother",
            "ParentTerm": "Father",
        }
        return pronouns
