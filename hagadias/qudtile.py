# https://stackoverflow.com/questions/3752476/python-pil-replace-a-single-rgba-color
import io
import logging
from pathlib import Path, PureWindowsPath
from typing import Callable, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as PILImage

from hagadias.constants import QUD_COLORS

TILE_COLOR = (0, 0, 0, 255)
DETAIL_COLOR = (255, 255, 255, 255)

tiles_dir = Path("Textures").resolve()
blank_image = Image.new("RGBA", (16, 24), color=(0, 0, 0, 0))
# index keys are like "creatures/caste_flipped_22.bmp" as in XML
image_cache = {}

log = logging.getLogger(__name__)


def fix_filename(filename: str) -> str:
    """Return repaired versions of certain broken filenames."""
    # repair bad access paths
    if filename.lower().startswith("assets_content_textures"):
        filename = filename[24:]
        filename = filename.replace("_", "/", 1)
    # repair lowercase first letter for case-sensitive operating systems (Linux)
    filename = filename[0].upper() + filename[1:]
    return filename


def check_filename(filename: str):
    """Inspect filenames for potential bad input from a network user."""
    if filename.startswith("/") or filename.startswith("\\") or ".." in filename:
        raise PermissionError


def check_filepath(filepath: Path) -> Path:
    """Inspect paths for potential bad input from a network user."""
    # eliminate symlinks and '..' components and raise FileNotFoundError if the file does not exist:
    try:
        resolved = filepath.resolve(strict=True)  # FileNotFoundError is raised here
    except FileNotFoundError:
        # Might be a case insensitive issue due to being on a POSIX-like machine
        parent_dir = filepath.parent.resolve(strict=True)
        tile_name = filepath.name.lower()
        matched = [
            path.resolve(strict=True)
            for path in parent_dir.iterdir()
            if path.name.lower() == tile_name
        ]

        if len(matched) == 1:
            resolved = matched[0]
        else:
            raise FileNotFoundError

    target_in_tiles_dir = False
    for parent in resolved.parents:
        if parent == tiles_dir:
            target_in_tiles_dir = True
    if not target_in_tiles_dir:
        raise PermissionError(f"File not in tiles directory: {resolved}")
    return resolved


class QudTile:
    """Class to load and color a Qud tile."""

    # Note: See info dump on tile rendering at
    # https://discordapp.com/channels/214532333900922882/482714670860468234/762827742424465411

    def __init__(
        self,
        filename,
        colorstring,
        raw_tilecolor,
        raw_detailcolor,
        qudname,
        raw_transparent="transparent",
        image_provider=None,
        prefab_applicator=None,
    ):
        """Loads and colors a tile, creating the corresponding PIL Image object.

        Args:
            filename: filename of the tile source image. Set to None if the image_provider parameter
            is specified.
            colorstring: the ColorString associated with this tile.
            raw_tilecolor: the TileColor associated with this tile.
            raw_detailcolor: the DetailColor associated with this tile.
            qudname: name of the Qud object. Used only for debug purposes.
            raw_transparent: an override color to use to fill the transparent pixels of the source.
            image_provider: a TileProvider that can return a PIL Image object. Can be used instead
                            of a filename. If specified, QudTile will call Image.copy() on the
                            provided image to avoid altering it.
            prefab_applicator: A method that will draw a fake Unity prefab colored overlay on top of
                         the 160x240 "big" size version of the tile. If specified, QudTile will
                         invoke this method before returning a big_tile version of this tile.
        """
        self.hasproblems = False  # set True if problems with tile generation encountered
        self.filename = filename
        self.colorstring = colorstring
        self.raw_tilecolor = raw_tilecolor
        self.raw_detailcolor = raw_detailcolor
        self.qudname = qudname
        self.raw_transparent = raw_transparent
        self.prefab_applicator = prefab_applicator

        if (raw_tilecolor is None or raw_tilecolor == "") and colorstring is not None:
            raw_tilecolor = colorstring  # fall back to text mode color
            if "^" in colorstring:
                raw_tilecolor = colorstring.split("^")[0]
                raw_transparent = colorstring.split("^")[1]

        if not raw_tilecolor:
            self.tilecolor = QUD_COLORS["y"]  # render in white
            self.tilecolor_letter = "y"
            self.transparentcolor = QUD_COLORS[raw_transparent]
        else:
            if "^" in raw_tilecolor:
                raw_transparent = raw_tilecolor.split("^")[1]
                raw_tilecolor = raw_tilecolor.split("^")[0]
            raw_tilecolor = raw_tilecolor.strip("&")
            self.tilecolor = QUD_COLORS[raw_tilecolor]
            self.tilecolor_letter = raw_tilecolor
            self.transparentcolor = QUD_COLORS[raw_transparent]
        self.transparentcolor_letter = raw_transparent if raw_transparent != "transparent" else None
        if not raw_detailcolor:
            if raw_detailcolor == "":
                pass  # log.warning(f'Object "{self.qudname}" has empty DetailColor')
            self.detailcolor = QUD_COLORS["transparent"]
            self.detailcolor_letter = None
        else:
            raw_detailcolor = raw_detailcolor.strip("&")
            self.detailcolor = QUD_COLORS[raw_detailcolor]
            self.detailcolor_letter = raw_detailcolor
        if image_provider is not None:
            self.image = image_provider.image.copy()
            if image_provider.needs_color:
                self._color_image()
        else:
            self.filename = fix_filename(self.filename)  # convert _ into /
            check_filename(self.filename)  # check for e.g. '*', '..'
            if self.filename in image_cache:  # have we already read this file?
                self.image = image_cache[self.filename].copy()
                self._color_image()
            else:
                # using a temporary PureWindowsPath eliminates bugs on Linux where a \ slash
                # is included in the textual filename
                fullpath = tiles_dir.joinpath(PureWindowsPath(self.filename))
                try:
                    # resolve path, and sanity check untrusted user input
                    fullpath = check_filepath(fullpath)
                    self.image = Image.open(fullpath)
                    image_cache[self.filename] = self.image.copy()
                    self._color_image()
                except FileNotFoundError:
                    log.warning(
                        "Couldn't render tile for %s: %s not found at %s",
                        self.qudname,
                        self.filename,
                        fullpath,
                    )
                    self.hasproblems = True
                    self.image = blank_image

    @classmethod
    def from_image_provider(cls, image_provider, qudname: str):
        """Create a QudTile given only an image provider object. Shorthand alternative to the usual
        QudTile __init__ constructor.
        """
        return cls(None, None, None, None, qudname, image_provider=image_provider)

    def _color_image(self):
        skip_trans = True if self.transparentcolor == QUD_COLORS["transparent"] else False
        alphas = self.image.getdata(3)  # A (alpha channel only)
        pixels = self.image.getdata()  # RGBA (all four channels as a tuple)
        width = self.image.width
        index = -1
        for alpha, pixel in zip(alphas, pixels):
            index += 1
            if alpha == 0 and skip_trans:
                continue  # skip all pixels that are already transparent
            x = index % width
            y = index // 16
            coords = (x, y)
            if alpha == 0:
                self.image.putpixel(coords, self.transparentcolor)
            elif pixel == TILE_COLOR:
                self.image.putpixel(coords, self.tilecolor)
            elif pixel == DETAIL_COLOR:
                self.image.putpixel(coords, self.detailcolor)
            else:
                # custom tinted image: uses R channel of special color from tile
                final = []
                detailpercent = pixel[0] / 255  # get opacity from R channel of tricolor
                for tile, det in zip(self.tilecolor, self.detailcolor):
                    minimum = min(tile, det)
                    final.append(int(abs((tile - det) * detailpercent + minimum)))
                final.append(255)  # transparency
                self.image.putpixel(coords, tuple(final))

    def get_bytesio(self):
        """Get a BytesIO representation of a PNG encoding of the tile.

        Used for uploading to the wiki and discord.
        Some applications may require .seek(0) on this before use (discord.py does,
        mwclient does not.)"""
        png_b = io.BytesIO()
        self.image.save(png_b, format="png")
        return png_b

    def get_bytes(self):
        """Return the bytes representation of self image in PNG format."""
        bytesio = self.get_bytesio()
        bytesio.seek(0)
        return bytesio.read()

    def get_big_image(self):
        """Draw the big (10x, 160x240) tile for the wiki or discord."""
        bigimage = self.image.resize((160, 240), resample=Image.Dither.NONE)
        if self.prefab_applicator is not None:
            self.prefab_applicator(bigimage)
        return bigimage

    def get_big_bytesio(self):
        """Get a BytesIO representation of a PNG encoding of the big (10x, 160x240) tile.

        Used for uploading to the wiki and discord.
        Some applications may require .seek(0) on this before use (discord.py does,
        mwclient does not.)"""
        png_b = io.BytesIO()
        self.get_big_image().save(png_b, format="png")
        return png_b

    def get_big_bytes(self):
        """Return the bytes representation of big self in PNG format."""
        bytesio = self.get_big_bytesio()
        bytesio.seek(0)
        return bytesio.read()


class TileProvider:
    def __init__(self, image_provider: Callable[[], Tuple[PILImage, bool]]):
        """Wrapper class for providing a stand-in tile for objects that do not actually have a
        tile specified in ObjectBlueprints.xml, but for which it makes sense to 'fake' a tile by
        drawing their code page 437 character. The prime example is gases.

        Args:
            image_provider: A method that can be called to return a Tuple object. The Tuple
                will contain both of the following:
                    - The stand-in image.
                    - A bool indicating whether the image needs to be colored. If True, the provided
                      stand-in tile will also be colored by QudTile, typically using the colors
                      specified in ObjectBlueprints.xml
        """
        self._image_provider = image_provider
        self._image: Optional[PILImage] = None
        self._needs_color: Optional[bool] = None

    @property
    def image(self) -> PILImage:
        if self._image is None:
            self._image, self._needs_color = self._image_provider()
        return self._image

    @property
    def needs_color(self) -> bool:
        if self._needs_color is None:
            self._image, self._needs_color = self._image_provider()
        return self._needs_color


class StandInTiles:
    """Provides PIL Image representations of certain Code Page 437 characters that are used for
    animations.

    Methods in this class can either return an uncolored tile image constructed from only black and
    transparent pixels, suitable to be colored by QudTile, or can return a pre-colored image.
    """

    ASSETS = Path(__file__).parent / "assets"
    SOURCECODEPRO_FILE = ASSETS / "SourceCodePro-Semibold.ttf"
    FONT_SOURCECODEPRO = ImageFont.truetype(str(SOURCECODEPRO_FILE), 260)

    _hologram_material_glyph1: Image = None
    _hologram_material_glyph2: Image = None
    _hologram_material_glyph3: Image = None
    _gas_glyph1: Image = None
    _gas_glyph2: Image = None
    _gas_glyph3: Image = None
    _gas_glyph4: Image = None
    _spacetime_vortex_glyph1: Image = None

    @staticmethod
    def get_tile_provider_for(qud_object) -> Optional[TileProvider]:
        """Returns a TileProvider that can provide a stand-in tile for the specified QudObject, if
        one is available. Enables specifying tiles for things that don't actually have a tile
        specified in ObjectBlueprints.xml, but for which it makes sense to 'fake' a tile by drawing
        their code page 437 character. The prime example is gases.

        We could consider loading this from config eventually, but I doubt there will be many things
        that use it."""
        if getattr(qud_object, "part_Gas") is not None:
            return TileProvider(StandInTiles.gas_glyph1)
        elif getattr(qud_object, "part_SpaceTimeVortex") is not None:
            return TileProvider(StandInTiles.spacetime_vortex_glyph1)
        return None

    @staticmethod
    def make_font_glyph(displaychar: str, color: str, trans: bool = False) -> PILImage:
        """Creates a Source Code Pro character tile using the specified displaychar and color. For
        example, can create glyphs used by the Space-Time Vortex effect.

        Args:
            displaychar: single character to render, such as '$'
            color: qud color character for the font, such as 'R'
            trans: Whether to use a transparent background. If false, a background of 'k' will be
                   used. Note that if this glyph will be used to create a GIF, it must have trans
                   set to False. The Pillow GIF library doesn't properly support partial alpha,
                   which will be present in any font-based character tile created by this method.
        """
        # draw large and then shrink with bicubic sampling to better imitate the in-game look
        image = Image.new("RGBA", (160, 240), color=QUD_COLORS["transparent" if trans else "k"])
        draw = ImageDraw.Draw(image)
        draw.text(
            (0, -60), displaychar, font=StandInTiles.FONT_SOURCECODEPRO, fill=QUD_COLORS[color]
        )
        return image.resize((16, 24))

    @staticmethod
    def spacetime_vortex_glyph1() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  §  character, which is used by SpaceTimeVortex
        animations. Also returns 'False' to indicate no further coloration is needed."""
        if StandInTiles._spacetime_vortex_glyph1 is None:
            StandInTiles._spacetime_vortex_glyph1 = StandInTiles.make_font_glyph("§", "W", True)
        return StandInTiles._spacetime_vortex_glyph1, False

    @staticmethod
    def hologram_material_glyph1() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  |  character, which is used by
        HologramMaterial animations. Also returns 'True' to indicate QudTile should apply colors."""
        if StandInTiles._hologram_material_glyph1 is None:
            image = Image.new("RGBA", (16, 24), color=QUD_COLORS["transparent"])
            draw = ImageDraw.Draw(image)
            draw.rectangle([7, 1, 8, image.height - 1], outline=TILE_COLOR)
            StandInTiles._hologram_material_glyph1 = image
        return StandInTiles._hologram_material_glyph1, True

    @staticmethod
    def hologram_material_glyph2() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  _  character, which is used by
        HologramMaterial animations. Also returns 'True' to indicate QudTile should apply colors."""
        if StandInTiles._hologram_material_glyph2 is None:
            image = Image.new("RGBA", (16, 24), color=QUD_COLORS["transparent"])
            draw = ImageDraw.Draw(image)
            draw.rectangle([1, 21, image.width - 1, 22], outline=TILE_COLOR)
            StandInTiles._hologram_material_glyph2 = image
        return StandInTiles._hologram_material_glyph2, True

    @staticmethod
    def hologram_material_glyph3() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  -  character, which is used by
        HologramMaterial animations. Also returns 'True' to indicate QudTile should apply colors."""
        if StandInTiles._hologram_material_glyph3 is None:
            image = Image.new("RGBA", (16, 24), color=QUD_COLORS["transparent"])
            draw = ImageDraw.Draw(image)
            draw.rectangle([2, 11, 13, 12], outline=TILE_COLOR)
            StandInTiles._hologram_material_glyph3 = image
        return StandInTiles._hologram_material_glyph3, True

    @staticmethod
    def gas_glyph1() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  ░  character, which is used by Gas
        animations. Also returns 'True' to indicate QudTile should apply colors."""
        if StandInTiles._gas_glyph1 is None:
            image = Image.new("RGBA", (16, 24), color=QUD_COLORS["transparent"])
            draw = ImageDraw.Draw(image)
            for y in range(0, image.height, 6):
                for x in range(4, image.width, 6):
                    draw.rectangle([x, y, x + 1, y + 1], outline=TILE_COLOR)
            for y in range(2, image.height, 6):
                for x in range(0, image.width, 6):
                    draw.rectangle([x, y, x + 1, y + 1], outline=TILE_COLOR)
            for y in range(4, image.height, 6):
                for x in range(2, image.width, 6):
                    draw.rectangle([x, y, x + 1, y + 1], outline=TILE_COLOR)
            StandInTiles._gas_glyph1 = image
        return StandInTiles._gas_glyph1, True

    @staticmethod
    def gas_glyph2() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  ▒  character, which is used by Gas
        animations. Also returns 'True' to indicate QudTile should apply colors."""
        if StandInTiles._gas_glyph2 is None:
            image = Image.new("RGBA", (16, 24), color=QUD_COLORS["transparent"])
            draw = ImageDraw.Draw(image)
            for y in range(0, image.height, 4):
                for x in range(0, image.width, 4):
                    draw.rectangle([x, y, x + 1, y + 1], outline=TILE_COLOR)
            for y in range(2, image.height, 4):
                for x in range(2, image.width, 4):
                    draw.rectangle([x, y, x + 1, y + 1], outline=TILE_COLOR)
            StandInTiles._gas_glyph2 = image
        return StandInTiles._gas_glyph2, True

    @staticmethod
    def gas_glyph3() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  ▓  character, which is used by Gas
        animations. Also returns 'True' to indicate QudTile should apply colors."""
        if StandInTiles._gas_glyph3 is None:
            image = Image.new("RGBA", (16, 24), color=TILE_COLOR)
            draw = ImageDraw.Draw(image)
            for y in range(0, image.height, 8):
                for x in range(6, image.width, 8):
                    draw.rectangle([x, y, x + 1, y + 1], outline=QUD_COLORS["transparent"])
            for y in range(2, image.height, 4):
                for x in range(0, image.width, 4):
                    draw.rectangle([x, y, x + 1, y + 1], outline=QUD_COLORS["transparent"])
            for y in range(4, image.height, 8):
                for x in range(2, image.width, 8):
                    draw.rectangle([x, y, x + 1, y + 1], outline=QUD_COLORS["transparent"])
            StandInTiles._gas_glyph3 = image
        return StandInTiles._gas_glyph3, True

    @staticmethod
    def gas_glyph4() -> Tuple[PILImage, bool]:
        """Creates a PIL Image representation of the  █  character, which is used by Gas
        animations. Also returns 'True' to indicate QudTile should apply colors."""
        if StandInTiles._gas_glyph4 is None:
            image = Image.new("RGBA", (16, 24), color=TILE_COLOR)
            StandInTiles._gas_glyph4 = image
        return StandInTiles._gas_glyph4, True
