# hagadias

Python package to extract game data from the [Caves of Qud](http://www.cavesofqud.com/) roguelike.

This library forms the base for several projects:

- the Caves of Qud wiki bot that builds and updates the [Caves of Qud wiki](https://wiki.cavesofqud.com/)
- the Discord bot that operates on the [Caves of Qud discord server](https://discordapp.com/invite/cavesofqud) (invite
  link)

## What does it do?

hagadias allows a user to read game data in the raw format used by the
[Caves of Qud](http://www.cavesofqud.com/) roguelike RPG, including the object tree, fully colored tiles, and character
data. It needs to be passed a path to a local installation of the game in order to do anything.

## Installation

hagadias requires Python 3.10.

To install the package from this GitHub repository without a package manager, run  
`pip install git+https://github.com/trashmonks/hagadias@main#egg=hagadias`  
If you're using pipenv to manage dependencies,  
`pipenv install -e git+https://github.com/trashmonks/hagadias.git@main#egg=hagadias`
If you're using Poetry to manage dependencies,
`poetry add git+https://github.com/trashmonks/hagadias#main`

## Tile support

Tile support requires the texture files from Caves of Qud to be unpacked into a "Textures" directory under the working
directory of your project that is importing hagadias. You can use the
[Brinedump](https://github.com/TrashMonks/brinedump)
game mod to export these textures from within the game.

## Example usage
### Startup
```python
import hagadias
from pprint import pprint
GAMEPATH = 'C:\\Steam\\steamapps\\common\\Caves of Qud'  # Windows
# GAMEPATH = '~/.local/share/Steam/steamapps/common/Caves of Qud'  # Linux
# GAMEPATH = '~/Library/Application Support/Steam/steamapps/common/Caves of Qud'  # macOS
root = hagadias.gameroot.GameRoot(GAMEPATH)
print(root.gamever)  # output version of the game
```
```
2.0.203.56
```

### Objects (Blueprints)
```
qud_object_root, qindex = root.get_object_tree()

# The above gives you two items:
# - a `qud_object_root` object of type `QudObjectProps` that is the root of the CoQ object hierarchy, allowing you to traverse the entire object tree and retrieve information about the items, characters, tiles, etc.
# - a `qindex` which is a dictionary that simply maps the Name (ingame object ID or wish ID) of each ingame object, as a string, to the Python object representing it.

# Example use of qud_object_root:
>>> qud_object_root.source
'<object Name="Object">\n    <part Name="Physics" Conductivity="0" IsReal="true" Solid="false" Weight="0"></part>\n  </object>'

# But what you really want is the qindex:
>>> snapjaw = qindex['Snapjaw']
>>> snapjaw.desc
'Tussocks of fur dress skin stretched over taut muscle. Upright =pronouns.subjective= =verb:stand:afterpronoun=, but =pronouns.subjective= =verb:look:afterpronoun= ready to drop onto fours. =pronouns.Possessive= snout snarls and =pronouns.possessive= ears twitch. =pronouns.Subjective= =verb:bark:afterpronoun=, and =pronouns.possessive= hyena tribesmen answer.'

>>> snapjaw.dv
6

>>> help(snapjaw)
# will give detailed help on all properties and methods, including a long list of properties that objects can have, like below:
...

 |  butcheredinto
 |      What a corpse item can be butchered into.
 |  
 |  canbuild
 |      Whether or not the player can tinker up this item.
 |  
 |  candisassemble
 |      Whether or not the player can disassemble this item.
 |  
 |  carrybonus
 |      The carry weight bonus.

# and so on.

# Tile support requires you to download the modding tile toolkit, described in the section above. But with it, you can do:

>>> youngivory = qindex['Young Ivory']

>>> youngivory.tile
<hagadias.qudtile.QudTile object at 0x0000018F898C3BA8>

>>> youngivory.tile.image
<PIL.PngImagePlugin.PngImageFile image mode=RGBA size=16x24 at 0x18F890B3320>

# for a PIL library format PNG image. There are other methods for retrieving BytesIO PNG binary data, see
>>> help(youngivory.tile)
# for details.
```

### Character codes
```python
gamecodes = root.get_character_codes()
# A dictionary containing some helpful information used to calculate the results of character builds.
# `gamecodes` contains the following items:
# 'class_bonuses': a dictionary mapping castes+callings to lists of stat bonuses
# 'class_skills': a dictionary mapping castes+callings to lists of skills (e.g. 'Horticulturalist': ['Meal Preparation', ...]
# 'class_tiles': a dictionary mapping castes+callings to tuples of (tile path, detail color) for that caste/calling's art
print(hagadias.character_codes.STAT_NAMES)
print(gamecodes["class_bonuses"]["Horticulturist"])  # 3-point Intelligence bonus
print(gamecodes["class_skills"]["Horticulturist"])
print(gamecodes["class_tiles"]["Horticulturist"])
```
```
('Strength', 'Agility', 'Toughness', 'Intelligence', 'Willpower', 'Ego')
[0, 0, 0, 3, 0, 0]
['Meal Preparation', 'Harvestry', '(Axe)', '(Bow and Rifle)', 'Wilderness Lore: Jungles']
('creatures/caste_1.bmp', 'g')
```

## Contributing

See `CONTRIBUTING.md`.

## Contributors

Thank you to the following people who have contributed code to this project:

- egocarib
- Wreckstation
- librarianmage
- HeladoDeBrownie
- elvres
- robbyblum
