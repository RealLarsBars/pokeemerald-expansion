"""Reads and edits a Pokemon's data: stats, types, abilities, evolutions and
level-up moves, straight in pokeemerald-expansion's own C files.

Only the values you change are rewritten. When the files give a value
differently depending on a generation setting (inside #if blocks), saving
sets the same value for every case, so your choice always applies."""

import glob
import os
import re

from common import ROOT, read_text, write_text

INFO_DIR = os.path.join(ROOT, 'src/data/pokemon/species_info')
LEARNSET_DIR = os.path.join(ROOT, 'src/data/pokemon/level_up_learnsets')
ENTRY_RE = re.compile(r'^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=', re.M)

STATS = ['baseHP', 'baseAttack', 'baseDefense', 'baseSpAttack', 'baseSpDefense', 'baseSpeed']
EVS = ['evYield_HP', 'evYield_Attack', 'evYield_Defense', 'evYield_SpAttack', 'evYield_SpDefense', 'evYield_Speed']
SIMPLE = STATS + ['catchRate', 'expYield', 'eggCycles', 'friendship', 'growthRate', 'height', 'weight']
OPTIONAL = EVS + ['itemCommon', 'itemRare']


class SpeciesError(Exception):
    pass


# ---- values that depend on generation settings ------------------------------

_CFG = {}


def _config_gen(name):
    """Numeric generation (1-9) or boolean (1/0) for a P_ setting in include/config."""
    if not _CFG:
        raw = {}
        for fn in ('pokemon.h', 'species_enabled.h'):
            cfg = read_text(os.path.join(ROOT, 'include/config', fn))
            for n, v in re.findall(r'#define\s+(P_\w+)\s+(\w+)', cfg):
                raw.setdefault(n, v)

        def value(v, depth=0):
            if v in raw and depth < 5:
                return value(raw[v], depth + 1)
            if v == 'GEN_LATEST':
                return 9
            if v == 'GEN_CHAMPIONS':
                return 10
            if re.fullmatch(r'GEN_\d', v):
                return int(v[4:])
            if v in ('TRUE', 'FALSE'):
                return 1 if v == 'TRUE' else 0
            return int(v) if v.isdigit() else 9
        for n, v in raw.items():
            _CFG[n] = value(v)
    return _CFG.get(name, 9)


TERNARY_RE = re.compile(r'^\(?\s*(P_\w+)\s*>=\s*GEN_(\d)\s*\)?\s*\?\s*(.+?)\s*:\s*(.+)$')


def resolve(expr):
    """'P_UPDATED_STATS >= GEN_2 ? 80 : 55' -> '80' with the current settings."""
    expr = expr.strip()
    while expr.startswith('(') and expr.endswith(')') and _balanced_after(expr, 0) == len(expr):
        expr = expr[1:-1].strip()
    m = TERNARY_RE.match(expr)
    if not m:
        return expr
    return resolve(m.group(3) if _config_gen(m.group(1)) >= int(m.group(2)) else m.group(4))


# ---- locating an entry -------------------------------------------------------

def _find(species_id):
    """Return (path, text, start, end) of the species' entry body."""
    for path in sorted(glob.glob(os.path.join(INFO_DIR, 'gen_*.h'))):
        text = read_text(path)
        for m in ENTRY_RE.finditer(text):
            if m.group(1) != species_id:
                continue
            start = m.end()
            nxt = ENTRY_RE.search(text, start)
            end = nxt.start() if nxt else len(text)
            return path, text, start, end
    raise SpeciesError('Could not find ' + species_id)


def _body_extent(text, start, end):
    """Narrow [start, end) to the braces of the entry, or None if it is a macro."""
    i = start
    while i < end and text[i] in ' \t\r\n':
        i += 1
    if i >= end or text[i] != '{':
        return None
    depth = 0
    for j in range(i, end):
        c = text[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i, j + 1
    return None


def _field_re(name):
    return re.compile(r'(\.' + name + r'\s*=\s*)([^,\n]+?)(\s*,)')


def _values(body, name):
    return [m.group(2).strip() for m in _field_re(name).finditer(body)]


def _call_args(body, field, macro):
    m = re.search(r'\.' + field + r'\s*=\s*' + macro + r'\(([^)]*)\)', body)
    return [a.strip() for a in m.group(1).split(',')] if m else None


def _balanced_after(body, pos):
    """Given body[pos] == '(', return index after the matching ')'."""
    depth = 0
    for j in range(pos, len(body)):
        if body[j] == '(':
            depth += 1
        elif body[j] == ')':
            depth -= 1
            if depth == 0:
                return j + 1
    return -1


def _split_top(s, sep=','):
    parts, depth, cur = [], 0, ''
    for c in s:
        if c in '({':
            depth += 1
        elif c in ')}':
            depth -= 1
        if c == sep and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += c
    if cur.strip():
        parts.append(cur)
    return [p.strip() for p in parts]


def _eval_condition(cond):
    expr = re.sub(r'\bGEN_(\d)\b', r'\1', cond)
    expr = re.sub(r'\bGEN_LATEST\b', '9', expr)
    expr = re.sub(r'\b(P_\w+)\b', lambda m: str(_config_gen(m.group(1))), expr)
    expr = expr.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ').replace(' not =', '!=')
    expr = re.sub(r'\bTRUE\b', '1', re.sub(r'\bFALSE\b', '0', expr))
    if not re.fullmatch(r'[\d\s()<>=!andortTRUEFALSE]*', expr):
        return True
    try:
        return bool(eval(expr, {'__builtins__': {}}, {}))
    except Exception:
        return True


def _preprocess(text):
    """Keep only the lines that the current settings use."""
    out, stack = [], []
    for line in text.split('\n'):
        t = line.strip()
        if t.startswith('#if'):
            cond = t[3:].strip()
            if t.startswith('#ifdef'):
                cond = '1'
            stack.append([_eval_condition(cond), False])
            stack[-1][1] = stack[-1][0]
            continue
        if t.startswith('#elif') and stack:
            hit = not stack[-1][1] and _eval_condition(t[5:].strip())
            stack[-1][0] = hit
            stack[-1][1] = stack[-1][1] or hit
            continue
        if t.startswith('#else') and stack:
            stack[-1][0] = not stack[-1][1]
            continue
        if t.startswith('#endif') and stack:
            stack.pop()
            continue
        if all(a for a, _ in stack):
            out.append(line)
    return '\n'.join(out)


_DEFS_CACHE = {}


def _file_defines(path, text):
    """Single-line #defines in a species file, using the branch the settings select."""
    key = (path, len(text), hash(text))
    if key not in _DEFS_CACHE:
        _DEFS_CACHE.clear()
        defs = {}
        for name, value in re.findall(r'^[ \t]*#define[ \t]+([A-Z_][A-Z0-9_]*)[ \t]+([^\n\\]+?)[ \t]*$', _preprocess(text), re.M):
            defs.setdefault(name, value.strip())
        _DEFS_CACHE[key] = defs
    return _DEFS_CACHE[key]


def _expand(value, defs):
    for _ in range(5):
        if value in defs:
            value = defs[value]
        else:
            break
    return resolve(value)


def _evolutions(body):
    m = re.search(r'\.evolutions\s*=\s*EVOLUTION\(', body)
    if not m:
        return {'entries': [], 'editable': True}
    open_paren = m.end() - 1
    close = _balanced_after(body, open_paren)
    inner = body[open_paren + 1:close - 1]
    flattened = '#' in inner
    if flattened:
        inner = _preprocess(inner)
    entries = []
    for part in _split_top(inner):
        if not (part.startswith('{') and part.endswith('}')):
            return {'entries': [], 'editable': False, 'raw': inner.strip()}
        fields = _split_top(part[1:-1])
        if len(fields) < 3:
            return {'entries': [], 'editable': False, 'raw': inner.strip()}
        entries.append({'method': fields[0], 'param': fields[1], 'target': fields[2],
                        'conditions': ', '.join(fields[3:])})
    return {'entries': entries, 'editable': True, 'flattened': flattened}


def _description(body):
    m = re.search(r'\.description\s*=\s*COMPOUND_STRING\(', body)
    if not m:
        return None
    close = _balanced_after(body, m.end() - 1)
    inner = body[m.end():close - 1]
    if '#' in inner:
        return None
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', inner)
    return ''.join(parts).replace('\\n', '\n')


# ---- learnsets ---------------------------------------------------------------

def active_learnset_file():
    """The level-up learnset file the build uses, from P_LVL_UP_LEARNSETS."""
    cfg = read_text(os.path.join(ROOT, 'include/config/pokemon.h'))
    m = re.search(r'#define\s+P_LVL_UP_LEARNSETS\s+(\w+)', cfg)
    value = m.group(1) if m else 'GEN_LATEST'
    gen = 9 if value in ('GEN_LATEST', 'GEN_CHAMPIONS') else int(value[4:]) if re.fullmatch(r'GEN_\d', value) else 9
    return os.path.join(LEARNSET_DIR, 'gen_%d.h' % gen), gen


def _learnset_block(text, symbol):
    m = re.search(r'static const struct LevelUpMove ' + re.escape(symbol) + r'\[\]\s*=\s*\{', text)
    if not m:
        return None
    end = text.find('};', m.end())
    return m.end(), end


def read_learnset(symbol):
    path, gen = active_learnset_file()
    info = {'file': os.path.relpath(path, ROOT), 'gen': gen, 'moves': [], 'editable': False}
    if not symbol or not os.path.exists(path):
        return info
    text = read_text(path)
    block = _learnset_block(text, symbol)
    if not block:
        return info
    inner = text[block[0]:block[1]]
    info['editable'] = '#' not in inner
    info['moves'] = [[int(lv), mv] for lv, mv in re.findall(r'LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_\w+)\s*\)', inner)]
    return info


def write_learnset(symbol, moves):
    path, _ = active_learnset_file()
    text = read_text(path)
    block = _learnset_block(text, symbol)
    if not block:
        raise SpeciesError('This Pokemon has no level-up list in ' + os.path.basename(path))
    if '#' in text[block[0]:block[1]]:
        raise SpeciesError('This level-up list depends on settings and cannot be edited here.')
    moves = sorted(((int(lv), mv) for lv, mv in moves), key=lambda x: x[0])
    for lv, mv in moves:
        if not (0 <= lv <= 100) or not re.fullmatch(r'MOVE_\w+', mv):
            raise SpeciesError('Bad level-up move: %s at %s' % (mv, lv))
    lines = ['\n'] + ['    LEVEL_UP_MOVE(%2d, %s),\n' % (lv, mv) for lv, mv in moves] + ['    LEVEL_UP_END\n']
    write_text(path, text[:block[0]] + ''.join(lines) + text[block[1]:])


# ---- public API --------------------------------------------------------------

def read(species_id):
    path, text, start, end = _find(species_id)
    extent = _body_extent(text, start, end)
    out = {'id': species_id, 'file': os.path.relpath(path, ROOT), 'editable': extent is not None, 'varies': []}
    if extent is None:
        out['note'] = 'This form is built from a shared template, so its data cannot be edited here.'
        return out
    body = text[extent[0]:extent[1]]
    _CFG.clear()
    defs = _file_defines(path, text)
    for name in SIMPLE + OPTIONAL:
        vals = _values(body, name)
        out[name] = _expand(vals[0], defs) if vals else ''
        if len(set(vals)) > 1 or (vals and out[name] != vals[0]):
            out['varies'].append(name)
    tm = re.search(r'\.types\s*=\s*(MON_TYPES\([^)]*\)|\w+)', body)
    types = None
    if tm:
        raw = _expand(tm.group(1), defs)
        inner = re.match(r'^(?:MON_TYPES\((.*)\)|\{(.*)\})$', raw.strip())
        if inner:
            types = [_expand(t.strip(), defs) for t in (inner.group(1) or inner.group(2)).split(',') if t.strip()]
            if len(types) == 2 and types[0] == types[1]:
                types = types[:1]
            if raw != tm.group(1) or any(t != x.strip() for t, x in zip(types, (inner.group(1) or inner.group(2)).split(','))):
                out['varies'].append('types')
    out['typesEditable'] = types is not None
    out['types'] = types or []
    if len(re.findall(r'\.types\s*=', body)) > 1 and 'types' not in out['varies']:
        out['varies'].append('types')
    out['eggGroups'] = _call_args(body, 'eggGroups', 'MON_EGG_GROUPS') or []
    am = re.findall(r'\.abilities\s*=\s*(\{[^}]*\}|\w+)', body)
    ab_raw = _expand(am[0], defs) if am else ''
    out['abilities'] = [a.strip() for a in ab_raw.strip('{} ').split(',')] if ab_raw.startswith('{') else []
    if len(set(am)) > 1 or (am and ab_raw != am[0]):
        out['varies'].append('abilities')
    if not out['baseHP']:
        out['editable'] = False
        out['note'] = 'This form is built from a shared template, so its data cannot be edited here.'
        return out
    g = _values(body, 'genderRatio')
    out['genderRatio'] = g[0] if g else ''
    name = re.search(r'\.speciesName\s*=\s*_\("((?:[^"\\]|\\.)*)"\)', body)
    out['speciesName'] = name.group(1) if name else ''
    cat = re.search(r'\.categoryName\s*=\s*_\("((?:[^"\\]|\\.)*)"\)', body)
    out['categoryName'] = cat.group(1) if cat else ''
    out['description'] = _description(body)
    out['evolutions'] = _evolutions(body)
    sym = re.search(r'\.levelUpLearnset\s*=\s*(\w+)', body)
    out['learnsetSymbol'] = sym.group(1) if sym else ''
    out['learnset'] = read_learnset(out['learnsetSymbol'])
    return out


def _replace_all(body, name, value):
    pattern = _field_re(name)
    if pattern.search(body):
        return pattern.sub(lambda m: m.group(1) + value + m.group(3), body)
    return None


def _insert_line(body, line, after_fields=('expYield', 'catchRate', 'baseSpDefense')):
    for f in after_fields:
        m = re.search(r'^([ \t]*)\.' + f + r'\s*=[^\n]*\n', body, re.M)
        if m:
            return body[:m.end()] + m.group(1) + line + '\n' + body[m.end():]
    raise SpeciesError('Could not find where to add ' + line)


def _check(value, pattern, what):
    if not re.fullmatch(pattern, str(value).strip()):
        raise SpeciesError('Bad %s: %r' % (what, value))
    return str(value).strip()


def save(species_id, changes):
    path, text, start, end = _find(species_id)
    extent = _body_extent(text, start, end)
    if extent is None:
        raise SpeciesError('This form cannot be edited here.')
    body = text[extent[0]:extent[1]]
    num = r'\d{1,5}'

    for name in STATS + ['catchRate', 'expYield', 'eggCycles', 'height', 'weight']:
        if name in changes:
            v = _check(changes[name], num, name)
            new = _replace_all(body, name, v)
            if new is None:
                body = _insert_line(body, '.%s = %s,' % (name, v))
            else:
                body = new
    if 'friendship' in changes:
        v = _check(changes['friendship'], r'\d{1,3}|[A-Z_]+', 'friendship')
        body = _replace_all(body, 'friendship', v) or _insert_line(body, '.friendship = %s,' % v)
    if 'growthRate' in changes:
        v = _check(changes['growthRate'], r'GROWTH_[A-Z_]+', 'growth rate')
        body = _replace_all(body, 'growthRate', v) or _insert_line(body, '.growthRate = %s,' % v)
    for name in EVS:
        if name in changes:
            v = _check(changes[name] or '0', r'[0-3]', name)
            new = _replace_all(body, name, v)
            if new is not None:
                body = new
            elif v != '0':
                body = _insert_line(body, '.%s = %s,' % (name, v))
    for name in ('itemCommon', 'itemRare'):
        if name in changes:
            v = (changes[name] or '').strip()
            if v and not re.fullmatch(r'ITEM_\w+', v):
                raise SpeciesError('Bad held item: ' + v)
            if v:
                body = _replace_all(body, name, v) or _insert_line(body, '.%s = %s,' % (name, v))
            else:
                body = re.sub(r'^[ \t]*\.' + name + r'\s*=[^\n]*\n', '', body, flags=re.M)
    if 'types' in changes:
        types = [_check(t, r'TYPE_[A-Z]+', 'type') for t in changes['types'] if t]
        if not 1 <= len(types) <= 2:
            raise SpeciesError('A Pokemon needs one or two types.')
        body = re.sub(r'(\.types\s*=\s*)(?:MON_TYPES\([^)]*\)|[A-Z_][A-Z0-9_]*)', lambda m: m.group(1) + 'MON_TYPES(%s)' % ', '.join(types), body)
    if 'eggGroups' in changes:
        groups = [_check(t, r'EGG_GROUP_[A-Z0-9_]+', 'egg group') for t in changes['eggGroups'] if t]
        if not 1 <= len(groups) <= 2:
            raise SpeciesError('A Pokemon needs one or two egg groups.')
        body = re.sub(r'(\.eggGroups\s*=\s*)MON_EGG_GROUPS\([^)]*\)', lambda m: m.group(1) + 'MON_EGG_GROUPS(%s)' % ', '.join(groups), body)
    if 'abilities' in changes:
        ab = [(_check(a, r'ABILITY_[A-Z0-9_]+', 'ability') if a else 'ABILITY_NONE') for a in changes['abilities']]
        ab = (ab + ['ABILITY_NONE'] * 3)[:3]
        body = re.sub(r'(\.abilities\s*=\s*)(?:\{[^}]*\}|[A-Z_][A-Z0-9_]*)', lambda m: m.group(1) + '{ %s }' % ', '.join(ab), body)
    if 'genderRatio' in changes:
        v = _check(changes['genderRatio'], r'MON_MALE|MON_FEMALE|MON_GENDERLESS|PERCENT_FEMALE\(\d{1,3}(\.\d+)?\)', 'gender ratio')
        body = _replace_all(body, 'genderRatio', v) or _insert_line(body, '.genderRatio = %s,' % v)
    for key in ('speciesName', 'categoryName'):
        if key in changes:
            v = changes[key].replace('"', '').strip()
            if not v or len(v) > 12 or '\\' in v:
                raise SpeciesError('Names must be 1 to 12 characters.')
            body = re.sub(r'(\.' + key + r'\s*=\s*_\(")(?:[^"\\]|\\.)*("\))', lambda m: m.group(1) + v + m.group(2), body)
    if 'description' in changes and changes['description'] is not None:
        m = re.search(r'\.description\s*=\s*COMPOUND_STRING\(', body)
        if m:
            close = _balanced_after(body, m.end() - 1)
            indent = re.search(r'([ \t]*)\.description', body).group(1) + '    '
            lines = changes['description'].replace('\r', '').replace('"', '\\"').split('\n')
            parts = ['"%s\\n"' % l for l in lines[:-1]] + ['"%s"' % lines[-1]]
            body = body[:m.end()] + '\n' + '\n'.join(indent + p for p in parts) + ')' + body[close:]
    if 'evolutions' in changes:
        entries = []
        for e in changes['evolutions']:
            method = _check(e['method'], r'EVO_[A-Z_]+', 'evolution method')
            param = _check(e.get('param') or '0', r'[A-Z0-9_]+', 'evolution value')
            target = _check(e['target'], r'SPECIES_[A-Z0-9_]+', 'evolution target')
            cond = (e.get('conditions') or '').strip()
            if cond and not re.fullmatch(r'CONDITIONS\([\w\s,{}()]*\)', cond):
                raise SpeciesError('Bad evolution condition: ' + cond)
            entries.append('{%s}' % ', '.join([method, param, target] + ([cond] if cond else [])))
        m = re.search(r'\.evolutions\s*=\s*EVOLUTION\(', body)
        if m:
            inner = body[m.end():_balanced_after(body, m.end() - 1) - 1]
            close = _balanced_after(body, m.end() - 1)
            if entries:
                body = body[:m.end()] + ',\n                                '.join(entries) + ')' + body[close:]
            else:
                line_start = body.rfind('\n', 0, m.start()) + 1
                line_end = body.find('\n', close)
                body = body[:line_start] + body[line_end + 1:]
        elif entries:
            closing = body.rstrip().rfind('}')
            indent = re.search(r'\n([ \t]*)\.\w', body).group(1)
            body = body[:closing].rstrip() + '\n' + indent + '.evolutions = EVOLUTION(%s),\n    ' % ', '.join(entries) + body[closing:]

    text = text[:extent[0]] + body + text[extent[1]:]
    write_text(path, text)

    if 'learnset' in changes:
        sym = re.search(r'\.levelUpLearnset\s*=\s*(\w+)', body)
        if not sym:
            raise SpeciesError('This Pokemon has no level-up move list.')
        write_learnset(sym.group(1), changes['learnset'])
    return read(species_id)


def lists():
    """Constants the data tab offers in dropdowns."""
    pk = read_text(os.path.join(ROOT, 'include/constants/pokemon.h'))
    growth = re.findall(r'^\s*(GROWTH_[A-Z_]+)\s*,', pk, re.M)
    eggs = [e for e in re.findall(r'^\s*(EGG_GROUP_[A-Z0-9_]+)\s*,', pk, re.M) if e != 'EGG_GROUP_NONE']
    evo_enum = re.search(r'(EVO_NONE.*?)\};', pk, re.S)
    evos = re.findall(r'^\s*(EVO_[A-Z_]+)\s*,?', evo_enum.group(1), re.M) if evo_enum else []
    types = [t for t in re.findall(r'^\s*(TYPE_[A-Z]+)\s*=\s*\d+', pk, re.M) if t not in ('TYPE_NONE', 'TYPE_MYSTERY', 'TYPE_STELLAR')]
    return {'growth': growth, 'eggGroups': eggs, 'evoMethods': [e for e in evos if e != 'EVO_NONE'], 'types': types}
