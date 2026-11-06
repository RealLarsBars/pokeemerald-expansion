"""Moves & items tab: a move's name, type, power, accuracy, PP, category,
priority and description (src/data/moves_info.h), and an item's name, price
and description (src/data/items.h).

Only the lines that change are rewritten. A value that depends on a generation
setting (like `B_UPDATED_MOVE_DATA >= GEN_6 ? 90 : 95`) is shown as your game
uses it now, and saved as a plain number once you change it."""

import os
import re

import fundata
from common import ROOT, read_text, write_text, pretty_name

MOVES_H = os.path.join(ROOT, 'src/data/moves_info.h')
ITEMS_H = os.path.join(ROOT, 'src/data/items.h')
MOVE_NAME_MAX = 16      # MOVE_NAME_LENGTH
ITEM_NAME_MAX = 20      # ITEM_NAME_LENGTH
CATEGORIES = ['DAMAGE_CATEGORY_PHYSICAL', 'DAMAGE_CATEGORY_SPECIAL', 'DAMAGE_CATEGORY_STATUS']


STRINGS = r'\s*(?:"(?:[^"\\\n]|\\.)*"\s*)+'   # one or more "..." pieces


class MoveItemError(Exception):
    pass


def _entry(text, const, kind):
    """(start, end) of one [MOVE_X] = {...} or [ITEM_X] = {...} entry."""
    m = re.search(r'^\s*\[' + re.escape(const) + r'\]\s*=', text, re.M)
    if not m:
        raise MoveItemError('Could not find %s.' % const)
    nxt = re.compile(r'^\s*\[' + kind + r'_\w+\]\s*=', re.M).search(text, m.end())
    return m.start(), nxt.start() if nxt else len(text)


def _field(body, key):
    m = re.search(r'^[ \t]{8}\.' + key + r'[ \t]*=[ \t]*([^\n]*?),?[ \t]*(?://[^\n]*)?$', body, re.M)
    return fundata.resolve(m.group(1)) if m else None


def _number(body, key, default=0):
    v = _field(body, key)
    m = re.match(r'-?\d+', v or '')
    return int(m.group()) if m else default


def _c_string_value(expr):
    """Joins "a\\n" "b" pieces into plain text with real line breaks."""
    pieces = re.findall(r'"((?:[^"\\]|\\.)*)"', expr)
    s = ''.join(pieces)
    return s.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')


def _string_field(body, key, wrapper):
    m = re.search(r'\.' + key + r'\s*=\s*' + wrapper + r'\((' + STRINGS + r')\)\s*,', body)
    return _c_string_value(m.group(1)) if m else None


def _c_string(text, indent):
    """Plain text -> COMPOUND_STRING( "line\\n" "line") laid out like the game's own."""
    lines = text.replace('\r\n', '\n').split('\n')
    esc = [l.replace('\\', '\\\\').replace('"', '\\"') for l in lines]
    if len(esc) == 1:
        return 'COMPOUND_STRING("%s")' % esc[0]
    pad = ' ' * (indent + 4)
    parts = ['"%s\\n"' % l for l in esc[:-1]] + ['"%s"' % esc[-1]]
    return 'COMPOUND_STRING(\n' + '\n'.join(pad + p for p in parts) + ')'


def _set_value(body, key, value):
    pat = re.compile(r'^([ \t]{8}\.' + key + r'[ \t]*=[ \t]*)([^\n]*?)(,[ \t]*(?://[^\n]*)?)$', re.M)
    if not pat.search(body):
        # Not written out yet (a default of 0): add it after the name.
        return re.sub(r'(\n[ \t]{8}\.name[ \t]*=[^\n]*\n)', lambda m: m.group(1) + '        .%s = %s,\n' % (key, value), body, count=1)
    return pat.sub(lambda m: m.group(1) + value + m.group(3), body)


def _set_string(body, key, wrapper, text):
    """Replaces .key = WRAPPER(...) or .key = someSharedString, with a new string."""
    new = _c_string(text, 8) if wrapper == 'COMPOUND_STRING' else '%s("%s")' % (wrapper, text.replace('"', '\\"'))
    m = re.search(r'(\.' + key + r'\s*=\s*)' + wrapper + r'\(' + STRINGS + r'\)(\s*,)', body)
    if m:
        return body[:m.start()] + m.group(1) + new + m.group(2) + body[m.end():]
    m = re.search(r'(\.' + key + r'\s*=\s*)[A-Za-z_]\w*(\s*,)', body)
    if m:
        return body[:m.start()] + m.group(1) + new + m.group(2) + body[m.end():]
    raise MoveItemError('Could not find the %s to change.' % key)


def _clean(text):
    import textdb
    return textdb.curly_quotes(text.replace('\r\n', '\n'))


def _check_text(text, max_len=None, what='name'):
    if '\n' in text and what == 'name':
        raise MoveItemError('A name has to fit on one line.')
    if max_len and len(text) > max_len:
        raise MoveItemError('That %s is too long: at most %d letters fit.' % (what, max_len))
    if '{' in text or '}' in text:
        raise MoveItemError('Curly brackets { } cannot be used here.')


# ---- moves --------------------------------------------------------------------

def move_list():
    text = read_text(MOVES_H)
    out = []
    for const, body in re.findall(r'^\s*\[(MOVE_[A-Z0-9_]+)\]\s*=\s*\n(.*?)(?=^\s*\[MOVE_|\Z)', text, re.S | re.M):
        if const == 'MOVE_NONE':
            continue
        name = _string_field(body, 'name', 'COMPOUND_STRING') or pretty_name(const[5:])
        out.append({'const': const, 'name': name, 'type': (re.search(r'TYPE_[A-Z]+', _field(body, 'type') or '') or [''])[0],
                    'power': _number(body, 'power'), 'category': _field(body, 'category') or ''})
    return out


def read_move(const):
    text = read_text(MOVES_H)
    s, e = _entry(text, const, 'MOVE')
    body = text[s:e]
    return {
        'kind': 'move', 'const': const,
        'name': _string_field(body, 'name', 'COMPOUND_STRING') or pretty_name(const[5:]),
        'description': _string_field(body, 'description', 'COMPOUND_STRING') or '',
        'power': _number(body, 'power'),
        'accuracy': _number(body, 'accuracy'),
        'pp': _number(body, 'pp'),
        'priority': _number(body, 'priority'),
        'type': (re.search(r'TYPE_[A-Z]+', _field(body, 'type') or '') or [''])[0],
        'category': _field(body, 'category') or '',
        'effect': pretty_name((_field(body, 'effect') or 'EFFECT_HIT')[7:]),
        'nameMax': MOVE_NAME_MAX,
    }


def save_move(const, changes, types):
    text = read_text(MOVES_H)
    s, e = _entry(text, const, 'MOVE')
    body = text[s:e]
    for key, lo, hi in (('power', 0, 255), ('accuracy', 0, 100), ('pp', 1, 64), ('priority', -7, 5)):
        if key in changes:
            try:
                v = int(changes[key])
            except (TypeError, ValueError):
                raise MoveItemError('%s must be a number.' % key.capitalize())
            if not lo <= v <= hi:
                raise MoveItemError('%s must be between %d and %d.' % ('PP' if key == 'pp' else key.capitalize(), lo, hi))
            body = _set_value(body, key, str(v))
    if 'type' in changes:
        if changes['type'] not in types:
            raise MoveItemError('Unknown type %s.' % changes['type'])
        body = _set_value(body, 'type', changes['type'])
    if 'category' in changes:
        if changes['category'] not in CATEGORIES:
            raise MoveItemError('Unknown category.')
        body = _set_value(body, 'category', changes['category'])
    if 'name' in changes:
        name = _clean(changes['name'].strip())
        _check_text(name, MOVE_NAME_MAX)
        if not name:
            raise MoveItemError('A move needs a name.')
        body = _set_string(body, 'name', 'COMPOUND_STRING', name)
    if 'description' in changes:
        d = _clean(changes['description'].strip('\n'))
        _check_text(d, None, 'description')
        body = _set_string(body, 'description', 'COMPOUND_STRING', d)
    write_text(MOVES_H, text[:s] + body + text[e:])
    fundata.reset_caches()
    return read_move(const)


# ---- items --------------------------------------------------------------------

def _item_price(body):
    v = _field(body, 'price')
    m = re.match(r'\d+', (v or '0').strip('() '))
    return int(m.group()) if m else 0


def item_list():
    text = read_text(ITEMS_H)
    out = []
    for const, body in re.findall(r'^\s*\[(ITEM_[A-Z0-9_]+)\]\s*=\s*\n(.*?)(?=^\s*\[ITEM_|\Z)', text, re.S | re.M):
        if const == 'ITEM_NONE':
            continue
        name = _string_field(body, 'name', 'ITEM_NAME')
        if not name:
            continue
        out.append({'const': const, 'name': name, 'price': _item_price(body),
                    'pocket': pretty_name((_field(body, 'pocket') or 'POCKET_ITEMS')[7:])})
    return out


def read_item(const):
    text = read_text(ITEMS_H)
    s, e = _entry(text, const, 'ITEM')
    body = text[s:e]
    icon = re.search(r'\.iconPic\s*=\s*gItemIcon_(\w+)', body)
    return {
        'kind': 'item', 'const': const,
        'name': _string_field(body, 'name', 'ITEM_NAME') or pretty_name(const[5:]),
        'description': _string_field(body, 'description', 'COMPOUND_STRING') or '',
        'price': _item_price(body),
        'pocket': pretty_name((_field(body, 'pocket') or 'POCKET_ITEMS')[7:]),
        'icon': _icon_path(icon.group(1)) if icon else None,
        'nameMax': ITEM_NAME_MAX,
        'isTM': const.startswith('ITEM_TM') or const.startswith('ITEM_HM'),
    }


def _icon_path(name):
    """gItemIcon_PokeBall -> graphics/items/icons/poke_ball.png (when it exists)."""
    snake = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', name).lower()
    for cand in (snake, snake.replace('_', '')):
        rel = 'graphics/items/icons/%s.png' % cand
        if os.path.exists(os.path.join(ROOT, rel)):
            return rel
    return None


def save_item(const, changes):
    text = read_text(ITEMS_H)
    s, e = _entry(text, const, 'ITEM')
    body = text[s:e]
    if 'price' in changes:
        try:
            price = int(changes['price'])
        except (TypeError, ValueError):
            raise MoveItemError('The price must be a number.')
        if not 0 <= price <= 999999:
            raise MoveItemError('The price must be between 0 and 999999.')
        body = _set_value(body, 'price', str(price))
    if 'name' in changes:
        name = _clean(changes['name'].strip())
        _check_text(name, ITEM_NAME_MAX)
        if not name:
            raise MoveItemError('An item needs a name.')
        body = _set_string(body, 'name', 'ITEM_NAME', name)
    if 'description' in changes:
        d = _clean(changes['description'].strip('\n'))
        _check_text(d, None, 'description')
        body = _set_string(body, 'description', 'COMPOUND_STRING', d)
    write_text(ITEMS_H, text[:s] + body + text[e:])
    return read_item(const)
