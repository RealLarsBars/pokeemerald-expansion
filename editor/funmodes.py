"""Fun Modes: randomizers, hard mode, level caps and shop tweaks.

Every mode works on the game's own source files, the same ones the other
tabs edit. A run never writes anything until you press Apply: Preview runs
the exact same code on an in-memory copy (an Overlay) and lists what would
change. With the same seed and settings you always get the same result.
"""

import json
import os
import random
import re

import fundata
import sets
import trainers
import versions
from common import ROOT, read_text, write_text, species_const

PARTY = 'src/data/trainers.party'
WILD = 'src/data/wild_encounters.json'
STARTERS = 'src/starter_choose.c'
CAPS_CFG = 'include/fun_level_caps.h'  # only the few files that use level caps include it
CAPS_C = 'src/caps.c'
ITEMS = 'src/data/items.h'

BOSS_CLASSES = ('Leader', 'Elite Four', 'Champion', 'Magma Leader', 'Aqua Leader', 'Magma Admin', 'Aqua Admin', 'Rival')
STARTER_IDS = ('SPECIES_TREECKO', 'SPECIES_TORCHIC', 'SPECIES_MUDKIP')
GYM_LEADERS = ['TRAINER_ROXANNE_1', 'TRAINER_BRAWLY_1', 'TRAINER_WATTSON_1', 'TRAINER_FLANNERY_1',
               'TRAINER_NORMAN_1', 'TRAINER_WINONA_1', 'TRAINER_TATE_AND_LIZA_1', 'TRAINER_JUAN_1']
CHAMPION = 'TRAINER_WALLACE'


class Overlay:
    """Pending file changes. Reads see earlier writes from the same run."""

    def __init__(self):
        self.files = {}

    def read(self, rel):
        if rel in self.files:
            return self.files[rel]
        return read_text(os.path.join(ROOT, rel))

    def write(self, rel, text):
        if text != self.read(rel):
            self.files[rel] = text

    def write_bytes(self, rel, data):
        """For images. Not readable back through read()."""
        with open(os.path.join(ROOT, rel), 'rb') as f:
            if f.read() == data:
                return
        self.files[rel] = data

    def commit(self):
        for rel, text in self.files.items():
            if isinstance(text, bytes):
                with open(os.path.join(ROOT, rel), 'wb') as f:
                    f.write(text)
            else:
                write_text(os.path.join(ROOT, rel), text)
        return sorted(self.files)


class Report:
    def __init__(self):
        self.sections = []

    def add(self, title, lines, count=None):
        self.sections.append({'title': title, 'lines': lines[:400], 'count': len(lines) if count is None else count})


# ---- trainers.party in memory ---------------------------------------------------

class Party:
    def __init__(self, text):
        pf = trainers.PartyFile.__new__(trainers.PartyFile)
        pf.path = None
        pf.load_text(text)
        self.pf = pf

    def items(self):
        for b in self.pf.blocks:
            yield b[0], trainers.parse_block(b[1])

    def put(self, tid, t):
        b = self.pf.find(tid)
        b[1] = trainers.serialize_block(tid, t, t.get('_tail', '\n'))

    def text(self):
        return self.pf.preamble + ''.join(b[1] for b in self.pf.blocks)


def is_boss(tid, t):
    return trainers.field(t, 'Class') in BOSS_CLASSES or tid in ('TRAINER_STEVEN',)


def max_level(t):
    lv = [int(m.get('Level') or 0) for m in t['party'] if str(m.get('Level', '')).isdigit()]
    return max(lv) if lv else 0


def set_field(t, key, value):
    for f in t['fields']:
        if f[0] == key:
            f[1] = value
            return
    t['fields'].append([key, value])


def species_of(m):
    return species_const(m.get('species', ''))


def set_species(m, const, p):
    if species_of(m) == const:
        return
    m['species'] = fundata.showdown_name(const, p)
    for k in ('Ability', 'Gigantamax', 'Tera Type'):
        m.pop(k, None)
    m['gender'] = ''
    m['moves'] = []


def edited_trainers(text_now):
    """Trainers whose block differs from the base game (hand edits to keep)."""
    base = versions.base_file(PARTY)
    if not base:
        return set()
    old = dict((tid, txt.strip()) for tid, txt in Party(base).pf.blocks)
    return {tid for tid, txt in Party(text_now).pf.blocks if old.get(tid) != txt.strip()}


# ---- choosing Pokemon -------------------------------------------------------------

class Picker:
    def __init__(self, rng, legendaries=False):
        self.rng = rng
        self.p = fundata.pool()
        self.all = [i for i in fundata.usable(self.p) if legendaries or not i['legendary']]
        self.all.sort(key=lambda i: i['const'])

    def random(self, exclude=()):
        cands = [i for i in self.all if i['const'] not in exclude]
        return self.rng.choice(cands)['const']

    def similar(self, const, exclude=(), types=None, spread=0.1):
        info = self.p.get(const)
        bst = info['bst'] if info else 400
        cands = []
        s = spread
        while not cands and s < 2:
            cands = [i for i in self.all if abs(i['bst'] - bst) <= bst * s and i['const'] not in exclude
                     and (not types or set(types) & set(i['types']))]
            s += 0.1
        if not cands and types:
            return self.similar(const, exclude, None, spread)
        return self.rng.choice(cands)['const'] if cands else self.random(exclude)

    def of_type(self, type_, exclude=()):
        cands = [i for i in self.all if type_ in i['types'] and i['const'] not in exclude]
        return self.rng.choice(cands)['const'] if cands else self.random(exclude)


def theme_type(t, p):
    counts = {}
    for m in t['party']:
        info = p.get(species_of(m))
        for ty in (info or {}).get('types', []):
            counts[ty] = counts.get(ty, 0) + 1
    if not counts:
        return None
    ty, n = max(counts.items(), key=lambda kv: kv[1])
    return ty if n >= max(2, len(t['party']) * 0.6) else None


# ---- randomizers --------------------------------------------------------------------

def randomize_wild(ov, opt, rng, report):
    mode = opt.get('mode', 'similar')
    pick = Picker(rng, opt.get('legendaries', False))
    data = json.loads(ov.read(WILD))
    global_map = {}
    changes = []
    for group in data['wild_encounter_groups']:
        if not group.get('for_maps'):
            continue
        for enc in group['encounters']:
            area_map = {}
            for key, field in enc.items():
                if not isinstance(field, dict) or 'mons' not in field:
                    continue
                for mon in field['mons']:
                    old = mon['species']
                    if mode == 'global':
                        if old not in global_map:
                            global_map[old] = pick.similar(old, exclude=set(global_map.values()))
                        new = global_map[old]
                    else:
                        if old not in area_map:
                            new = pick.random() if mode == 'random' else pick.similar(old, exclude=set(area_map.values()))
                            area_map[old] = new
                        new = area_map[old]
                    mon['species'] = new
            label = enc.get('map', enc.get('base_label', '?')).replace('MAP_', '').replace('_', ' ').title()
            if area_map:
                changes.append('%s: %s' % (label, ', '.join('%s → %s' % (_n(a), _n(b)) for a, b in list(area_map.items())[:5])))
    if global_map:
        changes = ['%s → %s' % (_n(a), _n(b)) for a, b in sorted(global_map.items())]
    ov.write(WILD, json.dumps(data, indent=2) + '\n')
    report.add('Wild Pokémon', changes)


def _n(const):
    p = fundata.pool()
    return p[const]['name'] if const in p else const.replace('SPECIES_', '').title()


def starter_families():
    p = fundata.pool()
    fam = {}
    for i, s in enumerate(STARTER_IDS):
        for stage, c in enumerate(fundata.evolution_line(s, p)):
            fam[c] = (i, stage)
    return fam


def randomize_trainers(ov, opt, rng, report, keep=()):
    mode = opt.get('mode', 'similar')
    pick = Picker(rng, opt.get('legendaries', False))
    p = pick.p
    party = Party(ov.read(PARTY))
    fam = starter_families()
    lines = []
    for tid, t in party.items():
        if tid in keep or not t['party']:
            continue
        rival = trainers.field(t, 'Class') == 'Rival'
        theme = theme_type(t, p) if opt.get('keepTheme', True) and is_boss(tid, t) else None
        used = set()
        before = [m['species'] for m in t['party']]
        for m in t['party']:
            old = species_of(m)
            if rival and old in fam:
                continue  # handled by the starter randomizer
            if mode == 'random':
                new = pick.of_type(theme, used) if theme else pick.random(used)
            else:
                new = pick.similar(old, used, [theme] if theme else None)
            used.add(new)
            set_species(m, new, p)
        party.put(tid, t)
        after = [m['species'] for m in t['party']]
        if after != before:
            lines.append('%s %s: %s' % (trainers.field(t, 'Class'), trainers.field(t, 'Name'), ', '.join(after)))
    ov.write(PARTY, party.text())
    report.add('Trainer teams', lines)


def randomize_starters(ov, opt, rng, report):
    p = fundata.pool()
    mode = opt.get('mode', 'triangle')
    pick = Picker(rng, opt.get('legendaries', False))
    three_stage = [i for i in pick.all if i['stage'] == 1 and len(fundata.evolution_line(i['const'], p)) == 3]
    if mode == 'custom':
        new = [species_const(s) if not s.startswith('SPECIES_') else s for s in opt.get('species', [])][:3]
        for s in new:
            if s not in p:
                raise ValueError('Unknown Pokémon for a starter: %s' % s)
        if len(new) != 3:
            raise ValueError('Pick three starters.')
    elif mode == 'triangle':
        new = []
        for ty in ('TYPE_GRASS', 'TYPE_FIRE', 'TYPE_WATER'):
            c = [i['const'] for i in three_stage if ty in i['types']]
            new.append(rng.choice(c))
    else:
        pool = three_stage if opt.get('threeStage', True) else [i for i in pick.all if i['stage'] == 1]
        new = rng.sample([i['const'] for i in pool], 3)
    text = ov.read(STARTERS)
    for kind, s in zip(('GRASS', 'FIRE', 'WATER'), new):
        text, n = re.subn(r'(#define %s_STARTER\s*\(IS_FRLG \? SPECIES_\w+\s*:\s*)SPECIES_\w+(\s*\))' % kind,
                          lambda m: m.group(1) + s + m.group(2), text)
        if n != 1:
            raise ValueError('Could not find the %s starter in %s' % (kind.lower(), STARTERS))
    ov.write(STARTERS, text)

    # Rivals carry the starter you did not pick: swap each stage for the new line.
    lines_new = [fundata.evolution_line(s, p) for s in new]
    fam = starter_families()
    party = Party(ov.read(PARTY))
    for tid, t in party.items():
        if trainers.field(t, 'Class') != 'Rival':
            continue
        changed = False
        for m in t['party']:
            old = species_of(m)
            if old in fam:
                idx, stage = fam[old]
                line = lines_new[idx]
                set_species(m, line[min(stage, len(line) - 1)], p)
                changed = True
        if changed:
            party.put(tid, t)
    ov.write(PARTY, party.text())
    report.add('Starters', ['Grass slot: %s' % _n(new[0]), 'Fire slot: %s' % _n(new[1]), 'Water slot: %s' % _n(new[2]),
                            'Rival teams now use the matching new starter and its evolutions.'])


# ---- hard mode -------------------------------------------------------------------------

def _boss_pack():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fun', 'boss_teams.party')
    pf = trainers.PartyFile.__new__(trainers.PartyFile)
    pf.path = None
    pf.load_text(read_text(path))
    return {tid: trainers.parse_block(txt) for tid, txt in pf.blocks}


def hard_mode(ov, opt, rng, report, keep=()):
    p = fundata.pool()
    party = Party(ov.read(PARTY))
    pack = _boss_pack() if opt.get('bossTeams', True) else {}
    boost = int(opt.get('levelBoost', 10))
    double_pct = int(opt.get('doublesPercent', 20))
    double_min = int(opt.get('doublesMinLevel', 20))
    leg_level = int(opt.get('legendaryLevel', 0) or 0)
    leg_pct = int(opt.get('legendaryPercent', 15))
    regular_items = opt.get('regularItems', True)
    lines = []
    legends = [i for i in fundata.usable(p) if i['legendary']]
    for tid, t in party.items():
        if tid in keep or not t['party']:
            continue
        boss = is_boss(tid, t)
        notes = []
        if tid in pack:
            new = pack[tid]
            t['party'] = new['party']
            for k, v in new['fields']:
                set_field(t, k, v)
            notes.append('hand-built team')
            sets.build_team(t['party'], p, rng, boss=True, doubles=trainers.field(t, 'Double Battle') == 'Yes',
                            items=True, fill_only=True)
        else:
            for m in t['party']:
                lv = str(m.get('Level', ''))
                if lv.isdigit() and boost:
                    m['Level'] = str(min(100, max(1, round(int(lv) * (100 + boost) / 100))))
            # bosses get one extra Pokemon (up to 6) once past the first gym
            if boss and opt.get('biggerBossTeams', True) and 2 <= len(t['party']) < 6 and max_level(t) >= 18:
                theme = theme_type(t, p)
                pick = Picker(rng, False)
                ace = t['party'][-1]
                extra = pick.similar(species_of(ace), {species_of(m) for m in t['party']}, [theme] if theme else None)
                lv = max(1, int(ace.get('Level') or 10) - 2)
                newmon = {'species': fundata.showdown_name(extra, p), 'nickname': '', 'gender': '', 'item': '',
                          'moves': [], 'extra': [], 'Level': str(lv)}
                t['party'].insert(len(t['party']) - 1, newmon)
                notes.append('+%s' % _n(extra))
            # legendaries above a level
            if leg_level and max_level(t) >= leg_level and len(t['party']) >= 2:
                chance = 100 if boss else leg_pct
                if rng.randrange(100) < chance:
                    theme = theme_type(t, p)
                    restricted_ok = max_level(t) >= leg_level + 15
                    cands = [i for i in legends if restricted_ok or not i['isRestrictedLegendary']]
                    themed = [i for i in cands if theme and theme in i['types']]
                    choice = rng.choice(themed or cands)['const']
                    slot = len(t['party']) - 2 if boss else rng.randrange(len(t['party']))
                    set_species(t['party'][slot], choice, p)
                    notes.append('legendary %s' % _n(choice))
            # some trainers turn into double battles
            if (not boss and double_pct and len(t['party']) >= 2 and max_level(t) >= double_min
                    and trainers.field(t, 'Double Battle', 'No') != 'Yes' and rng.randrange(100) < double_pct):
                set_field(t, 'Double Battle', 'Yes')
                notes.append('double battle')
            doubles = trainers.field(t, 'Double Battle') == 'Yes'
            sets.build_team(t['party'], p, rng, boss=boss, doubles=doubles, items=boss or regular_items)
        set_field(t, 'AI', 'Smart Trainer' if boss else 'Basic Trainer / Smart Switching')
        party.put(tid, t)
        if notes and (boss or 'double battle' in notes or any(n.startswith('legendary') for n in notes)):
            lines.append('%s %s: %s' % (trainers.field(t, 'Class'), trainers.field(t, 'Name'), ', '.join(notes)))
    ov.write(PARTY, party.text())
    report.add('Hard mode', ['Every trainer: smarter AI and built movesets' + (', +%d%% levels' % boost if boost else '')] + lines)


# ---- level caps ---------------------------------------------------------------------------

def gym_caps(ov):
    party = Party(ov.read(PARTY))
    lv = {tid: max_level(t) for tid, t in party.items()}
    caps = [lv.get(g, 0) for g in GYM_LEADERS] + [lv.get(CHAMPION, 0)]
    return caps


def level_caps(ov, opt, report):
    kind = {'hard': 'EXP_CAP_HARD', 'soft': 'EXP_CAP_SOFT', 'off': 'EXP_CAP_NONE'}[opt.get('type', 'hard')]
    values = [('B_EXP_CAP_TYPE', kind),
              ('B_LEVEL_CAP_TYPE', 'LEVEL_CAP_NONE' if kind == 'EXP_CAP_NONE' else 'LEVEL_CAP_FLAG_LIST'),
              ('B_RARE_CANDY_CAP', 'TRUE' if opt.get('candyCap', True) else 'FALSE')]
    block = ''.join('#undef %s\n#define %s %s\n' % (name, name, value) for name, value in values)
    cfg = ov.read(CAPS_CFG)
    cfg = re.sub(r'(// FUN MODES LEVEL CAPS START\n).*?(// FUN MODES LEVEL CAPS END)',
                 lambda m: m.group(1) + block + m.group(2), cfg, flags=re.S)
    ov.write(CAPS_CFG, cfg)
    if kind == 'EXP_CAP_NONE':
        report.add('Level caps', ['Turned off'])
        return
    caps = opt.get('caps') if opt.get('mode') == 'custom' else gym_caps(ov)
    caps = [max(1, min(100, int(c))) for c in caps][:9]
    text = ov.read(CAPS_C)
    m = re.search(r'(sLevelCapFlagMap\[\]\[2\]\s*=\s*\{)(.*?)(\n\s*\};)', text, re.S)
    if not m:
        raise ValueError('Could not find the level cap list in src/caps.c')
    rows = re.findall(r'\{(FLAG_\w+),\s*\d+\}', m.group(2))
    body = m.group(2)
    for flag, cap in zip(rows, caps):
        body = re.sub(r'\{' + flag + r',\s*\d+\}', '{%s, %d}' % (flag, cap), body)
    ov.write(CAPS_C, text[:m.start(2)] + body + text[m.end(2):])
    names = ['Badge %d' % (i + 1) for i in range(8)] + ['Champion']
    report.add('Level caps', ['%s type. Until %s: level %d' % (opt.get('type', 'hard').title(), n, c) for n, c in zip(names, caps)])


# ---- shops --------------------------------------------------------------------------------

def free_rare_candy(ov, report):
    text = ov.read(ITEMS)
    m = re.search(r'\[ITEM_RARE_CANDY\]\s*=\s*\{.*?\n\s*\.price\s*=\s*([^\n]+),', text, re.S)
    if not m:
        raise ValueError('Could not find the Rare Candy price in src/data/items.h')
    ov.write(ITEMS, text[:m.start(1)] + '0' + text[m.end(1):])
    count = 0
    import glob
    for path in sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc'))):
        rel = os.path.relpath(path, ROOT)
        s = ov.read(rel)
        labels = set(re.findall(r'^\s*pokemart\s+(\w+)', s, re.M))
        if not labels:
            continue
        for label in labels:
            lm = re.search(r'^' + label + r'::?\s*\n((?:\s*\.2byte\s+\w+\s*\n)+)', s, re.M)
            if not lm or 'ITEM_RARE_CANDY' in lm.group(1):
                continue
            s = s[:lm.start(1)] + '\t.2byte ITEM_RARE_CANDY\n' + s[lm.start(1):]
            count += 1
        ov.write(rel, s)
    report.add('Shops', ['Rare Candy costs ₽0 and is sold in all %d Poké Mart lists' % count])


def check_party(text):
    """Every species, move, item and ability in trainers.party must exist, or the build breaks."""
    import gamedata
    from common import to_const
    gd = gamedata.load()
    known = {k: {x['const'] if isinstance(x, dict) else x for x in gd[k]} for k in ('items', 'abilities')}
    p = fundata.pool()
    mv = fundata.moves()
    problems = []
    for tid, t in Party(text).items():
        for m in t['party']:
            s = species_of(m)
            if s not in p:
                problems.append('%s: unknown Pokémon %s' % (tid, m['species']))
                continue
            if m.get('Ability') and to_const('ABILITY', m['Ability']) not in p[s]['abilities']:
                problems.append('%s: %s cannot have %s' % (tid, m['species'], m['Ability']))
            if m.get('item') and to_const('ITEM', m['item']) not in known['items']:
                problems.append('%s: unknown item %s' % (tid, m['item']))
            for x in m.get('moves', []):
                if to_const('MOVE', x) not in mv:
                    problems.append('%s: unknown move %s' % (tid, x))
    return problems


# ---- running a plan -----------------------------------------------------------------------

def run(settings, apply=False):
    """settings: {seed, wild:{on,...}, trainers:{...}, starters:{...}, hard:{...}, caps:{...}, candy:{on}, comedy:{...}}"""
    import comedy
    seed = str(settings.get('seed') or '').strip() or str(random.randrange(10 ** 8))
    ov = Overlay()
    report = Report()
    fundata.reset_caches()

    def rng(part):
        return random.Random('%s:%s' % (seed, part))
    keep = set()
    if settings.get('keepEdited'):
        keep = edited_trainers(ov.read(PARTY))
        if keep:
            report.add('Kept as you edited them', sorted(keep))
    on = lambda k: settings.get(k, {}).get('on')  # noqa: E731
    if on('starters'):
        randomize_starters(ov, settings['starters'], rng('starters'), report)
    if on('wild'):
        randomize_wild(ov, settings['wild'], rng('wild'), report)
    if on('trainers'):
        randomize_trainers(ov, settings['trainers'], rng('trainers'), report, keep)
    if on('hard'):
        hard_mode(ov, settings['hard'], rng('hard'), report, keep)
    if on('caps'):
        level_caps(ov, settings['caps'], report)
    if on('candy'):
        free_rare_candy(ov, report)
    if on('comedy'):
        comedy.apply(ov, settings['comedy'], rng('comedy'), report)
    if PARTY in ov.files:
        problems = check_party(ov.files[PARTY])
        if problems:
            report.add('Problems (nothing was applied)', problems)
            apply = False
    files = sorted(ov.files)
    result = {'seed': seed, 'files': files, 'report': report.sections, 'applied': False}
    if apply and files:
        versions.before_fun()
        ov.commit()
        versions.record_fun({'seed': seed, 'modes': [s['title'] for s in report.sections]})
        result['applied'] = True
    return result
