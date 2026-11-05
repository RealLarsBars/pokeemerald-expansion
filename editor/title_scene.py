"""Game of Thrones title screen: a dragon burning a castle while two armies charge, in place
of Rayquaza. Drawn with Pillow (dev-time only, `python3 title_scene.py`), saved as
fun/title/thrones_scene.png (tiles) and thrones_scene.bin (tilemap). The game only needs those.

Colors are indices into the title screen's sky palette (rayquaza_and_clouds.pal), which the
Thrones theme sets in title_screen.py: 4-10 the sky from glowing red (low) to near black (high),
11 the darkest shadow, 12 pale flame, 14 red, 13 white, 15 the color the game makes pulse.
"""
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PNG = os.path.join(HERE, 'fun', 'title', 'thrones_scene.png')
BIN = os.path.join(HERE, 'fun', 'title', 'thrones_scene.bin')
BASE_PNG = os.path.join(ROOT, 'graphics', 'title_screen', 'rayquaza.png')
BASE_BIN = os.path.join(ROOT, 'graphics', 'title_screen', 'rayquaza.bin')
SHADOW, FLAME, WHITE, RED, PULSE, EMBER = 11, 12, 13, 14, 15, 3


def _sky():
    """The base game's sky bands (with their dithering), one tile per row, 240x160."""
    from PIL import Image
    im = Image.open(BASE_PNG)
    e = struct.unpack('<1024H', open(BASE_BIN, 'rb').read())
    sky = Image.new('P', (240, 160), 0)
    for r in range(20):
        x = e[r * 32]
        t = x & 0x3ff
        tile = im.crop(((t % 16) * 8, (t // 16) * 8, (t % 16) * 8 + 8, (t // 16) * 8 + 8))
        if x & 0x800:
            tile = tile.transpose(Image.FLIP_TOP_BOTTOM)
        for c in range(30):
            sky.paste(tile, (c * 8, r * 8))
    return sky


def draw():
    from PIL import ImageDraw
    im = _sky()
    d = ImageDraw.Draw(im)
    # Smoke from the burning castle, drifting left.
    for (x, y, rx, ry) in [(196, 70, 22, 9), (178, 60, 20, 8), (156, 52, 18, 7), (205, 84, 16, 8)]:
        d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=10)
    # Far hills.
    d.polygon([(0, 132), (40, 122), (90, 128), (140, 118), (200, 124), (240, 116), (240, 160), (0, 160)], fill=9)
    # The castle on its rock, right side.
    d.polygon([(132, 160), (146, 128), (240, 120), (240, 160)], fill=SHADOW)
    d.rectangle((152, 104, 232, 130), fill=SHADOW)  # curtain wall
    for x in range(152, 233, 8):                      # battlements
        d.rectangle((x, 100, x + 4, 104), fill=SHADOW)
    for (x0, x1, top) in [(146, 160, 84), (190, 204, 74), (222, 236, 88)]:  # towers
        d.rectangle((x0, top, x1, 130), fill=SHADOW)
        for x in range(x0, x1 + 1, 5):
            d.rectangle((x, top - 4, x + 2, top), fill=SHADOW)
    d.polygon([(193, 62), (197, 46), (201, 62)], fill=SHADOW)  # spire
    d.line((197, 46, 197, 38), fill=SHADOW)
    d.polygon([(198, 38), (206, 41), (198, 44)], fill=RED)     # banner
    for (x, y) in [(152, 96), (196, 88), (228, 100), (170, 114), (214, 114)]:  # lit windows
        d.rectangle((x, y, x + 1, y + 3), fill=FLAME)
    # The main tower is on fire.
    for (pts, c) in [([(186, 74), (190, 56), (194, 66), (198, 50), (202, 64), (206, 54), (208, 74)], RED),
                     ([(189, 74), (193, 62), (197, 70), (200, 58), (204, 74)], EMBER),
                     ([(193, 74), (197, 64), (201, 74)], FLAME)]:
        d.polygon(pts, fill=c)
    # The dragon, diving in from the left.
    d.polygon([(30, 92), (52, 84), (78, 82), (98, 86), (104, 92), (90, 98), (62, 100), (40, 99)], fill=SHADOW)  # body
    d.polygon([(98, 86), (110, 80), (120, 78), (126, 80), (118, 86), (104, 92)], fill=SHADOW)  # neck
    d.polygon([(118, 76), (132, 76), (140, 80), (132, 83), (122, 85)], fill=SHADOW)  # head
    d.polygon([(122, 76), (118, 70), (126, 75)], fill=SHADOW)  # horn
    d.point((128, 78), fill=PULSE)  # glowing eye
    d.polygon([(30, 92), (14, 98), (2, 108), (10, 106), (22, 100), (36, 97)], fill=SHADOW)  # tail
    d.polygon([(2, 108), (0, 114), (8, 108)], fill=SHADOW)
    # Wings: one up, one down, scalloped.
    d.polygon([(56, 86), (60, 56), (70, 40), (78, 50), (84, 46), (90, 58), (96, 56), (88, 84)], fill=SHADOW)
    d.polygon([(62, 86), (52, 60), (44, 52), (46, 66), (38, 64), (46, 80)], fill=SHADOW)
    d.polygon([(60, 98), (56, 112), (64, 108), (68, 116), (74, 104), (80, 98)], fill=SHADOW)
    # Dragon fire, a widening cone from the jaws to the castle wall.
    d.polygon([(138, 80), (152, 78), (168, 82), (184, 94), (180, 108), (164, 104), (150, 92), (139, 84)], fill=RED)
    d.polygon([(139, 81), (154, 81), (168, 87), (178, 98), (172, 102), (158, 92), (141, 84)], fill=FLAME)
    d.polygon([(140, 82), (156, 84), (168, 92), (160, 90), (142, 83)], fill=WHITE)
    for (x, y, r) in [(176, 108, 4), (184, 104, 3), (168, 112, 3), (186, 112, 2)]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=RED)
        d.point((x, y), fill=FLAME)
    # Two armies charging across the field below.
    d.polygon([(0, 140), (60, 134), (130, 140), (150, 160), (0, 160)], fill=SHADOW)
    for x in range(4, 70, 5):  # spears and helmets of the left army
        h = 8 + (x * 7) % 5
        d.line((x, 140 - h, x, 140), fill=SHADOW)
        d.ellipse((x - 2, 136, x + 2, 140), fill=SHADOW)
    for x in range(80, 140, 5):  # the castle's defenders
        h = 7 + (x * 3) % 4
        d.line((x + 2, 137 - h, x, 140), fill=SHADOW)
        d.ellipse((x - 2, 135, x + 2, 139), fill=SHADOW)
    for (x, c) in [(20, RED), (44, FLAME), (96, RED), (120, FLAME)]:  # banners
        d.line((x, 118, x, 136), fill=SHADOW)
        d.rectangle((x + 1, 118, x + 6, 123), fill=c)
    return im


def save():
    """Cuts the scene into tiles (with flips) and writes the png and tilemap."""
    from PIL import Image
    scene = draw()
    tiles, keys, entries = [bytes(64)], {bytes(64): (0, 0)}, []
    for r in range(32):
        for c in range(32):
            if r >= 20 or c >= 30:
                entries.append(0)
                continue
            t = bytes(scene.crop((c * 8, r * 8, c * 8 + 8, r * 8 + 8)).tobytes())
            if t not in keys:
                n = len(tiles)
                tiles.append(t)
                rows = [t[i * 8:i * 8 + 8] for i in range(8)]
                for flip, rr in [(0, rows), (0x400, [x[::-1] for x in rows]), (0x800, rows[::-1]),
                                 (0xC00, [x[::-1] for x in rows[::-1]])]:
                    keys.setdefault(b''.join(rr), (n, flip))
            n, flip = keys[t]
            entries.append(n | flip | (14 << 12))
    assert len(tiles) <= 256, len(tiles)
    sheet = Image.new('P', (128, 128), 0)
    sheet.putpalette(Image.open(BASE_PNG).getpalette()[:48])
    for i, t in enumerate(tiles):
        tile = Image.frombytes('P', (8, 8), t)
        sheet.paste(tile, ((i % 16) * 8, (i // 16) * 8))
    sheet.save(PNG, bits=4)
    with open(BIN, 'wb') as f:
        f.write(struct.pack('<1024H', *entries))
    return len(tiles)


if __name__ == '__main__':
    print(save(), 'tiles')
