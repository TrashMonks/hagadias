import os
from typing import List, Optional, Tuple, Callable

from PIL import Image, ImageDraw

from hagadias.helpers import extract_foreground_char, extract_background_char
from hagadias.qudtile import QudTile, StandInTiles
from hagadias.tilestyle import StyleManager

HOLO_PARTS = ["part_HologramMaterial", "part_HologramWallMaterial", "part_HologramMaterialPrimary"]
PAINTWALL_EXCEPTIONS = ["part_SultanMural"]  # parts that need custom painting; ignore PaintWall tag


class TilePainter:
    def __init__(self, obj):
        """Create a TilePainter instance for this object and calculate the details needed to
        color and render a tile.

        Determines the colors and filepath that are required to create the tile. Actual tile
        creation is deferred until the tile property is accessed.

        Parameters:
            obj: a QudObject
        """

        self.obj = obj
        self.color = None
        self.tilecolor = None
        self.detail = None
        self.trans = None
        self.file = None
        self.standin = None
        self.prefab_imitator = None

        self._style_manager = StyleManager(self)

        tile_count = self.tile_count()
        self._tiles: List[Optional[QudTile]] = [None] * tile_count
        self._tiles_metadata: List[Optional[TilePainterMetadata]] = [None] * tile_count

        if tile_count > 0:
            self._apply_primer()

            # fence must be prioritized over wall
            if obj.tag_PaintedFence and obj.tag_PaintedFence_Value != "*delete":
                self.paintpath = self.parse_paint_path(obj.tag_PaintedFence_Value)
                self._paint_fence()
            elif obj.tag_PaintedWall and obj.tag_PaintedWall_Value != "*delete":
                if any(getattr(self.obj, part, None) is not None for part in PAINTWALL_EXCEPTIONS):
                    pass
                else:
                    self.paintpath = self.parse_paint_path(obj.tag_PaintedWall_Value)
                    self._paint_wall()
            elif obj.part_Walltrap is not None:
                self._paint_walltrap()

            if self.file is None or self.file == "":
                self.standin = StandInTiles.get_tile_provider_for(obj)

            self.prefab_imitator = TilePrefabImitator.get_fake_prefab_for(obj)

    def tile(self, tile_index: int = 0) -> QudTile | None:
        """Retrieves the painted QudTile for this object. If an index is supplied for an object that
        has multiple tiles, returns the alternate tile at the specified index."""
        if tile_index >= len(self._tiles):
            return None
        if self._tiles[tile_index] is not None:
            return self._tiles[tile_index]
        if self.file is None or self.file == "":
            if not self.standin:
                return None
            self._stylize_tile_variant(tile_index)
            self._tiles[tile_index] = QudTile(
                None,
                self.color,
                self.tilecolor,
                self.detail,
                self.obj.name,
                self.trans,
                self.standin,
                self.prefab_imitator,
            )
        else:
            self._stylize_tile_variant(tile_index)
            self._tiles[tile_index] = QudTile(
                self.file,
                self.color,
                self.tilecolor,
                self.detail,
                self.obj.name,
                self.trans,
                None,
                self.prefab_imitator,
            )
        return self._tiles[tile_index]

    def all_tiles_and_metadata(self) -> Tuple[List[QudTile], List]:
        """Returns a list of QudTiles representing all the tile variations for this object, as well
        as a corrsponding list of TilePainterMetadata for each of those tiles."""
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
        """Analyzes this object's tile metadata and defines its basic colors and filepaths. Most
        of the time this just uses the values specified in the object's Render part, but we also
        handle various exceptions and unique cases related to coloring the tile during this
        initial analysis.

        When this function finishes, an object should have at least some basic tile properties
        defined to avoid raising errors later in the process. The result of this function doesn't
        necessarily need to match the final rendered tile, however, because it will also be
        passed through _stylize_tile_variant(). Thus, _apply_primer() is particularly important
        for objects that have no part_Render_Tile defined or that have other special logic but
        don't define styles in _stylize_tile_variant()."""

        # general case
        self.trans = "transparent"  # default transparency
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
            self.file = self.obj.part_RandomTile_Tiles.split(",")[0]

        # apply special initial tile properties to certain objects and parts
        if (
            any(self.obj.is_specified(part) for part in HOLO_PARTS)
            or self.obj.name == "Wraith-Knight Templar"
        ):
            # special handling for holograms
            self.color, self.tilecolor, self.detail = "&B", "&B", "b"
        elif self.obj.is_specified("part_AnimatedMaterialStasisfield"):
            # special handling for stasis fields
            self.color, self.tilecolor, self.detail, self.trans = "&C^M", "&C^M", "M", "M"
        elif self.obj.is_specified("part_Gas") and self.obj.part_Gas_ColorString is not None:
            # Cryo gas always retains ^Y bg color. Technically, other gases have ^k bg color if < 50
            # density, but we will paint the "dense" version with their additional color
            self.color = self.tilecolor = self.obj.part_Gas_ColorString
            self.detail = None
        elif self.obj.part_AnimatedMaterialTechlight is not None:
            self.color = self.obj.part_AnimatedMaterialTechlight_baseColor
            self.color = self.tilecolor = "&c" if self.color is None else self.color
            self.detail = "Y"
        elif self.obj.part_AnimatedMaterialGeneric is not None:
            # use the colors from the zero frame of the AnimatedMaterialGeneric part, because
            # when these are present, the object's Render part colors are never used.
            part_detail = self.obj.part_AnimatedMaterialGeneric_DetailColorAnimationFrames
            part_color = self.obj.part_AnimatedMaterialGeneric_ColorStringAnimationFrames
            if part_detail is not None and part_detail.startswith("0="):
                self.detail = (part_detail.split(",")[0]).split("=")[1]
            if part_color is not None and part_color.startswith("0="):
                self.color = self.tilecolor = (part_color.split(",")[0]).split("=")[1]
        elif self.obj.part_SultanShrine is not None:
            self.detail = "g"
            self.color = self.tilecolor = extract_foreground_char(self.color, "y")
            self.trans = "transparent"
            self.file = "Terrain/sw_sultanstatue_1.bmp"
        elif self.obj.part_SultanMural is not None:
            self.file = "Walls/sw_mural_blank_c.bmp"
        elif self.obj.part_PistonPressElement is not None:
            self.file = "Items/sw_crusher_s_press.bmp"
        elif self.obj.name == "PondDown":  # 'small crack' in Joppa
            self.color = self.tilecolor = "&Y"  # Applied by the HiddenRender part
            self.trans = "b"  # Applied by the RenderLiquidBackground part
        elif self.obj.part_JiltedLoverProperties is not None:
            part_color = self.obj.part_JiltedLoverProperties_Color
            part_color = part_color if part_color is not None else "g"
            self.color = self.tilecolor = f"&{part_color}"

    def _stylize_tile_variant(self, tile_index: int = 0):
        """Morphs a tile into one of its variants, based on the provided zero-based tile index.
        This function uses the StyleManager to retrieve an object's alternate tile variations
        in a predetermined order, and defines the TilePainterMetadata associated with each tile,
        storing that metadata in the self._tiles_metadata List."""

        metadata = self._style_manager.apply_style(tile_index)

        if self._tiles_metadata[tile_index] is None:
            painter_postfix = metadata.postfix
            painter_type = metadata.type
            painter_postfix = None if painter_postfix == "" else painter_postfix
            painter_type = "default" if painter_type == "" else painter_type
            painter_metadata = TilePainterMetadata(self.obj, painter_postfix, painter_type)
            self._tiles_metadata[tile_index] = painter_metadata

    def _paint_fence(self):
        """Paints a fence tile for this object. Assumes that tag_PaintedFence exists."""
        if not self.tilecolor:
            self.tilecolor = self.color
        if self.detail and self.detail == "k" and "^" in self.tilecolor:
            # detail 'k' means trans layer is used for secondary color (common with fence tiles)
            self.detail = "transparent"
            self.trans = self.tilecolor.split("^")[1]
            # remove ^ from tilecolor to prevent QudTile overriding trans
            self.tilecolor = self.tilecolor.split("^")[0]
        elif (self.detail is None or self.detail != "k") and "^" in self.tilecolor:
            bgcolor = self.tilecolor.split("^")[1]
            # remove ^ from tilecolor to prevent QudTile overriding trans
            self.tilecolor = self.tilecolor.split("^")[0]
            self.trans = bgcolor if bgcolor != "k" else self.trans
        self.color = self.tilecolor
        _ = self.obj.tag_PaintedFenceAtlas_Value
        tileloc = _ if _ else "Tiles/"
        _ = self.obj.tag_PaintedFenceExtension_Value
        tileext = _ if _ else ".bmp"
        tilename = self.paintpath
        # the following works for all the existing HydraulicPowerTransmission and
        # MechanicalPowerTransmission objects. This logic may need to be updated if additional
        # objects are added to the game. These two parts inherit from the same base
        # (IPowerTransmission) but the logic for rendering IPowerTransmission objects is very
        # complex.
        if self.obj.part_HydraulicPowerTransmission:
            if self.obj.part_HydraulicPowerTransmission_TileEffects == "true":
                powered = self.obj.part_HydraulicPowerTransmission_TileAppendWhenPowered
                unbroken = self.obj.part_HydraulicPowerTransmission_TileAppendWhenUnbroken
                if powered and unbroken:
                    tilename = tilename + powered + unbroken
                if not self.obj.part_HydraulicPowerTransmission_TileAnimateSuppressWhenUnbroken:
                    tilename += "_1"
        if self.obj.part_MechanicalPowerTransmission:
            if self.obj.part_MechanicalPowerTransmission_TileEffects == "true":
                tilename = tilename + "_1"
        self.file = tileloc + tilename + "_" + "nsew" + tileext

    def _paint_wall(self):
        """Paints a wall tile for this object. Assumes that tag_PaintedWall exists."""
        wallcolor = self.tilecolor if self.tilecolor else self.color
        if self.detail and self.detail == "k" and "^" in wallcolor:
            self.detail = "transparent"
            self.trans = wallcolor.split("^", 1)[1]
        elif self.detail is None and "^" in wallcolor:
            self.trans = wallcolor.split("^", 1)[1]
        _ = self.obj.tag_PaintedWallAtlas_Value
        tileloc = _ if _ else "Tiles/"
        _ = self.obj.tag_PaintedWallExtension_Value
        tileext = _ if _ and self.obj.name != "Dirt" else ".bmp"
        if self.paintpath == "" or self.paintpath is None:
            self.file = None
        else:
            self.file = tileloc + self.paintpath + "-00000000" + tileext

    def _paint_walltrap(self):
        """Renders a walltrap tile. These are normally colored in the C# code, so we handle them
        specially."""
        self.file = self.obj.part_Render_Tile
        warmcolor = self.obj.part_Walltrap_WarmColor
        fore = extract_foreground_char(warmcolor, "r")
        back = extract_background_char(warmcolor, "g")
        self.color = "&" + fore + "^" + back
        self.tilecolor = self.color
        self.trans = back
        self.detail = "transparent"

    def get_painted_liquid_path(self) -> str:
        """Retrieves the primary tile path for a painted liquid tile."""
        if self.obj.tag_PaintedLiquid_Value is None:
            return ""
        tileloc = "Water/"  # there is no support for a PaintedLiquidAtlas tag, it's always 'Water/'
        ext = self.obj.tag_PaintedLiquidExtension_Value
        tileext = ext if ext else ".bmp"
        return tileloc + self.obj.tag_PaintedLiquid_Value + "-00000000" + tileext

    def paint_harvestable(self, is_ripe: bool) -> None:
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

    def paint_aloe(self, is_ready: bool) -> None:
        """Renders either the 'Ready' or the 'Cooldown' variant of an aloe plant."""
        if is_ready:
            if self.obj.part_DischargeOnStep is not None:  # Aloe Volta
                self.color = self.tilecolor = "&W"
                self.detail = "w"
            elif self.obj.part_CrossFlameOnStep is not None:  # Aloe Pyra
                self.color = self.tilecolor = "&W"
                self.detail = "R"
            elif self.obj.part_FugueOnStep is not None:  # Aloe Fugues
                self.color = self.tilecolor = "&G"
                self.detail = "M"
        else:
            if self.obj.part_DischargeOnStep is not None:
                self.color = self.tilecolor = "&w"
                self.detail = "w"
            elif self.obj.part_CrossFlameOnStep is not None:
                self.color = self.tilecolor = "&w"
                self.detail = "r"
            elif self.obj.part_FugueOnStep is not None:
                self.color = self.tilecolor = "&g"
                self.detail = "m"

    def paint_door(self, is_closed: bool = False, double_door_alt: bool = False) -> None:
        if is_closed:
            closed_tile = self.obj.part_Door_ClosedTile
            self.file = "Tiles/sw_door_basic.bmp" if closed_tile is None else closed_tile
        else:
            open_tile = self.obj.part_Door_OpenTile
            self.file = "Tiles/sw_door_basic_open.bmp" if open_tile is None else open_tile
        if double_door_alt:
            self._invert_filename_direction()

    def paint_enclosing(self, is_closed: bool = False, double_enclosing_alt: bool = False) -> None:
        if is_closed:
            self.color = (
                self.color
                if self.obj.part_Enclosing_ClosedColor is None
                else self.obj.part_Enclosing_ClosedColor
            )
            self.tilecolor = (
                self.tilecolor
                if self.obj.part_Enclosing_ClosedTileColor is None
                else self.obj.part_Enclosing_ClosedTileColor
            )
            self.file = (
                self.file
                if self.obj.part_Enclosing_ClosedTile is None
                else self.obj.part_Enclosing_ClosedTile
            )
        else:
            self.color = (
                self.color
                if self.obj.part_Enclosing_OpenColor is None
                else self.obj.part_Enclosing_OpenColor
            )
            self.tilecolor = (
                self.tilecolor
                if self.obj.part_Enclosing_OpenTileColor is None
                else self.obj.part_Enclosing_OpenTileColor
            )
            self.file = (
                self.file
                if self.obj.part_Enclosing_OpenTile is None
                else self.obj.part_Enclosing_OpenTile
            )
        if double_enclosing_alt:
            self._invert_filename_direction()

    def _invert_filename_direction(self) -> bool:
        start_dirs = ["_w_", "_w.", "_e_", "_e."]
        transform_dirs = ["_e_", "_e.", "_w_", "_w."]
        for dir1, dir2 in zip(start_dirs, transform_dirs):
            if dir1 in self.file:
                self.file = self.file.replace(dir1, dir2)
                return True
        return False

    @staticmethod
    def parse_paint_path(path: str) -> str:
        """Accepts a value from part_PaintedFence_Value or part_PaintedWall_Value, and retrieves
        the tile that should be used for that painted fence or wall. Rarely, these parts have a
        comma delimited list of possible tiles that can be used."""
        return path.split(",")[0]

    @staticmethod
    def is_painted_fence(qud_object) -> bool:
        """Returns true if this object is a painted fence."""
        return (
            qud_object.tag_PaintedFence is not None
            and qud_object.tag_PaintedFence_Value != "*delete"
        )

    def tile_count(self) -> int:
        """Retrieves the total number of tiles that are available for this object. Some objects have
        alternate tiles."""
        if not self.obj.has_tile():
            return 0
        count = self._style_manager.style_count()
        return count if count > 0 else 1


class TilePainterMetadata:
    def __init__(self, qud_object, postfix, tiletype):
        """Stores basic metadata for a tile, such as the filename that should be used for saving
        the tile as well as the type of tile, such as 'harvestable' or 'random sprite #7'."""
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
        return self._filename_noextension() + ".png"

    @property
    def gif_filename(self) -> str | None:
        """The recommended filename for this tile's GIF."""
        if not self.is_animated():
            return None
        return self._filename_noextension() + " animated.gif"

    def _filename_noextension(self) -> str:
        """The recommended base filename with no extension."""
        if self._file_noex is None:
            if self._base_filename is None or self._base_filename == "none":
                raise Exception(f'Error: tile for "{self.obj_id}" does not have a filename.')
            self._base_filename = os.path.splitext(self._base_filename)[0]
            if self.postfix is None:
                self._file_noex = self._base_filename
            else:
                self._file_noex = self._base_filename + self.postfix
        return self._file_noex


class TilePrefabImitator:
    @staticmethod
    def get_fake_prefab_for(qud_object) -> Optional[Callable]:
        """Returns a method that can draw a fake colored Unity prefab overlay on top of a 160x240
        size PIL image. Enables creating more realistic tiles for things like campfire and
        torch sconce, since they always appear with animated Unity prefab imposters in game. We
        wont try to animate these due to complexity, but we can at least add something to the
        static tile that looks good.
        """
        prefab: Optional[str] = qud_object.part_UnityPrefabImposter_PrefabID
        if prefab is not None:
            if prefab == "Prefabs/Particles/CampfireFlames":
                return TilePrefabImitator.add_campfire_flames
            elif prefab == "Prefabs/Particles/TorchpostFlames":
                return TilePrefabImitator.add_torchpost_flames
        return None

    @staticmethod
    def add_campfire_flames(big_image: Image) -> None:
        """Draws a fake unity prefab for campfire flames."""
        TilePrefabImitator.add_flames(big_image, 0)

    @staticmethod
    def add_torchpost_flames(big_image: Image) -> None:
        """Draws a fake unity prefab for torch sconce flames."""
        TilePrefabImitator.add_flames(big_image, -17)

    @staticmethod
    def add_flames(big_image: Image, y_offset: int = 0) -> None:
        """Draws a fake unity prefab overlay onto flaming tiles, like campfires and torch sconces.

        Args:
            big_image: A PIL image object with dimensions 160x240 (large tile size)
            y_offset: An offset for the flame prefab overlay. Coordinates are based on the campfire
                    object, but can be offset so that this prefab also works for torch sconces
        """
        fire_colors = [
            (230, 0, 0, 255),  # Red
            (231, 202, 0, 255),  # Yellow
            (166, 202, 193, 102),  # Smoke grey 1
            (166, 202, 193, 89),  # Smoke grey 2
            (166, 202, 193, 77),  # Smoke grey 3
            (166, 202, 193, 67),  # Smoke grey 4
            (166, 202, 193, 56),  # Smoke grey 5
        ]
        fire_rects = [
            [
                (53, 152, 68, 167),
                (56, 127, 71, 142),
                (68, 145, 83, 160),
                (83, 158, 98, 173),
                (84, 140, 99, 155),
                (87, 133, 102, 148),
            ],
            [(54, 155, 69, 170)],
            [(91, 109, 106, 124)],
            [(62, 100, 77, 115)],
            [(96, 81, 111, 96)],
            [(85, 54, 100, 69)],
            [(127, 20, 142, 35)],
        ]
        canvas = ImageDraw.Draw(big_image)
        for fire_color, fire_shape_list in zip(fire_colors, fire_rects):
            for fire_shape in fire_shape_list:
                x1 = fire_shape[0]
                y1 = fire_shape[1] + y_offset
                x2 = fire_shape[2]
                y2 = fire_shape[3] + y_offset
                canvas.rectangle([x1, y1, x2, y2], fire_color, fire_color)
