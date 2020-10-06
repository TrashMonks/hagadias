# https://stackoverflow.com/questions/3752476/python-pil-replace-a-single-rgba-color
import io
import logging
from pathlib import Path

from PIL import Image

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
                 raw_transparent="transparent"):
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
                # TODO: this seems to be for setting background
                raw_tilecolor = raw_tilecolor.split('^')[0]
            raw_tilecolor = QUD_COLORS[raw_tilecolor.strip('&')]
            self.tilecolor = raw_tilecolor
            self.transparentcolor = QUD_COLORS[raw_transparent]
        filename = fix_filename(filename)
        if raw_detailcolor is None:
            self.detailcolor = QUD_COLORS['transparent']
        else:
            self.detailcolor = QUD_COLORS[raw_detailcolor.strip('&')]
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
        for y in range(self.image.height):
            for x in range(self.image.width):
                px = self.image.getpixel((x, y))
                if px == TILE_COLOR:
                    self.image.putpixel((x, y), self.tilecolor)
                elif px == DETAIL_COLOR:
                    self.image.putpixel((x, y), self.detailcolor)
                elif px[3] == 0:
                    self.image.putpixel((x, y), self.transparentcolor)
                else:
                    # custom tinted image: uses R channel of special color from tile
                    final = []
                    detailpercent = px[0] / 255  # get opacity from R channel of tricolor
                    for tile, det in zip(self.tilecolor, self.detailcolor):
                        minimum = min(tile, det)
                        final.append(int(abs((tile - det) * detailpercent + minimum)))
                    final.append(255)  # transparency
                    self.image.putpixel((x, y), tuple(final))

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
