[![Build Status](https://dev.azure.com/syntaxaire/hagadias-ci/_apis/build/status/TrashMonks.hagadias?branchName=master)](https://dev.azure.com/syntaxaire/hagadias-ci/_build/latest?definitionId=1&branchName=master)
# hagadias
Python package to extract game data from the [Caves of Qud](http://www.cavesofqud.com/) roguelike.  

This library forms the base for several projects:
 - the Caves of Qud wiki bot that builds and updates the [official Caves of Qud wiki](https://wiki.cavesofqud.com/)
 - the Discord bot that operates on the [Caves of Qud discord server](https://discordapp.com/invite/cavesofqud) (invite link)
 - an as yet unannounced project :)

## What does it do?
hagadias allows a user to read game data in the raw format used by the
[Caves of Qud](http://www.cavesofqud.com/) roguelike RPG, including the object tree,
fully colored tiles, and character data. It needs to be passed a path to a local
installation of the game in order to do anything.

## Installation
To install the package from this GitHub repository, run  
`pip install git+https://github.com/trashmonks/hagadias@main#egg=hagadias`  
or if you're using pipenv,  
`pipenv install -e git+https://github.com/trashmonks/hagadias.git@main#egg=hagadias`

## Tile support
Tile support currently requires a download of the latest Caves of Qud tile modding toolkit, extracted into the `hagadias` directory. We're working on making this easier to do. For the latest link, refer to [the Tile Support topic in qud-wiki](https://github.com/TrashMonks/qud-wiki#tile-support)

## Usage example
```
>>> from hagadias.gameroot import GameRoot
>>> GAMEPATH = r'C:\Steam\steamapps\common\Caves of Qud'  # Windows
# GAMEPATH = r'~/.local/share/Steam/steamapps/common/Caves of Qud'  # Linux
# GAMEPATH = r'~/Library/Application Support/Steam/steamapps/common/Caves of Qud'  # Mac OS
>>> root = GameRoot(GAMEPATH)

>>> gamever = root.gamever
# A string specifying the release version of Caves of Qud, like '2.0.193.0'.

>>> gamecodes = root.get_character_codes()
# A dictionary containing everything needed to calculate complete character sheets from character build codes.
# `gamecodes` contains the following items:
# 'genotype_codes': a dictionary mapping characters to genotypes (e.g. 'A': 'True Kin')
# 'caste_codes': a dictionary mapping characters to castes (e.g. 'A': 'Horticulturalist')
# 'calling_codes': a dictionary mapping characters to callings (e.g. 'A': 'Apostle')
# 'mod_codes': a dictionary mapping two-character strings to mutations (e.g. 'AA': 'Chimera')
# 'class_bonuses': a dictionary mapping castes+callings to lists of stat bonuses (e.g. 'Horticulturalist': [0, 0, 0, 3, 0, 0] for the 3-point Intelligence bonus)
# 'class_skills': a dictionary mapping castes+callings to lists of skills (e.g. 'Horticulturalist': ['Meal Preparation', ...]
# 'mod_bonuses': a dictionary mapping certain mutations to stat bonuses (e.g. 'BE': [2, 0, 0, 0, 0, 0] for the 2-point Strength bonus from Double-muscled)

>>> qud_object_root, qindex = root.get_object_tree()
Repairing invalid XML characters... done in 0.01 seconds
Repairing invalid XML line breaks... done in 1.47 seconds
Building Qud object hierarchy and adding tiles...

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

# Tile support requires you to download the modding tile toolkit, as in the readme section above. But with it, you can do:

>>> youngivory = qindex['Young Ivory']

>>> youngivory.tile
<hagadias.qudtile.QudTile object at 0x0000018F898C3BA8>

>>> youngivory.tile.image
<PIL.PngImagePlugin.PngImageFile image mode=RGBA size=16x24 at 0x18F890B3320>

# for a PIL library format PNG image. There are other methods for retrieving BytesIO PNG binary data, see
>>> help(youngivory.tile)
# for details.
```

## Contributing
See `CONTRIBUTING.md`.
