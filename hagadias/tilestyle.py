from __future__ import annotations  # allow forward type references

import itertools
import os
import random
from enum import Flag, auto
from typing import List, Optional, Type, Tuple

from hagadias.constants import LIQUID_COLORS
from hagadias.dicebag import DiceBag
from hagadias.helpers import (
    obj_has_any_part,
    extract_foreground_char,
    int_or_default,
    extract_background_char,
)


class RenderProps(Flag):
    """Bit flags that represent the render properties which styles may modify."""

    NONE = 0
    FILE = auto()  # Tile filepath
    COLOR = auto()  # TileColor
    DETAIL = auto()  # DetailColor
    TRANS = auto()  # Background/transparent color
    COLORS = COLOR | DETAIL
    NONFILE = COLOR | DETAIL | TRANS
    ALL = FILE | COLOR | DETAIL | TRANS


class StyleMetadata:
    def __init__(self, meta_type: str = "", f_postfix: str = None, meta_type_after: bool = False):
        """A style metadata object that defines the type of tile and recommended file postfix.

        Args:
            meta_type: The type of of tile (ex: 'random variant #3'). This could be used to display
                a label on the tile if this object's tiles are shown in a gallery or similar.
            f_postfix: The recommended file postfix (ex: 'variation 3'). Will be used to construct a
                filename for the tile in the format '[object name] [postfix].png'. Additional
                postfixes from merged metadata are appended after this postfix. If not specified,
                defaults to meta_type.
            meta_type_after: Controls how meta_type is combined with other metadata types when other
                style metadata is merged into this one. If meta_type_after is True, the format
                '[other_meta_type], [this_meta_type]' will be used, otherwise the format
                '[this_meta_type] [other_meta_type]' will be used.
        """
        self.merged_types = []
        self.merged_types_after = []
        self.merged_postfixes = []
        self.meta_type_after = meta_type_after
        self.meta_type = meta_type
        self.f_postfix = f_postfix if f_postfix is not None else meta_type

    def merge_with(self, mdata_to_merge: StyleMetadata):
        """Accepts another StyleMetadata instance and merges it's metadata into this instance.

        Args:
            mdata_to_merge: The StyleMetadata object that will be merged into this one. The
                instance provided as this argument will not be modified.
        """
        if mdata_to_merge.meta_type_after:
            self.merged_types_after.append(mdata_to_merge.meta_type)
        else:
            self.merged_types.append(mdata_to_merge.meta_type)
        self.merged_postfixes.append(mdata_to_merge.f_postfix)

    @property
    def type(self) -> str:
        """The descriptive metadata label for this tile (example: 'ripe, random sprite #2')"""
        if len("".join(self.merged_types)) == 0 and len("".join(self.merged_types_after)) == 0:
            if self.meta_type is not None:
                return self.meta_type.strip()
            return ""
        merged_types = " ".join(self.merged_types).strip()
        merged_types_after = " ".join(self.merged_types_after).strip()
        if self.meta_type_after and len(self.meta_type.strip()) > 0:
            composite_merged_types = f"{merged_types} {merged_types_after}".strip()
            composed = f"{composite_merged_types}, {self.meta_type.strip()}"
        else:
            composed = f"{self.meta_type.strip()} {merged_types}"
            if len(merged_types_after) > 0:
                composed = composed.strip()
                if len(composed) > 0:
                    composed = f"{composed.strip()}, {merged_types_after}"
                else:
                    composed = merged_types_after
        return composed.strip()

    @property
    def postfix(self) -> str:
        """The recommended filename postfix for this tile (example: ' variation 1 ripe')"""
        if len(self.merged_postfixes) == 0:
            if self.f_postfix is not None and len(self.f_postfix.strip()) > 0:
                return f" {self.f_postfix.strip()}"
            return ""
        merged_postfixes = " ".join(self.merged_postfixes).strip()
        final_postfix = f"{self.f_postfix.strip()} {merged_postfixes}"
        if len(final_postfix.strip()) > 0:
            # condense any consecutive spaces to a single space
            final_postfix = " ".join(final_postfix.split())
            final_postfix = final_postfix.strip()
            return f" {final_postfix}"
        return ""


class TileStyle:
    def __init__(
        self,
        _painter,  # Type: TilePainter
        _priority: int = 0,
        _modifies: RenderProps = RenderProps.ALL,
        _allows: RenderProps = RenderProps.ALL,
    ):
        """Base tile styling virtual class that should be subclassed by each TileStyle.

        Args:
            _painter: TilePainter instance that we will style (also holds the underlying QudObject).
            _priority: The priority of this style. Higher priority styles are applied first and may
                block lower priority styles if they both attempt to modify the same RenderProps.
            _modifies: RenderProperty flags representing the render props that this style modifies.
            _allows: RenderProperty flags representing the render props that will be allowed to
                accept further modifications after this style has been applied. Properties not
                specified here can no longer be modified by further styles on the style stack.
        """
        self._painter = _painter
        self._priority = _priority
        self._modifies = _modifies
        self._allows = _allows

    @property
    def object(self):
        return self._painter.obj  # Type: QudObject

    @property
    def painter(self):
        return self._painter  # Type: TilePainter

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def modifies(self) -> RenderProps:
        return self._modifies

    @property
    def allows(self) -> RenderProps:
        return self._allows

    @property
    def is_applicable(self) -> bool:
        return self._modification_count() > 0

    def modifies_within_scope(self, allowed_scope: RenderProps) -> bool:
        """True if this style modifies only the specified RenderProps."""
        return self._modifies & allowed_scope == self._modifies

    def modification_count(self) -> int:
        """Number of style permutations this style can contribute to the underlying object.
        Returns 0 if this style isn't applicable."""
        return self._modification_count()

    def _modification_count(self) -> int:
        """Returns the number of style permutations that this style can contribute to the
        underlying object. This should return 0 if the style does not apply.

        This method must be implemented by each style."""
        raise NotImplementedError()

    def apply_modification(self, index: int) -> StyleMetadata:
        """Apply this style to the TilePainter. A valid local style modification index must be
        provided; this index must be lower than this style's modification_count().

        Args:
            index: The zero-based style modification index.
        """
        if index >= self._modification_count():  # retrieve count from child implementation
            raise RuntimeError(f"{self.__class__.__name__} index overlow.")
        return self._apply_modification(index)

    def _apply_modification(self, index: int) -> StyleMetadata:
        """Applies this style to the TilePainter and returns metadata describing the modification.

        This method must be implemented by each style.

        Args:
            index: The zero-based style modification index, used to determine which tile style
            variant should be applied.
        """
        raise NotImplementedError()

    def style_limit_override(self) -> Optional[int]:
        """Retrieves the style limit override, or None if the style does not define one."""
        return self._style_limit_override()

    def _style_limit_override(self) -> Optional[int]:
        """Optional method - can be implemented to override style limit for particular object(s).
        If multiple styles implement this, only the highest-priority style's value will be used.
        """
        return None


class StyleSultanMuralWall(TileStyle):
    """Styles for SultanMuralWall<1-6> (wall 6 is the player's murals etched by Herododicus)."""

    MURAL_LABELS = [
        "appeases baetyl",
        "becomes loved",
        "blank",
        "body experience bad",
        "body experience good",
        "body experience neutral",
        "commits folly",
        "creates something",
        "crowned sultan",
        "dies",
        "does bureaucracy",
        "does something destructive",
        "does something humble",
        "does something rad",
        "endures hardship",
        "finds object",
        "has inspiring experience",
        "is born",
        "learns secret",
        "meets with counselors",
        "resists",
        "ruined variant 1",
        "ruined variant 2",
        "ruined variant 3",
        "ruined variant 4",
        "ruined variant 5",
        "ruined variant 6",
        "slays",
        "treats",
        "trysts",
        "visits location",
        "weird thing happens",
        "wields item in battle",
    ]
    MURAL_PATHS = [
        "appeasesbaetyl",
        "becomesloved",
        "blank",
        "bodyexperiencebad",
        "bodyexperiencegood",
        "bodyexperienceneutral",
        "commitsfolly",
        "createssomething",
        "crownedsultan",
        "dies",
        "doesbureaucracy",
        "doessomethingdestructive",
        "doessomethinghumble",
        "doessomethingrad",
        "endureshardship",
        "findsobject",
        "hasinspiringexperience",
        "isborn",
        "learnssecret",
        "meetswithcounselors",
        "resists",
        "ruined1",
        "ruined2",
        "ruined3",
        "ruined4",
        "ruined5",
        "ruined6",
        "slays",
        "treats",
        "trysts",
        "visitslocation",
        "weirdthinghappens",
        "wieldsiteminbattle",
    ]
    MURAL_POSITIONS = ["l", "c", "r"]

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=90, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        if self.object.part_SultanMural is not None:
            return len(StyleSultanMuralWall.MURAL_PATHS) * 3
        return 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        mural_type = StyleSultanMuralWall.MURAL_PATHS[index // 3]
        mural_label = StyleSultanMuralWall.MURAL_LABELS[index // 3]
        mural_pos = StyleSultanMuralWall.MURAL_POSITIONS[index % 3]
        self.painter.file = f"Walls/sw_mural_{mural_type}_{mural_pos}.bmp"
        return StyleMetadata(
            meta_type=f"{mural_label} {mural_pos.upper()}", f_postfix=f"{mural_type}_{mural_pos}"
        )

    def style_limit_override(self) -> Optional[int]:
        return len(StyleSultanMuralWall.MURAL_PATHS) * 3


class StyleSultanMuralMedian(TileStyle):
    """Styles for sultan mural medians."""

    MURAL_MEDIAN_COLOR = ["C", "m", "M", "r", "c", "K"]
    MURAL_MEDIAN_DETAIL = ["K", "y", "r", "c", "Y", "y"]

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=90, _modifies=RenderProps.ALL, _allows=RenderProps.NONE
        )

    def _modification_count(self) -> int:
        if self.object.name == "BaseMuralCenter":
            return 6
        return 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.color = StyleSultanMuralMedian.MURAL_MEDIAN_COLOR[index]
        self.painter.tilecolor = StyleSultanMuralMedian.MURAL_MEDIAN_COLOR[index]
        self.painter.detail = StyleSultanMuralMedian.MURAL_MEDIAN_DETAIL[index]
        self.painter.trans = "k"
        self.painter.file = f"Walls/sw_mural_centerpiece_period_{index + 1}.bmp"
        return StyleMetadata(
            meta_type=f"period {index + 1} sultanate", f_postfix=f"period {index + 1}"
        )


class StyleSultanMuralEndcap(TileStyle):
    """Styles for sultan mural endcaps."""

    MURAL_ENDCAP_COLOR = ["C", "m", "M", "r", "c", "K"]
    MURAL_ENDCAP_DETAIL = ["K", "y", "r", "c", "Y", "y"]

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=90, _modifies=RenderProps.ALL, _allows=RenderProps.NONE
        )

    def _modification_count(self) -> int:
        if self.object.name == "BaseMuralLeftend":
            return 12
        return 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        color_idx = index // 2
        period = index // 2 + 1
        self.painter.color = StyleSultanMuralEndcap.MURAL_ENDCAP_COLOR[color_idx]
        self.painter.tilecolor = StyleSultanMuralEndcap.MURAL_ENDCAP_COLOR[color_idx]
        self.painter.detail = StyleSultanMuralEndcap.MURAL_ENDCAP_DETAIL[color_idx]
        self.painter.trans = "k"
        orientation = "left" if (index % 2 == 0) else "right"
        self.painter.file = f"Walls/sw_mural_{orientation}end_period_{period}.bmp"
        return StyleMetadata(
            meta_type=f"period {period} sultanate ({orientation})",
            f_postfix=f"period {period} {orientation}end",
        )


class StyleRandomColors(TileStyle):
    """Styles for the RandomColors part."""

    RANDOM_COLORS_ALL = "R,W,G,B,M,C,Y,r,w,g,b,m,c,y"
    INDEX_MULTIPLIER = {"Bouquet": 5, "Flower": 6, "Flowers": 5}
    INDEX_OFFSET = {"Bouquet": 0, "Flower": 1, "Flowers": 2}

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=35, _modifies=RenderProps.COLORS, _allows=RenderProps.ALL
        )
        self._count = 0
        if self.object.part_RandomColors is not None:
            maincolors = self.object.part_RandomColors_MainColor
            maincolors = maincolors if maincolors != "all" else self.RANDOM_COLORS_ALL
            detailcolors = self.object.part_RandomColors_DetailColor
            detailcolors = detailcolors if detailcolors != "all" else self.RANDOM_COLORS_ALL
            tilecolors = self.object.part_RandomColors_TileColor
            tilecolors = tilecolors if tilecolors != "all" else self.RANDOM_COLORS_ALL
            bgcolors = self.object.part_RandomColors_BackgroundColor
            bgcolors = bgcolors if bgcolors != "all" else self.RANDOM_COLORS_ALL
            pairmaindetail = self.object.part_RandomColors_PairDetailWithForeground == "true"
            if pairmaindetail:
                # Keep all values, even duplicates
                maincolors = maincolors.split(",")
                detailcolors = detailcolors.split(",")
            else:
                # Filter out duplicates by temporary conversion to a set
                maincolors = [None] if maincolors is None else list(set(maincolors.split(",")))
                detailcolors = (
                    [None] if detailcolors is None else list(set(detailcolors.split(",")))
                )
            tilecolors = [None] if tilecolors is None else list(set(tilecolors.split(",")))
            bgcolors = [None] if bgcolors is None else list(set(bgcolors.split(",")))
            # Sort and then shuffle using Object ID as seed, to always get the same result
            random.seed(self.object.name)
            if not pairmaindetail:
                maincolors.sort()
                random.shuffle(maincolors)
                detailcolors.sort()
                random.shuffle(detailcolors)
            tilecolors.sort()
            random.shuffle(tilecolors)
            bgcolors.sort()
            random.shuffle(bgcolors)
            # Generate unique combinations
            if not pairmaindetail:
                self._combos = list(
                    itertools.product(*[maincolors, detailcolors, tilecolors, bgcolors])
                )
            else:
                self._combos = []
                for mc, dc in zip(maincolors, detailcolors):
                    for tc in tilecolors:
                        for bc in bgcolors:
                            self._combos.append((mc, dc, tc, bc))
            # Update count
            self._count = len(self._combos)

    def _modification_count(self) -> int:
        return self._count

    def _apply_modification(self, index: int) -> StyleMetadata:
        if self.object.name in self.INDEX_MULTIPLIER:
            # Special indexing for tiles with a lot of variations - this better shows off the color
            # variety of the tile, rather than repeating the same colors many times while we iterate
            # over other styles (like RandomTile)
            colorindex = (
                index * self.INDEX_MULTIPLIER[self.object.name]
                + self.INDEX_OFFSET[self.object.name]
            )
        else:
            colorindex = index
        maincolor, detailcolor, tilecolor, bgcolor = self._combos[colorindex]
        if bgcolor is None:
            bgcolor = extract_background_char(self.painter.color)
            if bgcolor is None:
                bgcolor = extract_background_char(self.painter.tilecolor)
        if maincolor is not None:
            self.painter.color = self.painter.tilecolor = maincolor
        if tilecolor is not None:
            self.painter.tilecolor = tilecolor
        if bgcolor is not None:
            self.painter.trans = bgcolor
        if detailcolor is not None:
            self.painter.detail = detailcolor
        pfix = "".join([(c if c is not None else "_") for c in self._combos[colorindex]])
        return StyleMetadata(
            meta_type=f"color #{index + 1}", f_postfix=f" (colors {pfix})", meta_type_after=True
        )


class StyleVillageMonument(TileStyle):
    """Styles for village monuments. This style includes only 30 sample color combinations, randomly
    seeded from the ObjectBluprint name. In game, these objects have closer to 100 variations."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=100, _modifies=RenderProps.COLORS, _allows=RenderProps.FILE
        )
        self._color_combos = []
        if self.object.inheritingfrom == "Village Monument":
            preserved_state = random.getstate()
            random.seed(self.object.name)
            while len(self._color_combos) < 30:
                vals = random.sample(StyleRandomColors.RANDOM_COLORS_ALL.split(","), 2)
                colors = f"{vals[0]}{vals[1]}"
                if colors not in self._color_combos:
                    self._color_combos.append(colors)
            random.setstate(preserved_state)

    def _modification_count(self) -> int:
        return len(self._color_combos)

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.color = self._color_combos[index][0]
        self.painter.tilecolor = self._color_combos[index][0]
        self.painter.trans = "transparent"
        self.painter.detail = self._color_combos[index][1]
        return StyleMetadata(
            meta_type=f"sample colors #{index + 1}",
            f_postfix=f"coloration {index + 1}" if index > 0 else "",
            meta_type_after=True,
        )


class StyleRandomTile(TileStyle):
    """Styles for the RandomTile part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=30, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )
        random_tiles = self.object.part_RandomTile_Tiles
        self._tiles = [] if random_tiles is None else random_tiles.split(",")

    def _modification_count(self) -> int:
        if len(self._tiles) == 0 or self.object.tag_PaintedLiquid is not None:
            return 0
        return len(self._tiles)

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.file = self._tiles[index]
        return StyleMetadata(
            meta_type=f"random sprite #{index + 1}",
            f_postfix=f"variation {index}" if index > 0 else "",
            meta_type_after=True,
        )


class StyleFracti(TileStyle):
    """Styles for the RandomTile part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=30, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        return 8 if self.object.part_Fracti is not None else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.file = f"Terrain/sw_fracti{index + 1}.bmp"
        return StyleMetadata(
            meta_type=f"random sprite #{index + 1}",
            f_postfix=f"variation {index}" if index > 0 else "",
            meta_type_after=True,
        )


class StyleTombstone(TileStyle):
    """Styles for the Tombstone part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=30, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        return (
            4
            if self.object.part_Tombstone is not None
            or self.object.part_RachelsTombstone is not None
            else 0
        )

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.file = f"Terrain/sw_tombstone_{index + 1}.bmp"
        return StyleMetadata(
            meta_type=f"random sprite #{index + 1}",
            f_postfix=f"variation {index + 1}" if index > 0 else "",
            meta_type_after=True,
        )


class StyleLiquidVolume(TileStyle):
    """Styles for liquids.

    Due to the complex interaction of RandomTile and PaintedLiquid, we handle liquids' RandomTile
    part within this style, rather than trying to combine this style with StyleRandomTile.
    Technically liquid pools are painted if >= 200 drams, but otherwise use RandomTile. However,
    we'll include both tile possibilities in this single style."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=90, _modifies=RenderProps.ALL, _allows=RenderProps.NONE
        )
        self._tiles = []
        self._liquids: Optional[List[str]] = None
        if self.object.part_LiquidVolume is not None:
            if self.object.part_LiquidVolume_MaxVolume == "-1":
                liquids: str = self.object.part_LiquidVolume_InitialLiquid
                if liquids is not None and len(liquids) > 0:
                    start_volume = self.object.part_LiquidVolume_StartVolume
                    if start_volume:
                        self._volume = DiceBag(start_volume).maximum()
                    else:
                        self._volume = int_or_default(self.object.part_LiquidVolume_Volume, 0)
                    self._liquids = liquids.split(",")
                    random_tiles = self.object.part_RandomTile_Tiles
                    self._tiles = [] if random_tiles is None else random_tiles.split(",")
                    self._tiles.insert(0, self.painter.get_painted_liquid_path())

    def _modification_count(self) -> int:
        return len(self._tiles)

    def _apply_modification(self, index: int) -> StyleMetadata:
        highest_pct: int = 0
        primary_liquid: str = "water"
        for liquid in self._liquids:
            liquid_name, pct = liquid.split("-")
            pct = int_or_default(pct, 0)
            if liquid_name in LIQUID_COLORS and pct > highest_pct:
                highest_pct = pct
                primary_liquid = liquid_name
        self.painter.trans = "transparent"
        self.painter.detail = extract_background_char(LIQUID_COLORS[primary_liquid], "transparent")
        self.painter.tilecolor = extract_foreground_char(LIQUID_COLORS[primary_liquid], "y")
        self.painter.color = self.painter.tilecolor
        self.painter.file = self._tiles[index]
        return StyleMetadata(
            meta_type="large pool" if index == 0 else f"puddle sprite #{index}",
            f_postfix=f"variation {index}" if index > 0 else "",
        )


class StyleHologram(TileStyle):
    """Style for the various Hologram parts."""

    PARTS = ["part_HologramMaterial", "part_HologramWallMaterial", "part_HologramMaterialPrimary"]

    def __init__(self, _painter):
        super().__init__(
            _painter,
            _priority=90,
            _modifies=RenderProps.COLORS,
            _allows=RenderProps.FILE | RenderProps.TRANS,
        )

    def _modification_count(self) -> int:
        return 1 if any(self.object.is_specified(part) for part in StyleHologram.PARTS) else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.color, self.painter.tilecolor, self.painter.detail = "&B", "&B", "b"
        return StyleMetadata(meta_type="")


class StyleExaminerUnknown(TileStyle):
    """Styles for the UnknownTile attribute of the Examiner part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=20, _modifies=RenderProps.ALL, _allows=RenderProps.NONE
        )
        self._unknown_tile = None
        if self.object.part_Examiner is not None:
            unktile = self.object.part_Examiner_UnknownTile
            if unktile is None or unktile != "":
                """Empty string means no special unidentified tile (ex: Furniture)"""
                unkcolor = self.object.part_Examiner_UnknownTileColor
                unkdetail = self.object.part_Examiner_UnknownDetailColor
                self._unknown_tile = unktile if unktile is not None else "items/sw_gadget.bmp"
                self._unknown_detail = unkdetail if unkdetail is not None else "C"
                self._unknown_color = unkcolor if unkcolor is not None else "&c"

    def _modification_count(self) -> int:
        if self._unknown_tile is not None:
            complexity = self.object.complexity
            if complexity is not None and complexity > 0:
                understanding = self.object.part_Examiner_Understanding
                if understanding is None or int(understanding) < complexity:
                    unknown_name = self.object.part_Examiner_UnknownDisplayName
                    if unknown_name is None or unknown_name != "*med":
                        # tonics excluded due to their random coloring - they have their own style
                        return 2
        return 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        is_identified = index % 2 == 0
        self._unknown_detail = (
            self._unknown_detail if self._unknown_detail != "" else self.painter.detail
        )
        c = self.painter.tilecolor if self.painter.tilecolor is not None else self.painter.color
        self._unknown_color = self._unknown_color if self._unknown_color != "" else c
        self.painter.file = self.painter.file if is_identified else self._unknown_tile
        self.painter.detail = self.painter.detail if is_identified else self._unknown_detail
        self.painter.color = self.painter.tilecolor = c if is_identified else self._unknown_color
        descriptor = "identified" if is_identified else "unidentified"
        return StyleMetadata(meta_type=descriptor, meta_type_after=True)


class StyleRandomTonic(TileStyle):
    """Styles for Tonics, which have random colors for each new playthrough."""

    NAMES_AND_COLORS = [
        "milky,&Y",
        "smokey,&K",
        "turquoise,&C",
        "cobalt,&b",
        "violet,&m",
        "rosey,&R",
        "mossy,&g",
        "muddy,&w",
        "gold-flecked,&W",
        "platinum,&y",
    ]

    def __init__(self, _painter):
        super().__init__(
            _painter,
            _priority=10,
            _modifies=RenderProps.COLOR,
            _allows=RenderProps.ALL ^ RenderProps.COLOR,
        )

    def _modification_count(self) -> int:
        return 10 if self.object.part_Examiner_UnknownDisplayName == "*med" else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        tonic_name, tonic_color = StyleRandomTonic.NAMES_AND_COLORS[index].split(",")
        self.painter.color = self.painter.tilecolor = tonic_color
        descriptor = f"a small {tonic_name} tube"
        return StyleMetadata(meta_type=descriptor, f_postfix=tonic_name)


class StyleSultanShrine(TileStyle):
    """Styles for the SultanShrine part."""

    COLORS = ["g", "r", "c", "w", "Y"]
    LABELS = ["under sky", "caves/red", "caves/cerulean", "caves/brown", "caves/white"]

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=90, _modifies=RenderProps.ALL, _allows=RenderProps.NONE
        )

    def _modification_count(self) -> int:
        return 80 if self.object.part_SultanShrine is not None else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        idx = index % 8 + 1
        descriptive_idx = index % 16 + 1
        is_rare = ((index // 8) % 2) == 1
        color_idx = index // 16
        self.painter.detail = StyleSultanShrine.COLORS[color_idx]
        self.painter.tilecolor = extract_foreground_char(self.painter.color, "y")
        self.painter.color = self.painter.tilecolor
        self.painter.trans = "transparent"
        self.painter.file = "Terrain/sw_sultanstatue_" + ("rare_" if is_rare else "") + f"{idx}.bmp"
        descriptor = f"sprite #{descriptive_idx}, {StyleSultanShrine.LABELS[color_idx]}"
        postfix = f" variant {descriptive_idx}, {StyleSultanShrine.COLORS[color_idx]}"
        return StyleMetadata(meta_type=descriptor, f_postfix=postfix)


class StylePistonPress(TileStyle):
    """Styles for the PistonPressElement part."""

    PATHS = [
        "Items/sw_crusher_s_press.bmp",
        "Items/sw_crusher_s_extend.bmp",
        "Items/sw_crusher_s_closed.png",
    ]
    TYPES = ["ready", "extended (base)", "extended (top)"]
    POSTFIXES = ["ready", "extended base", "extended top"]

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=90, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        return 3 if self.object.part_PistonPressElement is not None else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.file = StylePistonPress.PATHS[index]
        return StyleMetadata(
            meta_type=StylePistonPress.TYPES[index], f_postfix=StylePistonPress.POSTFIXES[index]
        )


class StyleMachineWallTubing(TileStyle):
    """Styles for machine wall objects."""

    TYPES = {
        "MachineWallHotTubing": ["hot", "hot (glowing in the dark)", "empty"],
        "MachineWallColdTubing": ["cold", "cold (glowing in the dark)", "empty"],
    }
    POSTFIXES = {
        "MachineWallHotTubing": [" hot", " hot glowing", " empty"],
        "MachineWallColdTubing": [" cold", " cold glowing", " empty"],
    }

    def __init__(self, _painter):
        super().__init__(
            _painter,
            _priority=90,
            _modifies=RenderProps.COLOR | RenderProps.TRANS,
            _allows=RenderProps.FILE | RenderProps.DETAIL,
        )

    def _modification_count(self) -> int:
        return 3 if self.object.name in self.TYPES else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        if index == 1:
            fg = self.object.part_DrawInTheDark_ForegroundTileColor
            bg = self.object.part_DrawInTheDark_BackgroundTileColor
            if fg is not None and bg is not None:
                self.painter.color = self.painter.tilecolor = f"&{fg}^{bg}"
        if index == 2:
            self.painter.color = self.painter.tilecolor = "&y^c"  # MachineWallEmptyTubing
        return StyleMetadata(
            meta_type=self.TYPES[self.object.name][index],
            f_postfix=self.POSTFIXES[self.object.name][index],
        )


class StyleHarvestable(TileStyle):
    """Styles for the Harvestable part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=20, _modifies=RenderProps.COLORS, _allows=RenderProps.ALL
        )
        self._count: Optional[int] = None

    def _modification_count(self) -> int:
        if self._count is None:
            self._count = 0
            ripe_tilecolor = self.object.part_Harvestable_RipeTileColor
            unripe_tilecolor = self.object.part_Harvestable_UnripeTileColor
            if (
                ripe_tilecolor is not None
                and unripe_tilecolor is not None
                and ripe_tilecolor != unripe_tilecolor
            ):
                self._count = 2
            else:
                unripe_detail = self.object.part_Harvestable_UnripeDetailColor
                ripe_detail = self.object.part_Harvestable_RipeDetailColor
                if (
                    ripe_detail is not None
                    and unripe_detail is not None
                    and ripe_detail != unripe_detail
                ):
                    self._count = 2
        return self._count

    def _apply_modification(self, index: int) -> StyleMetadata:
        is_ripe = index == 0
        self.painter.paint_harvestable(is_ripe=is_ripe)
        ripe_string = "ripe" if is_ripe else "not ripe"
        if self.object.name == "PhaseWeb":  # override 'ripe' language when it doesn't make sense
            ripe_string = "harvestable" if is_ripe else "not harvestable"
        return StyleMetadata(meta_type=ripe_string, f_postfix="ripe" if is_ripe else "unripe")


class StyleArspliceHyphae(TileStyle):
    """Styles for Arsplice Hyphae. Similar to Harvestable, except for a few unique things:
    Has two objects (Arsplice Hyphae A and Arsplice Hyphae B) which each contain a subset of the
    sprites, and also includes variable tiles (all other Harvestables permute colors only). This
    also supercedes the RandomTile part on Arsplice Hyphae to avoid additional complexity."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=100, _modifies=RenderProps.ALL, _allows=RenderProps.NONE
        )
        self._count: int = 0
        if self.object.inherits_from("Arsplice Hyphae"):
            self._ripe_tiles: List[str] = []
            self._unripe_tiles: List[str] = []
            for objkey in ["Arsplice Hyphae A", "Arsplice Hyphae B"]:
                if objkey in self.object.qindex:
                    obj = self.object.qindex[objkey]
                    self._ripe_color = obj.part_Harvestable_RipeColor
                    self._unripe_color = obj.part_Harvestable_UnripeColor
                    self._ripe_detail = obj.part_Harvestable_RipeDetailColor
                    self._unripe_detail = obj.part_Harvestable_UnripeDetailColor
                    self._ripe_tiles.extend(obj.part_Harvestable_RipeTiles.split(","))
                    self._unripe_tiles.extend(obj.part_Harvestable_UnripeTiles.split(","))
            self._count = len(self._ripe_tiles) + len(self._unripe_tiles)

    def _modification_count(self) -> int:
        return self._count

    def _apply_modification(self, index: int) -> StyleMetadata:
        is_ripe = index % 2 == 0
        file_idx = index // 2
        painter = self.painter
        if is_ripe:
            painter.color = painter.color if self._ripe_color is None else self._ripe_color
            painter.detail = painter.detail if self._ripe_detail is None else self._ripe_detail
            if len(self._ripe_tiles) > file_idx:
                painter.file = self._ripe_tiles[file_idx]
        else:
            painter.color = painter.color if self._unripe_color is None else self._unripe_color
            painter.detail = painter.detail if self._unripe_detail is None else self._unripe_detail
            if len(self._unripe_tiles) > file_idx:
                painter.file = self._unripe_tiles[file_idx]
        ripe_string = "ripe" if is_ripe else "not ripe"
        ripe_filestring = "ripe" if is_ripe else "unripe"
        return StyleMetadata(
            meta_type=f"{ripe_string} (variation #{file_idx + 1})",
            f_postfix=f"{ripe_filestring} variation {file_idx + 1}",
        )


class StyleAloes(TileStyle):
    """Styles for Aloe objects."""

    PARTS = ["DischargeOnStep", "CrossFlameOnStep", "FugueOnStep"]

    def __init__(self, _painter):
        super().__init__(
            _painter,
            _priority=20,
            _modifies=RenderProps.COLORS,
            _allows=RenderProps.FILE | RenderProps.TRANS,
        )

    def _modification_count(self) -> int:
        return 2 if obj_has_any_part(self.object, StyleAloes.PARTS) else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        is_ready = index == 0
        self.painter.paint_aloe(is_ready=is_ready)
        ready_string = "ready" if is_ready else "cooldown"
        return StyleMetadata(meta_type=ready_string, meta_type_after=True)


class StyleDoor(TileStyle):
    """Styles for the Door part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=50, _modifies=RenderProps.FILE, _allows=RenderProps.ALL
        )

    def _modification_count(self) -> int:
        if self.object.part_Door is None:
            return 0
        if self.object.inherits_from("Double Door"):
            dirs = ["_w_", "_w.", "_e_", "_e."]
            if (
                self.object.part_Door_ClosedTile is not None
                and any(d in self.object.part_Door_ClosedTile for d in dirs)
            ) or (
                self.object.part_Door_OpenTile is not None
                and any(d in self.object.part_Door_OpenTile for d in dirs)
            ):
                return 4
        return 2

    def _apply_modification(self, index: int) -> StyleMetadata:
        is_closed, double_door_alt = index % 2 == 0, index >= 2
        self.painter.paint_door(is_closed=is_closed, double_door_alt=double_door_alt)
        descriptor = "closed" if is_closed else "open"
        if self.object.inherits_from("Double Door"):
            if "_w_" in self.painter.file or "_w." in self.painter.file:
                descriptor += " (west)"
            elif "_e_" in self.painter.file or "_e." in self.painter.file:
                descriptor += " (east)"
        return StyleMetadata(meta_type=descriptor)


class StyleEnclosing(TileStyle):
    """Styles for the Enclosing part."""

    ATTRIBUTES = [
        "part_Enclosing_OpenTile",
        "part_Enclosing_ClosedTile",
        "part_Enclosing_OpenColor",
        "part_Enclosing_ClosedColor",
        "part_Enclosing_OpenTileColor",
        "part_Enclosing_ClosedTileColor",
    ]

    def __init__(self, _painter):
        super().__init__(
            _painter,
            _priority=40,
            _modifies=RenderProps.FILE | RenderProps.COLORS,
            _allows=RenderProps.TRANS,
        )

    def _modification_count(self) -> int:
        if self.object.part_Enclosing is not None:
            if any(getattr(self.object, att) is not None for att in StyleEnclosing.ATTRIBUTES):
                return 4 if self.object.part_DoubleEnclosing is not None else 2
        return 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        is_closed, double_enclosing_alt = index % 2 == 0, index >= 2
        self.painter.paint_enclosing(is_closed=is_closed, double_enclosing_alt=double_enclosing_alt)
        descriptor = "closed" if is_closed else "open"
        if self.object.part_DoubleEnclosing is not None:
            if "_w." in self.painter.file:
                descriptor += " (west)"
            elif "_e." in self.painter.file:
                descriptor += " (east)"
        return StyleMetadata(meta_type=descriptor)


class StyleDoubleContainer(TileStyle):
    """Styles for the DoubleContainer part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=40, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        return 2 if self.object.part_DoubleContainer is not None else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        if "_w." in self.painter.file and index == 1:
            self.painter.file = self.painter.file.replace("_w.", "_e.")
        if "_e." in self.painter.file and index == 0:
            self.painter.file = self.painter.file.replace("_e.", "_w.")
        if "_w." in self.painter.file:
            descriptor = "(west)"
        elif "_e." in self.painter.file:
            descriptor = "(east)"
        else:
            raise ValueError(
                "Unsupported format for DoubleContainer tile filepath in object"
                + f" {self.object.name}."
            )
        return StyleMetadata(meta_type=descriptor)


class StyleHangable(TileStyle):
    """Styles for the Hangable part."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=40, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        return 2 if self.object.part_Hangable_HangingTile is not None else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        is_hanging = index % 2 == 0
        self.painter.file = (
            self.object.part_Hangable_HangingTile if is_hanging else self.object.part_Render_Tile
        )
        descriptor = "hanging" if is_hanging else "unhung"
        return StyleMetadata(meta_type=descriptor)


class StyleSofa(TileStyle):
    """Styles for the Sofa object."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=40, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        return 3 if self.object.name == "Sofa" or self.object.inheritingfrom == "Sofa" else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        suffix, descriptor = [("l", "left"), ("c", "center"), ("r", "right")][index]
        filename, fileext = os.path.splitext(self.object.part_Render_Tile)
        self.painter.file = filename[:-1] + suffix + fileext
        return StyleMetadata(meta_type=descriptor)


class StyleOrnatePottedPlant(TileStyle):
    """Styles for the Ornate Potted Plant 1-4 objects."""

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=40, _modifies=RenderProps.ALL, _allows=RenderProps.NONE
        )

    def _modification_count(self) -> int:
        return 4 if self.object.name.startswith("Ornate Potted Plant ") else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        objkey = f"Ornate Potted Plant {index + 1}"
        if objkey in self.object.qindex:
            self.painter.color = self.object.qindex[objkey].part_Render_ColorString
            self.painter.tilecolor = self.object.qindex[objkey].part_Render_TileColor
            self.painter.detail = self.object.qindex[objkey].part_Render_DetailColor
            self.painter.file = self.object.qindex[objkey].part_Render_Tile
        descriptor = f"sprite #{index + 1}"
        postfix = f" variation {index}" if index > 0 else ""
        return StyleMetadata(meta_type=descriptor, f_postfix=postfix)


class StyleFixtureWithChildAlternates(TileStyle):
    """Styles for walls and other fixtures that define their own colors, and also have
    child (inherting) objects with the same display name that define variations of those colors."""

    PARENT_WALL_OBJECTS = ["FulcreteWithSquareWave", "ColumbariumWall", "GlassHydraulicPipe"]

    def __init__(self, _painter):
        super().__init__(
            _painter,
            _priority=40,
            _modifies=RenderProps.COLORS | RenderProps.TRANS,
            _allows=RenderProps.FILE,
        )
        self._matches = None
        for wallname in self.PARENT_WALL_OBJECTS:
            if self.object.name == wallname or self.object.inheritingfrom == wallname:
                self._matches = [
                    obj
                    for obj in self.object.qindex.values()
                    if (obj.inheritingfrom == wallname or obj.name == wallname)
                ]
                if len(self._matches) > 0:
                    uniquecolorcombos = {}
                    self._matches.sort(key=lambda obj: obj.name)  # sort by object name
                    for obj in self._matches:
                        colorstring = obj.part_Render_ColorString
                        tilecolor = obj.part_Render_TileColor
                        detailcolor = obj.part_Render_DetailColor
                        uniquecolorcombos[(colorstring, tilecolor, detailcolor)] = True
                    self._matches = list(uniquecolorcombos.keys())
                break

    def _modification_count(self) -> int:
        return 0 if self._matches is None else len(self._matches)

    def _apply_modification(self, index: int) -> StyleMetadata:
        if self._matches[index][0] is not None:
            self.painter.color = self.painter.tilecolor = self._matches[index][0]  # colorstring
        if self._matches[index][1] is not None:
            self.painter.tilecolor = self._matches[index][1]  # tilecolor
        if self._matches[index][2] is not None:
            self.painter.detail = self._matches[index][2]  # detailcolor
        return StyleMetadata(
            meta_type=f"style #{index + 1}",
            f_postfix=f"variation {index}" if index > 0 else "",
            meta_type_after=True,
        )


class StyleAsterisk(TileStyle):
    """Styles for the PointedAsteriskBuilder part."""

    TILES = [
        "Items/sw_asterisk_3.bmp",
        "Items/sw_asterisk_4.bmp",
        "Items/sw_asterisk_5.bmp",
        "Items/sw_asterisk_6plus.bmp",
    ]
    LABELS = ["three-pointed", "four-pointed", "five-pointed", "many-pointed"]

    def __init__(self, _painter):
        super().__init__(
            _painter, _priority=90, _modifies=RenderProps.FILE, _allows=RenderProps.NONFILE
        )

    def _modification_count(self) -> int:
        return 4 if self.object.part_PointedAsteriskBuilder is not None else 0

    def _apply_modification(self, index: int) -> StyleMetadata:
        self.painter.file = StyleAsterisk.TILES[index]
        return StyleMetadata(
            meta_type=StyleAsterisk.LABELS[index], f_postfix=f"({StyleAsterisk.LABELS[index]})"
        )


class StyleManager:
    # TODO: support grabbing a random style (for cryptogull)

    STYLE_LIMIT: int = 80
    """max limit for generated images for a single object ('flowers' has like 484 variants...)"""

    Styles: List[Type[TileStyle]] = [
        StyleAloes,
        StyleArspliceHyphae,
        StyleAsterisk,
        StyleDoor,
        StyleDoubleContainer,
        StyleEnclosing,
        StyleExaminerUnknown,
        StyleFixtureWithChildAlternates,
        StyleFracti,
        StyleHangable,
        StyleHarvestable,
        StyleHologram,
        # StyleLiquidVolume,
        StyleMachineWallTubing,
        StyleOrnatePottedPlant,
        StylePistonPress,
        StyleRandomColors,
        StyleRandomTile,
        StyleRandomTonic,
        StyleSofa,
        StyleSultanShrine,
        StyleSultanMuralEndcap,
        StyleSultanMuralMedian,
        StyleSultanMuralWall,
        StyleTombstone,
        StyleVillageMonument,
    ]
    """A list of all TileStyle classes as type objects. The order of this list does not matter."""

    def __init__(self, painter):
        """Accepts a TilePainter object and determines which styles are applicable to it.

        The StyleManager is a high-level abstraction over various TileStyle implementations. It
        handles sorting styles by priority, indexing styles, merging metadata when multiple
        styles are applied to a TilePainter, and generally simplifying the tile styling process."""
        self._painter = painter
        self._applicable_styles: List[TileStyle] = []
        self._index_combinations: List[Tuple[int, ...]] = []
        for style_class in StyleManager.Styles:
            style = style_class(painter)
            if style.is_applicable:
                self._applicable_styles.append(style)
        if len(self._applicable_styles) > 0:
            self._sort_styles()
            self._flatten_styles()
            self._make_combinations()

        self._style_limit: Optional[int] = None
        for style in self._applicable_styles:
            if self._style_limit is None:
                self._style_limit = style.style_limit_override()
        if self._style_limit is None:
            self._style_limit = StyleManager.STYLE_LIMIT

    def _sort_styles(self):
        """Sorts the applicable styles by priority (high to low)."""
        self._applicable_styles.sort(
            key=lambda style_instance: style_instance.priority, reverse=True
        )

    def _flatten_styles(self):
        """Pre-processes the style stack and removes styles that are not applicable (generally
        because other styles with higher priority don't allow their type of modifications)."""
        i = 0
        remaining = RenderProps.ALL
        while i < len(self._applicable_styles):
            style: TileStyle = self._applicable_styles[i]
            if style.modifies_within_scope(allowed_scope=remaining):
                # reduce allowed property scope of remaining styles
                remaining = remaining & style.allows
                i += 1
            else:
                # log.warning(
                #     'StyleManager discarded %s while flattening styles for object "%s"',
                #     type(self._applicable_styles[i]),
                #     self._painter.obj,
                # )
                # remove style because it's not within remaining allowed style scope
                del self._applicable_styles[i]

    def _make_combinations(self):
        """Generates all the possible indexing combinations for this set of styles.

        For example, if there is a 4-count style, a 2-count style, and a 3-count style which are
        applicable to this TilePainter, generates a 24-member list of Tuples like the following:
        [(1,1,1), (1,1,2), (1,1,3), (1,2,1), (1,2,2), (1,2,3), (2,1,1), ..., (4,2,2), (4,2,3)]"""
        index_arrays: List[List[int]] = []
        for style in self._applicable_styles:
            index_arrays.append(list(range(style.modification_count())))
        self._index_combinations = list(itertools.product(*index_arrays))

    def style_count(self) -> int:
        """Returns the global count of style combinations for this TilePainter. For example,
        Grave Moss has 5 RandomTile variants and a ripe/unripe Harvestable color variation. It will
        return 10 (5 * 2)."""
        if len(self._applicable_styles) <= 0:
            return 0
        count = 1
        for style in self._applicable_styles:
            count *= style.modification_count()
        return count if count <= self._style_limit else self._style_limit

    def apply_style(self, global_index: int) -> StyleMetadata:
        """Applies all applicable styles for this TilePainter, for the unique style permuation
        associated with the specified global style index. The indices used for each applicable style
        included in this permuation will vary (determined by _make_combinations() when this
        StyleManager was constructed).

        The general idea is to call style_count() to check the total number of merged global styles,
        and then call apply_style() in a loop or for a specific index less than that style count."""
        style_metadata: Optional[StyleMetadata] = None
        if len(self._applicable_styles) > 0:
            style_indices = self._index_combinations[global_index]
            for style_index, style in zip(style_indices, self._applicable_styles):
                metadata = style.apply_modification(style_index)
                if style_metadata is None:
                    style_metadata = metadata
                else:
                    style_metadata.merge_with(metadata)
        if style_metadata is None:
            style_metadata = StyleMetadata()
        return style_metadata
