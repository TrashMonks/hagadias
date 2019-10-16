[![Build Status](https://dev.azure.com/syntaxaire/hagadias-ci/_apis/build/status/TrashMonks.hagadias?branchName=master)](https://dev.azure.com/syntaxaire/hagadias-ci/_build/latest?definitionId=1&branchName=master)
# hagadias
Python package to extract game data from the [Caves of Qud](http://www.cavesofqud.com/) roguelike.  

This library forms the base for several projects:
 - the Caves of Qud wiki bot that builds and updates the [official Caves of Qud wiki](https://cavesofqud.gamepedia.com/)
 - the Discord bot that operates on the [Caves of Qud discord server](https://discordapp.com/invite/cavesofqud) (invite link)
 - an as yet unannounced project :)

## What does it do?
hagadias allows a user to read game data in the raw format used by the
[Caves of Qud](http://www.cavesofqud.com/) roguelike RPG, including the object tree,
fully colored tiles, and character data. It needs to be passed a path to a local
installation of the game in order to do anything.

## Installation
To install the package from this GitHub repository, run  
`pip install git+https://github.com/syntaxaire/hagadias@master#egg=hagadias`  
or if you're using pipenv,  
`pipenv install -e git+https://github.com/syntaxaire/hagadias.git@master#egg=hagadias`

## Usage
```python
from hagadias.gameroot import GameRoot
GAMEPATH = r'C:\Steam\steamapps\common\Caves of Qud'  # Windows
# GAMEPATH = r'~/.local/share/Steam/steamapps/common/Caves of Qud'  # Linux
# GAMEPATH = r'~/Library/Application Support/Steam/steamapps/common/Caves of Qud'  # Mac OS
root = GameRoot(GAMEPATH)
```

## API
```python
root.gamever
```
A string specifying the release version of Caves of Qud, like '2.0.193.0'.

```python
gamecodes = root.get_character_codes()
```
Gives you a dictionary containing everything needed to calculate complete character sheets from character build codes.

```python
qud_object_root, qindex = root.get_object_tree()
```
Gives you two items:
 - a `qud_object_root` of class `QudObjectProps` that is the root of the CoQ object hierarchy, allowing you to traverse the entire object tree and retrieve information about the items, characters, tiles, etc.
 - a `qindex` which is a dictionary that simply maps the Name (ingame object ID or wish ID) of each ingame object, as a string, to the Python object representing it.
