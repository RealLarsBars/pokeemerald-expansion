"""Reads and changes pokeemerald-expansion's feature switches in include/config/*.h.

Each simple line like
    #define B_CRIT_CHANCE   GEN_LATEST // Chances of landing a critical hit...
becomes one setting. Only the value is ever rewritten; spacing and the
comment stay as they are."""

import glob
import os
import re

from common import ROOT, read_text, write_text, project_path

CONFIG_DIR = os.path.join(ROOT, 'include/config')
DEFINE_RE = re.compile(r'^(?P<head>#define[ \t]+(?P<name>[A-Za-z_]\w*))(?P<gap>[ \t]+)(?P<value>[^/\n]*?)(?P<tail>[ \t]*(?://(?P<comment>.*))?)$')
SKIP_FILES = {'test.h'}

TITLES = {
    'ai.h': 'Battle AI', 'battle.h': 'Battle mechanics', 'caps.h': 'Level and EV caps',
    'contest.h': 'Contests', 'debug.h': 'Debug menu', 'dexnav.h': 'DexNav', 'fishing.h': 'Fishing',
    'follower_npc.h': 'Follower NPCs', 'general.h': 'General', 'item.h': 'Items',
    'map_preview_screen.h': 'Map preview screen', 'name_box.h': 'Name box above dialogue',
    'overworld.h': 'Overworld', 'pokedex_plus_hgss.h': 'Pokedex (HGSS style)', 'pokemon.h': 'Pokemon',
    'pokerus.h': 'Pokerus', 'quickstart.h': 'Quick start', 'save.h': 'Save data',
    'species_enabled.h': 'Which Pokemon are in the game', 'summary_screen.h': 'Summary screen',
    'text.h': 'Text', 'wild_encounter.h': 'Wild encounters',
}


def files():
    out = []
    for path in sorted(glob.glob(os.path.join(CONFIG_DIR, '*.h'))):
        fn = os.path.basename(path)
        if fn in SKIP_FILES:
            continue
        out.append({'file': fn, 'title': TITLES.get(fn, fn[:-2].replace('_', ' ').title())})
    return out


def _kind(value):
    v = value.strip()
    if v in ('TRUE', 'FALSE'):
        return 'bool'
    if re.fullmatch(r'GEN_(\d|LATEST|CHAMPIONS)', v):
        return 'gen'
    if re.fullmatch(r'-?\d+|0x[0-9A-Fa-f]+', v):
        return 'number'
    return 'text'


def read(fn):
    path = _path(fn)
    settings = []
    section = ''
    depth = 0  # inside #if blocks the same name may appear twice; keep the first
    seen = set()
    pending_comment = []
    for i, line in enumerate(read_text(path).split('\n')):
        stripped = line.strip()
        if stripped.startswith('#if'):
            depth += 1
        elif stripped.startswith('#endif'):
            depth = max(0, depth - 1)
        if stripped.startswith('//'):
            text = stripped.lstrip('/').strip()
            if text:
                pending_comment.append(text)
            continue
        if not stripped:
            if len(pending_comment) == 1 and len(pending_comment[0]) < 60:
                section = pending_comment[0]
            pending_comment = []
            continue
        m = DEFINE_RE.match(line)
        if m and not m.group('name').startswith(('GUARD_', 'GEN_')) and m.group('value').strip() and not line.rstrip().endswith('\\'):
            name = m.group('name')
            comment = (m.group('comment') or '').strip()
            if pending_comment:
                if comment and len(pending_comment) == 1 and len(pending_comment[0]) < 60:
                    section = pending_comment[0]
                elif not comment:
                    comment = ' '.join(pending_comment)
            if name not in seen:
                seen.add(name)
                settings.append({'name': name, 'value': m.group('value').strip(), 'kind': _kind(m.group('value')),
                                 'help': comment, 'section': section, 'line': i + 1})
        pending_comment = []
    return settings


def _path(fn):
    if not re.fullmatch(r'[a-z_]+\.h', fn) or fn in SKIP_FILES:
        raise ValueError('bad config file')
    path = project_path('include/config/' + fn)
    if not os.path.exists(path):
        raise ValueError('bad config file')
    return path


def save(fn, changes):
    """changes: {NAME: new value}. Returns the names that were changed."""
    path = _path(fn)
    lines = read_text(path).split('\n')
    done = set()
    for i, line in enumerate(lines):
        m = DEFINE_RE.match(line)
        if not m or m.group('name') not in changes or m.group('name') in done:
            continue
        name = m.group('name')
        new = str(changes[name]).strip()
        if not new or '\n' in new or '//' in new:
            raise ValueError('bad value for ' + name)
        old = m.group('value')
        if old.strip() == new:
            done.add(name)
            continue
        # keep the comment in the same column when the new value fits
        gap_after = m.group('tail')
        pad = len(old) - len(new)
        if gap_after.lstrip().startswith('//') and pad != 0:
            spaces = len(gap_after) - len(gap_after.lstrip())
            gap_after = ' ' * max(1, spaces + pad) + gap_after.lstrip()
        lines[i] = m.group('head') + m.group('gap') + new + gap_after
        done.add(name)
    write_text(path, '\n'.join(lines))
    return sorted(done)
