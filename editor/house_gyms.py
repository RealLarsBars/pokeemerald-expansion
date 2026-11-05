"""Game of Thrones: every Gym becomes a noble house with its own wild idea and Pokémon to match.

Levels and team sizes stay as they are (or as Hard mode made them); only the species
change. With Hard mode on, the new Pokémon get fresh movesets, abilities and items.
"""

# Per Gym: the house, a pool for its trainers, and the leader's team (ace last).
# Each house is its own wild idea, not the Gym's old type. Early Gyms use unevolved
# Pokémon so the levels still make sense. 'boss' replaces the leader's battle lines and
# 'text' replaces whole texts (the Gym Guide's advice names the new weaknesses).
HOUSES = [
    {'house': 'House Rustboro', 'words': 'We Did The Reading', 'key': 'ROXANNE',
     'idea': 'the haunted library: ghosts of students who died during finals, led by a ghost dog',
     'trainers': ['TRAINER_JOSH', 'TRAINER_TOMMY', 'TRAINER_MARC'],
     'leader': 'TRAINER_ROXANNE_',
     'pool': ['GASTLY', 'DUSKULL', 'SHUPPET', 'SINISTEA', 'PHANTUMP', 'LITWICK', 'DRIFLOON', 'SANDYGAST'],
     'team': ['SINISTEA', 'SHUPPET', 'LITWICK', 'GREAVARD'],
     'hard': ['SINISTEA', 'DRIFLOON', 'DUSKULL', 'LITWICK', 'SHUPPET', 'GREAVARD'],
     'boss': ("I am Roxanne of House Rustboro. Our library is haunted by everyone who failed my class. Our words: We Did The Reading.",
              "You beat me. The ghosts are applauding. It sounds like wind. It's mostly wind."),
     'text': {
        'RustboroCity_Gym_Text_GymGuideAdvice':
            "Ho there, how goes it?\n\nListen, friend! Would you like to sit on the Poké Ball Throne someday? It's very uncomfortable! Everybody wants it anyway!\n\n"
            "I'm no knight myself, but I give the best counsel in the realm. I counseled six kings! Four of them are still alive!\n\n"
            "That's settled, then! We march on the Throne together!\n\nA TRAINER must collect the GYM BADGES of every noble house, am I right?\n\n"
            "But this one is different. Lady ROXANNE's library is haunted. By students. Who died during finals.\n\n"
            "Her POKéMON are GHOSTS. NORMAL and FIGHTING moves go right through them. Like my advice through kings.\n\n"
            "Hit them with GHOST-type and DARK-type moves. Or a really mean book review.\n\n"
            "Come see me after, if you defeat the lady. I'll be out here. I don't go in there. Not since the whispering.",
        'RustboroCity_Gym_Text_JoshPostBattle':
            "You haven't seen the true terror of this library yet! The ghost dog fetches your soul! Then it wants you to throw it again!",
        'RustboroCity_Gym_Text_MarcIntro':
            "We may be in the middle of a city, but so what?\n\nThe dead don't care about zoning laws! Shhh! You're in a library! Fight quietly!",
        'RustboroCity_Gym_Text_MarcPostBattle':
            "I have to hand it to our lady.\n\nShe turned a library into a haunted house, so young? That's how you build a dynasty. Ghosts never leave. They also never return books.",
        'RustboroCity_Text_GymLeaderIsntEasyWithFire':
            "I challenged Lady ROXANNE, but…\n\nMy NORMAL-type POKéMON punched a ghost. Its fist went right through. Then it got very sad about death.\n\n"
            "NORMAL-type moves can't touch GHOST-type POKéMON at all…",
     }},
    {'house': 'House Dewford', 'words': 'Dinner Is Served. So Are You.', 'key': 'BRAWLY',
     'idea': 'the cave buffet: bread dogs, angry peppers, cotton candy, and a sushi dragon for dessert',
     'trainers': ['TRAINER_BRENDEN', 'TRAINER_CRISTIAN', 'TRAINER_JOCELYN', 'TRAINER_LAURA', 'TRAINER_LILITH',
                  'TRAINER_TAKAO'],
     'leader': 'TRAINER_BRAWLY_',
     'pool': ['FIDOUGH', 'CAPSAKID', 'SWIRLIX', 'MILCERY', 'SMOLIV', 'LECHONK', 'CHERUBI', 'BOUNSWEET', 'SHUCKLE'],
     'team': ['FIDOUGH', 'CAPSAKID', 'SWIRLIX', 'TATSUGIRI'],
     'hard': ['DOLLIV', 'DACHSBUN', 'SCOVILLAIN', 'SLURPUFF', 'APPLIN', 'TATSUGIRI'],
     'boss': ("I'm Brawly of House Dewford! Welcome to my cave buffet! Our words: Dinner Is Served. So Are You.",
              "You ate my whole menu! The Buffet pledges its leftovers to you! There's so much soup!"),
     'text': {
        'DewfordTown_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nBRAWLY of House Dewford doesn't fight with fists. He runs a buffet. In a cave. In the dark.\n\n"
            "His POKéMON are FOOD. Bread with legs. Angry peppers. Cotton candy that bites.\n\n"
            "POISON and STEEL moves spoil the desserts. FIRE and BUG moves ruin the salad.\n\n"
            "And the chef's special at the end is sushi. A DRAGON sushi. Bring DRAGON-type or FAIRY-type moves.\n\n"
            "Don't eat anything in there. I mean it. Okay, go for it!",
     }},
    {'house': 'House Wattson', 'words': "What's Yours Is Ours", 'key': 'WATTSON',
     'idea': "the Thieves' Guild of Mauville: pickpocket cats, a fox who steals berries, crows, and a trash heap boss",
     'trainers': ['TRAINER_ANGELO', 'TRAINER_BEN', 'TRAINER_KIRK', 'TRAINER_SHAWN', 'TRAINER_VIVIAN'],
     'leader': 'TRAINER_WATTSON_',
     'pool': ['PURRLOIN', 'NICKIT', 'MURKROW', 'TRUBBISH', 'GRIMER', 'KOFFING', 'IMPIDIMP', 'SHROODLE'],
     'team': ['NICKIT', 'PURRLOIN', 'MURKROW', 'GARBODOR'],
     'hard': ['LIEPARD', 'THIEVUL', 'GRAFAIAI', 'MURKROW', 'WEEZING', 'GARBODOR'],
     'boss': ("Wahahaha! Welcome to the Thieves' Guild of Mauville! Our words: What's Yours Is Ours! Empty your pockets!",
              "Wahahaha! You robbed the robbers! The Guild yields! Give me back my wallet, though. That's my wallet."),
     'text': {
        'MauvilleCity_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nWATTSON isn't a power man anymore. He runs the Thieves' Guild. He stole the GYM. From himself.\n\n"
            "His POKéMON are pickpockets and garbage. Literal garbage. It smells.\n\n"
            "The thieves are DARK-type. Hit them with BUG, FIGHTING, or FAIRY moves.\n\n"
            "The trash is POISON-type. GROUND and PSYCHIC moves take out the trash.\n\n"
            "Hold on to your wallet in there. I've lost four. Okay, go for it!",
     }},
    {'house': 'House Lavaridge', 'words': 'The Long Nap Is Coming', 'key': 'FLANNERY',
     'idea': 'the hot spring nap club: sleepy Pokémon, dream eaters, and Grandpa (a Snorlax) as the ace',
     'trainers': ['TRAINER_AXLE', 'TRAINER_COLE', 'TRAINER_DANIELLE', 'TRAINER_ELI', 'TRAINER_GERALD',
                  'TRAINER_JACE', 'TRAINER_JEFF', 'TRAINER_KEEGAN'],
     'leader': 'TRAINER_FLANNERY_',
     'pool': ['DROWZEE', 'SLOWPOKE', 'MUNCHLAX', 'JIGGLYPUFF', 'KOMALA', 'SPOINK', 'HOOTHOOT', 'CHINGLING'],
     'team': ['DROWZEE', 'JIGGLYPUFF', 'KOMALA', 'SNORLAX'],
     'hard': ['HYPNO', 'SLOWBRO', 'WIGGLYTUFF', 'GRUMPIG', 'KOMALA', 'SNORLAX'],
     'boss': ("I'm Flannery of House Lavaridge! Our words: The Long Nap Is Coming! Shh! Grandpa is sleeping! He's my ace!",
              "You won… and Grandpa slept through the whole thing. That's the most supportive he's ever been."),
     'text': {
        'LavaridgeTown_Gym_1F_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nFLANNERY of House Lavaridge has turned the hot springs into a nap club. Everyone in there is asleep. Even the trainers. Even the walls.\n\n"
            "Her POKéMON are sleepy NORMAL-types and PSYCHIC dream eaters.\n\n"
            "FIGHTING moves wake the NORMAL ones up. BUG, DARK and GHOST moves give the PSYCHIC ones nightmares.\n\n"
            "Bring AWAKENINGS. They love YAWN. Her grandpa is the ace. He's a SNORLAX. He's been asleep since the last king.\n\n"
            "Okay, go for it! Quietly!",
     }},
    {'house': 'House Petalburg', 'words': 'A Dad Has No Name', 'key': 'NORMAN',
     'idea': 'the Faceless Dads: shapeshifters, mimes, a costume ghost, and an illusion fox, so nothing is what it looks like',
     'trainers': ['TRAINER_ALEXIA', 'TRAINER_BERKE', 'TRAINER_GEORGE', 'TRAINER_JODY', 'TRAINER_MARY',
                  'TRAINER_PARKER', 'TRAINER_RANDALL'],
     'leader': 'TRAINER_NORMAN_',
     'pool': ['DITTO', 'KECLEON', 'ZORUA', 'MIME_JR', 'SMEARGLE', 'SPINDA', 'MIMIKYU'],
     'team': ['KECLEON', 'MR_MIME', 'MIMIKYU', 'ZOROARK'],
     'hard': ['DITTO', 'SMEARGLE', 'KECLEON', 'MR_MIME', 'MIMIKYU', 'ZOROARK'],
     'boss': ("You've come for the seat of House Petalburg, my child? Or am I your father at all? A Dad Has No Name.",
              "...Fine. You win. I am still your father. Probably. Take off the mask and do the dishes."),
     'text': {
        'PetalburgCity_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nYour father NORMAN joined the Faceless Dads. A Dad Has No Name. He still has a lawn, though.\n\n"
            "Nothing in there is what it looks like. Shapeshifters. Mimes. A ghost in a costume. A fox pretending to be your mom.\n\n"
            "STEEL and POISON moves crack the mimes and the costume. FIGHTING, BUG and FAIRY moves beat the fox.\n\n"
            "If a POKéMON looks like yours, it isn't. Okay, go for it!",
     }},
    {'house': 'House Fortree', 'words': 'Fire And Blood And Paperwork', 'key': 'WINONA',
     'idea': 'the Mother of Dragons: every bird is a dragon now, and the ace is a Salamence',
     'trainers': ['TRAINER_ASHLEY', 'TRAINER_DARIUS', 'TRAINER_EDWARDO', 'TRAINER_FLINT', 'TRAINER_HUMBERTO',
                  'TRAINER_JARED'],
     'leader': 'TRAINER_WINONA_',
     'pool': ['BAGON', 'GIBLE', 'AXEW', 'DEINO', 'DRATINI', 'NOIBAT', 'JANGMO_O', 'SWABLU', 'TRAPINCH'],
     'team': ['NOIVERN', 'FLYGON', 'DRAGONAIR', 'ALTARIA', 'SALAMENCE'],
     'hard': ['NOIVERN', 'FLYGON', 'DRAGONITE', 'GARCHOMP', 'HYDREIGON', 'SALAMENCE'],
     'boss': ("I am Winona, Mother of Dragons, Breaker of Branches, Lady of the Treehouses. Our words: Fire And Blood And Paperwork.",
              "My dragons bow to you. They've never bowed before. They're very confused. Pat them."),
     'text': {
        'FortreeCity_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nWINONA used to raise birds. Then she found some eggs in a fire. Now she's the Mother of Dragons.\n\n"
            "Every POKéMON in there is a DRAGON. They're up in the trees. They're very heavy. The trees are not happy.\n\n"
            "ICE-type moves. Bring ICE-type moves. Bring so many ICE-type moves. DRAGON and FAIRY work too.\n\n"
            "Most of her dragons fly, so GROUND moves won't hit. Okay, go for it! Wear something fireproof!",
     }},
    {'house': 'House Mossdeep', 'words': 'Sit At Your Own Risk', 'key': 'TATE',
     'idea': 'the Iron Throne: twins on a chair made of swords, with sword Pokémon and a haunted shield-sword ace',
     'trainers': ['TRAINER_BLAKE', 'TRAINER_CLIFFORD', 'TRAINER_HANNAH', 'TRAINER_KATHLEEN', 'TRAINER_MACEY',
                  'TRAINER_MAURA', 'TRAINER_NATE', 'TRAINER_NICHOLAS', 'TRAINER_PRESTON', 'TRAINER_SAMANTHA',
                  'TRAINER_SYLVIA', 'TRAINER_VIRGIL'],
     'leader': 'TRAINER_TATE_AND_LIZA_',
     'pool': ['HONEDGE', 'PAWNIARD', 'SCYTHER', 'OSHAWOTT', 'SIRFETCHD', 'ESCAVALIER', 'GALLADE', 'KARRABLAST'],
     'team': ['SIRFETCHD', 'GALLADE', 'BISHARP', 'AEGISLASH'],
     'hard': ['ESCAVALIER', 'SIRFETCHD', 'GALLADE', 'CERULEDGE', 'KINGAMBIT', 'AEGISLASH'],
     'boss': ("We are the twins of House Mossdeep! We sit on a throne made of swords! Our words: Sit At Your Own Risk! Ow!",
              "We both lose… equally. We're getting off the throne now. Slowly. Very slowly. Ow."),
     'text': {
        'MossdeepCity_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nTATE and LIZA built a throne out of a thousand swords. They both sit on it. Nobody has told them it's a bad idea.\n\n"
            "Every POKéMON in there is a sword. Or holds a sword. Or is a sword holding a sword.\n\n"
            "Most of them are STEEL. FIRE and GROUND moves melt and bury them. FLYING, PSYCHIC and FAIRY moves beat the fighting knights.\n\n"
            "It's a double battle, so bring two. Okay, go for it! Don't sit on anything!",
     }},
    {'house': 'House Sootopolis', 'words': 'Winter Came. It Stayed.', 'key': 'JUAN',
     'idea': 'the Night King froze the crater: ice ghosts, ice weasels, a mammoth, and an ice dragon',
     'trainers': ['TRAINER_ANDREA', 'TRAINER_ANNIKA', 'TRAINER_BETHANY', 'TRAINER_BRIANNA', 'TRAINER_BRIDGET',
                  'TRAINER_CONNIE', 'TRAINER_CRISSY', 'TRAINER_DAPHNE', 'TRAINER_OLIVIA', 'TRAINER_TIFFANY'],
     'leader': 'TRAINER_JUAN_',
     'pool': ['SNEASEL', 'SNORUNT', 'SWINUB', 'BERGMITE', 'CRYOGONAL', 'SPHEAL', 'FRIGIBAX', 'CUBCHOO', 'SNOM'],
     'team': ['FROSLASS', 'CRYOGONAL', 'WEAVILE', 'MAMOSWINE', 'BAXCALIBUR'],
     'hard': ['FROSLASS', 'WEAVILE', 'MAMOSWINE', 'AVALUGG', 'CETITAN', 'BAXCALIBUR'],
     'boss': ("I am Juan, the Night King of Sootopolis. I froze the whole crater. It took one afternoon. Our words: Winter Came. It Stayed.",
              "You have melted my winter and won all eight banners. Ever Grande awaits. Bring a coat. Bring two."),
     'text': {
        'SootopolisCity_Gym_1F_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nJUAN is the Night King now. He froze the whole GYM. The floor was already ice. Now the ice is also ice.\n\n"
            "Every POKéMON in there is ICE-type. Ice ghosts. Ice weasels. A mammoth. An ice dragon at the end.\n\n"
            "FIRE, FIGHTING, STEEL and ROCK moves shatter them. WATER and ICE moves do nothing.\n\n"
            "Okay, go for it! Winter is here and it's weak to fire!",
     }},
]


def text_overrides():
    """Whole texts that House Gyms replaces, by label."""
    out = {}
    for h in HOUSES:
        out.update(h.get('text', {}))
    return out


def boss_lines():
    """The leaders' house lines, by the key comedy uses (ROXANNE, TATE...)."""
    return {h['key']: h['boss'] for h in HOUSES}


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
