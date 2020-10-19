"""attr specification:
QudObject.part_name_attribute"""
import sys
from copy import deepcopy
from typing import Tuple, Union
# Force Python XML parser:
sys.modules['_elementtree'] = None
from xml.etree.ElementTree import Element  # noqa E402

from anytree import NodeMixin  # noqa E402

from hagadias.qudtile import QudTile  # noqa E402
from hagadias.tilepainter import TilePainter  # noqa E402
from hagadias.tileanimator import TileAnimator, StandInTiles  # noqa E402

HOLO_PARTS = ['part_HologramMaterial',
              'part_HologramWallMaterial',
              'part_HologramMaterialPrimary']


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

    def __init__(self, blueprint: Element, source: str, full_source: str, qindex: dict):
        """Create a new QudObject instance.

        Parameters:
            blueprint: an XML Element to parse into dictionaries
            source: a string with the XML source that created `blueprint`
            full_source: a string with the full XML source (preceding comments, whitespace, etc.)
            qindex: a dict in which to register this object after creation, keyed by object name"""
        self.source = source
        self.full_source = full_source
        self.qindex = qindex
        self.name = blueprint.get('Name')
        self.blueprint = blueprint
        qindex[self.name] = self
        parent_name = blueprint.get('Inherits')
        if parent_name:
            self.parent = qindex[parent_name]
        else:
            self.parent = None
        self.attributes = {}
        self.all_attributes = {}
        for element in blueprint:
            element_tag = element.tag
            if 'Name' not in element.attrib:
                if element_tag != 'inventoryobject' and element_tag[:4] != 'xtag':
                    # probably something we don't need
                    continue
                element_tag = element.tag if element.tag[:4] != 'xtag' else 'xtag'
            if element_tag not in self.attributes:
                self.attributes[element_tag] = {}
            if 'Name' in element.attrib:
                # most tags
                element_name = element.attrib.pop('Name')
            elif element_tag == 'xtag':
                # for xtags, use substring after 'xtag' prefix
                element_name = element.tag[4:]
            elif 'Blueprint' in element.attrib:
                # for tag: inventoryobject
                element_name = element.attrib.pop('Blueprint')
            if element_name in self.attributes[element_tag] and \
                    isinstance(self.attributes[element_tag][element_name], dict):
                # for rare cases like:
                # <part Name="Brain" Hostile="false" Wanders="false" Factions="Prey-100" />
                # followed by:
                # <part Name="Brain" Hostile="false" />
                # - we don't want to overwrite the former with the latter, so update instead
                self.attributes[element_tag][element_name].update(element.attrib)
            else:
                # normal case: just assign the attributes dictionary to this <tag>-Name combo
                self.attributes[element_tag][element_name] = element.attrib
        self.all_attributes, self.inherited = self.resolve_inheritance()

    @property
    def tile(self) -> QudTile:
        """Return a QudTile colored to match the in-game representation.

        Created on-demand to speed load times; cached in self._tile after first call."""
        if hasattr(self, '_tile'):
            # do we have a cached tile?
            return self._tile
        tile = None  # not all objects have tiles
        if self.has_tile():
            # determine coloration
            trans = 'transparent'  # default transparency
            if (any(self.is_specified(part) for part in HOLO_PARTS)
                    or self.name == "Wraith-Knight Templar"):
                # special handling for holograms
                color, tilecolor, detail = '&B', '&B', 'b'
            elif self.is_specified('part_AnimatedMaterialStasisfield'):
                # special handling for stasis fields
                color, tilecolor, detail, trans = '&C^M', '&C^M', 'M', 'M'
            elif self.is_specified('part_Gas') and self.part_Gas_ColorString is not None:
                color = tilecolor = self.part_Gas_ColorString
                detail = None
                # gastype = self.part_Gas_GasType
                # if gastype is None or 'Cryo' not in gastype:  # Cryo gas always retains ^Y background color
                #     color = color.split('^')[0] + '^k'  # other gases have ^k unless they are > 50 density
            else:
                # general case
                color = self.part_Render_ColorString
                tilecolor = self.part_Render_TileColor
                # default detail color when unspecified is black (0, 0, 0)
                # which matches the overlay UI inventory rendering
                # ------------------------------------
                detail = self.part_Render_DetailColor
                # below uses logic similar to non-overlay UI where default ('k') is
                # essentially invisible/transparent against the default background color ('k')
                # ------------------------------------
                # _ = self.part_Render_DetailColor
                # detail = _ if _ else 'transparent'

            # determine file and handle special tile attributes
            file = None
            if (self.tag_PaintedWall and self.tag_PaintedWall_Value != "*delete") or \
               (self.tag_PaintedFence and self.tag_PaintedFence_Value != "*delete") or \
               self.part_Walltrap is not None:
                # painted tile rendering
                painter = TilePainter(self, color, tilecolor, detail, trans)
                self._tile = painter.tile
                return self._tile
            else:
                # normal rendering
                file = self.part_Render_Tile
            if self.part_RandomTile:
                file = self.part_RandomTile_Tiles.split(',')[0]
            if file is not None:
                tile = QudTile(file, color, tilecolor, detail, self.name, raw_transparent=trans)
            else:
                standin_tile_provider = StandInTiles.get_tile_provider_for(self)
                if standin_tile_provider is not None:
                    tile = QudTile(None, color, tilecolor, detail, self.name, trans, standin_tile_provider)
        self._tile = tile
        return tile

    def has_tile(self) -> bool:
        """Returns true if this object qualifies for tile rendering."""
        if self.tag_BaseObject:
            return False
        if self.part_Render_Tile or self.part_RandomTile:
            return True
        if self.tag_PaintedFence and self.tag_PaintedFence_Value != "*delete":
            return True
        if self.tag_PaintedWall and self.tag_PaintedWall_Value != "*delete":
            return True
        if StandInTiles.get_tile_provider_for(self) is not None:
            return True
        return False

    @property
    def gif_image(self):
        """Returns the rendered GIF for this QudObject, which is a PIL Image object.

        Created on demand and then cached in self._gif after first call."""
        if not hasattr(self, '_gif'):
            if not self.has_gif_tile():
                self._gif = None
            else:
                self._gif = TileAnimator(self).gif
        return self._gif

    def has_gif_tile(self) -> bool:
        """Returns true if this object qualifies for GIF rendering."""
        return TileAnimator(self).has_gif

    def resolve_inheritance(self) -> Tuple[dict, dict]:
        """Compute and return dictionaries with all inherited tags and attributes.

        Returns a 2-tuple of dictionaries. The first contains the computed attributes for this
        QudObject. The second contains the computed attributes for its parent.

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
        if self.parent is None:
            return self.attributes, {}
        inherited = self.parent.all_attributes
        all_attributes = deepcopy(self.attributes)
        for tag in inherited:
            if tag not in all_attributes:
                all_attributes[tag] = {}
            for name in inherited[tag]:
                if name not in all_attributes[tag]:
                    all_attributes[tag][name] = {}
                for attr in inherited[tag][name]:
                    if attr not in all_attributes[tag][name]:
                        # parent has this attribute but we don't
                        if inherited[tag][name][attr] == '*noinherit':
                            # this attribute shows that its name should not be inherited
                            del all_attributes[tag][name]
                        else:
                            all_attributes[tag][name][attr] = inherited[tag][name][attr]
                    else:
                        # we already had this defined for us - don't overwrite
                        pass
        return all_attributes, inherited

    def ui_inheritance_path(self) -> str:
        """Return a textual representation of this object's inheritance path."""
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
        path = attr.split('_')
        try:
            seek = self.attributes[path[0]]
            if len(path) > 1:
                seek = seek[path[1]]
            if len(path) > 2:
                seek = seek[path[2]]
        except KeyError:
            return False
        return True

    def __getattr__(self, attr) -> Union[str, None]:
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
        if attr.startswith('_'):  # guard against NodeMixIn housekeeping
            raise AttributeError
        if attr == 'attributes' or attr == 'all_attributes':  # guard against uninvited recursion
            raise AttributeError
        path = attr.split('_')
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
        return self.name + ' ' + str(self.attributes)

    def __repr__(self) -> str:
        """Return a developer's string representation of self."""
        return 'QudObject(' + self.name + ')'
