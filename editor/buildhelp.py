"""Turns a failed build's output into plain words: what went wrong, where
(which trainer, map, text or setting), and how to fix it."""

import os
import re

from common import ROOT, map_display_name

# file:line[:col]: [fatal] error: message   (gcc, trainerproc, preproc)
ERR_RE = re.compile(r'^(?P<file>[\w./-]+):(?P<line>\d+)(?::\d+)?: (?:fatal )?(?:error|Error): ?(?P<msg>.*)$')
NO_RULE_RE = re.compile(r"No rule to make target '(?P<target>[^']+)'(?:, needed by '(?P<by>[^']+)')?")
OVERFLOW_RE = re.compile(r"region `(?P<region>\w+)' overflowed by (?P<bytes>\d+) bytes")
UNDEF_RE = re.compile(r"undefined reference to `(?P<name>[^']+)'")
UNDECLARED_RE = re.compile(r"'(?P<name>\w+)' undeclared")
GENERIC_RE = re.compile(r'(error|fatal|failed|Error)', re.I)


def _trainer_at(line):
    """The trainer whose block holds this line of trainers.party."""
    path = os.path.join(ROOT, 'src/data/trainers.party')
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    for i in range(min(line, len(lines)) - 1, -1, -1):
        m = re.match(r'^=== *(\S+) *=== *$', lines[i])
        if m:
            name = cls = ''
            for l in lines[i + 1:i + 6]:
                if l.startswith('Name:'):
                    name = l.split(':', 1)[1].strip()
                elif l.startswith('Class:'):
                    cls = l.split(':', 1)[1].strip()
            return {'id': m.group(1), 'name': ('%s %s' % (cls, name)).strip() or m.group(1)}
    return None


def place(rel, line=None):
    """Where a file lives in the editor: a description and how to open it."""
    rel = rel.lstrip('./')
    parts = rel.split('/')
    if rel == 'src/data/trainers.party':
        t = _trainer_at(line) if line else None
        if t:
            return {'where': 'the trainer %s' % t['name'], 'open': {'view': 'trainers', 'id': t['id']}}
        return {'where': 'a trainer team', 'open': {'view': 'trainers'}}
    if rel.startswith('data/maps/') and len(parts) >= 4:
        name = map_display_name(parts[2])
        if parts[3] == 'scripts.inc':
            return {'where': 'what happens on %s (its script)' % name, 'open': {'view': 'scripts', 'path': rel, 'line': line}}
        if parts[3] == 'text.inc':
            return {'where': 'a text on %s' % name, 'open': {'view': 'scripts', 'path': rel, 'line': line}}
        return {'where': 'the map %s' % name, 'open': {'view': 'maps', 'map': parts[2]}}
    if rel.startswith('data/text/') or rel.startswith('data/scripts/'):
        return {'where': 'a shared script or text (%s)' % parts[-1], 'open': {'view': 'scripts', 'path': rel, 'line': line}}
    if rel.startswith('include/config/'):
        return {'where': 'a game setting (%s)' % parts[-1], 'open': {'view': 'settings'}}
    if rel.startswith('src/data/pokemon/'):
        return {'where': 'Pokémon data', 'open': {'view': 'pokemon'}}
    if rel in ('src/data/moves_info.h',):
        return {'where': 'a move', 'open': {'view': 'moves'}}
    if rel in ('src/data/items.h',):
        return {'where': 'an item', 'open': {'view': 'moves'}}
    if rel == 'src/data/wild_encounters.json':
        return {'where': 'wild Pokémon on a map', 'open': {'view': 'maps'}}
    if rel == 'include/constants/opponents.h':
        return {'where': 'the list of trainers', 'open': {'view': 'trainers'}}
    if rel.startswith('graphics/'):
        return {'where': 'a picture (%s)' % rel, 'open': None}
    return {'where': 'a game file (%s)' % rel, 'open': None}


KINDS = (('SPECIES_', 'the Pokémon'), ('MOVE_', 'the move'), ('ITEM_', 'the item'), ('ABILITY_', 'the ability'),
         ('TRAINER_PIC_', 'the battle picture'), ('TRAINER_CLASS_', 'the trainer class'), ('TRAINER_', 'the trainer'),
         ('FLAG_', 'the flag'), ('VAR_', 'the variable'), ('MAP_', 'the map'), ('TYPE_', 'the type'),
         ('OBJ_EVENT_GFX_', 'the overworld sprite'), ('MUS_', 'the music'), ('NATURE_', 'the nature'))


def _friendly_const(name):
    from common import pretty_name
    for prefix, word in KINDS:
        if name.startswith(prefix):
            return '%s "%s"' % (word, pretty_name(name[len(prefix):]))
    return 'the name %s' % name


def _plain(msg):
    """A compiler's message, said simply."""
    m = UNDECLARED_RE.search(msg)
    if m:
        name = m.group('name')
        guess = re.search(r"did you mean '(\w+)'", msg)
        what = _friendly_const(name)
        out = 'It uses %s, which the game does not know. It is probably a typo, or something that was renamed or removed.' % what
        if guess:
            out += ' Did you mean %s?' % _friendly_const(guess.group(1))
        return out
    low = msg.lower()
    m = re.search(r"bad instruction `(\w+)", msg)
    if m:
        return ('The script uses the command "%s", which the game does not know. Check its spelling '
                '(in the Scripts tab, "+ Insert..." adds commands spelled right).' % m.group(1))
    if 'unknown character' in low or 'unknown charmap' in low or 'not in charmap' in low:
        return 'A text uses a letter or symbol the Game Boy font does not have. Plain letters, numbers and common punctuation are safe.'
    if 'unterminated' in low or 'missing terminating' in low:
        return 'A text or line is missing its closing quote mark (").'
    if 'unknown pseudo-op' in low or 'bad instruction' in low or 'unknown opcode' in low:
        return 'A line in the script has a command the game does not understand. Check its spelling.'
    if 'junk at end of line' in low or 'bad expression' in low or 'syntax error' in low or 'expected' in low:
        return 'A line is written in a way the game cannot read (a stray character, a missing comma or a typo). The message was: %s' % msg
    if 'redefin' in low or 'already defined' in low or 'symbol' in low and 'defined' in low:
        return 'Two things have the same name. Each label or name must be used only once.'
    if 'mapped string longer' in low:
        return 'A text is too long for one string. Split it into two messages.'
    return msg[0].upper() + msg[1:] if msg else 'The build stopped with an error.'


def explain(log):
    """Finds the first real error in a build log. Returns a dict or None."""
    lines = [l.rstrip() for l in log]
    for i, l in enumerate(lines):
        m = ERR_RE.match(l.strip())
        if m:
            rel = m.group('file')
            line = int(m.group('line'))
            p = place(rel, line)
            return {'what': _plain(m.group('msg').strip()), 'where': p['where'], 'open': p['open'],
                    'file': rel, 'line': line, 'raw': l.strip()}
    for l in lines:
        m = OVERFLOW_RE.search(l)
        if m:
            what = ('The game got too big to fit: it is %s bytes over the limit for %s. Take out some of the newest '
                    'additions (big pictures, music or lots of new text), or go back to the last version that worked.'
                    % (m.group('bytes'), 'the cartridge' if m.group('region').lower() == 'rom' else 'the game\'s memory'))
            return {'what': what, 'where': '', 'open': None, 'raw': l.strip()}
    for l in lines:
        m = NO_RULE_RE.search(l)
        if m:
            target = m.group('target')
            by = m.group('by') or ''
            what = 'A file the game needs is missing: %s.' % target
            if target.startswith('graphics/'):
                what = 'A picture the game needs is missing: %s. It was probably renamed or deleted.' % target
            p = place(by) if by else {'where': '', 'open': None}
            return {'what': what, 'where': ('needed by ' + p['where']) if by else '', 'open': p['open'], 'raw': l.strip()}
    for l in lines:
        m = UNDEF_RE.search(l)
        if m:
            return {'what': ('Something refers to %s, but nothing in the game is called that. It was probably '
                             'renamed or removed.' % m.group('name')), 'where': '', 'open': None, 'raw': l.strip()}
    for l in reversed(lines):
        if GENERIC_RE.search(l) and not l.startswith('make') and 'Error 1' not in l:
            return {'what': l.strip(), 'where': '', 'open': None, 'raw': l.strip()}
    return None
