"""Your own pictures: turns any picture into a Game Boy Advance sprite and puts
it in place of a trainer's battle picture, an overworld sprite, or a Pokémon's
front and back pictures.

The page draws the chosen picture at the right size (so any format the browser
opens works) and sends its pixels here as RGBA. This file then:
- makes the background see-through (using the picture's own transparency, or
  the colour in its corners when it has none),
- picks the best 15 colours (the GBA allows 16, and the first is see-through),
- writes a 4-bit PNG and, where the game keeps one, the .pal colour file.
Overworld sprites share their colours with other people, so their pixels are
matched to the colours that sprite already uses instead.
"""

import base64
import colorsys
import os
import re
import struct
import zlib

import fundata
from common import ROOT, read_text, write_text
from mapview import read_png, read_pal

TRAINERS_GFX = os.path.join(ROOT, 'src/data/graphics/trainers.h')
POKEMON_GFX = os.path.join(ROOT, 'src/data/graphics/pokemon.h')
OW_GFX = os.path.join(ROOT, 'src/data/object_events/object_event_graphics.h')


class PictureError(Exception):
    pass


# ---- PNG and palette files ---------------------------------------------------------

def _chunk(kind, body):
    return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)


def indexed_png(w, h, pixels, palette):
    """4-bit paletted PNG. pixels: list of rows of palette indexes (0-15)."""
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for x in range(0, w, 2):
            a = row[x]
            b = row[x + 1] if x + 1 < w else 0
            raw.append((a << 4) | b)
    plte = b''.join(bytes(c) for c in (list(palette) + [(0, 0, 0)] * 16)[:16])
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 4, 3, 0, 0, 0))
            + _chunk(b'PLTE', plte) + _chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + _chunk(b'IEND', b''))


def jasc_pal(palette):
    cols = (list(palette) + [(0, 0, 0)] * 16)[:16]
    return 'JASC-PAL\r\n0100\r\n16\r\n' + ''.join('%d %d %d\r\n' % c for c in cols)


def _png_palette(path):
    """The PLTE colours of a paletted PNG."""
    data = open(path, 'rb').read()
    pos = 8
    while pos < len(data):
        length, kind = struct.unpack('>I4s', data[pos:pos + 8])
        if kind == b'PLTE':
            body = data[pos + 8:pos + 8 + length]
            return [tuple(body[i:i + 3]) for i in range(0, len(body) - 2, 3)]
        pos += 12 + length
    return []


def _write_bytes(path, data):
    tmp = path + '.editor-tmp'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, path)


# ---- colours -----------------------------------------------------------------------

def _gba(c):
    """Rounds a colour to what the GBA can show (5 bits per channel)."""
    return tuple(min(248, (v + 4) & 0xF8) for v in c[:3])


def decode_rgba(data_b64, w, h):
    raw = base64.b64decode(data_b64)
    if len(raw) != w * h * 4:
        raise PictureError('The picture did not come through whole. Try again.')
    px = [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4)]
    return [px[y * w:(y + 1) * w] for y in range(h)]


def _see_through(rows):
    """Marks background pixels as see-through. Returns rows of colour or None."""
    w, h = len(rows[0]), len(rows)
    has_alpha = any(p[3] < 250 for r in rows for p in r)
    if has_alpha:
        return [[(p[0], p[1], p[2]) if p[3] >= 128 else None for p in r] for r in rows]
    corners = [rows[0][0], rows[0][w - 1], rows[h - 1][0], rows[h - 1][w - 1]]
    bg = max(set(c[:3] for c in corners), key=lambda c: sum(1 for k in corners if k[:3] == c))

    def near(p):
        return sum(abs(p[i] - bg[i]) for i in range(3)) < 24
    # Flood fill from the edges, so the same colour inside the picture stays.
    out = [[(p[0], p[1], p[2]) for p in r] for r in rows]
    seen = set()
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if out[y][x] is None or not near(rows[y][x]):
            continue
        out[y][x] = None
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return out


def _median_cut(colors, n):
    """colors: {rgb: count}. Returns up to n colours."""
    boxes = [list(colors.items())]
    while len(boxes) < n:
        boxes.sort(key=lambda b: max(max(c[0][i] for c in b) - min(c[0][i] for c in b) for i in range(3)) if len(b) > 1 else -1)
        box = boxes.pop()
        if len(box) < 2:
            boxes.append(box)
            break
        ch = max(range(3), key=lambda i: max(c[0][i] for c in box) - min(c[0][i] for c in box))
        box.sort(key=lambda c: c[0][ch])
        total = sum(c[1] for c in box)
        acc, cut = 0, 1
        for i, c in enumerate(box):
            acc += c[1]
            if acc >= total / 2:
                cut = max(1, min(len(box) - 1, i + 1))
                break
        boxes.extend([box[:cut], box[cut:]])
    out = []
    for b in boxes:
        total = sum(c[1] for c in b) or 1
        out.append(_gba(tuple(sum(c[0][i] * c[1] for c in b) // total for i in range(3))))
    uniq = []
    for c in out:
        if c not in uniq:
            uniq.append(c)
    return uniq


def _nearest(c, palette, start=1):
    best, bi = None, start
    for i in range(start, len(palette)):
        p = palette[i]
        # weighted distance: eyes notice green most
        d = 2 * (c[0] - p[0]) ** 2 + 4 * (c[1] - p[1]) ** 2 + 3 * (c[2] - p[2]) ** 2
        if best is None or d < best:
            best, bi = d, i
    return bi


def quantize(images, background=(152, 208, 160)):
    """images: list of rows (colour or None). One shared palette of 16 for all.
    Returns (palette, [index rows per image])."""
    counts = {}
    for rows in images:
        for r in rows:
            for p in r:
                if p is not None:
                    g = _gba(p)
                    counts[g] = counts.get(g, 0) + 1
    if not counts:
        raise PictureError('The picture is empty (everything is see-through).')
    palette = [_gba(background)] + _median_cut(counts, 15)
    palette = palette[:16]
    out = []
    cache = {}
    for rows in images:
        idx = []
        for r in rows:
            line = []
            for p in r:
                if p is None:
                    line.append(0)
                    continue
                g = _gba(p)
                if g not in cache:
                    cache[g] = _nearest(g, palette)
                line.append(cache[g])
            idx.append(line)
        out.append(idx)
    return palette, out


def map_to_palette(rows, palette):
    cache = {}
    out = []
    for r in rows:
        line = []
        for p in r:
            if p is None:
                line.append(0)
                continue
            if p not in cache:
                cache[p] = _nearest(p, palette)
            line.append(cache[p])
        out.append(line)
    return out


def shiny_palette(palette):
    """A shiny version: every colour's hue turned a little, like the games do."""
    out = [palette[0]]
    for c in palette[1:]:
        h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in c))
        if s < 0.12:  # greys and outlines stay
            out.append(c)
            continue
        r, g, b = colorsys.hls_to_rgb((h + 0.17) % 1.0, l, min(1.0, s * 1.05))
        out.append(_gba((int(r * 255), int(g * 255), int(b * 255))))
    return out


def preview_png(w, h, idx, palette):
    """An RGB preview as a data: URL (see-through shown as the palette's first colour)."""
    return 'data:image/png;base64,' + base64.b64encode(with_alpha(indexed_png(w, h, idx, palette))).decode()


def with_alpha(png):
    from pngutil import with_transparent_background
    return with_transparent_background(png)


# ---- where each picture lives --------------------------------------------------------

def _trainer_target(pic_const):
    gfx = read_text(TRAINERS_GFX)
    m = re.search(r'\[' + re.escape(pic_const) + r'\]\s*=\s*\{\s*\.frontPic\s*=\s*TRAINER_FRONT_PIC\((\w+),\s*(\w+)\)', gfx)
    if not m:
        raise PictureError('Could not find that battle picture.')
    pic_sym, pal_sym = m.group(1), m.group(2)
    png = re.search(re.escape(pic_sym) + r'\[\]\s*=\s*INCGFX_U32\("([^"]+)"', gfx)
    pal = re.search(re.escape(pal_sym) + r'\[\]\s*=\s*INCGFX_U16\("([^"]+)"', gfx)
    if not png or not pal:
        raise PictureError('Could not find the files for that battle picture.')
    shared = re.search(r'TRAINER_BACK_PIC\([^)]*\b' + re.escape(pal_sym) + r'\b', gfx)
    return png.group(1), pal.group(1), bool(shared)


def _species_target(species):
    block = None
    for path in sorted(os.listdir(os.path.join(ROOT, 'src/data/pokemon/species_info'))):
        text = read_text(os.path.join(ROOT, 'src/data/pokemon/species_info', path))
        m = re.search(r'\[' + re.escape(species) + r'\]\s*=', text)
        if m:
            nxt = re.search(r'\n\s*\[SPECIES_\w+\]\s*=', text[m.end():])
            block = text[m.end():m.end() + (nxt.start() if nxt else len(text))]
            break
    if block is None:
        raise PictureError('Could not find that Pokémon.')
    syms = {}
    for key in ('frontPic', 'backPic', 'palette', 'shinyPalette'):
        s = re.search(r'\.' + key + r'\s*=\s*(\w+)', block)
        if not s:
            raise PictureError('This Pokémon shares its pictures with another form, so its pictures cannot be changed here.')
        syms[key] = s.group(1)
    gfx = read_text(POKEMON_GFX)
    gba = fundata.config_value('P_GBA_STYLE_SPECIES_GFX') != 0
    paths = {}
    for key, sym in syms.items():
        found = re.findall(re.escape(sym) + r'\[\]\s*=\s*INCGFX_U(?:32|16)\("([^"]+)"', gfx)
        if not found:
            raise PictureError('Could not find the files for this Pokémon.')
        # With both a modern and a GBA-style file, use the one the game uses now.
        pick = [f for f in found if ('_gba' in f) == gba] or found
        paths[key] = pick[0]
    return paths


def _ow_target(gfx_const):
    import gamedata
    ow = next((o for o in gamedata.load()['overworld'] if o['const'] == gfx_const), None)
    if not ow:
        raise PictureError('Could not find that overworld sprite.')
    return ow


def info(kind, target):
    """Sizes the page should draw the picture at."""
    if kind == 'trainer':
        png, _pal, shared = _trainer_target(target)
        w, h, _ = read_png(os.path.join(ROOT, png))
        return {'w': w, 'h': h, 'current': png, 'shared': shared,
                'note': 'Battle pictures are %d×%d pixels.' % (w, h)}
    if kind == 'pokemon':
        p = _species_target(target)
        w, h, _ = read_png(os.path.join(ROOT, p['frontPic']))
        return {'w': w, 'h': w, 'frames': h // w, 'current': p['frontPic'], 'back': p['backPic'],
                'note': 'Pokémon pictures are %d×%d pixels. The back picture is optional: without one, the front picture is used, turned around.' % (w, w)}
    if kind == 'overworld':
        ow = _ow_target(target)
        w, h, _ = read_png(os.path.join(ROOT, ow['img']))
        return {'w': ow['w'], 'h': ow['h'], 'sheetW': w, 'sheetH': h, 'current': ow['img'],
                'note': ('Overworld sprites are %d×%d pixels per pose. One picture is used for every pose. '
                         'A full sheet of %d×%d pixels (every pose side by side, like the current one) keeps each pose.'
                         % (ow['w'], ow['h'], w, h))}
    raise PictureError('Unknown kind of picture.')


def _flip(rows):
    return [list(reversed(r)) for r in rows]


def convert(body, save=False):
    kind, target = body.get('kind'), body.get('target', '')
    meta = info(kind, target)
    front = _see_through(decode_rgba(body['front'], int(body['w']), int(body['h'])))
    if kind == 'trainer':
        png, pal, shared = _trainer_target(target)
        if shared and save:
            raise PictureError("This is the player's picture. Its colours are shared with the back picture used in battle, "
                               'so it cannot be replaced here. Pick another battle picture.')
        # Most battle pictures take their colours from the PNG itself; a few have a .pal file.
        pal_full = os.path.join(ROOT, pal)
        bg = (_png_palette(pal_full) or [(152, 208, 160)])[0] if pal.endswith('.png') else read_pal(pal_full)[0]
        palette, (idx,) = quantize([front], bg)
        out = {'preview': preview_png(meta['w'], meta['h'], idx, palette)}
        if save:
            _write_bytes(os.path.join(ROOT, png), indexed_png(meta['w'], meta['h'], idx, palette))
            if pal.endswith('.pal'):
                write_text(pal_full, jasc_pal(palette))
            elif pal != png:
                _write_bytes(pal_full, indexed_png(meta['w'], meta['h'], idx, palette))
        return out
    if kind == 'pokemon':
        p = _species_target(target)
        size = meta['w']
        back = _see_through(decode_rgba(body['back'], size, size)) if body.get('back') else _flip(front)
        bg = read_pal(os.path.join(ROOT, p['palette']))[0]
        palette, (fidx, bidx) = quantize([front, back], bg)
        frames = max(1, meta.get('frames', 1))
        sheet = [row for _ in range(frames) for row in fidx]
        out = {'preview': preview_png(size, size, fidx, palette), 'previewBack': preview_png(size, size, bidx, palette),
               'previewShiny': preview_png(size, size, fidx, shiny_palette(palette))}
        if save:
            _write_bytes(os.path.join(ROOT, p['frontPic']), indexed_png(size, size * frames, sheet, palette))
            _write_bytes(os.path.join(ROOT, p['backPic']), indexed_png(size, size, bidx, palette))
            write_text(os.path.join(ROOT, p['palette']), jasc_pal(palette))
            write_text(os.path.join(ROOT, p['shinyPalette']), jasc_pal(shiny_palette(palette)))
        return out
    if kind == 'overworld':
        ow = _ow_target(target)
        path = os.path.join(ROOT, ow['img'])
        palette = [tuple(c) for c in _png_palette(path)]
        if len(palette) < 2:
            raise PictureError('This sprite has no colour list to match.')
        fw, fh = int(body['w']), int(body['h'])
        idx = map_to_palette(front, palette)
        sw, sh = meta['sheetW'], meta['sheetH']
        if (fw, fh) == (sw, sh):
            sheet = idx
        elif (fw, fh) == (meta['w'], meta['h']):
            per_row = max(1, sw // fw)
            sheet = [[idx[y % fh][x % fw] for x in range(per_row * fw)] + [0] * (sw - per_row * fw) for y in range(sh)]
        else:
            raise PictureError('The picture is the wrong size.')
        out = {'preview': preview_png(fw, fh, idx, palette)}
        if save:
            _write_bytes(path, indexed_png(sw, sh, sheet, palette))
        return out
    raise PictureError('Unknown kind of picture.')
