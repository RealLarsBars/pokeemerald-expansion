"""Reads and writes src/data/trainers.party (Showdown-style trainer teams).

Only trainers you actually edit are rewritten; every other line of the file
stays byte-for-byte the same."""

import os
import re

from common import ROOT, read_text, write_text, to_const, species_const

PARTY_FILE = os.path.join(ROOT, 'src/data/trainers.party')
HEADER_RE = re.compile(r'^=== *(\S+) *=== *$')
COMMENT_RE = re.compile(r'/\*.*?\*/', re.S)

# Pokemon keys trainerproc understands, in the order the editor writes them.
MON_KEYS = ['Level', 'Ability', 'Tera Type', 'EVs', 'IVs', 'Ball', 'Happiness', 'Nature',
            'Shiny', 'Dynamax Level', 'Gigantamax', 'Tags']


class PartyFile:
    def __init__(self, path=PARTY_FILE):
        self.path = path
        self.mtime = None
        self.preamble = ''
        self.blocks = []  # list of [trainer_id, text]
        self.load()

    def load(self):
        text = read_text(self.path)
        self.mtime = os.path.getmtime(self.path)
        lines = text.splitlines(keepends=True)
        starts = [i for i, l in enumerate(lines) if HEADER_RE.match(l.rstrip('\r\n'))]
        self.preamble = ''.join(lines[:starts[0]]) if starts else text
        self.blocks = []
        for n, s in enumerate(starts):
            e = starts[n + 1] if n + 1 < len(starts) else len(lines)
            tid = HEADER_RE.match(lines[s].rstrip('\r\n')).group(1)
            self.blocks.append([tid, ''.join(lines[s:e])])

    def refresh(self):
        if os.path.getmtime(self.path) != self.mtime:
            self.load()

    def save(self):
        write_text(self.path, self.preamble + ''.join(b[1] for b in self.blocks))
        self.mtime = os.path.getmtime(self.path)

    def ids(self):
        return [b[0] for b in self.blocks]

    def find(self, tid):
        for b in self.blocks:
            if b[0] == tid:
                return b
        return None

    def get(self, tid):
        b = self.find(tid)
        return parse_block(b[1]) if b else None

    def put(self, tid, trainer):
        b = self.find(tid)
        if b is None:
            raise KeyError(tid)
        old = parse_block(b[1])
        b[1] = serialize_block(tid, trainer, old.get('_tail', '\n'))
        self.save()

    def add(self, tid, trainer):
        if self.find(tid):
            raise ValueError(tid + ' already exists')
        if self.blocks and not self.blocks[-1][1].endswith('\n\n'):
            self.blocks[-1][1] = self.blocks[-1][1].rstrip('\n') + '\n\n'
        self.blocks.append([tid, serialize_block(tid, trainer, '\n')])
        self.save()


def _split_tail(body):
    """Split trailing blank lines and comments (which belong to the next trainer) off a block."""
    end = len(body)
    while True:
        stripped = body[:end].rstrip()
        if stripped.endswith('*/'):
            start = stripped.rfind('/*')
            if start < 0:
                break
            end = start
            continue
        end = len(stripped)
        break
    return body[:end], body[end:]


def parse_block(text):
    first, _, rest = text.partition('\n')
    tid = HEADER_RE.match(first.rstrip('\r')).group(1)
    body, tail = _split_tail(rest)
    # tail starts with the newline that ends the trainer's last line
    tail = tail[1:] if tail.startswith('\n') else tail
    body = COMMENT_RE.sub('', body)
    paragraphs = [p for p in re.split(r'\n\s*\n', body.strip('\n')) if p.strip()]
    fields = []
    party = []
    if paragraphs:
        for line in paragraphs[0].splitlines():
            line = line.strip()
            if not line:
                continue
            key, _, value = line.partition(':')
            fields.append([key.strip(), value.strip()])
        for p in paragraphs[1:]:
            party.append(parse_mon(p))
    return {'id': tid, 'fields': fields, 'party': party, '_tail': tail}


def parse_mon(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    mon = {'species': '', 'nickname': '', 'gender': '', 'item': '', 'moves': [], 'extra': []}
    if not lines:
        return mon
    head = lines[0]
    if ' @ ' in head:
        head, _, item = head.partition(' @ ')
        mon['item'] = item.strip()
    elif head.endswith('@'):
        head = head[:-1]
    head = head.strip()
    g = re.search(r'\s*\((M|F)\)$', head)
    if g:
        mon['gender'] = g.group(1)
        head = head[:g.start()].strip()
    n = re.match(r'^(.*\S)\s*\(([^()]+)\)$', head)
    if n:
        mon['nickname'], mon['species'] = n.group(1).strip(), n.group(2).strip()
    else:
        mon['species'] = head
    for line in lines[1:]:
        if line.startswith('- '):
            mon['moves'].append(line[2:].strip())
            continue
        m = re.match(r'^(\w+) Nature$', line)
        if m:
            mon['Nature'] = m.group(1)
            continue
        key, sep, value = line.partition(':')
        key = key.strip()
        if not sep:
            mon['extra'].append(line)
        elif key in MON_KEYS:
            mon[key] = value.strip()
        else:
            mon['extra'].append(line)
    return mon


def serialize_mon(mon):
    head = mon.get('species', '').strip()
    if mon.get('nickname', '').strip():
        head = '%s (%s)' % (mon['nickname'].strip(), head)
    if mon.get('gender') in ('M', 'F'):
        head += ' (%s)' % mon['gender']
    if mon.get('item', '').strip():
        head += ' @ ' + mon['item'].strip()
    out = [head]
    for key in MON_KEYS:
        value = str(mon.get(key, '') or '').strip()
        if value:
            out.append('%s: %s' % (key, value))
    out.extend(l for l in mon.get('extra', []) if l.strip())
    for move in mon.get('moves', []):
        if move and move.strip():
            out.append('- ' + move.strip())
    return '\n'.join(out)


def serialize_block(tid, trainer, tail='\n'):
    """tail: text kept after the trainer (blank line, comments for the next one)."""
    out = ['=== %s ===' % tid]
    for key, value in trainer.get('fields', []):
        key, value = key.strip(), str(value).strip()
        if not key:
            continue
        if not value and key not in ('Name',):
            continue
        out.append('%s: %s' % (key, value) if value else key + ':')
    text = '\n'.join(out) + '\n'
    for mon in trainer.get('party', []):
        if mon.get('species', '').strip():
            text += '\n' + serialize_mon(mon) + '\n'
    return text + tail


def parse_showdown(text):
    """Parse a pasted Showdown team. Returns (party, warnings)."""
    text = text.replace('\r', '')
    party, warnings = [], []
    for p in re.split(r'\n\s*\n', text.strip()):
        if not p.strip():
            continue
        mon = parse_mon(p)
        dropped = mon.get('extra', [])
        if dropped:
            warnings.append('%s: skipped lines the game does not use: %s' % (mon['species'], '; '.join(dropped)))
            mon['extra'] = []
        party.append(mon)
    if len(party) > 6:
        warnings.append('Only the first 6 Pokemon were kept.')
        party = party[:6]
    return party, warnings


def field(trainer, key, default=''):
    for k, v in trainer['fields']:
        if k == key:
            return v
    return default


def summary(trainer):
    return {
        'id': trainer['id'],
        'name': field(trainer, 'Name'),
        'class': field(trainer, 'Class'),
        'pic': to_const('TRAINER_PIC', field(trainer, 'Pic')),
        'party': [species_const(m['species']) for m in trainer['party']],
        'levels': [m.get('Level', '') for m in trainer['party']],
    }
