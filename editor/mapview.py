"""Maps: draws every map as a picture (from its tilesets, the way the game does)
and edits what is placed on it: item balls and hidden items. Also lists the
people, trainers and warps on each map so the page can show them.

Only the values that change are written; map.json files are saved with the
same layout (two-space JSON) the project already uses."""

import json
import os
import re
import struct
import threading
import zlib

from common import ROOT, map_display_name, project_path, read_text, write_text

LAYOUTS = os.path.join(ROOT, 'data/layouts/layouts.json')
MAP_GROUPS = os.path.join(ROOT, 'data/maps/map_groups.json')
FLAGS_H = os.path.join(ROOT, 'include/constants/flags.h')
ITEM_BALL_GFX = 'OBJ_EVENT_GFX_ITEM_BALL'
FIND_ITEM = 'Common_EventScript_FindItem'
MAX_OBJECTS = 64
HIDDEN_ITEMS_START = 0x1F4

# How many tiles, metatiles and palettes the primary tileset owns.
SPLIT = {'emerald': (512, 512, 6), 'frlg': (640, 640, 7)}


class MapError(Exception):
    pass


# ---- reading the game's picture files ------------------------------------------------------

def read_png(path):
    """(width, height, rows) for a paletted or grayscale PNG; rows hold one
    palette index per pixel. Enough of PNG for the game's tile sheets."""
    data = open(path, 'rb').read()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise MapError('not a PNG: ' + path)
    pos, idat, w = 8, [], 0
    while pos < len(data):
        length, kind = struct.unpack('>I4s', data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b'IHDR':
            w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', body)
        elif kind == b'IDAT':
            idat.append(body)
        elif kind == b'IEND':
            break
        pos += 12 + length
    if ctype not in (0, 3) or interlace:
        raise MapError('unsupported PNG: ' + path)
    raw = zlib.decompress(b''.join(idat))
    stride = (w * depth + 7) // 8
    bpp = max(1, depth // 8)
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        if depth == 8:
            rows.append(bytes(line))
        elif depth == 4:
            rows.append(bytes(v for byte in line for v in (byte >> 4, byte & 15))[:w])
        elif depth == 2:
            rows.append(bytes(v for byte in line for v in (byte >> 6, (byte >> 4) & 3, (byte >> 2) & 3, byte & 3))[:w])
        else:
            rows.append(bytes(v for byte in line for v in ((byte >> s) & 1 for s in range(7, -1, -1)))[:w])
    return w, h, rows


def write_png(w, h, rgb_rows):
    raw = b''.join(b'\x00' + r for r in rgb_rows)

    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def read_pal(path):
    try:
        lines = read_text(path).split('\n')
    except OSError:
        return [(0, 0, 0)] * 16
    cols = []
    for l in lines[3:]:
        parts = l.split()
        if len(parts) >= 3:
            cols.append(tuple(int(p) & 0xF8 for p in parts[:3]))
    return (cols + [(0, 0, 0)] * 16)[:16]


# ---- tilesets ----------------------------------------------------------------------------

_TS_INDEX = None


def _tileset_index():
    """gTileset_X -> {'dir': folder with tiles.png, palettes/, metatiles.bin}."""
    global _TS_INDEX
    if _TS_INDEX is not None:
        return _TS_INDEX
    srcs = ''
    for rel in ('src/graphics.c', 'src/data/tilesets/graphics.h', 'src/data/tilesets/metatiles.h',
                'src/data/tilesets/headers.h'):
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            srcs += read_text(p) + '\n'
    sym_dir = {}
    for m in re.finditer(r'(gTilesetTiles_\w+|gMetatiles_\w+)\s*\[\]\s*=\s*\w+\(\s*"([^"]+)"', srcs):
        sym_dir[m.group(1)] = os.path.dirname(m.group(2))
    for m in re.finditer(r'(gTilesetPalettes_\w+)\s*\[\]\[16\]\s*=\s*\{\s*\w+\(\s*"([^"]+)"', srcs):
        sym_dir[m.group(1)] = os.path.dirname(m.group(2))
    out = {}
    for m in re.finditer(r'const struct Tileset (gTileset_\w+)\s*=\s*\{(.*?)\};', srcs, re.S):
        body = m.group(2)
        get = lambda k: (re.search(r'\.' + k + r'\s*=\s*(\w+)', body) or [None, None])[1]  # noqa: E731
        out[m.group(1)] = {'tiles': sym_dir.get(get('tiles')), 'palettes': sym_dir.get(get('palettes')),
                           'metatiles': sym_dir.get(get('metatiles'))}
    _TS_INDEX = out
    return out


class Tileset:
    def __init__(self, name):
        info = _tileset_index().get(name) or {}
        self.tiles = []
        self.pals = []
        self.metatiles = b''
        self.files = []
        if info.get('tiles'):
            p = os.path.join(ROOT, info['tiles'], 'tiles.png')
            if os.path.exists(p):
                self.files.append(p)
                w, h, rows = read_png(p)
                for ty in range(h // 8):
                    for tx in range(w // 8):
                        self.tiles.append(b''.join(rows[ty * 8 + r][tx * 8:tx * 8 + 8] for r in range(8)))
        if info.get('palettes'):
            d = os.path.join(ROOT, info['palettes'])
            self.pals = [read_pal(os.path.join(d, 'palettes', '%02d.pal' % i)) for i in range(16)]
            if not os.path.isdir(os.path.join(d, 'palettes')):
                self.pals = [read_pal(os.path.join(d, '%02d.pal' % i)) for i in range(16)]
        if info.get('metatiles'):
            p = os.path.join(ROOT, info['metatiles'], 'metatiles.bin')
            if os.path.exists(p):
                self.files.append(p)
                self.metatiles = open(p, 'rb').read()


_TS_CACHE = {}


def tileset(name):
    ts = _TS_CACHE.get(name)
    stamp = None
    if ts is not None:
        stamp = tuple(os.path.getmtime(f) for f in ts.files if os.path.exists(f))
        if stamp == ts.stamp:
            return ts
    ts = Tileset(name)
    ts.stamp = tuple(os.path.getmtime(f) for f in ts.files if os.path.exists(f))
    _TS_CACHE[name] = ts
    return ts


# ---- layouts and maps ----------------------------------------------------------------------

def layouts():
    data = json.loads(read_text(LAYOUTS))
    return {l['id']: l for l in data['layouts'] if l.get('id')}


def map_folders():
    """Every map in the game, in the game's own group order."""
    groups = json.loads(read_text(MAP_GROUPS))
    out = []
    for g in groups.get('group_order', []):
        for folder in groups.get(g, []):
            if os.path.exists(os.path.join(ROOT, 'data/maps', folder, 'map.json')):
                out.append(folder)
    return out


def map_path(folder):
    if not re.match(r'^\w+$', folder or ''):
        raise MapError('bad map name')
    p = project_path('data/maps/%s/map.json' % folder)
    if not os.path.exists(p):
        raise MapError('No map called ' + folder)
    return p


def load_map(folder):
    return json.loads(read_text(map_path(folder)))


def save_map(folder, data):
    write_text(map_path(folder), json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def blockdata(layout):
    p = os.path.join(ROOT, layout['blockdata_filepath'])
    raw = open(p, 'rb').read()
    n = layout['width'] * layout['height']
    vals = list(struct.unpack('<%dH' % min(n, len(raw) // 2), raw[:n * 2]))
    return vals + [0] * (n - len(vals))


class Renderer:
    def __init__(self, layout):
        self.layout = layout
        version = layout.get('layout_version', 'emerald')
        self.n_tiles, self.n_meta, self.n_pals = SPLIT.get(version, SPLIT['emerald'])
        self.prim = tileset(layout['primary_tileset'])
        self.sec = tileset(layout['secondary_tileset'])
        pals = (self.prim.pals or [[(0, 0, 0)] * 16] * 16)[:self.n_pals]
        sec_pals = self.sec.pals or [[(0, 0, 0)] * 16] * 16
        pals = pals + sec_pals[len(pals):]
        self.pals = [bytes(c for col in p for c in col) for p in pals]
        self.backdrop = self.pals[0][0:3]
        self.cache = {}

    def tile(self, idx):
        if idx < self.n_tiles:
            return self.prim.tiles[idx] if idx < len(self.prim.tiles) else None
        idx -= self.n_tiles
        return self.sec.tiles[idx] if idx < len(self.sec.tiles) else None

    def metatile_entries(self, mid):
        if mid < self.n_meta:
            src, i = self.prim.metatiles, mid
        else:
            src, i = self.sec.metatiles, mid - self.n_meta
        chunk = src[i * 16:i * 16 + 16]
        if len(chunk) < 16:
            return None
        return struct.unpack('<8H', chunk)

    def metatile(self, mid):
        """16 rows of 48 bytes (RGB) for one metatile."""
        got = self.cache.get(mid)
        if got is not None:
            return got
        px = bytearray(self.backdrop * 256)
        entries = self.metatile_entries(mid)
        if entries:
            for layer in (0, 1):
                for q in range(4):
                    e = entries[layer * 4 + q]
                    t = self.tile(e & 0x3FF)
                    if t is None:
                        continue
                    hflip, vflip, pal = e & 0x400, e & 0x800, (e >> 12) & 15
                    pal = self.pals[pal] if pal < len(self.pals) else self.pals[0]
                    ox, oy = (q & 1) * 8, (q >> 1) * 8
                    for y in range(8):
                        sy = 7 - y if vflip else y
                        row = t[sy * 8:sy * 8 + 8]
                        base = ((oy + y) * 16 + ox) * 3
                        for x in range(8):
                            c = row[7 - x if hflip else x]
                            if c == 0 and layer:
                                continue
                            k = base + x * 3
                            px[k:k + 3] = pal[c * 3:c * 3 + 3]
        rows = [bytes(px[r * 48:r * 48 + 48]) for r in range(16)]
        self.cache[mid] = rows
        return rows

    def render(self):
        w, h = self.layout['width'], self.layout['height']
        blocks = blockdata(self.layout)
        out = []
        for by in range(h):
            metas = [self.metatile(blocks[by * w + bx] & 0x3FF) for bx in range(w)]
            for r in range(16):
                out.append(b''.join(m[r] for m in metas))
        return write_png(w * 16, h * 16, out)


_IMG_CACHE = {}
_IMG_LOCK = threading.Lock()


def map_image(folder):
    data = load_map(folder)
    layout = layouts().get(data.get('layout'))
    if not layout:
        raise MapError('This map has no layout to draw.')
    with _IMG_LOCK:
        r = Renderer(layout)
        files = r.prim.files + r.sec.files + [os.path.join(ROOT, layout['blockdata_filepath'])]
        stamp = tuple(os.path.getmtime(f) for f in files if os.path.exists(f))
        got = _IMG_CACHE.get(layout['id'])
        if got and got[0] == stamp:
            return got[1]
        png = r.render()
        _IMG_CACHE[layout['id']] = (stamp, png)
        return png


# ---- what is on a map ----------------------------------------------------------------------

def _int(v, default=0):
    try:
        return int(str(v), 0)
    except (TypeError, ValueError):
        return default


def is_item_ball(o):
    return o.get('script') == FIND_ITEM


def map_list():
    lay = layouts()
    out = []
    for folder in map_folders():
        try:
            data = load_map(folder)
        except (ValueError, OSError, MapError):
            continue
        l = lay.get(data.get('layout'))
        if not l:
            continue
        objs = data.get('object_events') or []
        bgs = data.get('bg_events') or []
        out.append({'map': folder, 'name': map_display_name(folder), 'id': data.get('id', ''),
                    'type': data.get('map_type', ''),
                    'items': sum(1 for o in objs if is_item_ball(o)) + sum(1 for b in bgs if b.get('type') == 'hidden_item')})
    return out


def map_detail(folder, map_index=None):
    data = load_map(folder)
    layout = layouts().get(data.get('layout'))
    if not layout:
        raise MapError('This map has no layout to draw.')
    blocks = blockdata(layout)
    # one character per tile: '1' when the player cannot walk there
    walls = ''.join('1' if (b >> 10) & 3 else '0' for b in blocks)
    heights = ''.join('%x' % (b >> 12) for b in blocks)
    trainers_by_script = {}
    if map_index is not None:
        map_index.refresh()
        for tid, battles in map_index.battles.items():
            for b in battles:
                trainers_by_script.setdefault(b['label'], tid)
    objects = []
    for i, o in enumerate(data.get('object_events') or []):
        if o.get('type', 'object') != 'object':
            kind = 'other'
        elif is_item_ball(o):
            kind = 'item'
        elif o.get('trainer_type', 'TRAINER_TYPE_NONE') != 'TRAINER_TYPE_NONE' or o.get('script') in trainers_by_script:
            kind = 'trainer'
        elif o.get('movement_type') == 'MOVEMENT_TYPE_BERRY_TREE_GROWTH':
            kind = 'berry'
        else:
            kind = 'person'
        objects.append({
            'index': i, 'kind': kind, 'x': _int(o.get('x')), 'y': _int(o.get('y')),
            'graphics_id': o.get('graphics_id', ''), 'script': o.get('script', ''),
            'item': o.get('trainer_sight_or_berry_tree_id', '') if kind == 'item' else '',
            'quantity': max(1, _int(o.get('movement_range_x'), 1)) if kind == 'item' else 1,
            'flag': o.get('flag', '0'),
            'trainer': trainers_by_script.get(o.get('script', ''), ''),
        })
    hidden = []
    for i, b in enumerate(data.get('bg_events') or []):
        if b.get('type') == 'hidden_item':
            hidden.append({'index': i, 'x': _int(b.get('x')), 'y': _int(b.get('y')), 'item': b.get('item', ''),
                           'quantity': max(1, _int(b.get('quantity'), 1)), 'flag': b.get('flag', '')})
    warps = []
    for i, w in enumerate(data.get('warp_events') or []):
        dest = w.get('dest_map', '')
        warps.append({'x': _int(w.get('x')), 'y': _int(w.get('y')), 'to': dest,
                      'toName': map_display_name(_folder_of(dest)) if dest else ''})
    return {'map': folder, 'name': map_display_name(folder), 'id': data.get('id', ''),
            'width': layout['width'], 'height': layout['height'], 'walls': walls, 'heights': heights,
            'objects': objects, 'hidden': hidden, 'warps': warps}


_FOLDER_OF = {}


def _folder_of(map_id):
    if not _FOLDER_OF:
        for folder in map_folders():
            try:
                _FOLDER_OF[load_map(folder).get('id', '')] = folder
            except (ValueError, OSError, MapError):
                pass
    return _FOLDER_OF.get(map_id, map_id.replace('MAP_', '').title().replace('_', ''))


# ---- free flags for new items --------------------------------------------------------------

def free_flags(minimum=0):
    """FLAG_UNUSED_* flags nothing in the game or the editor uses yet, lowest first."""
    defined = re.findall(r'^#define\s+(FLAG_UNUSED_0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)', read_text(FLAGS_H), re.M)
    used = set()
    pattern = re.compile(r'FLAG_UNUSED_0x[0-9A-Fa-f]+')
    for top, exts in (('data', ('.inc', '.s', '.json', '.pory')), ('src', ('.c', '.h')),
                      ('include', ('.h',)), ('editor', ('.py',))):
        for dirpath, _, files in os.walk(os.path.join(ROOT, top)):
            for f in files:
                if f.endswith(exts) and not (top == 'include' and f == 'flags.h'):
                    try:
                        used.update(pattern.findall(read_text(os.path.join(dirpath, f))))
                    except (OSError, UnicodeDecodeError):
                        pass
    return [name for name, value in defined if name not in used and int(value, 16) >= minimum]


# ---- saving item changes -------------------------------------------------------------------

def _item_const(v):
    v = (v or '').strip()
    if not v:
        raise MapError('Pick an item for every item on the map.')
    if not v.startswith('ITEM_'):
        v = 'ITEM_' + re.sub(r'[^A-Z0-9]+', '_', v.upper()).strip('_')
    return v


def _elevation(blocks, width, x, y):
    if 0 <= y and 0 <= x < width and y * width + x < len(blocks):
        e = blocks[y * width + x] >> 12
        if e not in (0, 15):
            return e
    return 3


def save_items(folder, items, valid_items=None, moves=None):
    """items: the full list of items the map should have when saved, each
    {kind: 'ball'|'hidden', index: existing index or None, x, y, item, quantity}.
    Items that were on the map but are not in the list are removed.
    moves: {object index: [x, y]} for people and trainers dragged to a new spot."""
    data = load_map(folder)
    layout = layouts().get(data.get('layout'))
    if not layout:
        raise MapError('This map has no layout.')
    w, h = layout['width'], layout['height']
    blocks = blockdata(layout)
    objs = data.get('object_events') or []
    bgs = data.get('bg_events') or []
    keep_obj, keep_bg = {}, {}
    new_balls, new_hidden = [], []
    for it in items:
        x, y = _int(it.get('x'), -1), _int(it.get('y'), -1)
        if not (0 <= x < w and 0 <= y < h):
            raise MapError('An item is outside the map.')
        const = _item_const(it.get('item'))
        if valid_items is not None and const not in valid_items:
            raise MapError('I don\'t know an item called "%s".' % it.get('item'))
        qty = max(1, min(99, _int(it.get('quantity'), 1)))
        idx = it.get('index')
        entry = {'x': x, 'y': y, 'item': const, 'quantity': qty}
        if it.get('kind') == 'hidden':
            if idx is not None and 0 <= int(idx) < len(bgs) and bgs[int(idx)].get('type') == 'hidden_item':
                keep_bg[int(idx)] = entry
            else:
                new_hidden.append(entry)
        else:
            if idx is not None and 0 <= int(idx) < len(objs) and is_item_ball(objs[int(idx)]):
                keep_obj[int(idx)] = entry
            else:
                new_balls.append(entry)

    for idx, (x, y) in (moves or {}).items():
        idx, x, y = int(idx), int(x), int(y)
        if 0 <= idx < len(objs) and not is_item_ball(objs[idx]) and 0 <= x < w and 0 <= y < h:
            o = objs[idx]
            if (_int(o.get('x')), _int(o.get('y'))) != (x, y):
                o['x'], o['y'] = x, y
                o['elevation'] = _elevation(blocks, w, x, y)

    # update or drop the item balls already on the map
    out_objs = []
    for i, o in enumerate(objs):
        if is_item_ball(o):
            if i not in keep_obj:
                continue
            e = keep_obj[i]
            if (_int(o.get('x')), _int(o.get('y'))) != (e['x'], e['y']):
                o['elevation'] = _elevation(blocks, w, e['x'], e['y'])
            o['x'], o['y'] = e['x'], e['y']
            o['trainer_sight_or_berry_tree_id'] = e['item']
            o['movement_range_x'] = e['quantity'] if e['quantity'] > 1 else 0
        out_objs.append(o)
    out_bgs = []
    for i, b in enumerate(bgs):
        if b.get('type') == 'hidden_item':
            if i not in keep_bg:
                continue
            e = keep_bg[i]
            if (_int(b.get('x')), _int(b.get('y'))) != (e['x'], e['y']):
                b['elevation'] = _elevation(blocks, w, e['x'], e['y'])
            b['x'], b['y'], b['item'] = e['x'], e['y'], e['item']
            if e['quantity'] > 1 or 'quantity' in b:
                b['quantity'] = e['quantity']
        out_bgs.append(b)

    # brand new items get a flag nothing else uses, so each can only be picked up once
    if new_balls or new_hidden:
        if len(out_objs) + len(new_balls) > MAX_OBJECTS:
            raise MapError('A map can hold at most %d people and items.' % MAX_OBJECTS)
        flags = free_flags()
        hidden_ok = [f for f in flags if int(f.rsplit('0x', 1)[1], 16) >= HIDDEN_ITEMS_START]
        if len(new_hidden) > len(hidden_ok):
            raise MapError('There are no free flags left for more hidden items.')
        for e in new_hidden:
            f = hidden_ok.pop(0)
            flags.remove(f)
            out_bgs.append({'type': 'hidden_item', 'x': e['x'], 'y': e['y'],
                            'elevation': _elevation(blocks, w, e['x'], e['y']), 'item': e['item'], 'flag': f,
                            **({'quantity': e['quantity']} if e['quantity'] > 1 else {})})
        if len(new_balls) > len(flags):
            raise MapError('There are no free flags left for more items.')
        for e in new_balls:
            out_objs.append({
                'graphics_id': ITEM_BALL_GFX, 'x': e['x'], 'y': e['y'],
                'elevation': _elevation(blocks, w, e['x'], e['y']),
                'movement_type': 'MOVEMENT_TYPE_LOOK_AROUND', 'movement_range_x': e['quantity'] if e['quantity'] > 1 else 0,
                'movement_range_y': 0, 'trainer_type': 'TRAINER_TYPE_NONE',
                'trainer_sight_or_berry_tree_id': e['item'], 'script': FIND_ITEM, 'flag': flags.pop(0)})
    data['object_events'] = out_objs
    data['bg_events'] = out_bgs
    save_map(folder, data)
