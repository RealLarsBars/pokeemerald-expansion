"""Builds strong, sensible sets for trainer Pokemon: four moves with STAB and
coverage plus a setup or support move, an item that fits the role, a
nature, EVs and IVs, and the best ability the Pokemon can have.

Used by Hard mode. Moves come from what the Pokemon learns by level up at
its level, plus TMs and tutors for stronger trainers."""

from common import pretty_name
import fundata

NEVER = {
    'MOVE_HYPER_BEAM', 'MOVE_GIGA_IMPACT', 'MOVE_BLAST_BURN', 'MOVE_HYDRO_CANNON', 'MOVE_FRENZY_PLANT',
    'MOVE_ROCK_WRECKER', 'MOVE_ROAR_OF_TIME', 'MOVE_PRISMATIC_LASER', 'MOVE_ETERNABEAM', 'MOVE_METEOR_ASSAULT',
    'MOVE_EXPLOSION', 'MOVE_SELF_DESTRUCT', 'MOVE_MISTY_EXPLOSION', 'MOVE_MEMENTO', 'MOVE_FINAL_GAMBIT',
    'MOVE_SOLAR_BLADE', 'MOVE_SKY_ATTACK', 'MOVE_RAZOR_WIND', 'MOVE_SKULL_BASH', 'MOVE_FOCUS_PUNCH',
    'MOVE_DREAM_EATER', 'MOVE_SNORE', 'MOVE_BELCH', 'MOVE_LAST_RESORT', 'MOVE_SYNCHRONOISE', 'MOVE_DOOM_DESIRE',
    'MOVE_FUTURE_SIGHT', 'MOVE_DIG', 'MOVE_FLY', 'MOVE_DIVE', 'MOVE_BOUNCE', 'MOVE_PHANTOM_FORCE',
    'MOVE_SHADOW_FORCE', 'MOVE_SKY_DROP', 'MOVE_BIDE', 'MOVE_COUNTER', 'MOVE_MIRROR_COAT', 'MOVE_METAL_BURST',
    'MOVE_FRUSTRATION', 'MOVE_STRUGGLE', 'MOVE_NATURAL_GIFT', 'MOVE_FLING', 'MOVE_SPIT_UP', 'MOVE_ROLLOUT',
    'MOVE_ICE_BALL', 'MOVE_FURY_CUTTER', 'MOVE_UPROAR', 'MOVE_MIND_BLOWN', 'MOVE_SHELL_TRAP', 'MOVE_BEAK_BLAST',
    'MOVE_THRASH', 'MOVE_PETAL_DANCE', 'MOVE_STEEL_BEAM', 'MOVE_CHLOROBLAST', 'MOVE_METEOR_BEAM', 'MOVE_ELECTRO_SHOT',
    'MOVE_TERA_BLAST', 'MOVE_TERA_STARSTORM', 'MOVE_HIDDEN_POWER', 'MOVE_RAGE', 'MOVE_SNIPE_SHOT_DUMMY', 'MOVE_DRAGON_RAGE', 'MOVE_SONIC_BOOM', 'MOVE_SPLASH',
}
VARIABLE = {'MOVE_LOW_KICK': 65, 'MOVE_GRASS_KNOT': 65, 'MOVE_HEAVY_SLAM': 65, 'MOVE_HEAT_CRASH': 65,
            'MOVE_GYRO_BALL': 65, 'MOVE_ELECTRO_BALL': 65, 'MOVE_RETURN': 90, 'MOVE_STORED_POWER': 40,
            'MOVE_SEISMIC_TOSS': 60, 'MOVE_NIGHT_SHADE': 60, 'MOVE_PUNISHMENT': 60, 'MOVE_FOUL_PLAY': 85}
SETUP_PHYS = ['MOVE_DRAGON_DANCE', 'MOVE_SWORDS_DANCE', 'MOVE_BULK_UP', 'MOVE_SHIFT_GEAR', 'MOVE_VICTORY_DANCE',
              'MOVE_COIL', 'MOVE_HONE_CLAWS', 'MOVE_HOWL']
SETUP_SPEC = ['MOVE_QUIVER_DANCE', 'MOVE_NASTY_PLOT', 'MOVE_CALM_MIND', 'MOVE_TAIL_GLOW', 'MOVE_TAKE_HEART',
              'MOVE_GROWTH', 'MOVE_WORK_UP']
SETUP_BOTH = ['MOVE_SHELL_SMASH']
RECOVERY = ['MOVE_RECOVER', 'MOVE_ROOST', 'MOVE_SLACK_OFF', 'MOVE_SOFT_BOILED', 'MOVE_MILK_DRINK', 'MOVE_SHORE_UP',
            'MOVE_MOONLIGHT', 'MOVE_SYNTHESIS', 'MOVE_MORNING_SUN', 'MOVE_STRENGTH_SAP', 'MOVE_WISH']
STATUS = ['MOVE_SPORE', 'MOVE_SLEEP_POWDER', 'MOVE_WILL_O_WISP', 'MOVE_THUNDER_WAVE', 'MOVE_TOXIC', 'MOVE_GLARE',
          'MOVE_YAWN', 'MOVE_LEECH_SEED', 'MOVE_STEALTH_ROCK', 'MOVE_SPIKES', 'MOVE_TOXIC_SPIKES', 'MOVE_STICKY_WEB',
          'MOVE_TAUNT', 'MOVE_ENCORE', 'MOVE_STUN_SPORE', 'MOVE_HYPNOSIS']
SCREENS = ['MOVE_REFLECT', 'MOVE_LIGHT_SCREEN']
DOUBLES = ['MOVE_FAKE_OUT', 'MOVE_TAILWIND', 'MOVE_FOLLOW_ME', 'MOVE_RAGE_POWDER', 'MOVE_TRICK_ROOM',
           'MOVE_HELPING_HAND', 'MOVE_WIDE_GUARD', 'MOVE_ICY_WIND', 'MOVE_SNARL', 'MOVE_ELECTROWEB']
WEATHER_ABILITIES = {'ABILITY_DROUGHT': 'sun', 'ABILITY_DRIZZLE': 'rain', 'ABILITY_SAND_STREAM': 'sand',
                     'ABILITY_SNOW_WARNING': 'snow', 'ABILITY_ORICHALCUM_PULSE': 'sun'}
WEATHER_ROCK = {'sun': 'ITEM_HEAT_ROCK', 'rain': 'ITEM_DAMP_ROCK', 'sand': 'ITEM_SMOOTH_ROCK', 'snow': 'ITEM_ICY_ROCK'}
WEATHER_TYPE = {'sun': 'TYPE_FIRE', 'rain': 'TYPE_WATER'}
TYPE_ITEM = {
    'TYPE_NORMAL': 'ITEM_SILK_SCARF', 'TYPE_FIGHTING': 'ITEM_BLACK_BELT', 'TYPE_FLYING': 'ITEM_SHARP_BEAK',
    'TYPE_POISON': 'ITEM_POISON_BARB', 'TYPE_GROUND': 'ITEM_SOFT_SAND', 'TYPE_ROCK': 'ITEM_HARD_STONE',
    'TYPE_BUG': 'ITEM_SILVER_POWDER', 'TYPE_GHOST': 'ITEM_SPELL_TAG', 'TYPE_STEEL': 'ITEM_METAL_COAT',
    'TYPE_FIRE': 'ITEM_CHARCOAL', 'TYPE_WATER': 'ITEM_MYSTIC_WATER', 'TYPE_GRASS': 'ITEM_MIRACLE_SEED',
    'TYPE_ELECTRIC': 'ITEM_MAGNET', 'TYPE_PSYCHIC': 'ITEM_TWISTED_SPOON', 'TYPE_ICE': 'ITEM_NEVER_MELT_ICE',
    'TYPE_DRAGON': 'ITEM_DRAGON_FANG', 'TYPE_DARK': 'ITEM_BLACK_GLASSES', 'TYPE_FAIRY': 'ITEM_FAIRY_FEATHER',
}
# Abilities worth picking over the others, best first. Anything not listed counts as average.
GOOD_ABILITIES = [
    'ABILITY_HUGE_POWER', 'ABILITY_PURE_POWER', 'ABILITY_SPEED_BOOST', 'ABILITY_DROUGHT', 'ABILITY_DRIZZLE',
    'ABILITY_SAND_STREAM', 'ABILITY_SNOW_WARNING', 'ABILITY_INTIMIDATE', 'ABILITY_PROTEAN', 'ABILITY_LIBERO',
    'ABILITY_ADAPTABILITY', 'ABILITY_MAGIC_GUARD', 'ABILITY_REGENERATOR', 'ABILITY_LEVITATE', 'ABILITY_MOXIE',
    'ABILITY_TECHNICIAN', 'ABILITY_SHEER_FORCE', 'ABILITY_TOUGH_CLAWS', 'ABILITY_SWIFT_SWIM', 'ABILITY_CHLOROPHYLL',
    'ABILITY_SAND_RUSH', 'ABILITY_SLUSH_RUSH', 'ABILITY_UNBURDEN', 'ABILITY_GUTS', 'ABILITY_MULTISCALE',
    'ABILITY_THICK_FAT', 'ABILITY_STURDY', 'ABILITY_MAGIC_BOUNCE', 'ABILITY_PRANKSTER', 'ABILITY_DRY_SKIN',
    'ABILITY_WATER_ABSORB', 'ABILITY_VOLT_ABSORB', 'ABILITY_FLASH_FIRE', 'ABILITY_SAP_SIPPER', 'ABILITY_STORM_DRAIN',
    'ABILITY_LIGHTNING_ROD', 'ABILITY_MOTOR_DRIVE', 'ABILITY_SKILL_LINK', 'ABILITY_STRONG_JAW', 'ABILITY_IRON_FIST',
    'ABILITY_RECKLESS', 'ABILITY_HUSTLE', 'ABILITY_SNIPER', 'ABILITY_SUPER_LUCK', 'ABILITY_POISON_HEAL',
    'ABILITY_MARVEL_SCALE', 'ABILITY_SOLAR_POWER', 'ABILITY_TINTED_LENS', 'ABILITY_SERENE_GRACE', 'ABILITY_NATURAL_CURE',
    'ABILITY_FILTER', 'ABILITY_SOLID_ROCK', 'ABILITY_ROUGH_SKIN', 'ABILITY_IRON_BARBS', 'ABILITY_STATIC',
    'ABILITY_FLAME_BODY', 'ABILITY_EFFECT_SPORE', 'ABILITY_POISON_POINT', 'ABILITY_CLEAR_BODY', 'ABILITY_INNER_FOCUS',
    'ABILITY_SWARM', 'ABILITY_BLAZE', 'ABILITY_TORRENT', 'ABILITY_OVERGROW', 'ABILITY_CUTE_CHARM',
]
BAD_ABILITIES = {'ABILITY_TRUANT', 'ABILITY_SLOW_START', 'ABILITY_DEFEATIST', 'ABILITY_KLUTZ', 'ABILITY_STALL',
                 'ABILITY_NONE', 'ABILITY_RUN_AWAY', 'ABILITY_HONEY_GATHER', 'ABILITY_PICKUP', 'ABILITY_BALL_FETCH',
                 'ABILITY_ILLUMINATE', 'ABILITY_FRISK', 'ABILITY_FOREWARN', 'ABILITY_ANTICIPATION'}
NATURES = {('phys', 'fast'): 'Jolly', ('phys', 'slow'): 'Adamant', ('spec', 'fast'): 'Timid',
           ('spec', 'slow'): 'Modest', ('wall', 'phys'): 'Impish', ('wall', 'spec'): 'Bold'}


def power_cap(level, boss):
    if level < 15:
        return 60 if not boss else 70
    if level < 25:
        return 80 if not boss else 90
    if level < 35:
        return 100
    return 999


def move_name(const):
    return pretty_name(const[len('MOVE_'):])


def item_name(const):
    return pretty_name(const[len('ITEM_'):])


def ability_name(const):
    return pretty_name(const[len('ABILITY_'):])


def team_weather(party, p):
    for m in party:
        ab = m.get('Ability', '')
        for a, w in WEATHER_ABILITIES.items():
            if ab and ab.replace(' ', '_').upper() == a[len('ABILITY_'):]:
                return w
    return None


def best_ability(info, weather):
    abilities = [a for a in info['abilities'] if a and a != 'ABILITY_NONE']
    if not abilities:
        return None
    rank = {a: i for i, a in enumerate(GOOD_ABILITIES)}

    def score(a):
        s = -rank.get(a, len(GOOD_ABILITIES))
        if a in BAD_ABILITIES:
            s -= 1000
        if weather == 'sun' and a in ('ABILITY_CHLOROPHYLL', 'ABILITY_SOLAR_POWER'):
            s += 100
        if weather == 'rain' and a in ('ABILITY_SWIFT_SWIM', 'ABILITY_RAIN_DISH', 'ABILITY_DRY_SKIN'):
            s += 100
        if weather == 'sand' and a in ('ABILITY_SAND_RUSH', 'ABILITY_SAND_FORCE'):
            s += 100
        if weather == 'snow' and a in ('ABILITY_SLUSH_RUSH', 'ABILITY_ICE_BODY'):
            s += 100
        return s
    return max(abilities, key=score)


def role(info):
    st = info['stats']
    offense = max(st['baseAttack'], st['baseSpAttack'])
    bulk = st['baseHP'] + st['baseDefense'] + st['baseSpDefense']
    kind = 'phys' if st['baseAttack'] >= st['baseSpAttack'] else 'spec'
    if offense < 75 and bulk >= 230:
        return 'wall', kind
    return kind, 'fast' if st['baseSpeed'] >= 80 else 'slow'


def candidates(const, level, p, boss):
    learned = fundata.level_up_moves(const, level, p)
    teach = fundata.teachable_moves(const) if (boss or level >= 30) else []
    return list(dict.fromkeys(learned + teach))


def attack_score(mc, md, info, kind, weather, doubles, ability):
    if mc in NEVER or md['category'] == 'DAMAGE_CATEGORY_STATUS':
        return 0
    power = VARIABLE.get(mc, md['power'])
    if power <= 1:
        return 0
    if mc == 'MOVE_SOLAR_BEAM' and weather != 'sun':
        return 0
    power *= md.get('hits', 1)
    if ability == 'ABILITY_TECHNICIAN' and md['power'] <= 60:
        power *= 1.5
    st = info['stats']
    stat = st['baseAttack'] if md['category'] == 'DAMAGE_CATEGORY_PHYSICAL' else st['baseSpAttack']
    s = power * (md['accuracy'] or 100) / 100 * stat / 100
    if md['type'] in info['types']:
        s *= 2.0 if ability == 'ABILITY_ADAPTABILITY' else 1.5
    if weather and WEATHER_TYPE.get(weather) == md['type']:
        s *= 1.5
    if weather == 'sun' and md['type'] == 'TYPE_WATER' or weather == 'rain' and md['type'] == 'TYPE_FIRE':
        s *= 0.5
    if md['priority'] > 0 and mc != 'MOVE_FAKE_OUT':
        s *= 1.2
    if mc == 'MOVE_FAKE_OUT':
        s = 30 if doubles else 0
    if doubles and md['target'] in ('TARGET_BOTH', 'TARGET_FOES_AND_ALLY'):
        s *= 1.25
    if kind == 'phys' and md['category'] == 'DAMAGE_CATEGORY_SPECIAL' or kind == 'spec' and md['category'] == 'DAMAGE_CATEGORY_PHYSICAL':
        s *= 0.75
    return s


def pick_moves(const, level, p, rng, boss, doubles, weather, ability):
    info = p[const]
    moves = fundata.moves()
    cands = [m for m in candidates(const, level, p, boss) if m in moves]
    if not cands:
        return []
    r, speed = role(info)
    kind = r if r in ('phys', 'spec') else speed
    cap = power_cap(level, boss)
    attacks = []
    for mc in cands:
        md = moves[mc]
        if md['category'] != 'DAMAGE_CATEGORY_STATUS' and VARIABLE.get(mc, md['power']) > cap:
            continue
        sc = attack_score(mc, md, info, kind, weather, doubles, ability)
        if sc > 0:
            attacks.append((sc, mc))
    attacks.sort(reverse=True)

    support = []
    have = set(cands)
    if r == 'wall':
        support += [m for m in RECOVERY if m in have][:1]
        support += [m for m in STATUS if m in have][:1]
    else:
        setup = SETUP_BOTH + (SETUP_PHYS if r == 'phys' else SETUP_SPEC)
        found = [m for m in setup if m in have]
        if found and (boss or rng.random() < 0.35):
            support.append(found[0])
        elif boss or rng.random() < 0.4:
            st = [m for m in STATUS if m in have]
            if st:
                support.append(st[0] if boss else rng.choice(st))
    if doubles:
        d = [m for m in DOUBLES if m in have and m not in support]
        if 'MOVE_PROTECT' in have and boss:
            support.append('MOVE_PROTECT')
        elif d:
            support.append(d[0])
    if boss and r != 'wall' and len(support) < 1:
        rec = [m for m in RECOVERY if m in have]
        if rec and info['stats']['baseHP'] + info['stats']['baseDefense'] >= 160:
            support.append(rec[0])
    support = support[:2]

    chosen = []
    types = set()
    slots = 4 - len(support)
    for sc, mc in attacks:
        if len(chosen) >= slots:
            break
        t = moves[mc]['type']
        if t in types and len(attacks) > slots:
            continue
        chosen.append(mc)
        types.add(t)
    for sc, mc in attacks:  # fill from duplicates if coverage ran out
        if len(chosen) >= slots:
            break
        if mc not in chosen:
            chosen.append(mc)
    out = chosen + support
    if len(out) < 4:
        rest = [m for m in fundata.level_up_moves(const, level, p) if m not in out and m not in NEVER]
        out += rest[::-1][:4 - len(out)]
    return out[:4]


def pick_item(info, level, moves, used, boss, rng, weather_setter):
    p_moves = fundata.moves()
    r, speed = role(info)
    has_setup = any(m in SETUP_PHYS + SETUP_SPEC + SETUP_BOTH for m in moves)
    has_status = any(p_moves.get(m, {}).get('category') == 'DAMAGE_CATEGORY_STATUS' for m in moves)
    st = info['stats']
    bulky = st['baseHP'] + st['baseDefense'] + st['baseSpDefense'] >= 240
    options = []
    if weather_setter:
        options.append(WEATHER_ROCK[weather_setter])
    if not info['finalStage'] and level >= 20:
        options.append('ITEM_EVIOLITE')
    if level < 20:
        options += ['ITEM_ORAN_BERRY', 'ITEM_SITRUS_BERRY']
    if 'MOVE_SHELL_SMASH' in moves:
        options.append('ITEM_WHITE_HERB')
    if has_setup:
        options += ['ITEM_LIFE_ORB', 'ITEM_LUM_BERRY'] if not bulky else ['ITEM_WEAKNESS_POLICY', 'ITEM_LEFTOVERS']
    if r == 'wall' or (bulky and has_status):
        options.append('ITEM_BLACK_SLUDGE' if 'TYPE_POISON' in info['types'] else 'ITEM_LEFTOVERS')
        options += ['ITEM_ROCKY_HELMET', 'ITEM_SITRUS_BERRY']
    if not has_status and level >= 30:
        if speed == 'fast' and not bulky:
            options += ['ITEM_CHOICE_SCARF', 'ITEM_CHOICE_BAND' if r == 'phys' else 'ITEM_CHOICE_SPECS', 'ITEM_FOCUS_SASH']
        elif bulky:
            options.append('ITEM_ASSAULT_VEST')
    if level >= 25:
        options += ['ITEM_LIFE_ORB', 'ITEM_EXPERT_BELT']
    stab = [p_moves[m]['type'] for m in moves if m in p_moves and p_moves[m]['type'] in info['types']]
    if stab:
        options.append(TYPE_ITEM.get(stab[0], 'ITEM_SITRUS_BERRY'))
    options += ['ITEM_SITRUS_BERRY', 'ITEM_LUM_BERRY', 'ITEM_SHELL_BELL', 'ITEM_KINGS_ROCK', 'ITEM_SCOPE_LENS']
    for o in options:
        if o not in used:
            return o
    return options[0]


def evs_for(info):
    r, speed = role(info)
    if r == 'wall':
        return '252 HP / 252 %s / 4 %s' % ('Def' if speed == 'phys' else 'SpD', 'SpD' if speed == 'phys' else 'Def')
    atk = 'Atk' if r == 'phys' else 'SpA'
    if speed == 'fast':
        return '4 HP / 252 %s / 252 Spe' % atk
    return '252 HP / 252 %s / 4 Def' % atk


def nature_for(info):
    return NATURES[role(info)]


def build_team(party, p, rng, boss=False, doubles=False, items=True, fill_only=False):
    weather = team_weather(party, p)
    used_items = {('ITEM_' + m['item'].upper().replace(' ', '_').replace("'", '')) for m in party if m.get('item')}
    from common import species_const
    for m in party:
        const = species_const(m.get('species', ''))
        info = p.get(const)
        if not info:
            continue
        level = int(m.get('Level') or 5) if str(m.get('Level', '')).isdigit() else 5
        if not (fill_only and m.get('Ability')):
            ab = best_ability(info, weather)
            if ab:
                m['Ability'] = ability_name(ab)
                if not weather and ab in WEATHER_ABILITIES:
                    weather = WEATHER_ABILITIES[ab]
        ability = 'ABILITY_' + m.get('Ability', '').upper().replace(' ', '_') if m.get('Ability') else ''
        if not (fill_only and m.get('moves')):
            m['moves'] = [move_name(mv) for mv in pick_moves(const, level, p, rng, boss, doubles, weather, ability)]
        mv_consts = ['MOVE_' + x.upper().replace(' ', '_').replace('-', '_').replace("'", '') for x in m['moves']]
        if items and not m.get('item') and (boss or rng.random() < 0.5):
            setter = WEATHER_ABILITIES.get(ability) if ability in WEATHER_ABILITIES else None
            it = pick_item(info, level, mv_consts, used_items, boss, rng, setter)
            used_items.add(it)
            m['item'] = item_name(it)
        if boss:
            m.setdefault('IVs', '31 HP / 31 Atk / 31 Def / 31 SpA / 31 SpD / 31 Spe')
            if not fill_only or 'IVs' not in m:
                m['IVs'] = '31 HP / 31 Atk / 31 Def / 31 SpA / 31 SpD / 31 Spe'
            if not (fill_only and m.get('EVs')):
                m['EVs'] = evs_for(info) if level >= 20 else '%d HP / %d Atk / %d Def / %d SpA / %d SpD / %d Spe' % ((level * 2,) * 6)
            if not (fill_only and m.get('Nature')):
                m['Nature'] = nature_for(info)
        else:
            iv = min(31, 6 + level // 2)
            m['IVs'] = '%d HP / %d Atk / %d Def / %d SpA / %d SpD / %d Spe' % ((iv,) * 6)
            if level >= 30 and not m.get('Nature'):
                m['Nature'] = nature_for(info)
    return party
