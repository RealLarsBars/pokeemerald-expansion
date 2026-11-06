"""Game facts the Fun Modes need: every Pokemon that exists in this build
(stats, types, abilities, evolutions, legendary flags, moves it can learn)
and every move's power and type. Read straight from the C files."""

import glob
import json
import os
import re

import species
from common import ROOT, read_text, pretty_name

INFO_DIR = os.path.join(ROOT, 'src/data/pokemon/species_info')
ENTRY_RE = re.compile(r'^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*$', re.M)
FLAGS = ('isLegendary', 'isMythical', 'isUltraBeast', 'isParadox', 'isMegaEvolution', 'isPrimalReversion',
         'isGigantamax', 'isTotem', 'isTeraForm', 'isUltraBurst', 'isRestrictedLegendary', 'isSubLegendary',
         'isAlolanForm', 'isGalarianForm', 'isHisuianForm', 'isPaldeanForm', 'isFrontierBanned')
NO_FORMS = ('isMegaEvolution', 'isPrimalReversion', 'isGigantamax', 'isTotem', 'isTeraForm', 'isUltraBurst')
REGIONAL = ('isAlolanForm', 'isGalarianForm', 'isHisuianForm', 'isPaldeanForm')


_CONFIG = {}
_READER = None


def set_reader(fn):
    """Read game files through fn(rel_path) (Fun Modes' in-memory copy) instead of the disk."""
    global _READER
    _READER = fn
    reset_caches()


def _read(path):
    if _READER is not None:
        return _READER(os.path.relpath(path, ROOT))
    return read_text(path)


def config_value(name):
    """Numeric value of a setting in include/config (GEN_X -> X, TRUE -> 1)."""
    if not _CONFIG:
        raw = {}
        for path in sorted(glob.glob(os.path.join(ROOT, 'include/config/*.h'))):
            for n, v in re.findall(r'^\s*#define\s+(\w+)\s+([^\s/]+)', _read(path), re.M):
                raw.setdefault(n, v)
        _CONFIG['__raw'] = raw

    raw = _CONFIG['__raw']
    v, depth = name, 0
    while v in raw and depth < 6:
        v, depth = raw[v], depth + 1
    if v in ('GEN_LATEST',):
        return 9
    if v == 'GEN_CHAMPIONS':
        return 10
    if re.fullmatch(r'GEN_\d', v):
        return int(v[4:])
    if v in ('TRUE', 'FALSE'):
        return 1 if v == 'TRUE' else 0
    if re.fullmatch(r'\d+', v):
        return int(v)
    return 9 if name.startswith(('P_', 'B_', 'I_')) else 0


TERNARY_RE = re.compile(r'^\(?\s*([A-Z]\w*)\s*>=\s*GEN_(\d)\s*\)?\s*\?\s*(.+?)\s*:\s*(.+)$')


def resolve(expr, macros=None):
    """'B_UPDATED_MOVE_DATA >= GEN_6 ? 90 : 95' -> '90' with the current settings."""
    expr = expr.strip()
    for _ in range(4):
        if macros and expr in macros:
            expr = macros[expr].strip()
        while expr.startswith('(') and expr.endswith(')') and expr.count('(') == 1:
            expr = expr[1:-1].strip()
        m = TERNARY_RE.match(expr)
        if not m:
            break
        expr = m.group(3) if config_value(m.group(1)) >= int(m.group(2)) else m.group(4)
    return expr


def _cond_true(cond):
    """Evaluate a simple #if condition. Unknown expressions count as true."""
    cond = cond.strip()
    m = re.fullmatch(r'!?\s*(P_\w+)', cond)
    if m:
        v = config_value(m.group(1)) != 0
        return not v if cond.startswith('!') else v
    m = re.fullmatch(r'(P_\w+)\s*>=\s*GEN_(\d)', cond)
    if m:
        return config_value(m.group(1)) >= int(m.group(2))
    parts = re.split(r'\s*&&\s*', cond)
    if len(parts) > 1:
        return all(_cond_true(p) for p in parts)
    parts = re.split(r'\s*\|\|\s*', cond)
    if len(parts) > 1:
        return any(_cond_true(p) for p in parts)
    return True


def _active_lines(text):
    """Yield (line, active) honouring nested #if/#else/#endif."""
    stack = []
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('#if'):
            m = re.match(r'#if(n?def)?\s+(.*)', s)
            cond = m.group(2) if m else ''
            val = _cond_true(cond) if not (m and m.group(1)) else True
            stack.append([val, val])
            continue
        if s.startswith('#elif') and stack:
            prev_taken = stack[-1][1]
            val = (not prev_taken) and _cond_true(s[5:])
            stack[-1] = [val, prev_taken or val]
            continue
        if s.startswith('#else') and stack:
            stack[-1] = [not stack[-1][1], True]
            continue
        if s.startswith('#endif') and stack:
            stack.pop()
            continue
        yield line, all(v[0] for v in stack)


def _int(expr, default=0, macros=None):
    v = resolve(expr.split('//')[0].strip().rstrip(','), macros)
    m = re.match(r'\d+', v)
    return int(m.group()) if m else default


_POOL = None


def pool(refresh=False):
    """{SPECIES_X: info} for every Pokemon form that is turned on in this build."""
    global _POOL
    if _POOL is not None and not refresh:
        return _POOL
    out = {}
    for path in sorted(glob.glob(os.path.join(INFO_DIR, 'gen_*.h'))):
        lines = list(_active_lines(_read(path)))
        active = '\n'.join(l if a else '' for l, a in lines)
        macros = {}
        for l, a in lines:
            dm = re.match(r'\s*#define\s+(\w+)\s+(.+)$', l)
            if a and dm:
                macros[dm.group(1)] = dm.group(2).strip()
        starts = list(ENTRY_RE.finditer(active))
        for i, m in enumerate(starts):
            body = active[m.end(): starts[i + 1].start() if i + 1 < len(starts) else len(active)]
            const = m.group(1)
            if const in out:
                continue
            stats = {}
            for st in species.STATS:
                sm = re.search(r'\.' + st + r'\s*=\s*([^\n]+)', body)
                stats[st] = _int(sm.group(1), 0, macros) if sm else 0
            if not stats['baseHP']:
                continue
            tm = re.search(r'\.types\s*=\s*([^\n]+)', body)
            types = []
            if tm:
                texpr = re.sub(r'\b[A-Z][A-Z0-9_]+\b', lambda x: resolve(macros[x.group()], macros) if x.group() in macros else x.group(), tm.group(1).rstrip(','))
                types = re.findall(r'TYPE_[A-Z]+', resolve(texpr, macros))
            types = list(dict.fromkeys(types)) or ['TYPE_NORMAL']
            am = re.search(r'\.abilities\s*=\s*([^\n]+)', body)
            abilities = []
            if am:
                aexpr = re.sub(r'\b[A-Z][A-Z0-9_]+\b', lambda x: resolve(macros[x.group()], macros) if x.group() in macros else x.group(), am.group(1))
                abilities = re.findall(r'ABILITY_[A-Z0-9_]+', resolve(aexpr.rstrip(','), macros))
            name = re.search(r'\.speciesName\s*=\s*_\("([^"]*)"\)', body)
            evos = re.search(r'\.evolutions\s*=\s*EVOLUTION\((.*?)\)\s*,\s*\n', body, re.S)
            info = {
                'const': const,
                'name': name.group(1) if name else pretty_name(const[8:]),
                'stats': stats,
                'bst': sum(stats.values()),
                'types': types,
                'abilities': abilities,
                'evolvesTo': list(dict.fromkeys(re.findall(r'SPECIES_[A-Z0-9_]+', evos.group(1)))) if evos else [],
                'learnset': (re.search(r'\.levelUpLearnset\s*=\s*(\w+)', body) or [None, None])[1],
            }
            for f in FLAGS:
                info[f] = bool(re.search(r'\.' + f + r'\s*=\s*TRUE', body))
            out[const] = info
    # aliases such as SPECIES_MIMIKYU = SPECIES_MIMIKYU_DISGUISED
    consts = _read(os.path.join(ROOT, 'include/constants/species.h'))
    aliases = {}
    for a, b in re.findall(r'^\s*(SPECIES_[A-Z0-9_]+)\s*=\s*(SPECIES_[A-Z0-9_]+)\s*,', consts, re.M):
        if b in out and a not in out:
            aliases[a] = b
    # who evolves into whom
    for c, info in out.items():
        info['evolvesFrom'] = None
    for c, info in out.items():
        for t in info['evolvesTo']:
            if t in out and out[t]['evolvesFrom'] is None and t != c:
                out[t]['evolvesFrom'] = c
    seen_names = set()
    for c, info in out.items():
        info['legendary'] = any(info[f] for f in ('isLegendary', 'isMythical', 'isUltraBeast', 'isParadox',
                                                    'isRestrictedLegendary', 'isSubLegendary'))
        special_form = any(info[f] for f in NO_FORMS)
        regional = any(info[f] for f in REGIONAL)
        # Forms share a name with their base; keep the first one plus regional forms.
        info['usable'] = not special_form and (info['name'] not in seen_names or regional)
        if info['usable'] and not regional:
            seen_names.add(info['name'])
    for c, info in out.items():
        info['stage'] = _stage(out, c)
        info['finalStage'] = not any(t in out for t in info['evolvesTo'])
    for a, b in aliases.items():
        out[a] = dict(out[b], const=a, usable=False)
    _POOL = out
    return out


def _stage(p, c):
    n = 1
    seen = {c}
    while p[c]['evolvesFrom'] and p[c]['evolvesFrom'] not in seen:
        c = p[c]['evolvesFrom']
        seen.add(c)
        n += 1
    return n


def usable(p=None, legendaries=True):
    p = p or pool()
    return [i for i in p.values() if i['usable'] and (legendaries or not i['legendary'])]


def evolution_line(c, p=None):
    """[base, stage 2, stage 3] following the first evolution at each step."""
    p = p or pool()
    seen = {c}
    while p[c]['evolvesFrom'] and p[c]['evolvesFrom'] in p and p[c]['evolvesFrom'] not in seen:
        c = p[c]['evolvesFrom']  # some forms point back at each other, so stop on a loop
        seen.add(c)
    line = [c]
    while True:
        nxt = [t for t in p[line[-1]]['evolvesTo'] if t in p and p[t]['usable'] and t not in line]
        if not nxt:
            return line
        line.append(nxt[0])


def showdown_name(const, p=None):
    """A name trainerproc turns back into exactly this constant."""
    from common import species_const
    p = p or pool()
    info = p.get(const)
    for cand in ((info or {}).get('name'), pretty_name(const[8:])):
        if cand and species_const(cand) == const:
            return cand
    return const


# ---- moves -------------------------------------------------------------------

_MOVES = None


def moves():
    """{MOVE_X: {name, power, type, category, accuracy, effect, priority}}"""
    global _MOVES
    if _MOVES is not None:
        return _MOVES
    text = _read(os.path.join(ROOT, 'src/data/moves_info.h'))
    out = {}
    parts = re.split(r'^\s*\[(MOVE_[A-Z0-9_]+)\]\s*=\s*$', text, flags=re.M)
    for i in range(1, len(parts), 2):
        const, body = parts[i], parts[i + 1]

        def get(key, default=''):
            m = re.search(r'\n\s*\.' + key + r'\s*=\s*([^\n]+)', body)
            return resolve(m.group(1).rstrip(',').split('//')[0]) if m else default
        name = re.search(r'\.name\s*=\s*COMPOUND_STRING\("([^"]*)"\)', body)
        power = re.match(r'\d+', get('power', '0'))
        acc = re.match(r'\d+', get('accuracy', '0'))
        prio = re.match(r'-?\d+', get('priority', '0'))
        out[const] = {
            'name': name.group(1) if name else pretty_name(const[5:]),
            'power': int(power.group()) if power else 0,
            'type': (re.search(r'TYPE_[A-Z]+', get('type')) or [''])[0],
            'category': get('category'),
            'accuracy': int(acc.group()) if acc else 0,
            'effect': get('effect'),
            'priority': int(prio.group()) if prio else 0,
            'target': get('target'),
            'hits': 3 if re.search(r'\.multiHit\s*=\s*TRUE', body) else int((re.search(r'\.strikeCount\s*=\s*(\d+)', body) or [0, 1])[1]),
        }
    _MOVES = out
    return out


_LEARN_TEXT = None


def level_up_moves(const, level=100, p=None):
    """Moves the Pokemon knows by `level` from its level-up list."""
    global _LEARN_TEXT
    p = p or pool()
    sym = p[const].get('learnset')
    if not sym:
        return []
    if _LEARN_TEXT is None:
        _LEARN_TEXT = _read(species.active_learnset_file()[0])
    m = re.search(r'struct LevelUpMove ' + re.escape(sym) + r'\[\]\s*=\s*\{(.*?)\};', _LEARN_TEXT, re.S)
    if not m:
        return []
    return [mv for lv, mv in re.findall(r'LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_\w+)\s*\)', m.group(1)) if int(lv) <= level]


_TEACH = None


def teachable_moves(const):
    """TM, HM and tutor moves (from all_learnables.json, which the build uses)."""
    global _TEACH
    if _TEACH is None:
        try:
            _TEACH = json.loads(_read(os.path.join(ROOT, 'src/data/pokemon/all_learnables.json')))
        except (OSError, ValueError):
            _TEACH = {}
    key = const[8:]
    while key and key not in _TEACH:
        key = key.rpartition('_')[0]
    return _TEACH.get(key, [])


def reset_caches():
    global _POOL, _MOVES, _LEARN_TEXT, _TEACH
    _POOL = _MOVES = _LEARN_TEXT = _TEACH = None
    _CONFIG.clear()
