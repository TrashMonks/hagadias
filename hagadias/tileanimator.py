import logging
from io import BytesIO
from typing import List, Callable
from PIL import Image, ImageSequence

from hagadias.helpers import lowest_common_multiple, extract_foreground_char, extract_background_char, \
    parse_comma_equals_str_into_dict
from hagadias.qudtile import QudTile, StandInTiles
from hagadias.tileanimator_creategif import save_transparent_gif
from hagadias.tilepainter import TilePainter

POWER_TRANSMISSION_PARTS = ['ElectricalPowerTransmission', 'GenericPowerTransmission',
                            'HydraulicPowerTransmission', 'MechanicalPowerTransmission']


class TileAnimator:

    def __init__(self, qud_object):
        """Create a new TileAnimator for the specified QudObject.

        TileAnimator can create a GIF for the QudObject if it qualifies for GIF rendering. The creation
        of a GIF is deferred until the .gif property is accessed. For this reason, you can inexpensively
        instantiate a TileAnimator simply to check the .has_gif property for a particular QudObject."""
        self.qud_object = qud_object
        self._gif_image = None

    @property
    def is_valid(self) -> bool:
        """Basic validation check for this TileAnimator's QudObject. True if the object has a valid tile image."""
        if not self.qud_object.has_tile():
            return False
        if self.qud_object.tile.hasproblems:
            return False
        return True

    @property
    def has_gif(self) -> bool:
        """Whether this TileAnimator's QudObject qualifies for GIF rendering."""
        return len(self.get_animators()) > 0

    @property
    def gif(self) -> Image:
        """Selects an animation algorithm and applies it. This results in the creation of the GIF image,
        a PIL Image object, which is cached in the _gif_image attribute of this class.

        Note that a PIL Image object is really only a single frame of the GIF. PIL exposes an iterator
        that you can use to walk the GIF frames if you need to (ImageSequence.Iterator). If you want to
        save this GIF to a file or bytestream, you should call GifHelper.save() to ensure that all
        frames and animation delays are properly preserved."""
        if self._gif_image is None:
            for animation_applicator in self.get_animators():
                animation_applicator()
        return self._gif_image

    def get_animators(self) -> List[Callable]:
        """Returns all of the animation methods that are relevant to this object."""
        animators = []
        if not self.is_valid:
            return animators
        obj = self.qud_object
        if obj.part_AnimatedMaterialElectric is not None:
            animators.append(self.apply_animated_material_electric)
        if obj.part_AnimatedMaterialGeneric is not None or obj.part_AnimatedMaterialGenericAlternate is not None:
            if obj.part_CatacombsExitTeleporter is None:  # manually excluded parts
                if obj.name != 'Telescope' and obj.name != 'Full-Scale Recompositer':  # manually excluded objects
                    animators.append(self.apply_animated_material_generic)
        if obj.part_AnimatedMaterialForcefield is not None:
            animators.append(self.apply_animated_material_forcefield)
        if obj.part_AnimatedMaterialLuminous is not None:
            animators.append(self.apply_animated_material_luminous)
        if obj.part_AnimatedMaterialMainframeTapeDrive is not None:
            animators.append(self.apply_animated_material_mainframe_tape_drive)
        if obj.part_AnimatedMaterialRealityStabilizationField is not None:
            animators.append(self.apply_animated_material_reality_stabilization_field)
        if obj.part_AnimatedMaterialTechlight is not None:
            animators.append(self.apply_animated_material_techlight)
        if obj.part_Gas is not None:
            animators.append(self.apply_gas_animation)
        if obj.part_HologramMaterial is not None or obj.part_HologramWallMaterial is not None:
            animators.append(self.apply_hologram_material)
        for partname in POWER_TRANSMISSION_PARTS:
            part = getattr(obj, f'part_{partname}')
            if part is not None and 'TileBaseFromTag' in part:
                if 'TileEffects' in part and part['TileEffects'].lower() == 'true':
                    taswu = 'TileAnimateSuppressWhenUnbroken'  # don't animate this stuff (ex: unbroken metal pipe)
                    if taswu not in part or part[taswu].lower() != 'true':
                        animators.append(self.apply_power_transmission)
        if obj.part_Walltrap is not None:
            animators.append(self.apply_walltrap_animation)
        return animators

    def apply_animated_material_electric(self) -> None:
        """Renders a GIF loosely based on the behavior of the AnimatedMaterialElectric part."""
        tile = self.qud_object.tile
        frame1and2 = QudTile(tile.filename, '&W', None, tile.raw_detailcolor, tile.qudname, tile.raw_transparent)
        frame3 = QudTile(tile.filename, '&Y', None, tile.raw_detailcolor, tile.qudname, tile.raw_transparent)
        self._make_gif([frame1and2, frame3], [40, 20])

    def apply_animated_material_forcefield(self) -> None:
        """Renders a GIF loosely based on the behavior of the AnimatedMaterialForcefield part."""
        # tile rotates every 500 ms (_1 to _4), color rotates every 250 ms
        obj, tile = self.qud_object, self.qud_object.tile
        tile_prefix = tile.filename.rsplit('_', 1)[0][:-1]
        tile_postfix = '_' + tile.filename.rsplit('_', 1)[1]
        tile_numerals = ['1', '1', '2', '2', '3', '3', '4', '4']
        tile_colors = ['&C', '&c', '&C', '&c']
        tile_details = [None, 'K', 'c', 'C']
        forcefield_palette = obj.part_AnimatedMaterialForcefield_Color
        if forcefield_palette is not None:
            if forcefield_palette == 'Red':
                tile_colors = ['&R', '&r', '&R', '&r']
                tile_details = [None, 'r', 'r', 'r']
            elif forcefield_palette == 'Blue':
                tile_colors = ['&B', '&b', '&B', '&b']
                tile_details = [None, 'K', 'b', 'B']
        tile_colors = tile_colors + tile_colors
        tile_details = tile_details + tile_details
        frames = []
        durations = []
        for numeral, color, detail in zip(tile_numerals, tile_colors, tile_details):
            f = tile_prefix + numeral + tile_postfix  # construct filename
            frames.append(QudTile(f, color, color, detail, tile.qudname, tile.raw_transparent))
            durations.append(250)
        self._make_gif(frames, durations)

    def apply_animated_material_generic(self) -> None:
        """Renders a GIF loosely based on the behavior of the AnimatedMaterialGeneric and
        AnimatedMaterialGenericAlternate parts."""
        source_tile = self.qud_object.tile
        max_frames = 40  # set an upper limit to animation length to limit .gif size
        anim_parts = []
        if self.qud_object.part_AnimatedMaterialGeneric is not None:
            anim_parts.append(self.qud_object.part_AnimatedMaterialGeneric)
        if self.qud_object.part_AnimatedMaterialGenericAlternate is not None:
            anim_parts.append(self.qud_object.part_AnimatedMaterialGenericAlternate)

        # adjustments for particular objects
        # AnimatedMaterialGenericAlternate is often inherited from HighTechInstallation and used as the 'unpowered'
        # animation, so we don't always want to show it if we're animating an object that also has a 'powered' animation
        remove_alternate = ['Force Projector', 'GritGateChromeBeacon', 'Rodanis Y', 'Industrial Fan']
        if self.qud_object.name in remove_alternate:
            anim_parts.pop()  # ignore AnimatedMaterialGenericAlternate

        # get greatest animation length and move that animation to front of array
        max_animation_length = 60
        len1, len2 = 60, 60
        if 'AnimationLength' in anim_parts[0]:
            len1 = max_animation_length = int(anim_parts[0]['AnimationLength'])
        if len(anim_parts) == 2 and 'AnimationLength' in anim_parts[1]:
            len2 = int(anim_parts[1]['AnimationLength'])
            if len2 > max_animation_length:
                max_animation_length = int(anim_parts[1]['AnimationLength'])
                anim_parts[0], anim_parts[1] = anim_parts[1], anim_parts[0]
                len1, len2 = len2, len1

        # if necessary, calculate lowest common multiple of out-of-sync animation lengths
        total_duration = max_animation_length
        if len(anim_parts) > 1:
            total_duration = lowest_common_multiple(len1, len2)

        # extract frames from each animation
        tileframes: List[dict] = [{}, {}]
        colorframes: List[dict] = [{}, {}]
        detailframes: List[dict] = [{}, {}]
        for part, tframes, cframes, dframes in zip(anim_parts, tileframes, colorframes, detailframes):
            # set first frame to 'default' to absorb object's base render properties using special logic below
            tframes[0] = 'default'
            cframes[0] = 'default'
            dframes[0] = 'default'
            # add additional frames based on AnimatedMaterial* part
            if 'TileAnimationFrames' in part:
                parse_comma_equals_str_into_dict(part['TileAnimationFrames'], tframes)
            if 'ColorStringAnimationFrames' in part:
                parse_comma_equals_str_into_dict(part['ColorStringAnimationFrames'], cframes)
            if 'DetailColorAnimationFrames' in part:
                parse_comma_equals_str_into_dict(part['DetailColorAnimationFrames'], dframes)

        # merge animation frames until we reach total_duration or we hit the max_frames limit
        sequenced_animation = []
        tick, max_tick = -1, max_frames * 300
        frame_index, last_frame_tick, idx1, idx2 = 0, 0, 0, 0
        while tick < max_tick and tick < (total_duration - 1) and frame_index <= max_frames:
            tick += 1
            tile, color, detail = None, None, None
            idx1 = tick % len1
            idx2 = tick % len2
            if idx1 in tileframes[0]:
                tile = tileframes[0][idx1]
            if idx1 in colorframes[0]:
                color = colorframes[0][idx1]
            if idx1 in detailframes[0]:
                detail = detailframes[0][idx1]
            if idx2 in tileframes[1]:
                tile = tileframes[1][idx2]
            if idx2 in colorframes[1]:
                color = colorframes[1][idx2]
            if idx2 in detailframes[1]:
                detail = detailframes[1][idx2]
            if tile is None and color is None and detail is None:
                continue
            sequenced_animation.append((-1, tile, color, detail))
            if frame_index > 0:
                # insert duration into previous frame
                duration = tick - last_frame_tick
                prev_frame = sequenced_animation[frame_index - 1]
                sequenced_animation[frame_index - 1] = (duration, prev_frame[1], prev_frame[2], prev_frame[3])
            frame_index += 1
            last_frame_tick = tick
        # insert duration into final frame (or remove it)
        if tick == (total_duration - 1) or tick == max_tick:
            duration = tick - last_frame_tick
            last_frame = sequenced_animation[-1]
            sequenced_animation[-1] = (duration, last_frame[1], last_frame[2], last_frame[3])
        elif frame_index > max_frames:
            sequenced_animation.pop()

        finalized_tiles = []
        finalized_durations = []
        for frame in sequenced_animation:
            duration, tile, color, detail = frame
            # calculate GIF duration
            duration = (duration * (100 / 60)) // 1  # convert from game's 60fps to gif format's 100fps
            duration = duration * 10  # convert to 1000ms rate used by PIL Image
            finalized_durations.append(duration)
            # determine tile and colors for this animation frame
            tile = source_tile.filename if (tile is None or tile == 'default') else tile
            detail = source_tile.raw_detailcolor if (detail is None or detail == 'default') else detail
            # Some complexity follows: if ColorStringAnimationFrames is not specified or is 'default', the game
            # uses the Render part ColorString and does NOT touch TileColor. However, if ColorStringAnimationFrames
            # IS specified, the game will (effectively) set the specified color to BOTH ColorString and TileColor:
            animation_color_is_unspecified = (color is None or color == 'default')
            color = source_tile.colorstring if animation_color_is_unspecified else color
            tile_color = source_tile.raw_tilecolor if animation_color_is_unspecified else color
            # create tile
            qud_tile = QudTile(tile, color, tile_color, detail, source_tile.qudname, source_tile.raw_transparent)
            finalized_tiles.append(qud_tile)
        # generate GIF
        self._make_gif(finalized_tiles, finalized_durations)

    def apply_animated_material_luminous(self) -> None:
        """Renders a GIF loosely based on the behavior of the AnimatedMaterialLuminous part."""
        tile = self.qud_object.tile
        frame1and2 = QudTile(tile.filename, '&Y', None, 'C', tile.qudname, tile.raw_transparent)
        frame3 = QudTile(tile.filename, '&C', None, 'C', tile.qudname, tile.raw_transparent)
        self._make_gif([frame1and2, frame3], [40, 20])

    def apply_animated_material_mainframe_tape_drive(self) -> None:
        """Renders a GIF loosely based on the behavior of the AnimatedMaterialMainframeTapeDrive."""
        t = self.qud_object.tile
        pre = t.filename.split('-')[0][:-1]
        post = '-' + t.filename.split('-')[1]
        file1, file2, file3, file4 = f'{pre}1{post}', f'{pre}2{post}', f'{pre}3{post}', f'{pre}4{post}'
        frames: List[QudTile] = [
            QudTile(file1, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent),
            QudTile(file2, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent),
            QudTile(file3, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent),
            QudTile(file4, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent)]
        # tape drive rotates forward once every 500ms. But it also has a 1/64 chance (each) to enter RushingForward or
        # RushingBackward mode for a random duration between 15-120 frames. We have to restrain ourselves a bit to
        # keep the GIF at a manageable size. The GIF generated below is 80 frames and 926KB.
        sequence = []
        durations = []
        for cycle in range(2):  # Normal forward
            for rotation in range(4):
                sequence.append(frames[rotation])
                durations.append(500)
        for cycle in range(12):  # RushingBackward
            for rotation in [2, 1, 0, 3]:
                sequence.append(frames[rotation])
                durations.append(20)
        for cycle in range(1):  # Normal forward
            for rotation in range(4):
                sequence.append(frames[rotation])
                durations.append(500)
        for cycle in range(4):  # RushingForward
            for rotation in range(4):
                sequence.append(frames[rotation])
                durations.append(20)
        for cycle in range(1):  # Normal forward
            for rotation in range(4):
                sequence.append(frames[rotation])
                durations.append(500)
        self._make_gif(sequence, durations)

    def apply_animated_material_reality_stabilization_field(self) -> None:
        obj, tile = self.qud_object, self.qud_object.tile
        t_pre = tile.filename.rsplit('_', 1)[0][:-1]
        t_post = '_' + tile.filename.rsplit('_', 1)[1]
        tile_paths = [f'{t_pre}1{t_post}', f'{t_pre}2{t_post}', f'{t_pre}3{t_post}', f'{t_pre}4{t_post}']
        # tile_colors = ['&y^k', '&K^k', '&Y^y', '&Y^K', '&y^k']
        # tile_details = ['k', 'k', 'y', 'K', 'k']
        tile_colors = ['&y', '&K', '&Y^y', '&Y^K', '&y']
        tile_details = [None, None, 'y', 'K', None]
        color_tick_idxs = [0, 2000, 7000, 12000, 16000]
        frames = []
        durations = []
        path_idx = 0
        color_idx = 0
        prev_tick = None
        for tick in range(0, 36000, 100):
            update_frame = False
            if tick % 2400 == 0:
                path_idx = (tick // 2400) % 4
                update_frame = True
            if (tick % 18000) in color_tick_idxs:
                color_idx = color_tick_idxs.index((tick % 18000))
                update_frame = True
            if update_frame is True:
                path = tile_paths[path_idx]
                color = tile_colors[color_idx]
                detail = tile_details[color_idx]
                frames.append(QudTile(path, color, color, detail, tile.qudname, tile.raw_transparent))
                if prev_tick is not None:
                    durations[-1] = tick - prev_tick
                durations.append(0)
                prev_tick = tick
        durations[-1] = 36000 - prev_tick
        self._make_gif(frames, durations)

    def apply_animated_material_techlight(self) -> None:
        obj, tile = self.qud_object, self.qud_object.tile
        base_color = obj.part_AnimatedMaterialTechlight_baseColor
        base_color = '&c' if base_color is None else base_color
        frame1 = QudTile(tile.filename, None, base_color, 'Y', tile.qudname, tile.raw_transparent)
        frame2 = QudTile(tile.filename, None, base_color, 'C', tile.qudname, tile.raw_transparent)
        frame3 = QudTile(tile.filename, None, base_color, 'B', tile.qudname, tile.raw_transparent)
        frame4 = QudTile(tile.filename, None, base_color, 'b', tile.qudname, tile.raw_transparent)
        frame5 = QudTile(tile.filename, None, base_color, 'c', tile.qudname, tile.raw_transparent)
        frames = [
            (frame1, 650), (frame2, 10),
            (frame1, 900), (frame4, 10),
            (frame1, 750), (frame3, 10),
            (frame1, 800), (frame2, 10), (frame1, 40), (frame4, 10),
            (frame1, 1150), (frame2, 10),
            (frame1, 350), (frame5, 10),
            (frame1, 1000), (frame2, 10), (frame1, 10), (frame3, 10),
            (frame1, 200), (frame2, 10),
            (frame1, 2500), (frame5, 10),
        ]
        self._make_gif([f[0] for f in frames], [d[1] for d in frames])

    def apply_gas_animation(self) -> None:
        """Renders a GIF that replicates the behavior of the Gas part."""
        t = self.qud_object.tile
        glyph1 = StandInTiles.gas_glyph1
        glyph2 = StandInTiles.gas_glyph2
        glyph3 = StandInTiles.gas_glyph3
        glyph4 = StandInTiles.gas_glyph4
        frame1 = QudTile(None, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent, glyph1)
        frame2 = QudTile(None, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent, glyph2)
        frame3 = QudTile(None, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent, glyph3)
        frame4 = QudTile(None, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent, glyph4)
        self._make_gif([frame1, frame2, frame3, frame4], [250, 250, 250, 250])

    def apply_hologram_material(self) -> None:
        """Renders a GIF loosely based on the behavior of the HologramMaterial part.

        This particular method uses a preset algorithm, which (1) ensures we'll know when the existing wiki image
        matches, because it'll always be the same (2) is predictable and we know it'll look halfway decent.

        We could potentially also add an 'apply_hologram_material_random' method if we want to randomize the
        animation. For example, perhaps Cryptogull could apply randomized holographic animation to any tile."""
        tile = self.qud_object.tile
        glyph1 = StandInTiles.hologram_material_glyph1
        glyph2 = StandInTiles.hologram_material_glyph2
        glyph3 = StandInTiles.hologram_material_glyph3
        base = QudTile(tile.filename, '&B', '&B', 'b', tile.qudname, tile.raw_transparent)  # base most of the time
        frame2 = QudTile(tile.filename, '&C', '&C', 'c', tile.qudname, tile.raw_transparent)  # 2-4 somewhat common
        frame3 = QudTile(tile.filename, '&c', '&c', 'b', tile.qudname, tile.raw_transparent)
        frame4 = QudTile(tile.filename, '&b', '&b', 'C', tile.qudname, tile.raw_transparent)
        frame5 = QudTile(None, '&c', '&c', 'b', tile.qudname, tile.raw_transparent, glyph1)  # 5-8 less common
        frame6 = QudTile(None, '&C', '&C', 'b', tile.qudname, tile.raw_transparent, glyph2)
        frame7 = QudTile(None, '&B', '&B', 'b', tile.qudname, tile.raw_transparent, glyph3)
        frame8 = QudTile(tile.filename, '&Y', '&Y', 'b', tile.qudname, tile.raw_transparent)
        frame9 = QudTile(tile.filename, '&B', '&B', 'Y', tile.qudname, tile.raw_transparent)
        seq1 = [base, frame2, base, frame3, base, frame9, frame5, base, frame4, base, frame2, frame3, base]
        dur1 = [550, 40, 200, 40, 1100, 30, 10, 780, 40, 480, 40, 40, 900]
        seq2 = [frame2, base, frame4, base, frame2, base, frame3, base, frame8, base, frame4, base]
        dur2 = [40, 1100, 40, 850, 40, 500, 40, 1300, 40, 700, 40, 1250]
        seq3 = [frame3, base, frame2, base, frame7, frame9, base, frame4, base]
        dur3 = [40, 650, 40, 500, 10, 20, 900, 40, 350]
        self._make_gif(seq1 + seq2 + seq3, dur1 + dur2 + dur3)

    def apply_power_transmission(self) -> None:
        """Renders a GIF loosely based on the behavior of IPowerTransmission parts that have TileEffects enabled.

        To simplify things, we assume that the object is powered and unbroken, ignoring other potential variations."""
        obj, t = self.qud_object, self.qud_object.tile
        part, tile_path_start = None, None
        for partname in POWER_TRANSMISSION_PARTS:
            part = getattr(obj, f'part_{partname}')
            if part is not None and 'TileBaseFromTag' in part:
                if 'TileEffects' in part and part['TileEffects'].lower() == 'true':
                    tile_path_start = getattr(obj, f"tag_{part['TileBaseFromTag']}_Value")
                    break
        if tile_path_start is None or part is None:
            logging.error(f'Unexpectedly failed to generate .gif for "{obj.name}" - missing Tile rendering tag?')
            return
        directory = t.filename.split(tile_path_start)[0]

        # calculate tile path postfixes
        first_postfix = ''
        numeral_postfixes = []
        if 'TileAppendWhenUnbrokenAndPowered' in part:
            first_postfix += part['TileAppendWhenUnbrokenAndPowered']
        else:
            if 'TileAppendWhenPowered' in part:
                first_postfix += part['TileAppendWhenPowered']
            if 'TileAppendWhenUnbroken' in part:
                first_postfix += part['TileAppendWhenUnbroken']
        if 'TileAnimatePoweredFrames' in part:
            for num in range(1, int(part['TileAnimatePoweredFrames']) + 1):
                numeral_postfixes.append(f'_{num}')
        final_postfix = '_nsew' if TilePainter.is_painted_fence(obj) else ''
        ext = obj.tag_PaintedFenceExtension_Value
        ext = ext if ext else '.bmp'

        frame_duration = (100 // len(numeral_postfixes)) * 10  # divide frames evenly across 1000 milliseconds
        frames = []
        durations = []
        for numeral_postfix in numeral_postfixes:
            f = directory + tile_path_start + first_postfix + numeral_postfix + final_postfix + ext
            frames.append(QudTile(f, t.colorstring, t.raw_tilecolor, t.raw_detailcolor, t.qudname, t.raw_transparent))
            durations.append(frame_duration)
        self._make_gif(frames, durations)

    def apply_walltrap_animation(self) -> None:
        """Renders a GIF loosely based on the behavior of the Walltrap part."""
        tile = self.qud_object.tile
        frame1 = tile  # WarmColor
        readycolor = self.qud_object.part_Walltrap_ReadyColor
        turninterval = self.qud_object.part_Walltrap_TurnInterval
        turninterval = 3 if turninterval is None else int(turninterval)
        fore = extract_foreground_char(readycolor, 'R')
        back = extract_background_char(readycolor, 'g')
        color_string = '&' + fore + '^' + back
        tile_color = color_string
        trans_color = back
        detail_color = 'transparent'
        frame2 = QudTile(tile.filename, color_string, tile_color, detail_color, tile.qudname, trans_color)  # ReadyColor
        self._make_gif([frame1, frame2, frame1], [1600, 1200, turninterval * 1200 - 1600])

    def _make_gif(self, qud_tiles: List[QudTile], durations: List[int]) -> Image:
        """Performs the actual GIF Image creation. Resizes the supplied array of QudTile frames, and appends
        them together as a GIF Image with the specified frame durations (in milliseconds).

        Args:
            qud_tiles: The list of QudTile objects that compose this GIF animation
            durations: The list of durations for each frame in the GIF animation. You should specify durations as
                       milliseconds, but note that they actually only have one tenth of that resolution, because GIF
                       images work on a 100-tick-per-second model. For example, 50 will be internally converted to 5
        """
        frame = qud_tiles[0].get_big_image()
        next_frames: List[Image] = []
        for img in qud_tiles[1:]:
            next_frames.append(img.get_big_image())
        gif_b = BytesIO()

        # The following SHOULD work, but there's a bug with the PIL library when creating a new GIF that includes
        # transparency, which causes the GIF to have a black background, among other problems. This doesn't seem to
        # affect subsequent saves after creation, so you can use Image.save() or GifHelper.save() elsewhere in the
        # code to save this GIF instance. For example, we save the GIF in MainWindow.save_selected_tile().
        #   frame.save(gif_b,
        #              format='GIF',
        #              save_all=True,
        #              append_images=next_frames,
        #              transparency=transparency_palette_index,
        #              duration=durations,
        #              disposal=2
        #              loop=0)

        # Workaround code for transparent GIF creation:
        save_transparent_gif([frame] + next_frames, durations, gif_b)

        gif_b.seek(0)
        self._gif_image = Image.open(gif_b)


class GifHelper:

    @staticmethod
    def save(gif_image: Image, save_target):
        """Saves an existing GIF PIL Image object, ensuring that frames and animation delays are properly preserved.

        Args:
            gif_image: A GIF PIL Image object
            save_target: A filename (string), pathlib.Path object or file object. (This parameter corresponds
                         and is passed to the PIL.Image.save() method.)
        """
        durations = []
        for frame in ImageSequence.Iterator(gif_image):
            durations.append(frame.info['duration'])
        gif_image.save(save_target, format='GIF', save_all=True, duration=durations, loop=0, disposal=2)

    @staticmethod
    def get_bytes(gif_image: Image) -> bytes:
        """Converts a GIF PIL Image object to its bytes representation"""
        gif_b = BytesIO()
        GifHelper.save(gif_image, gif_b)
        return gif_b.getvalue()

    @staticmethod
    def get_bytesio(gif_image: Image) -> BytesIO:
        """Converts a GIF PIL Image object to its BytesIO representation"""
        gif_b = BytesIO()
        GifHelper.save(gif_image, gif_b)
        return gif_b
