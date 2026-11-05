"""A tiny pixel-art kit for the Thrones sprites (dev-time only, needs Pillow).

Shapes are drawn one by one, each with its own shading (light from the upper left) and a dark
line where it meets other shapes. The outside edge of the whole figure gets a near-black outline,
the way Gen 3 sprites look. Hand-drawn parts (faces, hair, crowns) are text grids, one letter
per pixel. `to_indexed` turns the result into a 16-color GBA picture.
"""
import colorsys

OUTLINE = (24, 20, 28)
BG = (115, 197, 164)


def ramp(rgb, spread=1.0):
    """Light, mid, shade and line tones from one base color."""
    r, g, b = [c / 255 for c in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    def tone(dv, ds, dh=0.0):
        rr, gg, bb = colorsys.hsv_to_rgb((h + dh) % 1, min(1, max(0, s + ds)), min(1, max(0, v + dv)))
        return (round(rr * 255), round(gg * 255), round(bb * 255))
    return {'hi': tone(0.16 * spread, -0.12 * spread, -0.01), 'mid': tuple(rgb),
            'lo': tone(-0.2 * spread, 0.1 * spread, 0.02), 'line': tone(-0.42 * spread, 0.18 * spread, 0.03)}


class Canvas:
    def __init__(self, w=64, h=64):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]

    def _mask(self, draw_fn):
        from PIL import Image, ImageDraw
        m = Image.new('1', (self.w, self.h), 0)
        draw_fn(ImageDraw.Draw(m))
        data = m.load()
        return {(x, y) for y in range(self.h) for x in range(self.w) if data[x, y]}

    def fill(self, mask, rp, shade=True, line=True, light=True, cut=0.66):
        """Paints a set of pixels with a ramp, rounded like a cylinder lit from the upper left:
        the right third in shade, a lit strip on the left, and a line around the edge."""
        spans = {}
        for (x, y) in mask:
            lo, hi = spans.get(y, (x, x))
            spans[y] = (min(lo, x), max(hi, x))
        for (x, y) in mask:
            c = rp['mid']
            x0, x1 = spans[y]
            w = x1 - x0
            if shade and (x >= x0 + cut * w + 0.5 or (x, y + 2) not in mask and w > 2):
                c = rp['lo']
            elif light and w >= 4 and x <= x0 + max(1, 0.2 * w) and (x, y - 1) in mask:
                c = rp['hi']
            elif light and (x, y - 1) not in mask and (x + 2, y) in mask and x < x0 + 0.6 * w:
                c = rp['hi']
            if line and any(n not in mask for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                c = rp['line']
            self.px[y][x] = c

    def poly(self, pts, rp, **kw):
        m = self._mask(lambda d: d.polygon(pts, fill=1))
        self.fill(m, rp, **kw)
        return m

    def ellipse(self, box, rp, **kw):
        m = self._mask(lambda d: d.ellipse(box, fill=1))
        self.fill(m, rp, **kw)
        return m

    def rect(self, box, rp, **kw):
        m = self._mask(lambda d: d.rectangle(box, fill=1))
        self.fill(m, rp, **kw)
        return m

    def line(self, pts, color, width=1):
        m = self._mask(lambda d: d.line(pts, fill=1, width=width))
        for (x, y) in m:
            self.px[y][x] = color

    def dot(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = color

    def grid(self, art, x0, y0, colors):
        """Paints a text grid. '.' and ' ' are skipped; other letters look up `colors`."""
        rows = art.strip('\n').split('\n')
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in '. ':
                    continue
                if ch == '_':
                    self.dot(x0 + x, y0 + y, None)
                    continue
                self.dot(x0 + x, y0 + y, colors[ch])

    def recolor(self, where, mapping):
        """Swaps colors (old: new) on pixels where `where(x, y)` is true."""
        for y in range(self.h):
            for x in range(self.w):
                c = self.px[y][x]
                if c in mapping and where(x, y):
                    self.px[y][x] = mapping[c]

    def flip(self):
        for row in self.px:
            row.reverse()

    def outline(self, color=OUTLINE):
        """Near-black edge wherever the figure meets the background."""
        out = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is None:
                    continue
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not (0 <= nx < self.w and 0 <= ny < self.h) or self.px[ny][nx] is None:
                        out.append((x, y))
                        break
        for x, y in out:
            self.px[y][x] = color

    def colors(self):
        seen = {}
        for row in self.px:
            for c in row:
                if c is not None:
                    seen[c] = seen.get(c, 0) + 1
        return seen


def _dist(a, b):
    return sum((p - q) ** 2 for p, q in zip(a, b))


def reduce_colors(canvas, limit=15, keep=(OUTLINE,)):
    """Merges the closest pair of colors (the rarer one into the commoner) until `limit` remain."""
    counts = canvas.colors()
    mapping = {c: c for c in counts}
    while len(counts) > limit:
        best = None
        cols = list(counts)
        for i, a in enumerate(cols):
            for b in cols[i + 1:]:
                d = _dist(a, b)
                if best is None or d < best[0]:
                    best = (d, a, b)
        _, a, b = best
        if a in keep or (counts[a] >= counts[b] and b not in keep):
            src, dst = b, a
        else:
            src, dst = a, b
        counts[dst] += counts.pop(src)
        for k, v in mapping.items():
            if v == src:
                mapping[k] = dst
    for row in canvas.px:
        for x, c in enumerate(row):
            if c is not None:
                row[x] = mapping[c]
    return sorted(counts, key=lambda c: sum(c))


def to_indexed(canvas, bg=BG):
    """A 16-color paletted image, index 0 = background (see-through in game)."""
    from PIL import Image
    cols = reduce_colors(canvas)
    pal = [bg] + cols
    pal += [(0, 0, 0)] * (16 - len(pal))
    idx = {c: i for i, c in enumerate(pal) if i}
    im = Image.new('P', (canvas.w, canvas.h), 0)
    im.putpalette([v for c in pal for v in c])
    for y, row in enumerate(canvas.px):
        for x, c in enumerate(row):
            if c is not None:
                im.putpixel((x, y), idx[c])
    return im


def gba_color(c):
    """What the GBA will actually show (5 bits per channel)."""
    return tuple((v >> 3) << 3 for v in c)
