"""Starters, gift Pokemon and one-time encounters.

Starters: the three Pokemon in Prof. Birch's bag (src/starter_choose.c) and
the level they start at (src/battle_setup.c).
Gifts and encounters: every `givemon`, `giveegg`, `setwildbattle` and
`seteventmon` line in the scripts (Castform, Beldum, the fossils, the
legendaries...). Changing the Pokemon also changes its cry and name in the
same script, so the scene still matches."""

import glob
import os
import re

from common import ROOT, map_display_name, read_text, write_text
from textdb import LABEL_RE

STARTERS_C = os.path.join(ROOT, 'src/starter_choose.c')
GIVE_STARTER_C = os.path.join(ROOT, 'src/battle_setup.c')
KINDS = {'givemon': 'Gift', 'giveegg': 'Egg', 'setwildbattle': 'Battle', 'seteventmon': 'Battle'}
LINE_RE = re.compile(r'^([ \t]*)(givemon|giveegg|setwildbattle|seteventmon)[ \t]+(SPECIES_\w+)(?:[ \t]*,[ \t]*(\d+))?(.*)$')


class GiftError(Exception):
    pass


# ---- starters -----------------------------------------------------------------------------

def starters():
    text = read_text(STARTERS_C)
    out = []
    for kind in ('GRASS', 'FIRE', 'WATER'):
        m = re.search(r'#define %s_STARTER\s*\(IS_FRLG \? (SPECIES_\w+)\s*:\s*(SPECIES_\w+)\s*\)' % kind, text)
        out.append(m.group(2) if m else '')
    lm = re.search(r'ScriptGiveMon\(starterMon,\s*(\d+)', read_text(GIVE_STARTER_C))
    return {'species': out, 'level': int(lm.group(1)) if lm else 5}


def save_starters(species, level, valid=None):
    text = read_text(STARTERS_C)
    for kind, sp in zip(('GRASS', 'FIRE', 'WATER'), species):
        if not re.fullmatch(r'SPECIES_\w+', sp or '') or (valid is not None and sp not in valid):
            raise GiftError('Pick a Pokemon for every starter.')
        text, n = re.subn(r'(#define %s_STARTER\s*\(IS_FRLG \? SPECIES_\w+\s*:\s*)SPECIES_\w+(\s*\))' % kind,
                          lambda m: m.group(1) + sp + m.group(2), text)
        if not n:
            raise GiftError('Could not find the %s starter.' % kind.lower())
    write_text(STARTERS_C, text)
    level = max(1, min(100, int(level)))
    t2 = read_text(GIVE_STARTER_C)
    t2, n = re.subn(r'(ScriptGiveMon\(starterMon,\s*)\d+', lambda m: m.group(1) + str(level), t2)
    if n:
        write_text(GIVE_STARTER_C, t2)
    return starters()


# ---- gifts and encounters -----------------------------------------------------------------

def _files():
    return sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc'))) + \
        sorted(glob.glob(os.path.join(ROOT, 'data/scripts/*.inc')))


def _where(rel):
    parts = rel.split('/')
    if parts[1] == 'maps':
        return parts[2], map_display_name(parts[2])
    return '', os.path.splitext(parts[-1])[0].replace('_', ' ')


def all_gifts(folder=None):
    out = []
    files = [os.path.join(ROOT, 'data/maps', folder, 'scripts.inc')] if folder else _files()
    for f in files:
        if not os.path.exists(f):
            continue
        rel = os.path.relpath(f, ROOT)
        where, name = _where(rel)
        if 'Frlg' in where or 'test' in rel.lower() or 'debug' in rel.lower():
            continue
        label = ''
        for n, line in enumerate(read_text(f).split('\n')):
            lm = LABEL_RE.match(line)
            if lm:
                label = lm.group(1)
                continue
            m = LINE_RE.match(line)
            if not m:
                continue
            rest = m.group(5) or ''
            item = re.match(r'\s*,\s*(ITEM_\w+)', rest)
            out.append({'file': rel, 'line': n, 'label': label, 'map': where, 'mapName': name,
                        'kind': KINDS[m.group(2)], 'command': m.group(2), 'species': m.group(3),
                        'level': int(m.group(4)) if m.group(4) else None,
                        'item': item.group(1) if item else '', 'text': line.strip()})
    return out


def save_gift(rel, line_no, expect, species, level=None, item=None, valid_species=None, valid_items=None):
    """Changes one gift or encounter line. `expect` is the line as it was read,
    so a file changed in the meantime is never overwritten by mistake."""
    path = os.path.join(ROOT, rel)
    if os.path.abspath(path) not in [os.path.abspath(f) for f in _files()]:
        raise GiftError('That is not a script file.')
    if not re.fullmatch(r'SPECIES_\w+', species or '') or (valid_species is not None and species not in valid_species):
        raise GiftError('Pick a Pokemon.')
    lines = read_text(path).split('\n')
    if not (0 <= line_no < len(lines)) or lines[line_no].strip() != (expect or '').strip():
        raise GiftError('That script changed since you opened it. Reload the map and try again.')
    m = LINE_RE.match(lines[line_no])
    if not m:
        raise GiftError('That line is not a gift or encounter any more.')
    indent, cmd, old, lv, rest = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5) or ''
    if level is not None and lv is not None:
        lv = str(max(1, min(100, int(level))))
    if item is not None and cmd in ('givemon', 'setwildbattle', 'seteventmon'):
        item = item.strip()
        if item and not item.startswith('ITEM_'):
            item = 'ITEM_' + re.sub(r'[^A-Z0-9]+', '_', item.upper()).strip('_')
        if item and valid_items is not None and item not in valid_items:
            raise GiftError('I don\'t know an item called "%s".' % item)
        im = re.match(r'(\s*,\s*)(ITEM_\w+)(.*)$', rest)
        if im:
            rest = im.group(1) + (item or 'ITEM_NONE') + im.group(3)
        elif item:
            rest = ', ' + item + rest
    lines[line_no] = indent + cmd + ' ' + species + (', ' + lv if lv is not None else '') + rest
    # the same scene's cry, picture and name lines follow the new Pokemon
    if species != old:
        start = line_no
        while start > 0 and not LABEL_RE.match(lines[start - 1]):
            start -= 1
        end = line_no + 1
        while end < len(lines) and not LABEL_RE.match(lines[end]):
            end += 1
        for i in range(start, end):
            if i != line_no and not lines[i].lstrip().startswith('.string') and re.search(r'\b%s\b' % old, lines[i]):
                lines[i] = re.sub(r'\b%s\b' % old, species, lines[i])
    write_text(path, '\n'.join(lines))
