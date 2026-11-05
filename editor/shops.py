"""Shops: what every Poke Mart sells (the `pokemart` lists in the map scripts)
and what items cost (src/data/items.h).

Only the list being saved is rewritten; the rest of each script file stays
as it was."""

import glob
import os
import re

from common import ROOT, map_display_name, read_text, write_text

ITEMS_H = os.path.join(ROOT, 'src/data/items.h')
MART_RE = re.compile(r'^\s*pokemart\s+(\w+)', re.M)


class ShopError(Exception):
    pass


def _script_files():
    return sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc'))) + \
        sorted(glob.glob(os.path.join(ROOT, 'data/scripts/*.inc')))


def _list_re(label):
    # Emerald lists end with pokemartlistend, FireRed ones with .2byte ITEM_NONE
    return re.compile(r'^' + re.escape(label) + r'::?[ \t]*\n((?:[ \t]*\.2byte[ \t]+(?!ITEM_NONE\b)\w+[ \t]*\n)*)'
                      r'([ \t]*(?:pokemartlistend|\.2byte[ \t]+ITEM_NONE))', re.M)


def _where(path):
    rel = os.path.relpath(path, ROOT)
    parts = rel.split('/')
    return (parts[2], map_display_name(parts[2])) if parts[1] == 'maps' else ('', os.path.splitext(parts[-1])[0].replace('_', ' '))


def all_shops(files=None):
    """Every Poke Mart list in the game: [{label, file, map, mapName, items}]."""
    labels = []
    texts = {}
    for f in files or _script_files():
        t = read_text(f)
        texts[f] = t
        for m in MART_RE.finditer(t):
            if m.group(1) not in [l for l, _ in labels]:
                labels.append((m.group(1), f))
    out = []
    for label, used_in in labels:
        for f, t in texts.items():
            m = _list_re(label).search(t)
            if m:
                folder, name = _where(used_in)
                out.append({'label': label, 'file': os.path.relpath(f, ROOT), 'map': folder, 'mapName': name,
                            'items': re.findall(r'\.2byte\s+(\w+)', m.group(1))})
                break
    return out


def shops_for_map(folder):
    own = os.path.join(ROOT, 'data/maps', folder, 'scripts.inc')
    if not os.path.exists(own):
        return []
    found = all_shops([own])
    wanted = set(MART_RE.findall(read_text(own)))
    if len(found) < len(wanted):  # a list kept in another file
        found = [s for s in all_shops() if s['map'] == folder]
    return found


def save_shop(rel_file, label, items, valid_items=None):
    path = os.path.join(ROOT, rel_file)
    if os.path.abspath(path) not in [os.path.abspath(f) for f in _script_files()]:
        raise ShopError('That is not a script file.')
    clean = []
    for it in items:
        it = (it or '').strip()
        if not it:
            continue
        if not it.startswith('ITEM_'):
            it = 'ITEM_' + re.sub(r'[^A-Z0-9]+', '_', it.upper()).strip('_')
        if valid_items is not None and it not in valid_items:
            raise ShopError('I don\'t know an item called "%s".' % it)
        if it not in clean:
            clean.append(it)
    if not clean:
        raise ShopError('A shop needs at least one item.')
    text = read_text(path)
    m = _list_re(label).search(text)
    if not m:
        raise ShopError('Could not find the shop list %s.' % label)
    indent = re.match(r'[ \t]*', m.group(2)).group(0) or '\t'
    body = ''.join('%s.2byte %s\n' % (indent, it) for it in clean)
    write_text(path, text[:m.start(1)] + body + text[m.end(1):])
    return clean


# ---- prices -------------------------------------------------------------------------------

def _config(name):
    for path in glob.glob(os.path.join(ROOT, 'include/config/*.h')):
        m = re.search(r'#define\s+' + name + r'\s+(\w+)', read_text(path))
        if m:
            v = m.group(1)
            if v == 'GEN_LATEST':
                return 9
            g = re.fullmatch(r'GEN_(\d)', v)
            return int(g.group(1)) if g else None
    return None


def _price_value(expr):
    expr = expr.strip()
    if re.fullmatch(r'\d+', expr):
        return int(expr)
    m = re.fullmatch(r'\((.*)\)\s*\?\s*(\d+)\s*:\s*(\d+)', expr)
    if not m:
        return None
    cond = re.sub(r'GEN_(\d)', r'\1', m.group(1))
    for name in set(re.findall(r'[A-Z][A-Z0-9_]+', cond)):
        gen = _config(name)
        if gen is None:
            return None
        cond = re.sub(r'\b' + name + r'\b', str(gen), cond)
    cond = cond.replace('&&', ' and ').replace('||', ' or ')
    if not re.fullmatch(r'[\d\s<>=!()andor]*', cond):
        return None
    try:
        ok = eval(cond, {'__builtins__': {}}, {})  # only numbers and comparisons get here
    except Exception:
        return None
    return int(m.group(2)) if ok else int(m.group(3))


def _price_span(text, item):
    """(start, end) of the price expression inside one item's entry, or None."""
    m = re.search(r'^\s*\[' + re.escape(item) + r'\]\s*=', text, re.M)
    if not m:
        return None
    nxt = re.compile(r'^\s*\[ITEM_\w+\]\s*=', re.M).search(text, m.end())
    stop = nxt.start() if nxt else len(text)
    p = re.compile(r'\.price\s*=\s*([^\n]+?),[ \t]*\n').search(text, m.end(), stop)
    return (p.start(1), p.end(1)) if p else None


def prices(items):
    text = read_text(ITEMS_H)
    out = {}
    for it in items:
        span = _price_span(text, it)
        if span:
            out[it] = _price_value(text[span[0]:span[1]])
    return out


def set_prices(changes):
    """changes: {ITEM_X: price}. Writes a plain number, so the price is the same
    whatever the generation setting says."""
    text = read_text(ITEMS_H)
    for it, price in changes.items():
        if not re.fullmatch(r'ITEM_\w+', it):
            raise ShopError('bad item')
        price = max(0, min(999999, int(price)))
        span = _price_span(text, it)
        if not span:
            raise ShopError('Could not find the price of %s.' % it)
        text = text[:span[0]] + str(price) + text[span[1]:]
    write_text(ITEMS_H, text)
