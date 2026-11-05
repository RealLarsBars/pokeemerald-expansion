"""Game of Thrones: every Gym's trainers and leader use Pokémon that fit their noble house.

Levels and team sizes stay as they are (or as Hard mode made them); only the species
change. With Hard mode on, the new Pokémon get fresh movesets, abilities and items.
"""

# Per Gym: the house, a pool for its trainers, and the leader's team (ace last).
# Early Gyms use unevolved Pokémon so the levels still make sense.
HOUSES = [
    {'house': 'House Rustboro', 'words': 'We Did The Reading',
     'idea': 'scholars of the ancient world: an army of fossils, led by the Helix',
     'trainers': ['TRAINER_JOSH', 'TRAINER_TOMMY', 'TRAINER_MARC'],
     'leader': 'TRAINER_ROXANNE_',
     'pool': ['KABUTO', 'ANORITH', 'LILEEP', 'CRANIDOS', 'SHIELDON', 'ARCHEN', 'TIRTOUGA', 'TYRUNT', 'AMAURA'],
     'team': ['KABUTO', 'LILEEP', 'NOSEPASS', 'OMANYTE'],
     'hard': ['KABUTO', 'LILEEP', 'ANORITH', 'SHIELDON', 'NOSEPASS', 'OMANYTE']},
    {'house': 'the Dewford Tide', 'words': 'Hit First, Ask Never',
     'idea': 'brawlers of the surf: angry fighters, a punching octopus',
     'trainers': ['TRAINER_BRENDEN', 'TRAINER_CRISTIAN', 'TRAINER_JOCELYN', 'TRAINER_LAURA', 'TRAINER_LILITH',
                  'TRAINER_TAKAO'],
     'leader': 'TRAINER_BRAWLY_',
     'pool': ['MANKEY', 'TYROGUE', 'TIMBURR', 'MIENFOO', 'CROAGUNK', 'CLOBBOPUS', 'MEDITITE', 'MACHOP', 'RIOLU'],
     'team': ['MANKEY', 'CLOBBOPUS', 'CROAGUNK', 'MAKUHITA'],
     'hard': ['RIOLU', 'MIENFOO', 'TIMBURR', 'CROAGUNK', 'CLOBBOPUS', 'HARIYAMA']},
    {'house': 'House Wattson', 'words': 'The Bills Are Paid',
     'idea': 'the power company: appliances, coin-counters, and a Voltorb that looks like a Poké Ball',
     'trainers': ['TRAINER_ANGELO', 'TRAINER_BEN', 'TRAINER_KIRK', 'TRAINER_SHAWN', 'TRAINER_VIVIAN'],
     'leader': 'TRAINER_WATTSON_',
     'pool': ['VOLTORB', 'MAGNEMITE', 'PACHIRISU', 'EMOLGA', 'DEDENNE', 'PAWMI', 'MEOWTH', 'TOGEDEMARU'],
     'team': ['MEOWTH', 'ROTOM', 'MAGNETON', 'MANECTRIC'],
     'hard': ['MEOWTH', 'PAWMO', 'EMOLGA', 'ROTOM', 'MAGNETON', 'MANECTRIC']},
    {'house': 'House Lavaridge', 'words': 'The Floor Is Lava',
     'idea': 'hot springs and fire, with Grandpa (a Torkoal) as the ace',
     'trainers': ['TRAINER_AXLE', 'TRAINER_COLE', 'TRAINER_DANIELLE', 'TRAINER_ELI', 'TRAINER_GERALD',
                  'TRAINER_JACE', 'TRAINER_JEFF', 'TRAINER_KEEGAN'],
     'leader': 'TRAINER_FLANNERY_',
     'pool': ['NUMEL', 'SLUGMA', 'HOUNDOUR', 'LITWICK', 'SALANDIT', 'SIZZLIPEDE', 'CARKOL', 'CHARCADET'],
     'team': ['SALANDIT', 'SLUGMA', 'CAMERUPT', 'TORKOAL'],
     'hard': ['SALAZZLE', 'MAGCARGO', 'HOUNDOOM', 'LAMPENT', 'CAMERUPT', 'TORKOAL']},
    {'house': 'House Petalburg', 'words': 'Family Is Complicated',
     'idea': 'families: a whole mouse family, a parent with a baby in the pouch, and the Vigoroth movers',
     'trainers': ['TRAINER_ALEXIA', 'TRAINER_BERKE', 'TRAINER_GEORGE', 'TRAINER_JODY', 'TRAINER_MARY',
                  'TRAINER_PARKER', 'TRAINER_RANDALL'],
     'leader': 'TRAINER_NORMAN_',
     'pool': ['TANDEMAUS', 'LECHONK', 'SKWOVET', 'BIDOOF', 'TEDDIURSA', 'AIPOM', 'SMEARGLE', 'SPINDA'],
     'team': ['MAUSHOLD', 'KANGASKHAN', 'VIGOROTH', 'SLAKING'],
     'hard': ['MAUSHOLD', 'OINKOLOGNE', 'URSARING', 'KANGASKHAN', 'VIGOROTH', 'SLAKING']},
    {'house': 'the High Skies', 'words': 'Our Wings Are Higher',
     'idea': 'birds that drop things on you from above',
     'trainers': ['TRAINER_ASHLEY', 'TRAINER_DARIUS', 'TRAINER_EDWARDO', 'TRAINER_FLINT', 'TRAINER_HUMBERTO',
                  'TRAINER_JARED'],
     'leader': 'TRAINER_WINONA_',
     'pool': ['SWABLU', 'WINGULL', 'TRANQUILL', 'CORVISQUIRE', 'FLAMIGO', 'SQUAWKABILLY', 'CRAMORANT', 'NOCTOWL'],
     'team': ['SQUAWKABILLY', 'CRAMORANT', 'BOMBIRDIER', 'SKARMORY', 'ALTARIA'],
     'hard': ['SQUAWKABILLY', 'CRAMORANT', 'BOMBIRDIER', 'CORVIKNIGHT', 'SKARMORY', 'ALTARIA']},
    {'house': 'the Twin House of Mossdeep', 'words': 'Two Heirs, No Answers',
     'idea': 'pairs and twins: two-headed, two-of-a-kind, and things that merged',
     'trainers': ['TRAINER_BLAKE', 'TRAINER_CLIFFORD', 'TRAINER_HANNAH', 'TRAINER_KATHLEEN', 'TRAINER_MACEY',
                  'TRAINER_MAURA', 'TRAINER_NATE', 'TRAINER_NICHOLAS', 'TRAINER_PRESTON', 'TRAINER_SAMANTHA',
                  'TRAINER_SYLVIA', 'TRAINER_VIRGIL'],
     'leader': 'TRAINER_TATE_AND_LIZA_',
     'pool': ['DUOSION', 'GIRAFARIG', 'PLUSLE', 'MINUN', 'DOUBLADE', 'GOTHORITA', 'MEOWSTIC', 'INDEEDEE'],
     'team': ['FARIGIRAF', 'REUNICLUS', 'LUNATONE', 'SOLROCK'],
     'hard': ['MEOWSTIC', 'GOTHITELLE', 'FARIGIRAF', 'REUNICLUS', 'LUNATONE', 'SOLROCK']},
    {'house': 'House Sootopolis', 'words': 'Beauty Is A Weapon',
     'idea': 'the most beautiful water Pokémon in the realm, and one Feebas who is trying its best',
     'trainers': ['TRAINER_ANDREA', 'TRAINER_ANNIKA', 'TRAINER_BETHANY', 'TRAINER_BRIANNA', 'TRAINER_BRIDGET',
                  'TRAINER_CONNIE', 'TRAINER_CRISSY', 'TRAINER_DAPHNE', 'TRAINER_OLIVIA', 'TRAINER_TIFFANY'],
     'leader': 'TRAINER_JUAN_',
     'pool': ['LUVDISC', 'FEEBAS', 'LUMINEON', 'GOREBYSS', 'CORSOLA', 'ALOMOMOLA', 'SPHEAL', 'FINIZEN'],
     'team': ['LUVDISC', 'LUMINEON', 'GOREBYSS', 'MILOTIC', 'KINGDRA'],
     'hard': ['LUMINEON', 'GOREBYSS', 'VAPOREON', 'PRIMARINA', 'MILOTIC', 'KINGDRA']},
]


def grown(c, level, p):
    """The evolution a trainer's Pokémon would have reached by this level."""
    import fundata
    line = fundata.evolution_line(c, p)
    if c not in line:
        return c
    stage = 2 if level >= 36 else 1 if level >= 22 else 0
    return line[min(stage, len(line) - 1)] if line.index(c) <= stage else c


def apply(ov, rng):
    """Returns report lines."""
    import fundata
    import funmodes
    import sets
    import trainers as T
    p = fundata.pool()
    party = funmodes.Party(ov.read(funmodes.PARTY))
    lines, missing = [], set()

    def const(name):
        c = 'SPECIES_' + name
        if c not in p:
            missing.add(name)
            return None
        return c

    for h in HOUSES:
        changed = 0
        pool = [c for c in (const(n) for n in h['pool']) if c]
        team = [c for c in (const(n) for n in h['team']) if c]
        hard_team = [c for c in (const(n) for n in h.get('hard', [])) if c]
        for tid, t in party.items():
            if not t['party']:
                continue
            is_leader = tid.startswith(h['leader'])
            if not is_leader and tid not in h['trainers']:
                continue
            hard = any(m.get('Ability') for m in t['party'])  # Hard mode built this team
            if is_leader:
                # Hard mode leaders get a full six, evolved for their higher levels. The ace stays
                # last; smaller teams drop the first members of the list.
                lst = hard_team if hard and hard_team else team
                picks = lst[-len(t['party']):] if len(t['party']) <= len(lst) else \
                    [rng.choice(pool) for _ in range(len(t['party']) - len(lst))] + lst
            else:
                picks = rng.sample(pool, min(len(pool), len(t['party'])))
                while len(picks) < len(t['party']):
                    picks.append(rng.choice(pool))
                # Trainers' Pokémon evolve when their level is high enough.
                picks = [grown(c, int(m.get('Level') or 5) if str(m.get('Level', '')).isdigit() else 5, p)
                         for c, m in zip(picks, t['party'])]
            for m, c in zip(t['party'], picks):
                funmodes.set_species(m, c, p)
                m['item'] = '' if not hard else m.get('item', '')
            if hard:
                # Hard mode already built this team: give the new Pokémon proper sets too.
                for m in t['party']:
                    if not m['moves']:
                        m.pop('Ability', None)
                        m['item'] = ''
                sets.build_team(t['party'], p, rng, boss=is_leader,
                                doubles=T.field(t, 'Double Battle') == 'Yes', items=True, fill_only=True)
            party.put(tid, t)
            changed += 1
        if changed:
            lines.append('%s (“%s”): %s' % (h['house'], h['words'], h['idea']))
    ov.write(funmodes.PARTY, party.text())
    if missing:
        lines.append('Not in this game, skipped: ' + ', '.join(sorted(missing)))
    return lines
