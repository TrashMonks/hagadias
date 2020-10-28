import os
from typing import List, Union, Optional, Tuple

from hagadias.helpers import extract_foreground_char, extract_background_char
from hagadias.qudtile import QudTile, StandInTiles

HOLO_PARTS = ['part_HologramMaterial',
              'part_HologramWallMaterial',
              'part_HologramMaterialPrimary']


class TilePainter:

    def __init__(self, obj):
        """Create a TilePainter instance for this object and calculate the details needed to color and render a tile.

        Determines the colors and filepath that are required to create the tile. Actual tile creation is
        deferred until the tile property is accessed.

        Parameters:
            obj: a QudObject
        """

        tile_count = self.tile_count(obj)
        self._tiles: List[Optional[QudTile]] = [None] * tile_count
        self._tiles_metadata: List[Optional[TilePainterMetadata]] = [None] * tile_count

        self.obj = obj
        self.color = None
        self.tilecolor = None
        self.detail = None
        self.trans = None
        self.file = None
        self.standin = None

        self._apply_primer()

        if obj.tag_PaintedFence and obj.tag_PaintedFence_Value != "*delete":  # fence must be prioritized over wall
            self.paintpath = self.parse_paint_path(obj.tag_PaintedFence_Value)
            self._paint_fence()
        elif obj.tag_PaintedWall and obj.tag_PaintedWall_Value != "*delete":
            self.paintpath = self.parse_paint_path(obj.tag_PaintedWall_Value)
            self._paint_wall()
        elif obj.part_Walltrap is not None:
            self._paint_walltrap()

        if self.file is None or self.file == '':
            self.standin = StandInTiles.get_tile_provider_for(obj)

    def tile(self, tile_index: int = 0) -> Union[QudTile, None]:
        """Retrieves the painted QudTile for this object. If an index is supplied for an object that has multiple
        tiles, returns the alternate tile at the specified index."""
        if tile_index >= len(self._tiles):
            return None
        if self._tiles[tile_index] is not None:
            return self._tiles[tile_index]
        if self.file is None or self.file == '':
            if not self.standin:
                return None
            self._stylize_tile_variant(tile_index)
            self._tiles[tile_index] = QudTile(None, self.color, self.tilecolor,
                                              self.detail, self.obj.name, self.trans, self.standin)
        else:
            self._stylize_tile_variant(tile_index)
            self._tiles[tile_index] = QudTile(self.file, self.color, self.tilecolor,
                                              self.detail, self.obj.name, self.trans)
        return self._tiles[tile_index]

    def all_tiles_and_metadata(self) -> Tuple[List[QudTile], List]:
        """Returns a list of QudTiles representing all the tile variations for this object, as well as a
        corrsponding list of TilePainterMetadata for each of those tiles."""
        qud_tiles: List[QudTile] = []
        metadata: List[TilePainterMetadata] = []
        for idx, entry in enumerate(self._tiles):
            qud_tile = self.tile(idx)
            if qud_tile is None:
                raise  # shouldn't happen
            qud_tiles.append(qud_tile)
            metadata.append(self._tiles_metadata[idx])
        return qud_tiles, metadata

    def _apply_primer(self):
        """Analyzes this object's tile metadata and defines its basic colors and filepaths. Most of the time this
        just uses the values specified in the object's Render part, but we also handle various exceptions and
        unique cases related to coloring the tile during this initial analysis."""

        # general case
        self.trans = 'transparent'  # default transparency
        self.color = self.obj.part_Render_ColorString
        self.tilecolor = self.obj.part_Render_TileColor
        self.detail = self.obj.part_Render_DetailColor

        # below uses logic similar to non-overlay UI where default ('k') is
        # essentially invisible/transparent against the default background color ('k')
        # ------------------------------------
        # _ = self.part_Render_DetailColor
        # detail = _ if _ else 'transparent'

        # determine tile filepath
        self.file = self.obj.part_Render_Tile
        if self.obj.part_RandomTile:
            self.file = self.obj.part_RandomTile_Tiles.split(',')[0]

        # apply special coloration to certain objects and parts
        if self.obj.part_Harvestable is not None:
            # show ripe color for harvestables
            self._paint_harvestable(is_ripe=True)
        elif any(self.obj.is_specified(part) for part in HOLO_PARTS) or self.obj.name == "Wraith-Knight Templar":
            # special handling for holograms
            self.color, self.tilecolor, self.detail = '&B', '&B', 'b'
        elif self.obj.is_specified('part_AnimatedMaterialStasisfield'):
            # special handling for stasis fields
            self.color, self.tilecolor, self.detail, self.trans = '&C^M', '&C^M', 'M', 'M'
        elif self.obj.is_specified('part_Gas') and self.obj.part_Gas_ColorString is not None:
            # Cryo gas always retains ^Y bg color. Technically, other gases have ^k bg color if < 50 density,
            # but we will paint the "dense" version with their additional color
            self.color = self.tilecolor = self.obj.part_Gas_ColorString
            self.detail = None
        elif self.obj.part_AnimatedMaterialTechlight is not None:
            self.color = self.obj.part_AnimatedMaterialTechlight_baseColor
            self.color = self.tilecolor = '&c' if self.color is None else self.color
            self.detail = 'Y'
        elif self.obj.part_DischargeOnStep is not None or self.obj.part_CrossFlameOnStep is not None \
                or self.obj.part_FugueOnStep is not None:  # Aloe Volta, Aloe Fugues, and Aloe Pyra
            self._paint_aloe(is_ready=True)
        elif self.obj.part_AnimatedMaterialGeneric is not None:
            # use the colors from the zero frame of the AnimatedMaterialGeneric part, because when these are
            # present, the object's Render part colors are never used.
            part_detail = self.obj.part_AnimatedMaterialGeneric_DetailColorAnimationFrames
            part_color = self.obj.part_AnimatedMaterialGeneric_ColorStringAnimationFrames
            if part_detail is not None and part_detail.startswith('0='):
                self.detail = (part_detail.split(',')[0]).split('=')[1]
            if part_color is not None and part_color.startswith('0='):
                self.color = self.tilecolor = (part_color.split(',')[0]).split('=')[1]
        elif self.obj.part_PistonPressElement is not None:
            self.file = 'Items/sw_crusher_s_press.bmp'

    def _stylize_tile_variant(self, tile_index: int = 0):
        """Morphs a tile into one of its variants, based on the provided zero-based tile index. This function
        controls the logic used to order an object's alternate tiles, and it also defines the TilePainterMetadata
        associated with each tile as it generates it, storing that metadata in the self._tiles_metadata List.

        The logic here should be kept in sync with the logic used in TilePainter.tile_count()"""
        harvestable_variants = self.obj.part_Harvestable is not None \
            and not any(self.obj.is_specified(part) for part in HOLO_PARTS)
        aloe_variants = self.obj.part_DischargeOnStep is not None or self.obj.part_CrossFlameOnStep is not None \
            or self.obj.part_FugueOnStep is not None
        meta_postfix = ''
        meta_type = ''
        if self.obj.part_RandomTile is not None:
            random_tiles = self.obj.part_RandomTile_Tiles.split(',')
            adjusted_randomtile_index = tile_index if not (harvestable_variants or aloe_variants) else (tile_index // 2)
            if adjusted_randomtile_index < len(random_tiles):
                self.file = self.obj.part_RandomTile_Tiles.split(',')[adjusted_randomtile_index]
                meta_type = f'random sprite #{adjusted_randomtile_index + 1}'
                # meta_tooltip = 'this object generates with a random sprite'
                meta_postfix = f' variation {adjusted_randomtile_index}' if adjusted_randomtile_index > 0 else ''
        # TODO: account for RandomColors part here
        if harvestable_variants:
            is_ripe = tile_index % 2 == 0
            self._paint_harvestable(is_ripe=is_ripe)
            ripe_string = 'ripe' if is_ripe else 'not ripe'
            if self.obj.name == 'PhaseWeb':  # override 'ripe' language when it doesn't make sense
                ripe_string = 'harvestable' if is_ripe else 'not harvestable'
            meta_type = f'{ripe_string}, {meta_type}' if len(meta_type) > 0 else ripe_string
            # if is_ripe:
            #     meta_tooltip = f'<br>{meta_tooltip}' if len(meta_tooltip) > 0 else meta_tooltip
            #     meta_tooltip = 'can be harvested for ingredients' + meta_tooltip
            meta_postfix += ' ripe' if is_ripe else ' unripe'
        elif aloe_variants:  # Aloe Volta, Aloe Fugues, and Aloe Pyra
            is_ready = tile_index % 2 == 0
            self._paint_aloe(is_ready=is_ready)
            ready_string = 'ready' if is_ready else 'cooldown'
            meta_type = f'{ready_string}, {meta_type}' if len(meta_type) > 0 else ready_string
            meta_postfix += f' {ready_string}'
        elif self.obj.part_PistonPressElement is not None:
            paths = ['Items/sw_crusher_s_press.bmp', 'Items/sw_crusher_s_extend.bmp', 'Items/sw_crusher_s_closed.png']
            types = ['ready', 'extended (base)', 'extended (top)']
            postfixes = [' ready', ' extended base', ' extended top']
            self.file, meta_type, meta_postfix = paths[tile_index], types[tile_index], postfixes[tile_index]
        if self._tiles_metadata[tile_index] is None:
            meta_postfix = None if meta_postfix == '' else meta_postfix
            meta_type = 'default' if meta_type == '' else meta_type
            # meta_tooltip = None if meta_tooltip == '' else meta_tooltip
            self._tiles_metadata[tile_index] = TilePainterMetadata(self.obj, meta_postfix, meta_type)

    def _paint_fence(self):
        """Paints a fence tile for this object. Assumes that tag_PaintedFence exists."""
        if not self.tilecolor:
            self.tilecolor = self.color
        if self.detail and self.detail == 'k' and '^' in self.tilecolor:
            # detail 'k' means trans layer is used for secondary color (common with fence tiles)
            self.detail = 'transparent'
            self.trans = self.tilecolor.split('^')[1]
            self.tilecolor = self.tilecolor.split('^')[0]  # remove ^ from tilecolor to prevent QudTile overriding trans
        elif (self.detail is None or self.detail != 'k') and '^' in self.tilecolor:
            bgcolor = self.tilecolor.split('^')[1]
            self.tilecolor = self.tilecolor.split('^')[0]  # remove ^ from tilecolor to prevent QudTile overriding trans
            self.trans = bgcolor if bgcolor != 'k' else self.trans
        self.color = self.tilecolor
        _ = self.obj.tag_PaintedFenceAtlas_Value
        tileloc = _ if _ else 'Tiles/'
        _ = self.obj.tag_PaintedFenceExtension_Value
        tileext = _ if _ else '.bmp'
        tilename = self.paintpath
        # the following works for all the existing HydraulicPowerTransmission and MechanicalPowerTransmission objects.
        # This logic may need to be updated if additional objects are added to the game. These two parts inherit from
        # the same base (IPowerTransmission) but the logic for rendering IPowerTransmission objects is very complex.
        if self.obj.part_HydraulicPowerTransmission:
            if self.obj.part_HydraulicPowerTransmission_TileEffects == 'true':
                powered = self.obj.part_HydraulicPowerTransmission_TileAppendWhenPowered
                unbroken = self.obj.part_HydraulicPowerTransmission_TileAppendWhenUnbroken
                if powered and unbroken:
                    tilename = tilename + powered + unbroken
                if not self.obj.part_HydraulicPowerTransmission_TileAnimateSuppressWhenUnbroken:
                    tilename += '_1'
        if self.obj.part_MechanicalPowerTransmission:
            if self.obj.part_MechanicalPowerTransmission_TileEffects == 'true':
                tilename = tilename + '_1'
        self.file = tileloc + tilename + "_" + "nsew" + tileext

    def _paint_wall(self):
        """Paints a wall tile for this object. Assumes that tag_PaintedWall exists."""
        wallcolor = self.tilecolor if self.tilecolor else self.color
        if self.detail and self.detail == 'k' and '^' in wallcolor:
            self.detail = 'transparent'
            self.trans = wallcolor.split('^', 1)[1]
        elif self.detail is None and '^' in wallcolor:
            self.trans = wallcolor.split('^', 1)[1]
        _ = self.obj.tag_PaintedWallAtlas_Value
        tileloc = _ if _ else 'Tiles/'
        _ = self.obj.tag_PaintedWallExtension_Value
        tileext = _ if _ and self.obj.name != 'Dirt' else '.bmp'
        self.file = tileloc + self.paintpath + '-00000000' + tileext

    def _paint_walltrap(self):
        """Renders a walltrap tile. These are normally colored in the C# code, so we handle them specially."""
        self.file = self.obj.part_Render_Tile
        warmcolor = self.obj.part_Walltrap_WarmColor
        fore = extract_foreground_char(warmcolor, 'r')
        back = extract_background_char(warmcolor, 'g')
        self.color = '&' + fore + '^' + back
        self.tilecolor = self.color
        self.trans = back
        self.detail = 'transparent'

    def _paint_harvestable(self, is_ripe: bool) -> None:
        """Renders either the ripe or the unripe variant for an object with the Harvestable part."""
        if is_ripe:
            ripe_color = self.obj.part_Harvestable_RipeColor
            self.color = self.color if ripe_color is None else ripe_color
            ripe_tilecolor = self.obj.part_Harvestable_RipeTileColor
            self.tilecolor = self.tilecolor if ripe_tilecolor is None else ripe_tilecolor
            ripe_detail = self.obj.part_Harvestable_RipeDetailColor
            self.detail = self.detail if ripe_detail is None else ripe_detail
        else:
            unripe_color = self.obj.part_Harvestable_UnripeColor
            self.color = self.color if unripe_color is None else unripe_color
            unripe_tilecolor = self.obj.part_Harvestable_UnripeTileColor
            self.tilecolor = self.tilecolor if unripe_tilecolor is None else unripe_tilecolor
            unripe_detail = self.obj.part_Harvestable_UnripeDetailColor
            self.detail = self.detail if unripe_detail is None else unripe_detail

    def _paint_aloe(self, is_ready: bool) -> None:
        """Renders either the 'Ready' or the 'Cooldown' variant of an aloe plant."""
        if is_ready:
            if self.obj.part_DischargeOnStep is not None:  # Aloe Volta
                self.color = self.tilecolor = '&W'
                self.detail = 'w'
            elif self.obj.part_CrossFlameOnStep is not None:  # Aloe Pyra
                self.color = self.tilecolor = '&W'
                self.detail = 'R'
            elif self.obj.part_FugueOnStep is not None:  # Aloe Fugues
                self.color = self.tilecolor = '&G'
                self.detail = 'M'
        else:
            if self.obj.part_DischargeOnStep is not None:
                self.color = self.tilecolor = '&w'
                self.detail = 'w'
            elif self.obj.part_CrossFlameOnStep is not None:
                self.color = self.tilecolor = '&w'
                self.detail = 'r'
            elif self.obj.part_FugueOnStep is not None:
                self.color = self.tilecolor = '&g'
                self.detail = 'm'


    @staticmethod
    def parse_paint_path(path: str) -> str:
        """Accepts a value from part_PaintedFence_Value or part_PaintedWall_Value, and retrieves the tile that
        should be used for that painted fence or wall. Rarely, these parts have a comma delimited list of
        possible tiles that can be used."""
        return path.split(',')[0]

    @staticmethod
    def is_painted_fence(qud_object) -> bool:
        """Returns true if this object is a painted fence."""
        return qud_object.tag_PaintedFence is not None and qud_object.tag_PaintedFence_Value != "*delete"

    @staticmethod
    def tile_count(qud_object) -> int:
        """Retrieves the total number of tiles that are available for this object. Some objects have
        alternate tiles.

        The logic here should be kept in sync with the logic used in <TilePainter>._stylize_tile_variant()"""
        if not qud_object.has_tile():
            return 0
        if qud_object.part_PistonPressElement is not None:
            return 3
        tile_count = 1
        if qud_object.part_RandomTile is not None:
            tile_count = len(qud_object.part_RandomTile_Tiles.split(','))
        # TODO: account for RandomColors part here
        if any(qud_object.is_specified(part) for part in HOLO_PARTS):
            return tile_count  # hologram overrides colors, so any dynamic colors below don't matter
        if qud_object.part_Harvestable is not None:
            ripe_tilecolor = qud_object.part_Harvestable_RipeTileColor
            unripe_tilecolor = qud_object.part_Harvestable_UnripeTileColor
            if ripe_tilecolor is not None and unripe_tilecolor is not None and ripe_tilecolor != unripe_tilecolor:
                tile_count *= 2  # for example, Grave Moss has RandomTile and Harvestable
            else:
                unripe_detail = qud_object.part_Harvestable_UnripeDetailColor
                ripe_detail = qud_object.part_Harvestable_RipeDetailColor
                if ripe_detail is not None and unripe_detail is not None and ripe_detail != unripe_detail:
                    tile_count *= 2
        elif qud_object.part_DischargeOnStep is not None or qud_object.part_CrossFlameOnStep is not None \
                or qud_object.part_FugueOnStep is not None:  # Aloe Volta, Aloe Fugues, and Aloe Pyra
            tile_count *= 2
        return tile_count


class TilePainterMetadata:

    def __init__(self, qud_object, postfix, tiletype):
        """Stores basic metadata for a tile, such as the filename that should be used for saving the tile as well
        as the type of tile, such as 'harvestable' or 'random sprite #7'."""
        self.postfix = postfix
        self.type = tiletype
        self.obj_id = qud_object.name
        self._base_filename = qud_object.image
        self._file_noex = None
        self._file = None
        self._has_gif = qud_object.has_gif_tile()

    def is_animated(self):
        """Whether this tile has a corresponding animated GIF"""
        return self._has_gif

    @property
    def filename(self) -> str:
        """The recommended filename for this tile."""
        return self._filename_noextension() + '.png'

    @property
    def gif_filename(self) -> str:
        """The recommended filename for this tile's GIF."""
        if not self.is_animated():
            return None
        return self._filename_noextension() + ' animated.gif'

    def _filename_noextension(self) -> str:
        """The recommended base filename with no extension."""
        if self._file_noex is None:
            if self._base_filename is None or self._base_filename == 'none':
                raise Exception(f'Error: tile for "{self.obj_id}" does not have a filename.')
            self._base_filename = os.path.splitext(self._base_filename)[0]
            if self.postfix is None:
                self._file_noex = self._base_filename
            else:
                self._file_noex = self._base_filename + self.postfix
        return self._file_noex
