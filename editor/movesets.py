"""TM, HM, tutor and egg moves.

- Which move each TM and HM teaches: include/constants/tms_hms.h.
- Which TMs, HMs and tutor moves a Pokemon can learn: the build makes this
  list from src/data/pokemon/all_learnables.json (every move the Pokemon can
  learn in any game), keeping only the moves that are TMs, HMs or tutors in
  this game. So ticking a TM adds the move to that list, and unticking
  removes it.
- Egg moves: src/data/pokemon/egg_moves.h."""

import glob
import json
import os
import re

from common import ROOT, read_text, write_text

TMS_H = os.path.join(ROOT, 'include/constants/tms_hms.h')
LEARNABLES = os.path.join(ROOT, 'src/data/pokemon/all_learnables.json')
SPECIAL = os.path.join(ROOT, 'src/data/pokemon/special_movesets.json')
EGG_H = os.path.join(ROOT, 'src/data/pokemon/egg_moves.h')
SNAKE = re.compile(r'(?!^)([A-Z]+)')


class MovesetError(Exception):
    pass


# ---- the TM and HM list -------------------------------------------------------------------

def _block(text, name):
    m = re.search(r'#define %s\(F\)\s*\\\n((?:[ \t]*F\(\w+\)[ \t]*\\?\n?)*)' % name, text)
    return m


def tm_list():
    text = read_text(TMS_H)
    out = {}
    for name, key in (('FOREACH_TM', 'tms'), ('FOREACH_HM', 'hms')):
        m = _block(text, name)
        out[key] = ['MOVE_' + x for x in re.findall(r'F\((\w+)\)', m.group(1))] if m else []
    return out


def save_tm_list(tms, hms, valid_moves=None):
    """Changes which move each TM and HM teaches. The number of TMs stays the same
    (each one is an item the game knows by number). Items named after the old move
    (ITEM_TM_FOCUS_PUNCH...) are renamed everywhere they are used."""
    text = read_text(TMS_H)
    old = tm_list()
    if len(tms) != len(old['tms']) or len(hms) != len(old['hms']):
        raise MovesetError('The number of TMs and HMs cannot change.')
    for name, moves in (('FOREACH_TM', tms), ('FOREACH_HM', hms)):
        clean = []
        for mv in moves:
            if not re.fullmatch(r'MOVE_\w+', mv or '') or (valid_moves is not None and mv not in valid_moves):
                raise MovesetError('Pick a move for every TM and HM.')
            clean.append(mv[len('MOVE_'):])
        if len(set(clean)) != len(clean):
            raise MovesetError('A move can only be on one TM or HM.')
        if not clean and name == 'FOREACH_TM':
            raise MovesetError('Keep at least one TM.')
        m = _block(text, name)
        if not m:
            raise MovesetError('Could not find the %s list.' % name)
        body = ''.join('    F(%s) \\\n' % c for c in clean[:-1]) + ('    F(%s)\n' % clean[-1] if clean else '\n')
        text = text[:m.start(1)] + body + text[m.end(1):]
    if len(set(tms) & set(hms)):
        raise MovesetError('A move can only be on one TM or HM.')
    renames = {}
    for kind, before, after in (('TM', old['tms'], tms), ('HM', old['hms'], hms)):
        for a, b in zip(before, after):
            if a != b:
                renames['ITEM_%s_%s' % (kind, a[len('MOVE_'):])] = ('ITEM_%s_%s' % (kind, b[len('MOVE_'):]), b)
    write_text(TMS_H, text)
    if renames:
        _rename_tm_items(renames)
    return tm_list()


def _wrap(words, width=18, lines=3):
    out, cur = [], ''
    for w in words.split():
        if cur and len(cur) + 1 + len(w) > width:
            out.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = out[-1][:width - 3].rstrip() + '...'
    return out


def _move_description(move):
    text = read_text(os.path.join(ROOT, 'src/data/moves_info.h'))
    m = re.search(r'\[%s\]\s*=\s*\{.*?\.description\s*=\s*COMPOUND_STRING\((.*?)\),' % re.escape(move), text, re.S)
    if not m:
        return None
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))
    return ' '.join(''.join(parts).replace('\\n', ' ').split())


def _rename_tm_items(renames):
    """ITEM_TM_OLD -> ITEM_TM_NEW in every file that uses it, in two steps so
    two TMs can swap moves; the TM's bag description follows the new move."""
    pattern = re.compile(r'\b(%s)\b' % '|'.join(re.escape(k) for k in renames))
    files = []
    for top, exts in (('data', ('.inc', '.json', '.s')), ('src', ('.c', '.h')), ('include', ('.h',))):
        for dirpath, _, names in os.walk(os.path.join(ROOT, top)):
            for n in names:
                if n.endswith(exts) and n != 'events.inc':
                    files.append(os.path.join(dirpath, n))
    for f in files:
        try:
            t = read_text(f)
        except (OSError, UnicodeDecodeError):
            continue
        if not pattern.search(t):
            continue
        t = pattern.sub(lambda m: '@@TMRENAME@@' + renames[m.group(1)][0], t)
        write_text(f, t.replace('@@TMRENAME@@', ''))
    items = os.path.join(ROOT, 'src/data/items.h')
    t = read_text(items)
    for new_item, move in renames.values():
        desc = _move_description(move)
        if not desc:
            continue
        m = re.search(r'\[%s\]\s*=\s*\{.*?\.description\s*=\s*COMPOUND_STRING\((.*?)\),' % re.escape(new_item), t, re.S)
        if not m or '[ITEM_' in t[m.start() + 2:m.start(1)]:
            continue
        lines = _wrap(desc)
        body = '\n' + ''.join('            "%s%s"%s' % (l.replace('"', '\\"'), '\\n' if i < len(lines) - 1 else '', '\n' if i < len(lines) - 1 else '')
                              for i, l in enumerate(lines))
        t = t[:m.start(1)] + body + t[m.end(1):]
    write_text(items, t)


def tutor_moves():
    """Moves taught by the move tutors in the overworld (the same rule the build uses)."""
    found = []
    for f in glob.glob(os.path.join(ROOT, 'data/**/*.inc'), recursive=True):
        t = read_text(f)
        if 'ChooseMonForMoveTutor' not in t and 'SELECT_PC_MON_MOVE_TUTOR' not in t:
            continue
        for m in re.finditer(r'setvar VAR_0x8005, (MOVE_[A-Z_]*)|move_tutor (MOVE_[A-Z_]*)', t):
            mv = m.group(1) or m.group(2)
            if mv not in found:
                found.append(mv)
    return sorted(found)


# ---- one Pokemon's TM / tutor moves -------------------------------------------------------

def learnables_key(teach_symbol):
    m = re.fullmatch(r's(\w+?)TeachableLearnset', teach_symbol or '')
    return SNAKE.sub(r'_\1', m.group(1)).upper() if m else None


def _special():
    try:
        return json.loads(read_text(SPECIAL))
    except (OSError, ValueError):
        return {}


def teachables(teach_symbol, teaching_type=''):
    key = learnables_key(teach_symbol)
    data = json.loads(read_text(LEARNABLES))
    lists = tm_list()
    out = {'key': key, 'tms': lists['tms'], 'hms': lists['hms'], 'tutors': tutor_moves(),
           'universal': _special().get('universalMoves', []), 'teachingType': teaching_type,
           'editable': bool(key and key in data), 'learns': []}
    if out['editable']:
        out['learns'] = data[key]
    return out


def save_teachables(teach_symbol, add, remove, valid_moves=None):
    key = learnables_key(teach_symbol)
    data = json.loads(read_text(LEARNABLES))
    if not key or key not in data:
        raise MovesetError('This Pokemon has no TM list of its own.')
    moves = list(data[key])
    for mv in add:
        if not re.fullmatch(r'MOVE_\w+', mv) or (valid_moves is not None and mv not in valid_moves):
            raise MovesetError('Unknown move %s.' % mv)
        if mv not in moves:
            moves.append(mv)
    moves = [mv for mv in moves if mv not in set(remove)]
    data[key] = sorted(moves)
    write_text(LEARNABLES, json.dumps(data, indent=2))
    return data[key]


# ---- egg moves ----------------------------------------------------------------------------

def _egg_block(text, symbol):
    return re.search(r'static const u16 %s\[\]\s*=\s*\{(.*?)\};' % re.escape(symbol), text, re.S)


def egg_moves(symbol):
    if not symbol or not re.fullmatch(r'\w+', symbol):
        return {'editable': False, 'moves': []}
    m = _egg_block(read_text(EGG_H), symbol)
    if not m:
        return {'editable': False, 'moves': []}
    return {'editable': True, 'moves': [mv for mv in re.findall(r'MOVE_\w+', m.group(1)) if mv != 'MOVE_UNAVAILABLE']}


def save_egg_moves(symbol, moves, valid_moves=None):
    text = read_text(EGG_H)
    m = _egg_block(text, symbol or '')
    if not m:
        raise MovesetError('This Pokemon has no egg move list. Only the first Pokemon in an evolution line has one.')
    clean = []
    for mv in moves:
        if not re.fullmatch(r'MOVE_\w+', mv or '') or (valid_moves is not None and mv not in valid_moves):
            raise MovesetError('Unknown move %s.' % mv)
        if mv not in clean:
            clean.append(mv)
    body = '\n' + ''.join('    %s,\n' % mv for mv in clean) + '    MOVE_UNAVAILABLE,\n'
    write_text(EGG_H, text[:m.start(1)] + body + text[m.end(1):])
    return clean
