"""Universal Randomizer: every setting from the Universal Pokemon Randomizer
(ZX) that makes sense for Emerald, done as edits to the game's own source
files through Fun Modes' Overlay (nothing is written until Apply).

The groups match the randomizer's tabs:
  traits    base stats, types, abilities, evolutions, EXP curves, palettes
  starters  (in funmodes.py), static Pokemon, roamers, in-game trades,
            the catching tutorial
  moves     move data (power, accuracy, PP, type, category), level-up
            movesets, Metronome only
  tms       TM moves, TM compatibility, tutor moves, tutor compatibility
  trainers  (in funmodes.py) plus names, class names, levels, extra
            Pokemon, held items, fully evolved, double battles
  wild      (in funmodes.py) plus type-themed areas, catch 'em all,
            levels, catch rates, held items
  items     field items, hidden items, shops, Pickup
  types     the type chart
  misc      quality of life switches

Each function takes (ov, opt, rng, report) like the other Fun Modes.
"""

import colorsys
import glob
import json
import os
import re

import fundata
import movesets
import species as species_mod
from common import ROOT

INFO_GLOB = 'src/data/pokemon/species_info/gen_*.h'
MOVES_INFO = 'src/data/moves_info.h'
MOVES_H = 'include/constants/moves.h'
ABILITIES_H = 'include/constants/abilities.h'
TMS_H = 'include/constants/tms_hms.h'
LEARNABLES = 'src/data/pokemon/all_learnables.json'
TRADES = 'src/data/trade.h'
ITEMS = 'src/data/items.h'
PICKUP = 'src/battle_script_commands.c'
TYPES_INFO = 'src/data/types_info.h'
TRAINER_CLASSES = 'src/battle_main.c'
ROAMER = 'src/roamer.c'
WALLY_RALTS = 'src/battle_setup.c'
WALLY_ZIGZAGOON = 'src/field_specials.c'
NEW_GAME = 'src/new_game.c'
TUTORS = 'data/scripts/move_tutors.inc'
TUTOR_TEXT = 'data/text/move_tutors.inc'

STATS = species_mod.STATS
TYPES = ['TYPE_NORMAL', 'TYPE_FIGHTING', 'TYPE_FLYING', 'TYPE_POISON', 'TYPE_GROUND', 'TYPE_ROCK', 'TYPE_BUG',
         'TYPE_GHOST', 'TYPE_STEEL', 'TYPE_FIRE', 'TYPE_WATER', 'TYPE_GRASS', 'TYPE_ELECTRIC', 'TYPE_PSYCHIC',
         'TYPE_ICE', 'TYPE_DRAGON', 'TYPE_DARK', 'TYPE_FAIRY']

# Abilities that only work on the Pokemon they belong to (form changes and so on).
ABILITY_NEVER = {
    'ABILITY_NONE', 'ABILITY_CACOPHONY', 'ABILITY_MULTITYPE', 'ABILITY_STANCE_CHANGE', 'ABILITY_SCHOOLING',
    'ABILITY_BATTLE_BOND', 'ABILITY_POWER_CONSTRUCT', 'ABILITY_SHIELDS_DOWN', 'ABILITY_DISGUISE', 'ABILITY_RKS_SYSTEM',
    'ABILITY_ICE_FACE', 'ABILITY_GULP_MISSILE', 'ABILITY_HUNGER_SWITCH', 'ABILITY_ZEN_MODE', 'ABILITY_FORECAST',
    'ABILITY_FLOWER_GIFT', 'ABILITY_ZERO_TO_HERO', 'ABILITY_COMMANDER', 'ABILITY_AS_ONE_ICE_RIDER',
    'ABILITY_AS_ONE_SHADOW_RIDER', 'ABILITY_TERA_SHIFT', 'ABILITY_TERAFORM_ZERO', 'ABILITY_TERA_SHELL',
    'ABILITY_POISON_PUPPETEER', 'ABILITY_COMATOSE', 'ABILITY_MIMICRY', 'ABILITY_PIXILATE_DUMMY',
}
ABILITY_TRAPPING = {'ABILITY_SHADOW_TAG', 'ABILITY_ARENA_TRAP', 'ABILITY_MAGNET_PULL'}
ABILITY_NEGATIVE = {'ABILITY_TRUANT', 'ABILITY_SLOW_START', 'ABILITY_DEFEATIST', 'ABILITY_KLUTZ', 'ABILITY_STALL'}
ABILITY_BAD = {
    'ABILITY_HONEY_GATHER', 'ABILITY_BALL_FETCH', 'ABILITY_ILLUMINATE', 'ABILITY_RUN_AWAY', 'ABILITY_PICKUP',
    'ABILITY_FOREWARN', 'ABILITY_ANTICIPATION', 'ABILITY_FRISK', 'ABILITY_PLUS', 'ABILITY_MINUS', 'ABILITY_TELEPATHY',
    'ABILITY_SYMBIOSIS', 'ABILITY_RECEIVER', 'ABILITY_POWER_OF_ALCHEMY', 'ABILITY_BATTERY', 'ABILITY_POWER_SPOT',
    'ABILITY_HEALER', 'ABILITY_FLOWER_VEIL', 'ABILITY_CUTE_CHARM', 'ABILITY_STEADFAST', 'ABILITY_LEAF_GUARD',
    'ABILITY_COLOR_CHANGE', 'ABILITY_CURIOUS_MEDICINE', 'ABILITY_PASTEL_VEIL', 'ABILITY_AROMA_VEIL',
    'ABILITY_SWEET_VEIL', 'ABILITY_FRIEND_GUARD', 'ABILITY_HONEY_GATHER', 'ABILITY_DAMP', 'ABILITY_KEEN_EYE',
    'ABILITY_BIG_PECKS', 'ABILITY_ILLUMINATE',
}
ABILITY_WONDER = {'ABILITY_WONDER_GUARD'}

# Moves the randomizer never hands out: they break the game or only work for one Pokemon.
MOVE_NEVER = {'MOVE_NONE', 'MOVE_STRUGGLE', 'MOVE_AURA_WHEEL', 'MOVE_HYPERSPACE_FURY', 'MOVE_DARK_VOID',
              'MOVE_BEHEMOTH_BLADE', 'MOVE_BEHEMOTH_BASH', 'MOVE_DYNAMAX_CANNON', 'MOVE_SNIPE_SHOT_DUMMY',
              'MOVE_TERA_STARSTORM', 'MOVE_IVY_CUDGEL', 'MOVE_RAGING_BULL', 'MOVE_REVELATION_DANCE',
              'MOVE_MULTI_ATTACK', 'MOVE_JUDGMENT', 'MOVE_TECHNO_BLAST', 'MOVE_SPIT_UP', 'MOVE_SWALLOW',
              'MOVE_TERA_BLAST'}
# What the randomizer calls "game-breaking": fixed damage early on and one-hit KOs.
MOVE_GAME_BREAKING = {'MOVE_SONIC_BOOM', 'MOVE_DRAGON_RAGE', 'MOVE_SPORE', 'MOVE_SHEER_COLD', 'MOVE_FISSURE',
                      'MOVE_HORN_DRILL', 'MOVE_GUILLOTINE', 'MOVE_DARK_VOID', 'MOVE_HYPNOSIS_DUMMY'}
FIELD_TMS = {'MOVE_DIG', 'MOVE_SECRET_POWER', 'MOVE_FLASH', 'MOVE_SWEET_SCENT', 'MOVE_TELEPORT'}

ITEM_BAD_SORT = {'ITEM_TYPE_MAIL', 'ITEM_TYPE_SELLABLE', 'ITEM_TYPE_SHARD', 'ITEM_TYPE_RELIC', 'ITEM_TYPE_CONTEST_HELD_ITEM',
                 'ITEM_TYPE_FLUTE', 'ITEM_TYPE_TERA_SHARD', 'ITEM_TYPE_UNCATEGORIZED', 'ITEM_TYPE_FOSSIL',
                 'ITEM_TYPE_NECTAR', 'ITEM_TYPE_DRIVE', 'ITEM_TYPE_MEMORY'}
ITEM_NEVER_SORT = {'ITEM_TYPE_Z_CRYSTAL', 'ITEM_TYPE_MEGA_STONE', 'ITEM_TYPE_GEM'}
ITEM_NEVER = {'ITEM_NONE', 'ITEM_MASTER_BALL_DUMMY', 'ITEM_ENIGMA_BERRY_E_READER', 'ITEM_DYNAMAX_CANDY',
              'ITEM_DYNAMAX_CRYSTALS', 'ITEM_MAX_MUSHROOMS', 'ITEM_ABILITY_PATCH_DUMMY'}
ITEM_OVERPOWERED = {'ITEM_MASTER_BALL', 'ITEM_RARE_CANDY', 'ITEM_PP_MAX', 'ITEM_ABILITY_PATCH', 'ITEM_LEFTOVERS',
                    'ITEM_LIFE_ORB', 'ITEM_CHOICE_BAND', 'ITEM_CHOICE_SPECS', 'ITEM_CHOICE_SCARF', 'ITEM_FOCUS_SASH',
                    'ITEM_EXP_CANDY_XL', 'ITEM_BOTTLE_CAP', 'ITEM_GOLD_BOTTLE_CAP', 'ITEM_LUCKY_EGG'}
REGULAR_SHOP = {'ITEM_POKE_BALL', 'ITEM_GREAT_BALL', 'ITEM_ULTRA_BALL', 'ITEM_POTION', 'ITEM_SUPER_POTION',
                'ITEM_HYPER_POTION', 'ITEM_MAX_POTION', 'ITEM_FULL_RESTORE', 'ITEM_REVIVE', 'ITEM_ANTIDOTE',
                'ITEM_PARALYZE_HEAL', 'ITEM_AWAKENING', 'ITEM_BURN_HEAL', 'ITEM_ICE_HEAL', 'ITEM_FULL_HEAL',
                'ITEM_ESCAPE_ROPE', 'ITEM_REPEL', 'ITEM_SUPER_REPEL', 'ITEM_MAX_REPEL'}
CONSUMABLE_SORT = {'ITEM_TYPE_HEALTH_RECOVERY', 'ITEM_TYPE_STATUS_RECOVERY', 'ITEM_TYPE_PP_RECOVERY'}


# ---- small helpers ---------------------------------------------------------------

def _n(const):
    p = fundata.pool()
    return p[const]['name'] if const in p else const.split('_', 1)[-1].replace('_', ' ').title()


def _pretty(const):
    return const.split('_', 1)[-1].replace('_', ' ').title()


def _set_line(body, field, value, indent=None):
    """Every `.field = ...,` line in body gets `value` (all #if branches alike).
    indent: only lines indented exactly this much (skips nested structs)."""
    lead = r'[ \t]*' if indent is None else ' ' * indent
    pat = re.compile(r'^(' + lead + r'\.' + field + r'[ \t]*=[ \t]*)([^\n]*?)(,[ \t]*(?://[^\n]*)?)$', re.M)
    return pat.sub(lambda m: m.group(1) + value + m.group(3), body)


def species_files():
    return sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, INFO_GLOB)))


def edit_species(ov, fn):
    """fn(const, body) -> new body or None, for every species entry written out in full."""
    changed = 0
    for rel in species_files():
        text = ov.read(rel)
        out, last = [], 0
        for m in species_mod.ENTRY_RE.finditer(text):
            nxt = species_mod.ENTRY_RE.search(text, m.end())
            ext = species_mod._body_extent(text, m.end(), nxt.start() if nxt else len(text))
            if not ext:
                continue
            body = text[ext[0]:ext[1]]
            new = fn(m.group(1), body)
            if new is not None and new != body:
                out.append(text[last:ext[0]])
                out.append(new)
                last = ext[1]
                changed += 1
        if out:
            out.append(text[last:])
            ov.write(rel, ''.join(out))
    return changed


def families(p):
    """{root const: [members]} following evolvesFrom."""
    fam = {}
    for c, info in p.items():
        if not info['usable']:
            continue
        r, seen = c, {c}
        while p[r]['evolvesFrom'] and p[r]['evolvesFrom'] in p and p[r]['evolvesFrom'] not in seen:
            r = p[r]['evolvesFrom']
            seen.add(r)
        fam.setdefault(r, []).append(c)
    return fam


def family_root(p):
    out = {}
    for r, members in families(p).items():
        for c in members:
            out[c] = r
    return out


def all_moves(ov):
    """Real moves in the order of the moves enum (no Z-Moves or Max Moves)."""
    text = ov.read(MOVES_H)
    head = text.split('MOVES_COUNT = ', 1)[0]
    found = re.findall(r'^\s*(MOVE_[A-Z0-9_]+)\s*(?:=|,)', head, re.M)
    mv = fundata.moves()
    return [m for m in dict.fromkeys(found) if m in mv and m not in MOVE_NEVER]


def all_abilities(ov):
    text = ov.read(ABILITIES_H)
    head = text.split('ABILITIES_COUNT = ', 1)[0]
    return [a for a in dict.fromkeys(re.findall(r'^\s*(ABILITY_[A-Z0-9_]+)\s*(?:=|,)', head, re.M))
            if a not in ABILITY_NEVER]


def damaging(md):
    return md['category'] != 'DAMAGE_CATEGORY_STATUS' and md['power'] > 1


# ---- base stats -------------------------------------------------------------------

def base_stats(ov, opt, rng, report):
    mode = opt.get('mode', 'shuffle')
    follow = opt.get('followEvolutions', True)
    p = fundata.pool()
    root = family_root(p)
    plan = {}
    perm_by_root, weights_by_root = {}, {}
    for c, info in p.items():
        if not info['usable'] or c == 'SPECIES_SHEDINJA':
            continue
        vals = [info['stats'][s] for s in STATS]
        key = root.get(c, c) if follow else c
        if mode == 'shuffle':
            if key not in perm_by_root:
                order = list(range(6))
                rng.shuffle(order)
                perm_by_root[key] = order
            new = [vals[i] for i in perm_by_root[key]]
        else:
            if key not in weights_by_root:
                weights_by_root[key] = [rng.uniform(0.6, 1.6) for _ in range(6)]
            w = weights_by_root[key]
            bst = sum(vals)
            floor = 20 if bst >= 300 else 10
            spare = max(0, bst - floor * 6)
            new = [floor + int(spare * x / sum(w)) for x in w]
            new[rng.randrange(6)] += bst - sum(new)
            new = [max(1, min(255, v)) for v in new]
        plan[c] = new
    lines = []

    def fn(const, body):
        if const not in plan:
            return None
        for st, v in zip(STATS, plan[const]):
            body = _set_line(body, st, str(v))
        return body
    edit_species(ov, fn)
    for key in ('SPECIES_TREECKO', 'SPECIES_TORCHIC', 'SPECIES_MUDKIP', 'SPECIES_RAYQUAZA'):
        if key in plan:
            lines.append('%s: %s' % (_n(key), ' / '.join(str(v) for v in plan[key])))
    report.add('Base stats', ['%s for %d Pokémon%s' % ('Shuffled' if mode == 'shuffle' else 'Randomized (same total)', len(plan),
                                                      ', evolutions follow' if follow else '')] + lines, len(plan))


def exp_curves(ov, opt, rng, report):
    p = fundata.pool()
    mode = opt.get('mode', 'legendarySlow')
    plan = {}
    for c, info in p.items():
        if not info['usable']:
            continue
        if mode == 'allMediumFast':
            plan[c] = 'GROWTH_MEDIUM_FAST'
        else:
            plan[c] = 'GROWTH_SLOW' if info['legendary'] else 'GROWTH_MEDIUM_FAST'
    edit_species(ov, lambda c, b: _set_line(b, 'growthRate', plan[c]) if c in plan else None)
    report.add('EXP curves', ['Every Pokémon uses Medium Fast' if mode == 'allMediumFast' else
                              'Legendaries use Slow, every other Pokémon Medium Fast'], len(plan))


# ---- types -------------------------------------------------------------------------

def types(ov, opt, rng, report):
    mode = opt.get('mode', 'follow')
    dual = opt.get('forceDual', False)
    p = fundata.pool()
    fam = families(p)
    plan = {}

    def rand_types(single_ok=True):
        a = rng.choice(TYPES)
        if dual or not single_ok or rng.random() < 0.5:
            b = rng.choice([t for t in TYPES if t != a])
            return [a, b]
        return [a]
    if mode == 'follow':
        for r, members in fam.items():
            base = rand_types()
            # walk the family from the base: evolutions keep the types, single types may gain a second one
            todo = [(r, base)]
            seen = set()
            while todo:
                c, t = todo.pop()
                if c in seen:
                    continue
                seen.add(c)
                plan[c] = t
                for nxt in p[c]['evolvesTo']:
                    if nxt in p and p[nxt]['usable']:
                        nt = list(t)
                        if len(nt) == 1 and rng.random() < 0.35:
                            nt.append(rng.choice([x for x in TYPES if x != nt[0]]))
                        todo.append((nxt, nt))
            for c in members:
                plan.setdefault(c, base)
    else:
        for c, info in p.items():
            if info['usable']:
                plan[c] = rand_types()

    def fn(const, body):
        if const not in plan:
            return None
        return _set_line(body, 'types', 'MON_TYPES(%s)' % ', '.join(plan[const]))
    edit_species(ov, fn)
    show = [k for k in ('SPECIES_TREECKO', 'SPECIES_TORCHIC', 'SPECIES_MUDKIP', 'SPECIES_ZIGZAGOON', 'SPECIES_RAYQUAZA') if k in plan]
    report.add('Types', ['%s: %s' % (_n(k), ' / '.join(_pretty(t) for t in plan[k])) for k in show], len(plan))


# ---- abilities ---------------------------------------------------------------------

def abilities(ov, opt, rng, report):
    p = fundata.pool()
    pool = set(all_abilities(ov))
    if not opt.get('wonderGuard', False):
        pool -= ABILITY_WONDER
    if opt.get('banTrapping', True):
        pool -= ABILITY_TRAPPING
    if opt.get('banNegative', True):
        pool -= ABILITY_NEGATIVE
    if opt.get('banBad', False):
        pool -= ABILITY_BAD
    pool = sorted(pool)
    follow = opt.get('followEvolutions', True)
    root = family_root(p)
    by_root, plan = {}, {}
    for c, info in p.items():
        if not info['usable'] or c == 'SPECIES_SHEDINJA':
            continue
        old = (info['abilities'] + ['ABILITY_NONE'] * 3)[:3]
        key = root.get(c, c) if follow else c
        if key not in by_root:
            picks = rng.sample(pool, 3)
            by_root[key] = picks
        picks = by_root[key]
        # keep the same shape: a slot that was empty stays empty
        new = [picks[i] if old[i] != 'ABILITY_NONE' or i == 0 else 'ABILITY_NONE' for i in range(3)]
        plan[c] = new

    edit_species(ov, lambda c, b: _set_line(b, 'abilities', '{ %s }' % ', '.join(plan[c])) if c in plan else None)
    show = [k for k in ('SPECIES_TREECKO', 'SPECIES_TORCHIC', 'SPECIES_MUDKIP', 'SPECIES_RALTS') if k in plan]
    report.add('Abilities', ['%s: %s' % (_n(k), ', '.join(_pretty(a) for a in plan[k] if a != 'ABILITY_NONE')) for k in show], len(plan))


def fix_party_abilities(ov, report):
    """After abilities change, trainer Pokemon with an ability their species no longer has lose it."""
    import funmodes
    from common import to_const
    p = fundata.pool()
    party = funmodes.Party(ov.read(funmodes.PARTY))
    n = 0
    for tid, t in party.items():
        changed = False
        for m in t['party']:
            s = funmodes.species_of(m)
            if m.get('Ability') and s in p and to_const('ABILITY', m['Ability']) not in p[s]['abilities']:
                m.pop('Ability')
                changed = True
                n += 1
        if changed:
            party.put(tid, t)
    if n:
        ov.write(funmodes.PARTY, party.text())
    return n


# ---- evolutions ---------------------------------------------------------------------

def _evo_block(body):
    m = re.search(r'\.evolutions\s*=\s*EVOLUTION\(', body)
    if not m:
        return None
    close = species_mod._balanced_after(body, m.end() - 1)
    return m.end(), close - 1


def evolutions(ov, opt, rng, report):
    mode = opt.get('mode', 'random')
    p = fundata.pool()
    cands = [i for i in fundata.usable(p) if opt.get('legendaries', False) or not i['legendary']]
    new_to = {}
    lines = []
    if mode == 'everyLevel':
        for c, info in p.items():
            if info['usable']:
                new_to[c] = [rng.choice([i for i in cands if i['const'] != c])['const']]
    else:
        similar = opt.get('similarStrength', True)
        same_type = opt.get('sameTyping', False)
        force_change = opt.get('forceChange', True)
        no_conv = opt.get('noConvergence', True)
        growth = opt.get('forceGrowth', True)
        limit3 = opt.get('limit3', True)
        used = set()
        graph = {c: [t for t in info['evolvesTo'] if t in p] for c, info in p.items() if info['usable']}

        def depth_before(c, g):
            d, seen = 0, {c}
            parents = {t: s for s, ts in g.items() for t in ts}
            while c in parents and parents[c] not in seen:
                c = parents[c]
                seen.add(c)
                d += 1
            return d

        def reaches(a, b, g, seen=None):
            seen = seen or set()
            if a == b:
                return True
            if a in seen:
                return False
            seen.add(a)
            return any(reaches(t, b, g, seen) for t in g.get(a, []))
        order = sorted(graph)
        rng.shuffle(order)
        for c in order:
            olds = graph.get(c, [])
            if not olds:
                continue
            src = p[c]
            new_list = []
            for old in olds:
                target = p.get(old) or src
                best = []
                spread = 0.15
                while not best and spread < 3:
                    for i in cands:
                        t = i['const']
                        if t == c or (force_change and t == old) or (no_conv and t in used) or t in new_list:
                            continue
                        if similar and abs(i['bst'] - target['bst']) > target['bst'] * spread:
                            continue
                        if growth and i['bst'] <= src['bst']:
                            continue
                        if same_type and not set(i['types']) & set(src['types']):
                            continue
                        best.append(t)
                    spread += 0.15
                rng.shuffle(best)
                pick = None
                for t in best:
                    g2 = dict(graph)
                    g2[c] = new_list + [t]
                    if reaches(t, c, g2):
                        continue  # no loops
                    if limit3 and depth_before(c, g2) + 1 + _chain(t, g2) > 3:
                        continue
                    pick = t
                    break
                if pick is None:
                    pick = old
                new_list.append(pick)
                used.add(pick)
            graph[c] = new_list
            new_to[c] = new_list

    def fn(const, body):
        if const not in new_to:
            return None
        blk = _evo_block(body)
        if mode == 'everyLevel':
            entry = '{EVO_LEVEL, 1, %s}' % new_to[const][0]
            if blk and '#' in body[blk[0]:blk[1]]:
                return None
            if blk:
                return body[:blk[0]] + entry + body[blk[1]:]
            if not re.search(r'\.baseHP\s*=', body):
                return None  # built from a template that may set evolutions itself
            closing = body.rstrip().rfind('}')
            indent = re.search(r'\n([ \t]*)\.\w', body).group(1)
            return body[:closing].rstrip() + '\n' + indent + '.evolutions = EVOLUTION(%s),\n    ' % entry + body[closing:]
        if not blk:
            return None
        inner = body[blk[0]:blk[1]]
        if '#' in inner:
            return None
        parts = species_mod._split_top(inner)
        targets = list(new_to[const])
        out = []
        remap = {}
        for part in parts:
            if not (part.startswith('{') and part.endswith('}')):
                return None
            fields = species_mod._split_top(part[1:-1])
            if len(fields) < 3:
                return None
            old = fields[2]
            if old not in remap:
                remap[old] = targets.pop(0) if targets else old
            fields[2] = remap[old]
            out.append('{' + ', '.join(fields) + '}')
        return body[:blk[0]] + ', '.join(out) + body[blk[1]:]
    edit_species(ov, fn)
    for k in ('SPECIES_TREECKO', 'SPECIES_TORCHIC', 'SPECIES_MUDKIP', 'SPECIES_ZIGZAGOON', 'SPECIES_WURMPLE'):
        if k in new_to:
            lines.append('%s now evolves into %s' % (_n(k), ', '.join(_n(t) for t in new_to[k])))
    head = 'Every Pokémon evolves into a random one every level' if mode == 'everyLevel' else 'Evolutions point to new Pokémon'
    report.add('Evolutions', [head] + lines, len(new_to))


def _chain(c, g, seen=None):
    """How many Pokemon from c to the end of its longest evolution chain (c counts)."""
    seen = seen or set()
    if c in seen:
        return 99
    seen = seen | {c}
    nxt = g.get(c, [])
    return 1 + (max(_chain(t, g, seen) for t in nxt) if nxt else 0)


def evolution_tweaks(ov, opt, rng, report):
    """Impossible (trade) evolutions become level or item ones, high levels come down, time conditions go away."""
    impossible = opt.get('changeImpossible', True)
    easier = opt.get('easier', False)
    no_time = opt.get('noTime', False)
    counts = {'trade': 0, 'easier': 0, 'time': 0}

    def fn(const, body):
        blk = _evo_block(body)
        if not blk:
            return None
        inner = body[blk[0]:blk[1]]
        if '#' in inner:
            return None
        parts = species_mod._split_top(inner)
        out = []
        for part in parts:
            if not (part.startswith('{') and part.endswith('}')):
                return None
            f = species_mod._split_top(part[1:-1])
            if len(f) < 3:
                return None
            method = f[0]
            if impossible and method == 'EVO_TRADE':
                f[0], f[1] = 'EVO_LEVEL', '37'
                counts['trade'] += 1
            elif impossible and method == 'EVO_TRADE_ITEM':
                f[0] = 'EVO_ITEM'
                counts['trade'] += 1
            elif impossible and method == 'EVO_TRADE_SPECIFIC_MON':
                f[0], f[1] = 'EVO_LEVEL', '37'
                counts['trade'] += 1
            if easier and f[0] == 'EVO_LEVEL' and f[1].isdigit() and int(f[1]) > 40:
                f[1] = '40'
                counts['easier'] += 1
            if no_time and len(f) > 3 and re.search(r'IF_TIME|IF_NOT_TIME|IF_TIME_OF_DAY', f[3]):
                f = f[:3]
                counts['time'] += 1
            out.append('{' + ', '.join(f) + '}')
        return body[:blk[0]] + ', '.join(out) + body[blk[1]:]
    edit_species(ov, fn)
    lines = []
    if impossible:
        lines.append('%d trade evolutions now happen by level 37 or by using the item' % counts['trade'])
    if easier:
        lines.append('%d evolutions above level 40 now happen at 40' % counts['easier'])
    if no_time:
        lines.append('%d day or night evolutions work at any time' % counts['time'])
    report.add('Evolution helpers', lines, sum(counts.values()))


# ---- palettes ----------------------------------------------------------------------

def palettes(ov, opt, rng, report):
    """Shifts the colors of every Pokemon's palette. Families share one shift."""
    p = fundata.pool()
    root = family_root(p)
    follow = opt.get('followEvolutions', True)
    shifts = {}
    files = 0
    gfx = ov.read('src/data/graphics/pokemon.h')
    pal_of = {}
    for sym, path in re.findall(r'(gMon(?:Shiny)?Palette_\w+)\[\]\s*=\s*INCGFX_U16\("([^"]+\.pal)"', gfx):
        pal_of.setdefault(sym, []).append(path)
    for rel in species_files():
        text = ov.read(rel)
        for m in species_mod.ENTRY_RE.finditer(text):
            const = m.group(1)
            if const not in p or not p[const]['usable']:
                continue
            nxt = species_mod.ENTRY_RE.search(text, m.end())
            body = text[m.end(): nxt.start() if nxt else len(text)]
            key = root.get(const, const) if follow else const
            if key not in shifts:
                shifts[key] = rng.uniform(0.15, 0.85)
            for field in ('palette', 'shinyPalette'):
                pm = re.search(r'\.' + field + r'\s*=\s*(gMon\w+)', body)
                for path in pal_of.get(pm.group(1), []) if pm else []:
                    if os.path.exists(os.path.join(ROOT, path)):
                        files += _shift_pal(ov, path, shifts[key])
    report.add('Pokémon colors', ['New colors for %d Pokémon (%d palette files)%s' % (len(shifts), files,
                                  ', families share colors' if follow else '')], files)


def _shift_pal(ov, rel, shift):
    text = ov.read(rel)
    lines = text.replace('\r\n', '\n').split('\n')
    if len(lines) < 4 or lines[0].strip() != 'JASC-PAL':
        return 0
    out = lines[:3]
    for i, line in enumerate(lines[3:]):
        parts = line.split()
        if len(parts) != 3 or not all(x.isdigit() for x in parts):
            out.append(line)
            continue
        if i == 0:  # the first color is see-through
            out.append(line)
            continue
        r, g, b = (int(x) / 255 for x in parts)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if s < 0.12:  # greys, black and white stay
            out.append(line)
            continue
        r, g, b = colorsys.hsv_to_rgb((h + shift) % 1, s, v)
        out.append('%d %d %d' % (round(r * 255), round(g * 255), round(b * 255)))
    nl = '\r\n'  # .gitattributes keeps palettes in CRLF
    ov.write(rel, nl.join(out))
    return 1


# ---- static Pokemon, roamers, trades, catching tutorial -------------------------------

def _script_files():
    out = sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc'))) + sorted(glob.glob(os.path.join(ROOT, 'data/scripts/*.inc')))
    return [os.path.relpath(f, ROOT) for f in out if 'frlg' not in f.lower() and 'debug' not in f.lower() and 'test' not in f.lower()]


def _static_pick(old, mode, pick, p, legends, rng, used):
    info = p.get(old)
    if mode == 'legendSwap' and info and info['legendary']:
        cands = [i['const'] for i in legends if i['const'] not in used] or [i['const'] for i in legends]
        return rng.choice(cands)
    if mode == 'similar':
        return pick.similar(old, used)
    return pick.random(used)


def statics(ov, opt, rng, report):
    import funmodes
    from gifts import LINE_RE
    from textdb import LABEL_RE
    p = fundata.pool()
    mode = opt.get('mode', 'legendSwap')
    pick = funmodes.Picker(rng, legendaries=mode == 'random' and opt.get('legendaries', True))
    legends = [i for i in fundata.usable(p) if i['legendary']]
    level_mod = int(opt.get('levelPercent', 0) or 0)
    mapping, lines = {}, []
    for rel in _script_files():
        text = ov.read(rel)
        if not re.search(r'^\s*(givemon|giveegg|setwildbattle|seteventmon)\s', text, re.M):
            continue
        rows = text.split('\n')
        changed = False
        for n, line in enumerate(rows):
            m = LINE_RE.match(line)
            if not m or m.group(3) not in p:
                continue
            old = m.group(3)
            if old not in mapping:
                mapping[old] = _static_pick(old, mode, pick, p, legends, rng, set(mapping.values()))
            new = mapping[old]
            lv = m.group(4)
            if lv and level_mod:
                lv = str(max(1, min(100, round(int(lv) * (100 + level_mod) / 100))))
            rows[n] = m.group(1) + m.group(2) + ' ' + new + (', ' + lv if lv else '') + (m.group(5) or '')
            # the scene's cry and picture follow
            start = n
            while start > 0 and not LABEL_RE.match(rows[start - 1]):
                start -= 1
            end = n + 1
            while end < len(rows) and not LABEL_RE.match(rows[end]):
                end += 1
            for i in range(start, end):
                if i != n and not rows[i].lstrip().startswith('.string') and re.search(r'\b%s\b' % old, rows[i]):
                    rows[i] = re.sub(r'\b%s\b' % old, new, rows[i])
            changed = True
        if changed:
            ov.write(rel, '\n'.join(rows))
    if opt.get('roamers', True):
        t = ov.read(ROAMER)
        for old in ('SPECIES_LATIAS', 'SPECIES_LATIOS'):
            if old not in mapping:
                mapping[old] = _static_pick(old, mode, pick, p, legends, rng, set(mapping.values()))
        t = re.sub(r'TryAddRoamer\((SPECIES_LATI(?:AS|OS)),', lambda m: 'TryAddRoamer(%s,' % mapping[m.group(1)], t)
        ov.write(ROAMER, t)
    lines = ['%s → %s' % (_n(a), _n(b)) for a, b in sorted(mapping.items(), key=lambda kv: _n(kv[0]))]
    report.add('Gifts, legendaries and one-time battles', lines)


def catching_tutorial(ov, opt, rng, report):
    import funmodes
    pick = funmodes.Picker(rng)
    ralts = pick.similar('SPECIES_RALTS')
    zig = pick.similar('SPECIES_ZIGZAGOON', {ralts})
    t = ov.read(WALLY_RALTS)
    t = re.sub(r'(CreateMaleMon\(&gParties\[B_TRAINER_OPPONENT_A\]\[0\],\s*)SPECIES_RALTS', lambda m: m.group(1) + ralts, t)
    ov.write(WALLY_RALTS, t)
    t = ov.read(WALLY_ZIGZAGOON)
    t = re.sub(r'(CreateRandomMon\(&gParties\[B_TRAINER_PLAYER\]\[0\],\s*)SPECIES_ZIGZAGOON', lambda m: m.group(1) + zig, t)
    ov.write(WALLY_ZIGZAGOON, t)
    report.add('Catching tutorial', ['Wally catches %s instead of Ralts, using a borrowed %s' % (_n(ralts), _n(zig))])


NICKNAMES = ['BIGBOY', 'NUGGET', 'SIR', 'LADY', 'TOAST', 'PICKLE', 'MOCHI', 'BEANS', 'CHAMP', 'ZIGGY', 'GUS', 'DOTTIE',
             'SPROUT', 'BISCUIT', 'NOODLE', 'PEBBLE', 'TANK', 'COCO', 'BLAZE', 'WAFFLE']
OT_NAMES = ['KOBE', 'ROMAN', 'SKYLAR', 'ISIS', 'BRAD', 'TAYLOR', 'JORDAN', 'RILEY', 'CASEY', 'MORGAN', 'AVERY', 'QUINN']


def trades(ov, opt, rng, report):
    import funmodes
    text = ov.read(TRADES)
    m = re.search(r'sIngameTrades\[\]\s*=\s*\{', text)
    if not m:
        report.add('In-game trades', ['Could not find the trade list, left as it was'])
        return
    end = text.find('\n};', m.end())
    block = text[m.end():end]
    pick = funmodes.Picker(rng)
    items = item_pool(ov, ban_bad=True)
    both = opt.get('mode', 'given') == 'both'
    lines = []

    def one(mm):
        b = mm.group(0)
        old = re.search(r'\.species\s*=\s*(SPECIES_\w+)', b)
        new = pick.random()
        b = re.sub(r'(\.species\s*=\s*)SPECIES_\w+', lambda x: x.group(1) + new, b)
        b = re.sub(r'(\.abilityNum\s*=\s*)\d+', lambda x: x.group(1) + '0', b)
        req = re.search(r'\.requestedSpecies\s*=\s*(SPECIES_\w+)', b)
        if both:
            r2 = pick.random({new})
            b = re.sub(r'(\.requestedSpecies\s*=\s*)SPECIES_\w+', lambda x: x.group(1) + r2, b)
            req_name = _n(r2)
        else:
            req_name = _n(req.group(1)) if req else '?'
        if opt.get('nicknames', True):
            b = re.sub(r'(\.nickname\s*=\s*_\(")[^"]*("\))', lambda x: x.group(1) + rng.choice(NICKNAMES) + x.group(2), b)
        if opt.get('otNames', True):
            b = re.sub(r'(\.otName\s*=\s*_\(")[^"]*("\))', lambda x: x.group(1) + rng.choice(OT_NAMES) + x.group(2), b)
        if opt.get('ivs', True):
            b = re.sub(r'(\.ivs\s*=\s*\{)[^}]*(\})', lambda x: x.group(1) + ', '.join(str(rng.randint(0, 31)) for _ in range(6)) + x.group(2), b)
        if opt.get('items', True) and items:
            it = rng.choice(items)
            b = re.sub(r'(\.heldItem\s*=\s*)ITEM_\w+', lambda x: x.group(1) + it, b)
            b = re.sub(r'(\.mailNum\s*=\s*)-?\d+', lambda x: x.group(1) + '-1', b)
        lines.append('%s for your %s (was %s)' % (_n(new), req_name, _n(old.group(1)) if old else '?'))
        return b
    block = re.sub(r'\[INGAME_TRADE_\w+\]\s*=\s*\{.*?\n    \}', one, block, flags=re.S)
    ov.write(TRADES, text[:m.end()] + block + text[end:])
    report.add('In-game trades', lines)


# ---- move data -------------------------------------------------------------------------

def move_data(ov, opt, rng, report):
    text = ov.read(MOVES_INFO)
    mv = fundata.moves()
    keep = set(all_moves(ov))
    parts = re.split(r'(^\s*\[MOVE_[A-Z0-9_]+\]\s*=\s*$)', text, flags=re.M)
    counts = {'power': 0, 'accuracy': 0, 'pp': 0, 'type': 0, 'category': 0}
    for i in range(1, len(parts), 2):
        const = re.search(r'MOVE_[A-Z0-9_]+', parts[i]).group()
        if const not in keep:
            continue
        md = mv[const]
        body = parts[i + 1]
        dmg = damaging(md) and md['power'] >= 20
        if opt.get('power') and dmg:
            new = max(20, min(150, int(rng.gauss(md['power'], 25)) // 5 * 5))
            body = _set_line(body, 'power', str(new), 8)
            counts['power'] += 1
        if opt.get('accuracy') and md['accuracy'] and md['accuracy'] < 101 and md['accuracy'] != 0:
            new = rng.choice([70, 75, 80, 85, 90, 95, 100, 100, 100, 100])
            body = _set_line(body, 'accuracy', str(new), 8)
            counts['accuracy'] += 1
        if opt.get('pp') and re.search(r'\.pp\s*=', body):
            new = rng.choice([5, 10, 10, 15, 15, 20, 20, 25, 30, 35, 40])
            body = _set_line(body, 'pp', str(new), 8)
            counts['pp'] += 1
        if opt.get('type') and md['type'] and dmg and const not in ('MOVE_HIDDEN_POWER', 'MOVE_WEATHER_BALL', 'MOVE_NATURAL_GIFT'):
            body = _set_line(body, 'type', rng.choice(TYPES), 8)
            counts['type'] += 1
        if opt.get('category') and dmg:
            body = _set_line(body, 'category', rng.choice(['DAMAGE_CATEGORY_PHYSICAL', 'DAMAGE_CATEGORY_SPECIAL']), 8)
            counts['category'] += 1
        parts[i + 1] = body
    ov.write(MOVES_INFO, ''.join(parts))
    names = {'power': 'power', 'accuracy': 'accuracy', 'pp': 'PP', 'type': 'type', 'category': 'physical or special'}
    report.add('Move data', ['New %s for %d moves' % (names[k], v) for k, v in counts.items() if v], sum(counts.values()))


# ---- level-up movesets -------------------------------------------------------------------

def _learnset_rel():
    return os.path.relpath(species_mod.active_learnset_file()[0], ROOT)


def movesets_level_up(ov, opt, rng, report):
    mode = opt.get('mode', 'preferType')
    p = fundata.pool()
    mv = fundata.moves()
    pool = all_moves(ov)
    if opt.get('noGameBreaking', True):
        pool = [m for m in pool if m not in MOVE_GAME_BREAKING]
    dmg_pool = [m for m in pool if damaging(mv[m])]
    good_pct = int(opt.get('goodDamagingPercent', 0) or 0)
    start_moves = max(1, min(4, int(opt.get('startMoves', 1) or 1)))
    rel = _learnset_rel()
    text = ov.read(rel)
    sym_species = {}
    for c, info in p.items():
        if info.get('learnset') and info['usable']:
            sym_species.setdefault(info['learnset'], c)
    count = 0

    def one(m):
        nonlocal count
        sym, inner = m.group(1), m.group(2)
        if '#' in inner or sym not in sym_species:
            return m.group(0)
        info = p[sym_species[sym]]
        old = [(int(lv), x) for lv, x in re.findall(r'LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_\w+)\s*\)', inner)]
        if not old:
            return m.group(0)
        if mode == 'metronome':
            new = [(1, 'MOVE_METRONOME')]
        else:
            levels = [lv for lv, _ in old]
            ones = sum(1 for lv in levels if lv <= 1)
            if ones < start_moves:
                extra = [1] * (start_moves - ones)
                levels = sorted(extra + levels)[:max(len(levels), start_moves)]
            chosen = []
            for _ in levels:
                use_dmg = good_pct and rng.randrange(100) < good_pct
                src = dmg_pool if use_dmg else pool
                if mode == 'preferType' and rng.random() < 0.6:
                    typed = [x for x in src if mv[x]['type'] in info['types'] and x not in chosen]
                    if typed:
                        chosen.append(rng.choice(typed))
                        continue
                choices = [x for x in src if x not in chosen] or src
                chosen.append(rng.choice(choices))
            # a damaging move first, so a fresh Pokemon can fight
            if not any(damaging(mv[x]) for x in chosen[:start_moves]):
                d = [x for x in dmg_pool if mv[x]['power'] <= 50 and x not in chosen] or dmg_pool
                chosen[0] = rng.choice(d)
            if opt.get('reorderDamaging', True):
                dmg_slots = [i for i, x in enumerate(chosen) if damaging(mv[x])]
                dmg_moves = sorted((chosen[i] for i in dmg_slots), key=lambda x: mv[x]['power'])
                for i, x in zip(dmg_slots, dmg_moves):
                    chosen[i] = x
            new = list(zip(levels, chosen))
        count += 1
        body = '\n' + ''.join('    LEVEL_UP_MOVE(%2d, %s),\n' % (lv, x) for lv, x in new) + '    LEVEL_UP_END\n'
        return m.group(0)[:m.start(2) - m.start(0)] + body + m.group(0)[m.end(2) - m.start(0):]
    text = re.sub(r'static const struct LevelUpMove (\w+)\[\]\s*=\s*\{(.*?)\};', one, text, flags=re.S)
    ov.write(rel, text)
    head = {'metronome': 'Every Pokémon only knows Metronome', 'preferType': 'Random moves, mostly of the Pokémon\'s own types',
            'random': 'Completely random moves'}[mode]
    report.add('Level-up moves', ['%s (%d Pokémon)' % (head, count)], count)


def metronome_trainers(ov, report):
    import funmodes
    party = funmodes.Party(ov.read(funmodes.PARTY))
    for tid, t in party.items():
        for m in t['party']:
            m['moves'] = ['Metronome']
        party.put(tid, t)
    ov.write(funmodes.PARTY, party.text())
    report.add('Metronome only', ['Every trainer Pokémon knows only Metronome too'])


# ---- TMs, HMs and tutors -------------------------------------------------------------------

def _tm_lists(ov):
    text = ov.read(TMS_H)
    out = {}
    for name, key in (('FOREACH_TM', 'tms'), ('FOREACH_HM', 'hms')):
        m = re.search(r'#define %s\(F\)\s*\\\n((?:[ \t]*F\(\w+\)[ \t]*\\?\n?)*)' % name, text)
        out[key] = ['MOVE_' + x for x in re.findall(r'F\((\w+)\)', m.group(1))] if m else []
    return out


def _tutor_moves(ov):
    t = ov.read(TUTORS)
    return re.findall(r'^\s*move_tutor\s+(MOVE_\w+)', t, re.M)


def tm_moves(ov, opt, rng, report):
    lists = _tm_lists(ov)
    mv = fundata.moves()
    pool = all_moves(ov)
    if opt.get('noGameBreaking', True):
        pool = [m for m in pool if m not in MOVE_GAME_BREAKING]
    taken = set(lists['hms'])
    keep_field = opt.get('keepField', True)
    good_pct = int(opt.get('goodDamagingPercent', 0) or 0)
    new = []
    for old in lists['tms']:
        if keep_field and old in FIELD_TMS:
            new.append(old)
            taken.add(old)
    out = []
    for old in lists['tms']:
        if keep_field and old in FIELD_TMS:
            out.append(old)
            continue
        src = [m for m in pool if m not in taken]
        if good_pct and rng.randrange(100) < good_pct:
            src = [m for m in src if damaging(mv[m]) and mv[m]['power'] >= 70] or src
        choice = rng.choice(src)
        taken.add(choice)
        out.append(choice)
    renames = {}
    for a, b in zip(lists['tms'], out):
        if a != b:
            renames['ITEM_TM_%s' % a[5:]] = ('ITEM_TM_%s' % b[5:], b)
    text = ov.read(TMS_H)
    m = re.search(r'#define FOREACH_TM\(F\)\s*\\\n((?:[ \t]*F\(\w+\)[ \t]*\\?\n?)*)', text)
    clean = [x[5:] for x in out]
    body = ''.join('    F(%s) \\\n' % c for c in clean[:-1]) + '    F(%s)\n' % clean[-1]
    ov.write(TMS_H, text[:m.start(1)] + body + text[m.end(1):])
    if renames:
        _rename_tm_items(ov, renames)
    report.add('TM moves', ['TM%02d: %s' % (i + 1, mv[x]['name']) for i, x in enumerate(out)], len(renames))


def _rename_tm_items(ov, renames):
    """Fun Modes version of movesets._rename_tm_items: through the overlay."""
    pattern = re.compile(r'\b(%s)\b' % '|'.join(re.escape(k) for k in renames))
    for top, exts in (('data', ('.inc', '.json', '.s')), ('src', ('.c', '.h')), ('include', ('.h',))):
        for dirpath, _, names in os.walk(os.path.join(ROOT, top)):
            for n in names:
                if not n.endswith(exts) or n == 'events.inc':
                    continue
                rel = os.path.relpath(os.path.join(dirpath, n), ROOT)
                if rel == TMS_H:
                    continue
                try:
                    t = ov.read(rel)
                except (OSError, UnicodeDecodeError):
                    continue
                if 'ITEM_TM_' not in t or not pattern.search(t):
                    continue
                t = pattern.sub(lambda m: '@@TMRENAME@@' + renames[m.group(1)][0], t)
                ov.write(rel, t.replace('@@TMRENAME@@', ''))
    t = ov.read(ITEMS)
    for new_item, move in renames.values():
        t = movesets.set_tm_description(t, new_item, move)
    ov.write(ITEMS, t)


def tutor_moves(ov, opt, rng, report):
    t = ov.read(TUTORS)
    mv = fundata.moves()
    lists = _tm_lists(ov)
    pool = [m for m in all_moves(ov) if m not in set(lists['tms']) | set(lists['hms'])]
    if opt.get('noGameBreaking', True):
        pool = [m for m in pool if m not in MOVE_GAME_BREAKING]
    olds = _tutor_moves(ov)
    taken = set(olds)
    mapping = {}
    for old in olds:
        choice = rng.choice([m for m in pool if m not in taken])
        taken.add(choice)
        mapping[old] = choice
    t = re.sub(r'^(\s*move_tutor\s+)(MOVE_\w+)', lambda m: m.group(1) + mapping.get(m.group(2), m.group(2)), t, flags=re.M)
    ov.write(TUTORS, t)
    # the tutors say which move they teach
    tx = ov.read(TUTOR_TEXT)
    for old, new in mapping.items():
        a, b = mv[old]['name'].upper(), mv[new]['name'].upper()
        tx = re.sub(r'(?<![A-Z])%s(?![A-Z])' % re.escape(a), b, tx)
    ov.write(TUTOR_TEXT, tx)
    report.add('Tutor moves', ['%s → %s' % (mv[a]['name'], mv[b]['name']) for a, b in mapping.items()])


def _learnable_key(c):
    return c[8:]


def compatibility(ov, opt, rng, report, which):
    """which = 'tm' or 'tutor'. Rewrites who can learn the TMs (or tutor moves) in all_learnables.json."""
    data = json.loads(ov.read(LEARNABLES))
    lists = _tm_lists(ov)
    mv = fundata.moves()
    p = fundata.pool()
    if which == 'tm':
        taught = list(lists['tms'])
        hms = list(lists['hms'])
    else:
        taught = _tutor_moves(ov)
        hms = []
    mode = opt.get('mode', 'preferType')
    follow = opt.get('followEvolutions', True)
    lvl_ok = opt.get('levelUpCompatible', False)
    root = family_root(p)
    key_species = {}
    for c, info in p.items():
        k = _learnable_key(c)
        if k in data and info['usable']:
            key_species.setdefault(k, c)
    by_root = {}
    for key in sorted(data):
        c = key_species.get(key)
        if not c:
            continue
        info = p[c]
        cur = set(data[key])
        before = [m for m in taught if m in cur]
        if mode == 'full':
            chosen = set(taught)
        else:
            fam_key = root.get(c, c) if follow else c
            if fam_key in by_root:
                chosen = set(by_root[fam_key])
            else:
                share = max(0.15, min(0.6, len(before) / max(1, len(taught)))) if before else 0.3
                chosen = set()
                for m in taught:
                    chance = share
                    if mode == 'preferType':
                        if mv[m]['type'] in info['types']:
                            chance = 0.9
                        elif mv[m]['type'] == 'TYPE_NORMAL' or mv[m]['category'] == 'DAMAGE_CATEGORY_STATUS':
                            chance = share * 1.2
                        else:
                            chance = share * 0.6
                    if rng.random() < chance:
                        chosen.add(m)
                by_root[fam_key] = set(chosen)
        if lvl_ok:
            chosen |= set(fundata.level_up_moves(c, 100, p)) & set(taught)
        new = (cur - set(taught)) | chosen
        if which == 'tm' and opt.get('fullHM', True):
            new |= set(hms)
        data[key] = sorted(new)
    ov.write(LEARNABLES, json.dumps(data, indent=2))
    head = {'full': 'Every Pokémon can learn every one', 'preferType': 'Random, more likely for moves of the Pokémon\'s own type',
            'random': 'Completely random'}[mode]
    extra = [', and every Pokémon can learn every HM'] if which == 'tm' and opt.get('fullHM', True) else ['']
    report.add('TM compatibility' if which == 'tm' else 'Tutor compatibility', [head + extra[0]], len(key_species))


def hm_full(ov, report):
    data = json.loads(ov.read(LEARNABLES))
    hms = _tm_lists(ov)['hms']
    for k in data:
        data[k] = sorted(set(data[k]) | set(hms))
    ov.write(LEARNABLES, json.dumps(data, indent=2))
    report.add('HM compatibility', ['Every Pokémon can learn every HM'])


# ---- items ------------------------------------------------------------------------------------

_ITEMS = {}


def item_info(ov):
    text = ov.read(ITEMS)
    key = hash(text)
    if _ITEMS.get('key') == key:
        return _ITEMS['data']
    out = {}
    parts = re.split(r'^\s*\[(ITEM_[A-Z0-9_]+)\]\s*=\s*$', text, flags=re.M)
    for i in range(1, len(parts), 2):
        const, body = parts[i], parts[i + 1]
        pocket = re.search(r'\.pocket\s*=\s*(POCKET_\w+)', body)
        sort = re.search(r'\.sortType\s*=\s*(ITEM_TYPE_\w+)', body)
        price = re.search(r'\.price\s*=\s*([^\n]+),', body)
        pv = fundata.resolve(price.group(1)) if price else '0'
        pm = re.match(r'\d+', pv)
        out[const] = {'pocket': pocket.group(1) if pocket else '', 'sort': sort.group(1) if sort else '',
                      'price': int(pm.group()) if pm else 0, 'name': (re.search(r'ITEM_NAME\("([^"]*)"\)', body) or [0, _pretty(const)])[1]}
    _ITEMS.update(key=key, data=out)
    return out


def item_pool(ov, ban_bad=True, allow_tms=False, ban=()):
    info = item_info(ov)
    out = []
    for c, i in info.items():
        if c in ITEM_NEVER or c in ban or i['pocket'] in ('POCKET_KEY_ITEMS', '') or i['sort'] in ITEM_NEVER_SORT:
            continue
        if i['pocket'] == 'POCKET_TM_HM' and (not allow_tms or c.startswith('ITEM_HM')):
            continue
        if ban_bad and (i['sort'] in ITEM_BAD_SORT or i['price'] == 0 and i['pocket'] != 'POCKET_BERRIES'):
            continue
        out.append(c)
    return sorted(out)


def _map_jsons():
    return [os.path.relpath(f, ROOT) for f in sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/map.json'))) if 'frlg' not in f.lower()]


def field_items(ov, opt, rng, report):
    mode = opt.get('mode', 'shuffle')
    ban_bad = opt.get('banBad', True)
    hidden = opt.get('hidden', True)
    info = item_info(ov)
    spots = []  # (rel, data, obj, key)
    datas = {}
    for rel in _map_jsons():
        d = json.loads(ov.read(rel))
        datas[rel] = d
        for o in d.get('object_events') or []:
            it = o.get('trainer_sight_or_berry_tree_id', '')
            if o.get('script') == 'Common_EventScript_FindItem' and it in info and info[it]['pocket'] != 'POCKET_KEY_ITEMS':
                spots.append((o, 'trainer_sight_or_berry_tree_id'))
        if hidden:
            for b in d.get('bg_events') or []:
                if b.get('type') == 'hidden_item' and b.get('item') in info and info[b['item']]['pocket'] != 'POCKET_KEY_ITEMS':
                    spots.append((b, 'item'))
    tms = [o[k] for o, k in spots if info[o[k]]['pocket'] == 'POCKET_TM_HM']
    if mode == 'shuffle':
        pool = [o[k] for o, k in spots]
        rng.shuffle(pool)
        for (o, k), it in zip(spots, pool):
            o[k] = it
    else:
        pool = item_pool(ov, ban_bad=ban_bad)
        tm_pool = [c for c, i in info.items() if c.startswith('ITEM_TM_')]
        even = mode == 'even'
        bag = []
        for o, k in spots:
            if info[o[k]]['pocket'] == 'POCKET_TM_HM':
                o[k] = rng.choice(tm_pool)  # TMs stay TMs, so none go missing
                continue
            if even:
                if not bag:
                    bag = list(pool)
                    rng.shuffle(bag)
                o[k] = bag.pop()
            else:
                o[k] = rng.choice(pool)
    for rel, d in datas.items():
        ov.write(rel, json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    names = {'shuffle': 'Shuffled', 'random': 'Random', 'even': 'Random, each item about as often'}
    report.add('Items on the ground', ['%s: %d item balls%s' % (names[mode], len(spots), ' and hidden items' if hidden else ''),
                                       '%d TMs stay TMs' % len(tms)], len(spots))


def _shop_lists(ov):
    from shops import MART_RE, _list_re
    found = []
    for rel in _script_files():
        t = ov.read(rel)
        for label in dict.fromkeys(MART_RE.findall(t)):
            found.append((label, rel))
    out = []
    for label, used_in in found:
        for rel in [used_in] + _script_files():
            t = ov.read(rel)
            m = _list_re(label).search(t)
            if m:
                out.append({'label': label, 'file': rel, 'items': re.findall(r'\.2byte\s+(\w+)', m.group(1))})
                break
    return out


def shop_items(ov, opt, rng, report):
    from shops import _list_re
    mode = opt.get('mode', 'shuffle')
    keep_regular = not opt.get('banRegular', False)
    info = item_info(ov)
    shops = _shop_lists(ov)
    ban = set()
    if opt.get('banOverpowered', True):
        ban |= ITEM_OVERPOWERED
    pool = item_pool(ov, ban_bad=opt.get('banBad', True), allow_tms=True, ban=ban)
    evo_items = [c for c, i in info.items() if i['sort'] in ('ITEM_TYPE_EVOLUTION_STONE', 'ITEM_TYPE_EVOLUTION_ITEM') and c in pool]
    x_items = [c for c, i in info.items() if i['sort'] == 'ITEM_TYPE_X_ITEM']
    changeable = []
    for s in shops:
        for i, it in enumerate(s['items']):
            if keep_regular and it in REGULAR_SHOP:
                continue
            if it not in info or info[it]['pocket'] == 'POCKET_KEY_ITEMS':
                continue
            changeable.append((s, i))
    if mode == 'shuffle':
        bag = [s['items'][i] for s, i in changeable]
        rng.shuffle(bag)
        for (s, i), it in zip(changeable, bag):
            s['items'][i] = it
    else:
        for s, i in changeable:
            s['items'][i] = rng.choice(pool)
    if opt.get('guaranteeEvo', True) and evo_items and shops:
        missing = [e for e in evo_items if not any(e in s['items'] for s in shops)]
        for e in missing[:12]:
            rng.choice(shops)['items'].append(e)
    if opt.get('guaranteeX', True) and x_items and shops:
        if not any(x in s['items'] for s in shops for x in x_items):
            rng.choice(shops)['items'].extend(x_items)
    for s in shops:
        s['items'] = list(dict.fromkeys(s['items']))
        t = ov.read(s['file'])
        m = _list_re(s['label']).search(t)
        if not m:
            continue
        indent = re.match(r'[ \t]*', m.group(1)).group() if m.group(1) else '\t'
        body = ''.join('%s.2byte %s\n' % (indent or '\t', it) for it in s['items'])
        ov.write(s['file'], t[:m.start(1)] + body + t[m.end(1):])
    report.add('Shops', ['%s items in %d shops%s' % ('Shuffled' if mode == 'shuffle' else 'Random', len(shops),
                                                      ' (Poké Balls, potions and other basics stay)' if keep_regular else '')],
               len(changeable))


def pickup_items(ov, opt, rng, report):
    t = ov.read(PICKUP)
    m = re.search(r'(static const struct PickupItem sPickupTable\[\]\s*=\s*\{)(.*?)(\n\};)', t, re.S)
    if not m:
        report.add('Pickup', ['Could not find the Pickup list, left as it was'])
        return
    pool = item_pool(ov, ban_bad=True, ban=ITEM_OVERPOWERED - {'ITEM_RARE_CANDY'})
    used = set()
    names = []
    rows = m.group(2).split('\n')
    for i, row in enumerate(rows):
        rm = re.match(r'(\s*\{\s*)(ITEM_\w+)(\s*,.*)$', row)
        if rm:
            choice = rng.choice([x for x in pool if x not in used])
            used.add(choice)
            names.append(item_info(ov)[choice]['name'])
            rows[i] = rm.group(1) + choice + rm.group(3)
    ov.write(PICKUP, t[:m.start(2)] + '\n'.join(rows) + t[m.end(2):])
    report.add('Pickup', ['Pokémon with Pickup now find: ' + ', '.join(names)], len(names))


# ---- type chart ---------------------------------------------------------------------------------

def type_chart(ov, opt, rng, report):
    mode = opt.get('mode', 'shuffle')
    t = ov.read(TYPES_INFO)
    m = re.search(r'(gTypeEffectivenessTable\[NUMBER_OF_MON_TYPES\]\[NUMBER_OF_MON_TYPES\]\s*=\s*\{)(.*?)(\n\};)', t, re.S)
    if not m:
        report.add('Type chart', ['Could not find the type chart, left as it was'])
        return
    rows = m.group(2).split('\n')
    entries = []
    for r in rows:
        rm = re.match(r'(\s*\[(TYPE_\w+)\]\s*=\s*\{)(.*)(\},?\s*)$', r)
        if rm:
            cells = [c.strip() for c in rm.group(3).split(',')]
            entries.append([rm.group(1), rm.group(2), cells, rm.group(4)])
    order = [e[1] for e in entries]
    real = [i for i, ty in enumerate(order) if ty in TYPES]
    resolve = {'______': '______', 'STL_RS': 'X(1.0)' if fundata.config_value('B_UPDATED_TYPE_MATCHUPS') >= 6 else 'X(0.5)',
               'PSN_RS': 'X(0.5)', 'BUG_RS': 'X(1.0)', 'PSY_RS': 'X(2.0)', 'FIR_RS': 'X(0.5)'}

    def val(c):
        c = resolve.get(c, c)
        return 1.0 if c == '______' else float(re.search(r'[\d.]+', c).group())

    def cell(v):
        return '______' if v == 1.0 else 'X(%.1f)' % v
    grid = {(a, d): val(entries[a][2][d]) for a in real for d in real}
    lines = []
    if mode == 'inverse':
        for k, v in grid.items():
            grid[k] = 2.0 if v in (0.0, 0.5) else 0.5 if v == 2.0 else 1.0
        lines.append('Inverse battle chart: weaknesses become resistances and the other way round')
    elif mode == 'shuffle':
        # keep how many weaknesses there are, move them around
        vals = list(grid.values())
        rng.shuffle(vals)
        for k, v in zip(list(grid), vals):
            grid[k] = v
        lines.append('Every matchup shuffled (same number of weaknesses, resistances and immunities)')
    elif mode == 'identities':
        # each type keeps its row, but the defending types swap places
        perm = list(real)
        rng.shuffle(perm)
        old = dict(grid)
        for a in real:
            for d, d2 in zip(real, perm):
                grid[(a, d)] = old[(a, d2)]
        lines.append('Each type keeps how strong it is, but what it is good against is shuffled')
    else:
        for k in grid:
            grid[k] = rng.choices([1.0, 2.0, 0.5, 0.0], [62, 19, 16, 3])[0]
        lines.append('Every matchup is random')
    for a in real:
        for d in real:
            entries[a][2][d] = cell(grid[(a, d)])
    by_type = {e[1]: e for e in entries}
    new_rows = []
    for r in rows:
        rm = re.match(r'\s*\[(TYPE_\w+)\]', r)
        if rm and rm.group(1) in by_type:
            e = by_type[rm.group(1)]
            new_rows.append(e[0] + ', '.join(e[2]) + e[3])
        else:
            new_rows.append(r)
    ov.write(TYPES_INFO, t[:m.start(2)] + '\n'.join(new_rows) + t[m.end(2):])
    for ty in ('TYPE_FIRE', 'TYPE_WATER', 'TYPE_GRASS'):
        a = order.index(ty)
        strong = [_pretty(order[d]) for d in real if grid[(a, d)] == 2.0]
        lines.append('%s is now strong against: %s' % (_pretty(ty), ', '.join(strong) or 'nothing'))
    report.add('Type chart', lines)


# ---- trainers: extras ---------------------------------------------------------------------------

def trainer_extras(ov, opt, rng, report, keep=()):
    import funmodes
    import sets
    import trainers
    p = fundata.pool()
    party = funmodes.Party(ov.read(funmodes.PARTY))
    pick = funmodes.Picker(rng, opt.get('legendaries', False))
    lines = []
    lvl = int(opt.get('levelPercent', 0) or 0)
    full_at = int(opt.get('fullyEvolvedAt', 0) or 0)
    extra_boss = int(opt.get('extraBoss', 0) or 0)
    extra_regular = int(opt.get('extraRegular', 0) or 0)
    items_boss = opt.get('itemsBoss', False)
    items_regular = opt.get('itemsRegular', False)
    all_doubles = opt.get('allDoubles', False)
    better = opt.get('betterMovesets', False)
    n_trainers = 0
    for tid, t in party.items():
        if tid in keep or not t['party']:
            continue
        boss = funmodes.is_boss(tid, t)
        changed = False
        if lvl:
            for m in t['party']:
                lv = str(m.get('Level', ''))
                if lv.isdigit():
                    m['Level'] = str(min(100, max(1, round(int(lv) * (100 + lvl) / 100))))
            changed = True
        extra = extra_boss if boss else extra_regular
        if extra and len(t['party']) < 6:
            used = {funmodes.species_of(m) for m in t['party']}
            ace = t['party'][-1]
            for _ in range(min(extra, 6 - len(t['party']))):
                new = pick.similar(funmodes.species_of(ace), used)
                used.add(new)
                lv = max(1, int(ace.get('Level') or 5) - 1) if str(ace.get('Level', '')).isdigit() else 5
                t['party'].insert(0, {'species': fundata.showdown_name(new, p), 'nickname': '', 'gender': '', 'item': '',
                                      'moves': [], 'extra': [], 'Level': str(lv)})
            changed = True
        if full_at:
            for m in t['party']:
                lv = int(m.get('Level') or 0) if str(m.get('Level', '')).isdigit() else 0
                c = funmodes.species_of(m)
                if lv >= full_at and c in p:
                    final = c
                    seen = {c}
                    while True:
                        nxt = [x for x in p[final]['evolvesTo'] if x in p and p[x]['usable'] and x not in seen]
                        if not nxt:
                            break
                        final = rng.choice(nxt)
                        seen.add(final)
                    if final != c:
                        funmodes.set_species(m, final, p)
                        changed = True
        if all_doubles and len(t['party']) >= 2 and trainers.field(t, 'Double Battle', 'No') != 'Yes':
            funmodes.set_field(t, 'Double Battle', 'Yes')
            changed = True
        if better or (items_boss and boss) or (items_regular and not boss):
            give_items = (items_boss and boss) or (items_regular and not boss)
            if better:
                sets.build_team(t['party'], p, rng, boss=boss, doubles=trainers.field(t, 'Double Battle') == 'Yes',
                                items=give_items)
            else:
                for m in t['party']:
                    if m.get('item'):
                        continue
                    info = p.get(funmodes.species_of(m))
                    if not info:
                        continue
                    lv = int(m.get('Level') or 5) if str(m.get('Level', '')).isdigit() else 5
                    if opt.get('consumableOnly', False):
                        it = rng.choice(['ITEM_SITRUS_BERRY', 'ITEM_ORAN_BERRY', 'ITEM_LUM_BERRY', 'ITEM_CHESTO_BERRY',
                                         'ITEM_WHITE_HERB', 'ITEM_MENTAL_HERB', 'ITEM_FOCUS_SASH', 'ITEM_AIR_BALLOON'])
                    else:
                        mvs = ['MOVE_' + x.upper().replace(' ', '_').replace('-', '_') for x in m.get('moves', [])]
                        it = sets.pick_item(info, lv, mvs, set(), boss, rng, None)
                    m['item'] = sets.item_name(it)
            changed = True
        if changed:
            party.put(tid, t)
            n_trainers += 1
    ov.write(funmodes.PARTY, party.text())
    if lvl:
        lines.append('Trainer levels %+d%%' % lvl)
    if extra_boss or extra_regular:
        lines.append('Extra Pokémon: bosses +%d, others +%d (up to 6)' % (extra_boss, extra_regular))
    if full_at:
        lines.append('Fully evolved from level %d' % full_at)
    if all_doubles:
        lines.append('Every trainer with two or more Pokémon fights in a double battle')
    if better:
        lines.append('Smarter movesets')
    if items_boss or items_regular:
        lines.append('Held items for %s' % ' and '.join([x for x, on in (('bosses', items_boss), ('other trainers', items_regular)) if on]))
    report.add('Trainer extras', lines, n_trainers)


def trainer_names(ov, opt, rng, report):
    import funmodes
    import trainers
    party = funmodes.Party(ov.read(funmodes.PARTY))
    regular = [(tid, t) for tid, t in party.items() if not funmodes.is_boss(tid, t) and trainers.field(t, 'Name')]
    names = [trainers.field(t, 'Name') for _, t in regular]
    rng.shuffle(names)
    for (tid, t), nm in zip(regular, names):
        funmodes.set_field(t, 'Name', nm)
        party.put(tid, t)
    ov.write(funmodes.PARTY, party.text())
    report.add('Trainer names', ['%d trainers swapped names (Gym Leaders and other bosses keep theirs)' % len(regular)], len(regular))


KEEP_CLASSES = {'TRAINER_CLASS_LEADER', 'TRAINER_CLASS_ELITE_FOUR', 'TRAINER_CLASS_CHAMPION', 'TRAINER_CLASS_RIVAL',
                'TRAINER_CLASS_PKMN_TRAINER_1', 'TRAINER_CLASS_PKMN_TRAINER_2', 'TRAINER_CLASS_PKMN_TRAINER_3',
                'TRAINER_CLASS_MAGMA_LEADER', 'TRAINER_CLASS_AQUA_LEADER', 'TRAINER_CLASS_MAGMA_ADMIN',
                'TRAINER_CLASS_AQUA_ADMIN', 'TRAINER_CLASS_TEAM_AQUA', 'TRAINER_CLASS_TEAM_MAGMA',
                'TRAINER_CLASS_SALON_MAIDEN', 'TRAINER_CLASS_DOME_ACE', 'TRAINER_CLASS_PALACE_MAVEN',
                'TRAINER_CLASS_ARENA_TYCOON', 'TRAINER_CLASS_FACTORY_HEAD', 'TRAINER_CLASS_PIKE_QUEEN',
                'TRAINER_CLASS_PYRAMID_KING', 'TRAINER_CLASS_NONE'}


def trainer_class_names(ov, opt, rng, report):
    t = ov.read(TRAINER_CLASSES)
    pat = re.compile(r'^(\s*\[(TRAINER_CLASS_\w+)\]\s*=\s*\{\s*_\(")([^"]*)("\))', re.M)
    rows = [m for m in pat.finditer(t) if m.group(2) not in KEEP_CLASSES]
    names = [m.group(3) for m in rows]
    rng.shuffle(names)
    mapping = {m.group(2): n for m, n in zip(rows, names)}

    def one(m):
        if m.group(2) in mapping:
            return m.group(1) + mapping[m.group(2)] + m.group(4)
        return m.group(0)
    ov.write(TRAINER_CLASSES, pat.sub(one, t))
    show = ['%s are now called %s' % (m.group(3).title(), mapping[m.group(2)].title()) for m in rows[:6]]
    report.add('Trainer class names', show, len(rows))


def type_themed_trainers(ov, opt, rng, report, keep=()):
    """Every trainer (or only Gyms and the Elite Four) uses one random type."""
    import funmodes
    import trainers
    p = fundata.pool()
    party = funmodes.Party(ov.read(funmodes.PARTY))
    pick = funmodes.Picker(rng, opt.get('legendaries', False))
    fam = funmodes.starter_families()
    only_gyms = opt.get('mode') == 'gymTypes'
    gym_types = {}
    pool_types = list(TYPES)
    rng.shuffle(pool_types)
    lines = []
    for tid, t in party.items():
        if tid in keep or not t['party']:
            continue
        cls = trainers.field(t, 'Class')
        boss = cls in ('Leader', 'Elite Four', 'Champion')
        if only_gyms and not boss:
            continue
        name = trainers.field(t, 'Name')
        if boss:
            if name not in gym_types:
                gym_types[name] = pool_types[len(gym_types) % len(pool_types)]
            ty = gym_types[name]
        else:
            ty = rng.choice(TYPES)
        used = set()
        for m in t['party']:
            old = funmodes.species_of(m)
            if cls == 'Rival' and old in fam:
                continue
            cands = [i for i in pick.all if ty in i['types'] and i['const'] not in used]
            info = p.get(old)
            bst = info['bst'] if info else 400
            close = [i for i in cands if abs(i['bst'] - bst) <= bst * 0.2] or cands
            new = rng.choice(close)['const'] if close else pick.random(used)
            used.add(new)
            funmodes.set_species(m, new, p)
        party.put(tid, t)
        if boss:
            lines.append('%s %s: %s' % (cls, name, _pretty(ty)))
    ov.write(funmodes.PARTY, party.text())
    report.add('Type-themed trainers', list(dict.fromkeys(lines)))


# ---- wild extras ------------------------------------------------------------------------------------

def wild_themed(ov, opt, rng, report):
    """Every area gets one type (and catch 'em all spreads the Pokemon so each one shows up somewhere)."""
    import funmodes
    data = json.loads(ov.read(funmodes.WILD))
    pick = funmodes.Picker(rng, opt.get('legendaries', False))
    p = pick.p
    themed = opt.get('typeThemed', False)
    catch_all = opt.get('catchEmAll', False)
    remaining = [i['const'] for i in pick.all]
    rng.shuffle(remaining)
    lines = []
    for group in data['wild_encounter_groups']:
        if not group.get('for_maps'):
            continue
        for enc in group['encounters']:
            ty = rng.choice(TYPES) if themed else None
            area = {}
            for key, field in enc.items():
                if not isinstance(field, dict) or 'mons' not in field:
                    continue
                for mon in field['mons']:
                    old = mon['species']
                    if old in area:
                        mon['species'] = area[old]
                        continue
                    new = None
                    if catch_all and remaining:
                        if ty:
                            for j, c in enumerate(remaining):
                                if ty in p[c]['types']:
                                    new = remaining.pop(j)
                                    break
                        else:
                            new = remaining.pop()
                    if not new:
                        new = pick.of_type(ty, set(area.values())) if ty else pick.similar(old, set(area.values()))
                    area[old] = new
                    mon['species'] = new
            if ty:
                label = enc.get('map', enc.get('base_label', '?')).replace('MAP_', '').replace('_', ' ').title()
                lines.append('%s: %s' % (label, _pretty(ty)))
    ov.write(funmodes.WILD, json.dumps(data, indent=2) + '\n')
    head = []
    if catch_all:
        head.append('Catch \'em all: %d different Pokémon spread over the wild areas' % (len(pick.all) - len(remaining)))
    report.add('Wild Pokémon areas', head + lines)


def wild_levels(ov, opt, report):
    import funmodes
    pct = int(opt.get('levelPercent', 0) or 0)
    if not pct:
        return
    data = json.loads(ov.read(funmodes.WILD))
    n = 0
    for group in data['wild_encounter_groups']:
        if not group.get('for_maps'):
            continue
        for enc in group['encounters']:
            for key, field in enc.items():
                if isinstance(field, dict) and 'mons' in field:
                    for mon in field['mons']:
                        for k in ('min_level', 'max_level'):
                            if k in mon:
                                mon[k] = max(1, min(100, round(mon[k] * (100 + pct) / 100)))
                        n += 1
    ov.write(funmodes.WILD, json.dumps(data, indent=2) + '\n')
    report.add('Wild levels', ['Wild Pokémon levels %+d%%' % pct], n)


def catch_rates(ov, opt, report):
    """The randomizer's 'minimum catch rate' levels 1 to 5."""
    level = int(opt.get('minCatchRate', 0) or 0)
    if not level:
        return
    floor = {1: 45, 2: 75, 3: 120, 4: 200, 5: 255}[max(1, min(5, level))]
    plan = {}

    def fn(const, body):
        m = re.search(r'\.catchRate\s*=\s*([^\n]+),', body)
        if not m:
            return None
        v = re.match(r'\d+', fundata.resolve(m.group(1)))
        if v and int(v.group()) >= floor:
            return None
        plan[const] = floor
        return _set_line(body, 'catchRate', str(floor))
    edit_species(ov, fn)
    report.add('Catch rates', ['Every Pokémon is at least as easy to catch as catch rate %d' % floor], len(plan))


def wild_held_items(ov, opt, rng, report):
    pool = item_pool(ov, ban_bad=opt.get('banBadItems', True))
    p = fundata.pool()
    n = [0]

    def fn(const, body):
        if const not in p or not p[const]['usable'] or not re.search(r'\.baseHP\s*=', body):
            return None  # template-built forms keep the template's items
        common = rng.choice(pool) if rng.random() < 0.3 else ''
        rare = rng.choice(pool) if rng.random() < 0.3 else ''
        for name, v in (('itemCommon', common), ('itemRare', rare)):
            body = re.sub(r'^[ \t]*\.' + name + r'\s*=[^\n]*\n', '', body, flags=re.M)
            if v:
                try:
                    body = species_mod._insert_line(body, '.%s = %s,' % (name, v),
                                                    ('expYield', 'catchRate', 'baseSpDefense', 'baseSpeed', 'types'))
                except species_mod.SpeciesError:
                    pass
        n[0] += 1
        return body
    edit_species(ov, fn)
    report.add('Wild held items', ['About 1 in 3 wild Pokémon of each kind can hold a random item'], n[0])


# ---- quality of life ----------------------------------------------------------------------------------

EXP_SHARE_FLAG = 'FLAG_UNUSED_0x4FF'  # nothing else uses it (the Maps tab skips flags named in editor/*.py)
CONFIG_TWEAKS = {
    'instantText': ('include/config/text.h', 'TEXT_SPEED_INSTANT', 'TRUE', 'Text appears instantly'),
    'reusableTMs': ('include/config/item.h', 'I_REUSABLE_TMS', 'TRUE', 'TMs can be used again and again'),
    'expShare': ('include/config/item.h', 'I_EXP_SHARE_FLAG', 'FLAG_UNUSED_0x4FF', 'Your whole party gets EXP from every battle (Gen 6 Exp. Share, always on)'),
    'showTypes': ('include/config/battle.h', 'B_SHOW_TYPES', 'SHOW_TYPES_ALWAYS', 'Types are shown in battle'),
    'showEffectiveness': ('include/config/battle.h', 'B_SHOW_EFFECTIVENESS', 'SHOW_EFFECTIVENESS_ALWAYS', 'Move effectiveness is always shown'),
    'fastIntro': ('include/config/battle.h', 'B_FAST_INTRO_NO_SLIDE', 'TRUE', 'Battles start without the slide-in'),
}


def misc(ov, opt, report):
    lines = []
    for key, (rel, name, value, label) in CONFIG_TWEAKS.items():
        if not opt.get(key):
            continue
        t = ov.read(rel)
        t2, n = re.subn(r'^(#define\s+%s\s+)(\S+)' % name, lambda m: m.group(1) + value, t, flags=re.M)
        if n:
            ov.write(rel, t2)
            lines.append(label)
    start = []
    if opt.get('nationalDex'):
        start.append('    EnableNationalPokedex();')
        lines.append('National Pokédex from the start')
    if opt.get('expShare'):
        start.append('    FlagSet(%s);' % EXP_SHARE_FLAG)
    if opt.get('runningShoes'):
        start.append('    FlagSet(FLAG_SYS_B_DASH);')
        lines.append('Running Shoes from the start')
    if start:
        t = ov.read(NEW_GAME)
        t = re.sub(r'\n    // FUN MODES START\n.*?    // FUN MODES END\n', '\n', t, flags=re.S)
        block = '    // FUN MODES START\n' + '\n'.join(start) + '\n    // FUN MODES END\n'
        t = re.sub(r'(void NewGameInitData\(void\)\n\{.*?\n)(\}\n)', lambda m: m.group(1) + block + m.group(2), t, count=1, flags=re.S)
        if '#include "event_data.h"' not in t:
            t = t.replace('#include "global.h"\n', '#include "global.h"\n#include "event_data.h"\n', 1)
        ov.write(NEW_GAME, t)
    report.add('Quality of life', lines)


# ---- order --------------------------------------------------------------------------------------------

def run_before(ov, s, rng, report):
    """Changes to the Pokemon themselves, done before starters, wild and trainers pick Pokemon."""
    on = lambda k: (s.get(k) or {}).get('on')  # noqa: E731
    changed_species = False
    if on('baseStats'):
        base_stats(ov, s['baseStats'], rng('baseStats'), report)
        changed_species = True
    if on('types'):
        types(ov, s['types'], rng('types'), report)
        changed_species = True
    if on('abilities'):
        abilities(ov, s['abilities'], rng('abilities'), report)
        changed_species = True
    if on('evolutions'):
        evolutions(ov, s['evolutions'], rng('evolutions'), report)
        changed_species = True
    if on('evoHelpers'):
        evolution_tweaks(ov, s['evoHelpers'], rng('evoHelpers'), report)
        changed_species = True
    if on('expCurves'):
        exp_curves(ov, s['expCurves'], rng('expCurves'), report)
    if changed_species:
        fundata.reset_caches()
    if on('moveData'):
        move_data(ov, s['moveData'], rng('moveData'), report)
        fundata.reset_caches()
    if on('movesets'):
        movesets_level_up(ov, s['movesets'], rng('movesets'), report)
        fundata.reset_caches()
    if on('tmMoves'):
        tm_moves(ov, s['tmMoves'], rng('tmMoves'), report)
    if on('tmCompat'):
        compatibility(ov, s['tmCompat'], rng('tmCompat'), report, 'tm')
    elif on('tmMoves') and s['tmMoves'].get('fullHM'):
        hm_full(ov, report)
    if on('tutorMoves'):
        tutor_moves(ov, s['tutorMoves'], rng('tutorMoves'), report)
    if on('tutorCompat'):
        compatibility(ov, s['tutorCompat'], rng('tutorCompat'), report, 'tutor')
    fundata.reset_caches()


def run_after(ov, s, rng, report, keep=()):
    """Everything that works on trainers, wild areas, items and the rest, after the main randomizers."""
    on = lambda k: (s.get(k) or {}).get('on')  # noqa: E731
    if on('statics'):
        statics(ov, s['statics'], rng('statics'), report)
        if s['statics'].get('catchingTutorial', True):
            catching_tutorial(ov, s['statics'], rng('tutorial'), report)
    if on('trades'):
        trades(ov, s['trades'], rng('trades'), report)
    tr = s.get('trainers') or {}
    if tr.get('on') and tr.get('mode') in ('typeThemed', 'gymTypes'):
        type_themed_trainers(ov, tr, rng('trainerTypes'), report, keep)
    if on('trainerExtras'):
        trainer_extras(ov, s['trainerExtras'], rng('trainerExtras'), report, keep)
        if s['trainerExtras'].get('randomNames'):
            trainer_names(ov, s['trainerExtras'], rng('trainerNames'), report)
        if s['trainerExtras'].get('randomClassNames'):
            trainer_class_names(ov, s['trainerExtras'], rng('classNames'), report)
    wild = s.get('wild') or {}
    if wild.get('on') and (wild.get('typeThemed') or wild.get('catchEmAll')):
        wild_themed(ov, wild, rng('wildThemed'), report)
    if on('wildExtras'):
        wild_levels(ov, s['wildExtras'], report)
        catch_rates(ov, s['wildExtras'], report)
        if s['wildExtras'].get('heldItems'):
            wild_held_items(ov, s['wildExtras'], rng('wildItems'), report)
    if on('fieldItems'):
        field_items(ov, s['fieldItems'], rng('fieldItems'), report)
    if on('shopItems'):
        shop_items(ov, s['shopItems'], rng('shopItems'), report)
    if on('pickup'):
        pickup_items(ov, s['pickup'], rng('pickup'), report)
    if on('typeChart'):
        type_chart(ov, s['typeChart'], rng('typeChart'), report)
    if on('palettes'):
        palettes(ov, s['palettes'], rng('palettes'), report)
    if on('misc'):
        misc(ov, s['misc'], report)


def finish(ov, s, report):
    """Last fixes after Hard mode and the rest built their teams."""
    on = lambda k: (s.get(k) or {}).get('on')  # noqa: E731
    if on('movesets') and s['movesets'].get('mode') == 'metronome':
        metronome_trainers(ov, report)
    if on('abilities'):
        n = fix_party_abilities(ov, report)
        if n:
            report.add('Trainer abilities', ['%d trainer Pokémon had an ability their species lost, so they use a normal one now' % n], n)

