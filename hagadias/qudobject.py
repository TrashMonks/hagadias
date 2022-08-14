"""attr specification:
QudObject.part_name_attribute"""
from copy import deepcopy
from functools import cached_property
from typing import Tuple, List

from anytree import NodeMixin
from lxml import etree

from hagadias.qudtile import QudTile
from hagadias.tileanimator import TileAnimator, StandInTiles
from hagadias.tilepainter import TilePainter


class QudObject(NodeMixin):
    """Represents a Caves of Qud object blueprint with attribute inheritance.

    Tags from the section of XML that create each QudObject can be accessed by attempting to
    retrieve an attribute of the object that encodes the XML tag and attributes in its name.

    Example: For a QudObject `qobj` constructed from the following XML,

    <object Name="SleepGasGrenade1" Inherits="Grenade">
        <part Name="Render" DisplayName="&amp;wsleep &amp;cgas grenade mk I" />
        <part Name="GasGrenade" Density="40" GasObject="SleepGas" />
        <part Name="Commerce" Value="20" />
        <part Name="Description" Short="A silver cylinder with a pull ring.~J211" />
        <tag Name="Mark" Value="1" />
        <tag Name="TurretStockWeight" Value="2" />
    </object>

    the DisplayName attribute of the <part> tag with Name 'Render' can be retrieved from `qobj` by:
        qobj.part_Render_DisplayName
    or the entire <part> tag with name 'Render' can be retrieved as a dictionary by:
        qobj.part_Render
    or both the <tag> tags can be retrieved as a dictionary, indexed by their Name attribute, by:
        qobj.tag

    This class is intended to be subclassed by classes that implement more sophisticated lookups
    using this API. The QudObjectProps class implements many of these.

    This class subclasses NodeMixin to reconstruct the in-game object hierarchy for inheritance
    purposes. This also makes it easy to print or traverse the tree since all housekeeping is done
    by the AnyTree module that provides NodeMixin.
    """

    def __init__(self, blueprint: etree.Element, qindex: dict, gameroot):
        """Create a new QudObject instance.

        Parameters:
            blueprint: an XML Element to parse into dictionaries
            qindex: a dict in which to register this object after creation, keyed by object name
            gameroot: a reference to the GameRoot instance that spawned this object
        """
        self.gameroot = gameroot
        self.source = etree.tostring(blueprint).decode("utf8")
        self.qindex = qindex
        self.name = blueprint.get("Name")
        self.blueprint = blueprint
        qindex[self.name] = self
        self.attributes = {}
        self.all_attributes = {}
        self.inherited = {}
        self.baked = False  # Indicates whether inheritance has been resolved for this object yet
        for element in blueprint:
            element_tag = str(element.tag)
            if "Name" not in element.attrib:
                if element_tag != "inventoryobject" and element_tag[:4] != "xtag":
                    # probably something we don't need
                    continue
                element_tag = element.tag if element.tag[:4] != "xtag" else "xtag"
            if element_tag not in self.attributes:
                self.attributes[element_tag] = {}
            if "Name" in element.attrib:
                # most tags
                element_name = element.attrib.pop("Name")
            elif element_tag == "xtag":
                # for xtags, use substring after 'xtag' prefix
                element_name = element.tag[4:]
            elif "Blueprint" in element.attrib:
                # for tag: inventoryobject
                element_name = element.attrib.pop("Blueprint")
            if element_name in self.attributes[element_tag] and isinstance(
                self.attributes[element_tag][element_name], dict
            ):
                # for rare cases like:
                # <part Name="Brain" Hostile="false" Wanders="false" Factions="Prey-100" />
                # followed by:
                # <part Name="Brain" Hostile="false" />
                # - we don't want to overwrite the former with the latter, so update instead
                self.attributes[element_tag][element_name].update(element.attrib)
            else:
                # normal case: just assign the attributes dictionary to this <tag>-Name combo
                self.attributes[element_tag][element_name] = element.attrib

    @cached_property
    def tile(self) -> QudTile:
        """Return a QudTile colored to match the in-game representation. This is only the
        'primary' tile for objects that have more than one tile. Use <QudObject>.tiles to
        retrieve the full tile collection.

        Created on-demand to speed load times; cached after first call."""
        tile = None  # not all objects have tiles
        if self.has_tile():
            painter = self.tile_painter
            tile = painter.tile()
        self._tile = tile
        return tile

    @cached_property
    def tile_painter(self) -> TilePainter:
        if hasattr(self, "_tile_painter"):
            return self._tile_painter
        self._tile_painter = TilePainter(self)
        return self._tile_painter

    @cached_property
    def tiles(self) -> List[QudTile]:
        """Returns all of the QudTiles for this object, including any alternate tiles. If you
        want to first check whether more than one tile exists, you can call
        <QudObject>.number_of_tiles().

        Created on-demand and cached after first call."""
        return self.tiles_and_metadata()[0]

    def tiles_and_metadata(self) -> Tuple[List[QudTile], List]:
        """Returns all of the QudTiles for this object including any alternate tiles, along with
        a corresponding TilePainterMetadata array with metadata about each tile. If you want to
        first check whether more than one tile exists, you can call <QudObject>.number_of_tiles(
        ). The TilePainterMetadata includes some suggestions for file naming or labeling the
        images when there are more than one.

        Created on-demand and cached in self._alltiles and self._allmetadata after first call."""
        if hasattr(self, "_alltiles") and hasattr(self, "_allmetadata"):
            return self._alltiles, self._allmetadata
        alltiles, metadata = [], []
        if self.tile_painter.tile_count() > 0:
            alltiles, metadata = self.tile_painter.all_tiles_and_metadata()
        self._alltiles: List[QudTile] = alltiles
        self._allmetadata: List = metadata
        return alltiles, metadata

    def has_tile(self) -> bool:
        """Returns true if this object qualifies for tile rendering."""
        if self.tag_BaseObject:
            if self.name in ["ScrapCape", "CatacombWall"]:
                return True  # special cases, not sure why they're marked as BaseObjects
            return False
        if self.part_Render_Tile or self.part_RandomTile is not None:
            return True
        if self.tag_PaintedFence and self.tag_PaintedFence_Value != "*delete":
            return True
        if self.tag_PaintedWall and self.tag_PaintedWall_Value != "*delete":
            return True
        if self.part_PistonPressElement is not None:
            return True
        if StandInTiles.get_tile_provider_for(self) is not None:
            return True
        return False

    def number_of_tiles(self) -> int:
        """The number of tiles that this object has. Some objects have many variant tiles."""
        return self.tile_painter.tile_count()

    def gif_image(self, index: int):
        """Returns the rendered GIF for this QudObject, which is a PIL Image object. Accepts an
        index which corresponds to the object's tile of the same index, if the object has
        multiple tiles. Objects with multiple tiles may also have multiple GIFs.

        Created on demand and then cached in self._tile_gifs after first call."""
        if not self.has_gif_tile():
            return None
        if not hasattr(self, "_tile_gifs"):
            self._tile_gifs = [None] * self.number_of_tiles()
        if index >= len(self._tile_gifs):
            return None
        if self._tile_gifs[index] is None and index < len(self.tiles):
            self._tile_gifs[index] = TileAnimator(self, self.tiles[index]).gif
        return self._tile_gifs[index]

    def has_gif_tile(self) -> bool:
        """Returns true if this object qualifies for GIF rendering."""
        return TileAnimator(self).has_gif

    def unidentified_tile_and_metadata(self) -> Tuple | None:
        if self.part_Examiner is not None:
            if self.number_of_tiles() > 1:
                tiles, metadata = self.tiles_and_metadata()
                for tile, meta in zip(tiles, metadata):
                    if meta.type == "unidentified":
                        return tile, meta

    def unidentified_tile(self) -> QudTile:
        data = self.unidentified_tile_and_metadata()
        if data is not None:
            return data[0]

    def unidentified_metadata(self):
        data = self.unidentified_tile_and_metadata()
        if data is not None:
            return data[1]

    def resolve_inheritance(self) -> None:
        """Compute dictionaries with all inherited tags and attributes. This method should be
        called only after all objects are loaded from XML (in other words, a two-pass load should
        be performed, which mimics the logic the game uses when loading ObjectBlueprints.xml)

        Resolves two internal object dictionaries. The first contains the computed attributes for
        this QudObject. The second contains the computed attributes for its parent.

        Recurses back all the way to the root Object and combines all data into
        the returned dict. Attributes of tags in children overwrite ancestors.

        Example:
          <object Name="BaseFarmer" Inherits="NPC">
            <part Name="Render" DisplayName="[farmer]" ...
        with the child object:
          <object Name="BaseWatervineFarmer" Inherits="BaseFarmer">
            <part Name="Render" DisplayName="watervine farmer" ...
        overwrites the DisplayName but not the rest of the Render dict.
        """
        if self.baked:
            return
        parent_name = self.blueprint.get("Inherits")
        self.parent = self.qindex[parent_name] if parent_name else None
        if self.parent is None:
            self.all_attributes = self.attributes
            self.inherited = {}
            self.baked = True
            return
        elif not self.parent.baked:
            # if parent appears later in ObjectBlueprints than child, it won't be baked yet
            self.parent.resolve_inheritance()
        inherited = self.parent.all_attributes
        all_attributes = deepcopy(self.attributes)
        removes_parts = "removepart" in all_attributes
        for tag in inherited:
            if tag not in all_attributes:
                all_attributes[tag] = {}
            for name in inherited[tag]:
                if name not in all_attributes[tag]:
                    if tag == "part" and removes_parts:
                        if name in all_attributes["removepart"]:
                            # remove `name` part from `self.name` due to `removepart` tag
                            continue  # don't inherit part if it's explicitly removed from the child
                    all_attributes[tag][name] = {}
                elif (
                    tag == "tag"
                    and "Value" in all_attributes[tag][name]
                    and all_attributes[tag][name]["Value"] == "*delete"
                ):
                    # remove `name` tag from `self.name` due to Value of `*delete`
                    del all_attributes[tag][name]
                    continue
                for attr in inherited[tag][name]:
                    if attr not in all_attributes[tag][name]:
                        # parent has this attribute but we don't
                        if inherited[tag][name][attr] == "*noinherit":
                            # this attribute shows that its name should not be inherited
                            # TODO: fix when the child also specifies this tag:
                            #       BaseTierShield1 is showing up as wiki eligible when it
                            #       shouldn't. I think it's something to do with this logic.
                            #       Other similar base objects seemingly not affected because they
                            #       have '[' in their display names per is_wiki_eligible() logic
                            del all_attributes[tag][name]
                        else:
                            all_attributes[tag][name][attr] = inherited[tag][name][attr]
                    else:
                        # we already had this defined for us - don't overwrite
                        pass
        self.all_attributes = all_attributes
        self.inherited = inherited
        self.baked = True

    def ui_inheritance_path(self) -> str:
        """Return a textual representation of this object's inheritance path.

        Useful for higher level utilities.
        Example output:
        "Object➜PhysicalObject➜Creature➜Humanoid➜BaseHumanoid➜Snapjaw➜Snapjaw Scavenger"
        """
        text = self.name
        ancestor = self.parent
        while ancestor is not None:
            text = ancestor.name + "➜" + text
            ancestor = ancestor.parent
        return text

    def inherits_from(self, name: str) -> bool:
        """Returns True if this object is 'name' or inherits from 'name', False otherwise."""
        if self.name == name:
            return True
        if self.is_root:
            return False
        return self.parent.inherits_from(name)

    def is_specified(self, attr) -> bool:
        """Return True if `attr` is specified explicitly for this object,
        False if it is inherited or does not exist"""
        # TODO: doesn't work right
        path = attr.split("_")
        try:
            seek = self.attributes[path[0]]
            if len(path) > 1:
                seek = seek[path[1]]
            if len(path) > 2:
                seek = seek[path[2]]
        except KeyError:
            return False
        return True

    def __getattr__(self, attr) -> str | None:
        """Implemented to get explicit or inherited tags from the Qud object tree.

        These virtual attributes take the form
          (XML tag) _ (Value of name attribute) _ (Other attribute)

        Example: given the following Qud object in the XML source file:
          <object Name="Bandage" Inherits="Item">
            <part Name="Examiner" Complexity="0"></part>
            <part Name="Render" Tile="Items/sw_hit.bmp" DetailColor="R" DisplayName="&amp;ybandage"
            ColorString="&amp;y" RenderString="012" RenderLayer="5"></part>
            <part Name="Physics" Category="Meds" Weight="0"></part>
            <part Name="Description" Short="A roll of gauze, suited to staunch bleeding."></part>
            <part Name="Commerce" Value="1"></part>
            <part Name="Medication"></part>
            <part Name="BandageMedication"></part>
            <tag Name="AlwaysStack" Value="Yes"></tag>
            <intproperty Name="Inorganic" Value="0" />
          </object>

        For the most basic usage,
            `this_object.part_Render_Tile` would retrieve the string 'Items/sw_hit.bmp'

        Other uses:
        this_object.tag would retrieve the dictionary {'AlwaysStack': {'Value': 'Yes'}}
        this_object.stat_Strength would retrieve None (after searching the inheritance tree)
        The expression:
          'meds' if this_object.part_Medication is not None else 'no_meds'
        would evaluate to 'meds'
        thisobject.tag_TinkerCategory would retrieve the dictionary {'Value': 'utility'}
          (inherited from Item)

        Usage note:
          Empty <part> and <tag> tags (with no attributes) will evaluate to an empty dictionary,
          which has the Boolean value False. Check to see that they are `is not None` rather than
          using them as a Boolean (i.e. in an `if`).
        """
        if attr.startswith("_"):  # guard against NodeMixIn housekeeping
            raise AttributeError
        if attr == "attributes" or attr == "all_attributes":  # guard against uninvited recursion
            raise AttributeError
        path = attr.split("_")
        try:
            seek = self.all_attributes[path[0]]  # XML tag portion
            if len(path) > 1:
                seek = seek[path[1]]  # Name portion
            if len(path) > 2:
                seek = seek[path[2]]  # attribute portion
        except KeyError:
            seek = None
        return seek

    def __str__(self) -> str:
        """Return a string representation of self."""
        return self.name + " " + str(self.attributes)

    def __repr__(self) -> str:
        """Return a developer's string representation of self."""
        return "QudObject(" + self.name + ")"
