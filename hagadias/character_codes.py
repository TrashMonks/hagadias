"""Load Caves of Qud game data from gamefiles.
We're mostly interested in the two-character codes that map to specific implants and mutations.
"""
from pathlib import Path

from lxml import etree as et
from lxml.etree import _Element

no_comments_parser = et.XMLParser(remove_comments=True)  # don't read XML comments as elements
STAT_NAMES = ("Strength", "Agility", "Toughness", "Intelligence", "Willpower", "Ego")
# these are not available from XML:
MOD_BONUSES = {
    "Double-muscled": [2, 0, 0, 0, 0, 0],
    "Triple-jointed": [0, 2, 0, 0, 0, 0],
    "Two-hearted": [0, 0, 2, 0, 0, 0],
    "Beak": [0, 0, 0, 0, 0, 1],
}


def read_gamedata(xmlroot: Path) -> dict:
    """Read assorted character data from Qud XML files.

    :param xmlroot: the game data path of the CoQ executable, containing the XML files.
    """
    skills = et.parse(xmlroot / "Skills.xml", parser=no_comments_parser).getroot()  # noqa S320
    subtypes = et.parse(xmlroot / "Subtypes.xml", parser=no_comments_parser).getroot()  # noqa S320
    # Read skill internal names and user facing names
    # These are not returned, but used to parse the powers of subtypes, below.
    skill_names = {}
    for skill_cat in skills:
        skill_names[skill_cat.attrib["Class"]] = "(" + skill_cat.attrib["Name"] + ")"
        for power in skill_cat:
            skill_names[power.attrib["Class"]] = power.attrib["Name"]
    classes = [subtype for arcology in subtypes[0] for subtype in arcology]  # True Kin Castes
    classes.extend(subtype for subtype in subtypes[1])  # mutant Callings
    bonuses, skills, tiles = {}, {}, {}
    for _class in classes:
        name = _class.attrib["Name"]
        bonuses[name] = _get_bonuses(_class)
        skills[name] = _get_skills(_class, skill_names)
        tiles[name] = _class.attrib["Tile"], _class.attrib["DetailColor"]
    return {
        "class_bonuses": bonuses,
        "class_skills": skills,
        "class_tiles": tiles,
        "mod_bonuses": MOD_BONUSES,
    }


def _get_bonuses(subtype: _Element) -> list[int]:
    """Return the skill bonuses applicable to this subtype."""
    stat_bonuses = [0, 0, 0, 0, 0, 0]
    for element in subtype:
        if element.tag == "stat" and (element.attrib["Name"] in STAT_NAMES):
            bonus = int(element.attrib["Bonus"])
            stat_bonuses[STAT_NAMES.index(element.attrib["Name"])] = bonus
    return stat_bonuses


def _get_skills(subtype: _Element, skill_names: dict[str:str]) -> list[str]:
    """Return the skill names for this subtype, mapped from the internal names."""
    skills_raw = subtype.find("skills")
    skills = []
    for skill in skills_raw:
        skills.append(skill_names[skill.attrib["Name"]])
    return skills
