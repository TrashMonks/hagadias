# https://stackoverflow.com/questions/3752476/python-pil-replace-a-single-rgba-color
import io
import logging
from pathlib import Path

from PIL import Image, ImageDraw

from hagadias.constants import QUD_COLORS, QUD_VIRIDIAN

TILE_COLOR = (0, 0, 0, 255)
DETAIL_COLOR = (255, 255, 255, 255)

tiles_dir = Path('Textures')
blank_image = Image.new('RGBA', (16, 24), color=(0, 0, 0, 0))
# index keys are like "creatures/caste_flipped_22.bmp" as in XML
image_cache = {}


def fix_filename(filename: str) -> str:
    """Return repaired versions of certain broken filenames."""
    # repair bad access paths
    if filename.lower().startswith('assets_content_textures'):
        filename = filename[24:]
        filename = filename.replace('_', '/', 1)
    # repair lowercase first letter for case-sensitive operating systems (Linux)
    filename = filename[0].upper() + filename[1:]
    return filename


class QudTile:
    """Class to load and color a Qud tile."""
    # Note: See info dump on tile rendering at
    # https://discordapp.com/channels/214532333900922882/482714670860468234/762827742424465411

    def __init__(self, filename, colorstring, raw_tilecolor, raw_detailcolor, qudname,
                 raw_transparent="transparent", image_provider=None):
        """Loads and colors a tile, creating the corresponding PIL Image object.

        Args:
            filename: filename of the tile source image. Set to None if the image_provider parameter is specified.
            colorstring: the ColorString associated with this tile.
            raw_tilecolor: the TileColor associated with this tile.
            raw_detailcolor: the DetailColor associated with this tile.
            qudname: name of the Qud object. Used only for debug purposes.
            raw_transparent: an override color to use to fill the transparent pixels of the source.
            image_provider: a method that returns a PIL Image object. Can be used instead of a filename. If
                            specified, QudTile will call Image.copy() to avoid altering the provided image.
        """
        self.hasproblems = False  # set True if problems with tile generation encountered
        self.filename = filename
        self.colorstring = colorstring
        self.raw_tilecolor = raw_tilecolor
        self.raw_detailcolor = raw_detailcolor
        self.qudname = qudname
        self.raw_transparent = raw_transparent

        if raw_tilecolor is None and colorstring is not None:
            raw_tilecolor = colorstring  # fall back to text mode color
            if '^' in colorstring:
                raw_tilecolor = colorstring.split('^')[0]
                raw_transparent = colorstring.split('^')[1]

        if raw_tilecolor is None:
            self.tilecolor = QUD_COLORS['y']  # render in white
            self.transparentcolor = QUD_COLORS[raw_transparent]
        else:
            if '^' in raw_tilecolor:
                raw_transparent = raw_tilecolor.split('^')[1]
                raw_tilecolor = raw_tilecolor.split('^')[0]
            raw_tilecolor = QUD_COLORS[raw_tilecolor.strip('&')]
            self.tilecolor = raw_tilecolor
            self.transparentcolor = QUD_COLORS[raw_transparent]
        if raw_detailcolor is None:
            self.detailcolor = QUD_COLORS['transparent']
        else:
            self.detailcolor = QUD_COLORS[raw_detailcolor.strip('&')]
        if image_provider is not None:
            self.image = image_provider().copy()
            self._color_image()
        else:
            filename = fix_filename(filename)
            if filename in image_cache:
                self.image = image_cache[filename].copy()
                self._color_image()
            else:
                fullpath = tiles_dir / filename
                try:
                    self.image = Image.open(fullpath)
                    image_cache[filename] = self.image.copy()
                    self._color_image()
                except FileNotFoundError:
                    logging.warning(f'Couldn\'t render tile for {self.qudname}: {filename} not found')
                    self.hasproblems = True
                    self.image = blank_image

    def _color_image(self):
        skip_trans = True if self.transparentcolor == QUD_COLORS['transparent'] else False
        alphas = self.image.getdata(3)  # A (alpha channel only)
        pixels = self.image.getdata()   # RGBA (all four channels as a tuple)
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
        self.image.save(png_b, format='png')
        return png_b

    def get_bytes(self):
        """Return the bytes representation of self image in PNG format."""
        bytesio = self.get_bytesio()
        bytesio.seek(0)
        return bytesio.read()

    def get_big_image(self):
        """Draw the big (10x, 160x240) tile for the wiki or discord."""
        return self.image.resize((160, 240), resample=Image.NEAREST)

    def get_big_bytesio(self):
        """Get a BytesIO representation of a PNG encoding of the big (10x, 160x240) tile.

        Used for uploading to the wiki and discord.
        Some applications may require .seek(0) on this before use (discord.py does,
        mwclient does not.)"""
        png_b = io.BytesIO()
        self.get_big_image().save(png_b, format='png')
        return png_b

    def get_big_bytes(self):
        """Return the bytes representation of big self in PNG format."""
        bytesio = self.get_big_bytesio()
        bytesio.seek(0)
        return bytesio.read()


class StandInTiles:
    """Provides PIL Image representations of certain Code Page 437 characters that are used for animations.

    Methods in this class return an uncolored tile image constructed from only black and transparent pixels.
    """
    _hologram_material_glyph1: Image = None
    _hologram_material_glyph2: Image = None
    _hologram_material_glyph3: Image = None
    _gas_glyph1: Image = None
    _gas_glyph2: Image = None
    _gas_glyph3: Image = None
    _gas_glyph4: Image = None

    @staticmethod
    def hologram_material_glyph1() -> Image:
        """Creates a PIL Image representation of the  |  character, which is used by HologramMaterial animations."""
        if StandInTiles._hologram_material_glyph1 is None:
            image = Image.new('RGBA', (16, 24), color=QUD_COLORS['transparent'])
            draw = ImageDraw.Draw(image)
            draw.rectangle([7, 1, 8, image.height-1], outline=TILE_COLOR)
            StandInTiles._hologram_material_glyph1 = image
        return StandInTiles._hologram_material_glyph1

    @staticmethod
    def hologram_material_glyph2() -> Image:
        """Creates a PIL Image representation of the  _  character, which is used by HologramMaterial animations."""
        if StandInTiles._hologram_material_glyph2 is None:
            image = Image.new('RGBA', (16, 24), color=QUD_COLORS['transparent'])
            draw = ImageDraw.Draw(image)
            draw.rectangle([1, 21, image.width-1, 22], outline=TILE_COLOR)
            StandInTiles._hologram_material_glyph2 = image
        return StandInTiles._hologram_material_glyph2

    @staticmethod
    def hologram_material_glyph3() -> Image:
        """Creates a PIL Image representation of the  -  character, which is used by HologramMaterial animations."""
        if StandInTiles._hologram_material_glyph3 is None:
            image = Image.new('RGBA', (16, 24), color=QUD_COLORS['transparent'])
            draw = ImageDraw.Draw(image)
            draw.rectangle([2, 11, 13, 12], outline=TILE_COLOR)
            StandInTiles._hologram_material_glyph3 = image
        return StandInTiles._hologram_material_glyph3

    @staticmethod
    def gas_glyph1() -> Image:
        """Creates a PIL Image representation of the  ░  character, which is used by Gas animations."""
        if StandInTiles._gas_glyph1 is None:
            image = Image.new('RGBA', (16, 24), color=QUD_COLORS['transparent'])
            draw = ImageDraw.Draw(image)
            for y in range(0, image.height, 6):
                for x in range(4, image.width, 6):
                    draw.rectangle([x, y, x+1, y+1], outline=TILE_COLOR)
            for y in range(2, image.height, 6):
                for x in range(0, image.width, 6):
                    draw.rectangle([x, y, x+1, y+1], outline=TILE_COLOR)
            for y in range(4, image.height, 6):
                for x in range(2, image.width, 6):
                    draw.rectangle([x, y, x+1, y+1], outline=TILE_COLOR)
            StandInTiles._gas_glyph1 = image
        return StandInTiles._gas_glyph1

    @staticmethod
    def gas_glyph2() -> Image:
        """Creates a PIL Image representation of the  ▒  character, which is used by Gas animations."""
        if StandInTiles._gas_glyph2 is None:
            image = Image.new('RGBA', (16, 24), color=QUD_COLORS['transparent'])
            draw = ImageDraw.Draw(image)
            for y in range(0, image.height, 4):
                for x in range(0, image.width, 4):
                    draw.rectangle([x, y, x+1, y+1], outline=TILE_COLOR)
            for y in range(2, image.height, 4):
                for x in range(2, image.width, 4):
                    draw.rectangle([x, y, x+1, y+1], outline=TILE_COLOR)
            StandInTiles._gas_glyph2 = image
        return StandInTiles._gas_glyph2

    @staticmethod
    def gas_glyph3() -> Image:
        """Creates a PIL Image representation of the  ▓  character, which is used by Gas animations."""
        if StandInTiles._gas_glyph3 is None:
            image = Image.new('RGBA', (16, 24), color=TILE_COLOR)
            draw = ImageDraw.Draw(image)
            for y in range(0, image.height, 8):
                for x in range(6, image.width, 8):
                    draw.rectangle([x, y, x+1, y+1], outline=QUD_COLORS['transparent'])
            for y in range(2, image.height, 4):
                for x in range(0, image.width, 4):
                    draw.rectangle([x, y, x+1, y+1], outline=QUD_COLORS['transparent'])
            for y in range(4, image.height, 8):
                for x in range(2, image.width, 8):
                    draw.rectangle([x, y, x+1, y+1], outline=QUD_COLORS['transparent'])
            StandInTiles._gas_glyph3 = image
        return StandInTiles._gas_glyph3

    @staticmethod
    def gas_glyph4() -> Image:
        """Creates a PIL Image representation of the  █  character, which is used by Gas animations."""
        if StandInTiles._gas_glyph4 is None:
            image = Image.new('RGBA', (16, 24), color=TILE_COLOR)
            StandInTiles._gas_glyph4 = image
        return StandInTiles._gas_glyph4
