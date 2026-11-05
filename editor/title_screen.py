"""A title screen for each comedy theme.

Swaps the "EMERALD VERSION" banner for the theme's own name and recolors the sky
behind RAYQUAZA. Only two files change, and resetting Fun Modes puts them back.
"""
import io
import os

from common import ROOT

BANNER = 'graphics/title_screen/emerald_version.png'
SKY = 'graphics/title_screen/rayquaza_and_clouds.pal'

FONTS = {
    'serif': ['/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
              'C:/Windows/Fonts/georgiab.ttf', 'C:/Windows/Fonts/timesbd.ttf'],
    'sans': ['/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/impact.ttf'],
}

# Per theme: the big word on the banner, its font, the banner's 16 colors
# (index 0 is see-through) and the sky's 16 colors (same order as the original file).
TITLES = {
    'thrones': {
        'word': 'THRONES', 'font': 'serif',
        # Gold letters with a near-black edge.
        'banner': [(255, 74, 238), (214, 160, 40), (120, 70, 10), (255, 214, 90), (24, 8, 8),
                   (90, 50, 10), (255, 232, 140), (50, 20, 10), (230, 180, 60), (140, 90, 20),
                   (240, 196, 72), (190, 130, 30), (248, 220, 110), (170, 110, 25), (60, 20, 20),
                   (255, 248, 210)],
        # Fire and blood: the green sky turns ember red, fading to near black.
        'sky': [(189, 106, 8), (139, 16, 0), (255, 255, 255), (172, 40, 16), (156, 32, 16),
                (139, 24, 16), (123, 16, 16), (106, 8, 16), (90, 8, 16), (74, 8, 16), (57, 0, 16),
                (41, 0, 8), (255, 200, 120), (255, 255, 255), (255, 0, 0), (41, 0, 8)],
    },
    'madlibs': {
        'word': 'MAD LIBS', 'font': 'sans',
        # Hot pink letters with a purple edge.
        'banner': [(0, 255, 0), (255, 120, 200), (150, 20, 110), (255, 190, 230), (40, 0, 60),
                   (110, 10, 90), (255, 220, 245), (70, 0, 70), (255, 150, 215), (190, 40, 150),
                   (255, 170, 222), (230, 80, 180), (255, 205, 238), (210, 60, 165), (80, 0, 80),
                   (255, 255, 255)],
        # A candy sky: yellow at the top, through orange and pink, to purple.
        'sky': [(189, 106, 8), (230, 90, 160), (255, 255, 255), (255, 210, 60), (255, 180, 50),
                (255, 150, 60), (255, 120, 90), (240, 90, 130), (210, 70, 160), (170, 60, 180),
                (130, 50, 190), (90, 40, 150), (255, 240, 170), (255, 255, 255), (255, 0, 0),
                (90, 40, 150)],
    },
}


def _font(kind, size):
    from PIL import ImageFont
    for path in FONTS[kind]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _word_mask(word, kind, max_w, max_h):
    """The word as a black-and-white picture, as big as fits in max_w x max_h."""
    from PIL import Image, ImageDraw
    for size in range(40, 6, -1):
        font = _font(kind, size)
        x0, y0, x1, y1 = font.getbbox(word)
        if x1 - x0 <= max_w and y1 - y0 <= max_h:
            img = Image.new('L', (x1 - x0, y1 - y0), 0)
            ImageDraw.Draw(img).text((-x0, -y0), word, font=font, fill=255)
            return img.point(lambda v: 255 if v >= 110 else 0)
    raise ValueError('word does not fit')


def _draw(opx, mask, ox, oy, w, h, shades):
    m = mask.load()
    mw, mh = mask.size
    inside = lambda x, y: 0 <= x < mw and 0 <= y < mh and m[x, y]  # noqa: E731
    # A dark edge and a drop shadow first, then the letters, light at the top, darker below.
    for y in range(-2, mh + 2):
        for x in range(-2, mw + 2):
            X, Y = ox + x, oy + y
            if not (0 <= X < w and 0 <= Y < h) or inside(x, y):
                continue
            near = any(inside(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            if near or inside(x - 1, y - 2) or inside(x, y - 2):
                opx[X, Y] = 4
    for y in range(mh):
        for x in range(mw):
            if m[x, y] and 0 <= ox + x < w and 0 <= oy + y < h:
                opx[ox + x, oy + y] = shades[min(len(shades) - 1, y * len(shades) // max(1, mh))]


def make_banner(key):
    """Draws the theme's banner with Pillow. Only needed when changing the design:
    the finished pictures are saved in fun/title/, so the editor itself never needs Pillow."""
    from PIL import Image
    t = TITLES[key]
    w, h = 128, 32
    left, right = 4, 108  # where the original banner sits, under the POKéMON logo
    out = Image.new('P', (w, h), 0)
    opx = out.load()
    word = _word_mask(t['word'], t['font'], right - left - 4, 16)
    _draw(opx, word, left + (right - left - word.size[0]) // 2, 1, w, h, [15, 6, 3, 12, 10, 8])
    ver = _word_mask('VERSION', 'sans', 70, 10)
    _draw(opx, ver, left + (right - left - ver.size[0]) // 2, 20, w, h, [15, 3, 10])
    pal = []
    for c in t['banner']:
        pal += list(c)
    out.putpalette(pal)
    buf = io.BytesIO()
    out.save(buf, format='PNG')
    return buf.getvalue()


TITLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fun', 'title')


def banner_png(key):
    with open(os.path.join(TITLE_DIR, key + '_banner.png'), 'rb') as f:
        return f.read()


def sky_pal(key):
    lines = ['JASC-PAL', '0100', '16'] + ['%d %d %d' % c for c in TITLES[key]['sky']]
    return '\r\n'.join(lines) + '\r\n'


def apply(ov, key):
    if key not in TITLES:
        return []
    ov.write_bytes(BANNER, banner_png(key))
    ov.write(SKY, sky_pal(key))
    return ['Title screen: %s VERSION banner and a new sky' % TITLES[key]['word']]


if __name__ == '__main__':
    # Redraw the saved banners: python3 title_screen.py
    os.makedirs(TITLE_DIR, exist_ok=True)
    for k in TITLES:
        with open(os.path.join(TITLE_DIR, k + '_banner.png'), 'wb') as f:
            f.write(make_banner(k))
        print('wrote', k)
