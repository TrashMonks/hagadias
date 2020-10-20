from hagadias.helpers import extract_foreground_char, extract_background_char
from hagadias.qudtile import QudTile


class TilePainter:

    def __init__(self, obj, color: str, tilecolor: str, detail: str, trans: str):
        """Create a new TilePainter instance and calculate the details needed for painted tile creation.

        Determines the colors and filepath that are required to create the painted tile. Actual tile creation is
        deferred until the tile property is accessed.

        Parameters:
            obj: a QudObject
            color: the object's initially calculated ColorString
            tilecolor: the object's initially calculated TileColor
            detail: the object's initially calculated DetailColor
            trans: the object's initially calculated transparent (background) color
        """
        # obj is a QudObject, but I don't know how to import QudObject without causing errors
        self.obj = obj
        self.color = color
        self.tilecolor = tilecolor
        self.detail = detail
        self.trans = trans
        self.file = ''
        self._tile = None
        if obj.tag_PaintedFence and obj.tag_PaintedFence_Value != "*delete":  # fence must be prioritized over wall
            self.paintpath = self.parse_paint_path(obj.tag_PaintedFence_Value)
            self.paint_fence()
        elif obj.tag_PaintedWall and obj.tag_PaintedWall_Value != "*delete":
            self.paintpath = self.parse_paint_path(obj.tag_PaintedWall_Value)
            self.paint_wall()
        elif obj.part_Walltrap is not None:
            self.paint_walltrap()

    @property
    def tile(self):
        """Retrieves the painted QudTile for this object."""
        if self._tile is not None:
            return self._tile
        if self.file == '':
            return None
        self._tile = QudTile(self.file, self.color, self.tilecolor, self.detail, self.obj.name
                             , raw_transparent=self.trans)
        return self._tile

    def paint_fence(self):
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

    def paint_wall(self):
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

    def paint_walltrap(self):
        """Renders a walltrap tile. These are normally colored in the C# code, so we handle them specially."""
        self.file = self.obj.part_Render_Tile
        warmcolor = self.obj.part_Walltrap_WarmColor
        fore = extract_foreground_char(warmcolor, 'r')
        back = extract_background_char(warmcolor, 'g')
        self.color = '&' + fore + '^' + back
        self.tilecolor = self.color
        self.trans = back
        self.detail = 'transparent'

    @staticmethod
    def parse_paint_path(path: str) -> str:
        return path.split(',')[0]

    @staticmethod
    def is_painted_fence(qud_object) -> bool:
        return qud_object.tag_PaintedFence is not None and qud_object.tag_PaintedFence_Value != "*delete"
