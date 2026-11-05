"""Game of Thrones: every Gym becomes a noble house with its own story and Pokémon to match.

Levels and team sizes stay as they are (or as Hard mode made them); only the species
change. With Hard mode on, the new Pokémon get fresh movesets, abilities and items.
"""

# Per Gym: the house, a pool for its trainers, and the leader's team (ace last).
# Each house is its own idea, not the Gym's old type, told straight in the voice of the
# books. Early Gyms use unevolved Pokémon so the levels still make sense. 'boss' replaces
# the leader's battle lines and 'text' replaces whole texts (the Gym Guide's advice names
# the new weaknesses).
HOUSES = [
    {'house': 'House Rustboro', 'words': 'We Remember', 'key': 'ROXANNE',
     'idea': 'Keepers of the Crypts: Lady Roxanne tends the dead beneath the school, and they fight for her',
     'trainers': ['TRAINER_JOSH', 'TRAINER_TOMMY', 'TRAINER_MARC'],
     'leader': 'TRAINER_ROXANNE_',
     'pool': ['GASTLY', 'DUSKULL', 'SHUPPET', 'SINISTEA', 'PHANTUMP', 'LITWICK', 'DRIFLOON', 'SANDYGAST'],
     'team': ['SINISTEA', 'SHUPPET', 'LITWICK', 'GREAVARD'],
     'hard': ['SINISTEA', 'DRIFLOON', 'DUSKULL', 'LITWICK', 'SHUPPET', 'GREAVARD'],
     'boss': ("I am ROXANNE of House Rustboro, Keeper of the Crypts. Every scholar who ever taught here lies below "
              "this floor, and every one of them is watching. Our words are: We Remember.",
              "The dead have seen enough. House Rustboro will remember this day. Take the badge, and do not make us "
              "remember you badly."),
     'text': {
        'RustboroCity_Gym_Text_GymGuideAdvice':
            "Yo, how's it going?\n\nListen, my friend! Would you like to sit the THRONE someday?\n\n"
            "I'm no lord, but I've given counsel in every GYM in HOENN. I know what each house hides.\n\n"
            "Then we're agreed. Every house must bend the knee, one GYM at a time.\n\n"
            "Lady ROXANNE keeps the crypts beneath the school. Her POKéMON are the restless dead.\n\n"
            "GHOST-type POKéMON. NORMAL and FIGHTING moves pass right through them.\n\n"
            "GHOST-type and DARK-type moves will put them back in the ground.\n\n"
            "Come see me after, if you beat the lady. I'll wait out here. I don't go below.",
        'RustboroCity_Gym_Text_JoshPostBattle':
            "You haven't seen the crypts yet. Down there, the candles light themselves.",
        'RustboroCity_Gym_Text_MarcIntro':
            "We might be in the middle of town, but so what?\n\nThe dead were here before the town. They'll be here after.",
        'RustboroCity_Gym_Text_MarcPostBattle':
            "I have to hand it to our lady.\n\nShe went down into the crypts at twelve and came back up their keeper. "
            "No one else has ever come back up.",
        'RustboroCity_Text_GymLeaderIsntEasyWithFire':
            "I challenged Lady ROXANNE, but…\n\nMy NORMAL-type POKéMON struck at her ghosts, and struck nothing.\n\n"
            "NORMAL-type moves can't touch GHOST-type POKéMON at all…",
     }},
    {'house': 'House Dewford', 'words': 'The Sea Takes Its Due', 'key': 'BRAWLY',
     'idea': 'the reavers of Dewford, sworn to Lord Archie: sea raiders, with a ghost anchor as the ace',
     'trainers': ['TRAINER_BRENDEN', 'TRAINER_CRISTIAN', 'TRAINER_JOCELYN', 'TRAINER_LAURA', 'TRAINER_LILITH',
                  'TRAINER_TAKAO'],
     'leader': 'TRAINER_BRAWLY_',
     'pool': ['CARVANHA', 'CORPHISH', 'KRABBY', 'WINGULL', 'CLAUNCHER', 'TENTACOOL', 'BINACLE', 'SKRELP'],
     'team': ['WINGULL', 'CORPHISH', 'CARVANHA', 'DHELMISE'],
     'hard': ['PELIPPER', 'CRAWDAUNT', 'BARBARACLE', 'CLAWITZER', 'SHARPEDO', 'DHELMISE'],
     'boss': ("I'm BRAWLY of House Dewford, captain of the reavers, sworn to Lord ARCHIE. "
              "We pay no iron price for what we take. Our words are: The Sea Takes Its Due.",
              "The sea took nothing from you today. That has not happened in a long time. "
              "House Dewford bends the knee, for now."),
     'text': {
        'DewfordTown_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nBRAWLY of House Dewford is a reaver captain, "
            "sworn to Lord ARCHIE. His crews raid the coast from this cave.\n\n"
            "His POKéMON came out of the sea with him. Most are WATER-type.\n\n"
            "GRASS and ELECTRIC moves cut them down. His ace is an anchor that a ghost took for its body. "
            "GHOST and DARK moves sink it.\n\n"
            "What's worse, the cave is as dark as the ocean floor.\n\n"
            "It gets brighter as his crew falls. Hey, okay, go for it!",
     }},
    {'house': 'House Wattson', 'words': 'Every Wall Has Ears', 'key': 'WATTSON',
     'idea': "the Master of Whispers of Mauville: thieves, informers, and ravens",
     'trainers': ['TRAINER_ANGELO', 'TRAINER_BEN', 'TRAINER_KIRK', 'TRAINER_SHAWN', 'TRAINER_VIVIAN'],
     'leader': 'TRAINER_WATTSON_',
     'pool': ['PURRLOIN', 'NICKIT', 'MURKROW', 'SABLEYE', 'POOCHYENA', 'IMPIDIMP', 'SHROODLE', 'SNEASEL'],
     'team': ['NICKIT', 'PURRLOIN', 'SABLEYE', 'MURKROW'],
     'hard': ['LIEPARD', 'THIEVUL', 'SABLEYE', 'GRAFAIAI', 'MIGHTYENA', 'HONCHKROW'],
     'boss': ("Wahahaha! I'm WATTSON of House Wattson, Master of Whispers. I knew you were coming before you did. "
              "Our words are: Every Wall Has Ears.",
              "Wahahaha! A whisper I didn't hear. How rare. My little birds will sing for you now. "
              "Mind what you tell them."),
     'text': {
        'MauvilleCity_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nWATTSON is the Master of Whispers. "
            "Half the secrets in HOENN pass through this GYM, and he sells the other half.\n\n"
            "His POKéMON are thieves and informers. They're DARK-type.\n\n"
            "BUG, FIGHTING and FAIRY moves will flush them out. His ace is a raven. ROCK, ICE and ELECTRIC moves "
            "bring it down.\n\n"
            "And, he's put in switch-controlled doors all over his GYM, so he always knows where you are.\n\n"
            "Hey, go for it!",
     }},
    {'house': 'House Lavaridge', 'words': 'We Dream What Comes', 'key': 'FLANNERY',
     'idea': 'the dream springs: Lady Flannery and her priestesses read the future in their sleep',
     'trainers': ['TRAINER_AXLE', 'TRAINER_COLE', 'TRAINER_DANIELLE', 'TRAINER_ELI', 'TRAINER_GERALD',
                  'TRAINER_JACE', 'TRAINER_JEFF', 'TRAINER_KEEGAN'],
     'leader': 'TRAINER_FLANNERY_',
     'pool': ['DROWZEE', 'SPOINK', 'MUNNA', 'NATU', 'CHINGLING', 'SLOWPOKE', 'HATENNA', 'ESPURR'],
     'team': ['NATU', 'SPOINK', 'MUNNA', 'HYPNO'],
     'hard': ['XATU', 'GRUMPIG', 'MUSHARNA', 'SLOWKING', 'BRONZONG', 'HYPNO'],
     'boss': ("I'm FLANNERY of House Lavaridge. I have seen this battle in the springs, three nights running. "
              "I did not see how it ended. Our words are: We Dream What Comes.",
              "So that is how it ends. I'll dream of you again tonight, I think. I hope the dream is kinder "
              "than the last one."),
     'text': {
        'LavaridgeTown_Gym_1F_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nLady FLANNERY is a priestess of the dream springs. "
            "She sleeps in the steam and wakes up knowing things she shouldn't.\n\n"
            "Her POKéMON read minds and walk in dreams. They're PSYCHIC-type.\n\n"
            "BUG, GHOST and DARK moves break their visions. Her ace eats dreams. Bring AWAKENINGS.\n\n"
            "Don't breathe the steam too deep. Go for it!",
     }},
    {'house': 'House Petalburg', 'words': 'No One Sees Us Come', 'key': 'NORMAN',
     'idea': 'the faceless: your father was trained across the sea, and nothing in his Gym is what it seems',
     'trainers': ['TRAINER_ALEXIA', 'TRAINER_BERKE', 'TRAINER_GEORGE', 'TRAINER_JODY', 'TRAINER_MARY',
                  'TRAINER_PARKER', 'TRAINER_RANDALL'],
     'leader': 'TRAINER_NORMAN_',
     'pool': ['DITTO', 'KECLEON', 'ZORUA', 'SMEARGLE', 'MIMIKYU', 'SHUPPET'],
     'team': ['KECLEON', 'DITTO', 'MIMIKYU', 'ZOROARK'],
     'hard': ['SMEARGLE', 'DITTO', 'KECLEON', 'BANETTE', 'MIMIKYU', 'ZOROARK'],
     'boss': ("So you've come for the seat of House Petalburg, my child. Look closely. Nothing in this room is what "
              "it seems, not even me. Our words are: No One Sees Us Come.",
              "...You saw through every face. I taught you that without meaning to. The seat is yours. "
              "We'll speak when the room is empty."),
     'text': {
        'PetalburgCity_Gym_Text_GymGuideAdvice':
            "Hey, how's it going, CHAMPION-bound {PLAYER}?\n\nThe doors in this GYM open when you beat the awaiting "
            "TRAINERS.\n\nWhoops! The doors in this room are already open, so don't attack me!\n\n"
            "The TRAINERS of House Petalburg wear other faces. Shapeshifters, mimics, a ghost under a cloth, "
            "a fox that looks like whatever you fear.\n\n"
            "FIGHTING, BUG and FAIRY moves see through the fox. STEEL and POISON moves tear the cloth.\n\n"
            "The door at the left leads to the SPEED ROOM.\n\nThe door at the right leads to the ACCURACY ROOM.\n\n"
            "Once you've chosen the door… Well, hey, go for it!",
     }},
    {'house': 'House Fortree', 'words': 'From The Ashes, Wings', 'key': 'WINONA',
     'idea': 'the Mother of Dragons: Lady Winona hatched her eggs in fire, and every bird in Fortree is a dragon now',
     'trainers': ['TRAINER_ASHLEY', 'TRAINER_DARIUS', 'TRAINER_EDWARDO', 'TRAINER_FLINT', 'TRAINER_HUMBERTO',
                  'TRAINER_JARED'],
     'leader': 'TRAINER_WINONA_',
     'pool': ['BAGON', 'GIBLE', 'AXEW', 'DEINO', 'DRATINI', 'NOIBAT', 'JANGMO_O', 'SWABLU', 'TRAPINCH'],
     'team': ['NOIVERN', 'FLYGON', 'DRAGONAIR', 'ALTARIA', 'SALAMENCE'],
     'hard': ['NOIVERN', 'FLYGON', 'DRAGONITE', 'GARCHOMP', 'HYDREIGON', 'SALAMENCE'],
     'boss': ("I am WINONA of House Fortree, the Unburnt, Mother of Dragons. I walked into the fire with three eggs "
              "and walked out with this. Our words are: From The Ashes, Wings.",
              "My dragons bow to you. They have never bowed to anyone but me. Do not mistake it for love."),
     'text': {
        'FortreeCity_Gym_Text_GymGuideAdvice':
            "Yo, how's it going, CHAMPION-bound {PLAYER}?\n\nLady WINONA raised birds, once. "
            "Then she walked into a fire with three eggs, and came out the Mother of Dragons.\n\n"
            "Every POKéMON in there is a DRAGON. ICE, DRAGON and FAIRY moves are your best hope.\n\n"
            "Most of them fly, so GROUND moves won't touch them.\n\n"
            "She's waiting behind the rotating doors. Okay, go for it!",
     }},
    {'house': 'House Mossdeep', 'words': 'Forged, Not Born', 'key': 'TATE',
     'idea': 'the Sword Twins: their forge made the thousand swords of the Throne, and their Pokémon are blades',
     'trainers': ['TRAINER_BLAKE', 'TRAINER_CLIFFORD', 'TRAINER_HANNAH', 'TRAINER_KATHLEEN', 'TRAINER_MACEY',
                  'TRAINER_MAURA', 'TRAINER_NATE', 'TRAINER_NICHOLAS', 'TRAINER_PRESTON', 'TRAINER_SAMANTHA',
                  'TRAINER_SYLVIA', 'TRAINER_VIRGIL'],
     'leader': 'TRAINER_TATE_AND_LIZA_',
     'pool': ['HONEDGE', 'PAWNIARD', 'SCYTHER', 'OSHAWOTT', 'SIRFETCHD', 'ESCAVALIER', 'GALLADE', 'KARRABLAST'],
     'team': ['SIRFETCHD', 'GALLADE', 'BISHARP', 'AEGISLASH'],
     'hard': ['ESCAVALIER', 'SIRFETCHD', 'GALLADE', 'CERULEDGE', 'KINGAMBIT', 'AEGISLASH'],
     'boss': ("We are TATE and LIZA of House Mossdeep. Our forge made the thousand swords of the THRONE. "
              "We will see if you are fit to sit on them. Our words are: Forged, Not Born.",
              "Tempered, then. Not broken. House Mossdeep bends the knee. The swords will remember your weight."),
     'text': {
        'MossdeepCity_Gym_Text_GymGuideAdvice':
            "Yo, how's it going, CHAMPION-bound {PLAYER}?\n\nTATE and LIZA keep the old forge, "
            "where the swords of the THRONE were made.\n\n"
            "Every POKéMON in there is a blade, or carries one. Most are STEEL-type.\n\n"
            "FIRE and GROUND moves melt and bury them. FLYING, PSYCHIC and FAIRY moves beat the knights.\n\n"
            "Plus, they'll come at you with outstanding combination attacks. It's a double battle. Go for it!",
     }},
    {'house': 'House Sootopolis', 'words': 'The Long Night Is Ours', 'key': 'JUAN',
     'idea': 'the Lord of the Long Night: Juan froze the crater, and his Pokémon are the cold itself',
     'trainers': ['TRAINER_ANDREA', 'TRAINER_ANNIKA', 'TRAINER_BETHANY', 'TRAINER_BRIANNA', 'TRAINER_BRIDGET',
                  'TRAINER_CONNIE', 'TRAINER_CRISSY', 'TRAINER_DAPHNE', 'TRAINER_OLIVIA', 'TRAINER_TIFFANY'],
     'leader': 'TRAINER_JUAN_',
     'pool': ['SNEASEL', 'SNORUNT', 'SWINUB', 'BERGMITE', 'CRYOGONAL', 'SPHEAL', 'FRIGIBAX', 'CUBCHOO', 'SNOM'],
     'team': ['FROSLASS', 'CRYOGONAL', 'WEAVILE', 'MAMOSWINE', 'BAXCALIBUR'],
     'hard': ['FROSLASS', 'WEAVILE', 'MAMOSWINE', 'AVALUGG', 'CETITAN', 'BAXCALIBUR'],
     'boss': ("I am JUAN of House Sootopolis. The crater has been frozen since the last king died, and I have kept "
              "it so. Our words are: The Long Night Is Ours.",
              "The ice breaks. All eight banners are yours. EVER GRANDE waits, and so does the night. "
              "Remember us when it comes."),
     'text': {
        'SootopolisCity_Gym_1F_Text_GymGuideAdvice':
            "Yo! How's it going, CHAMPION-bound {PLAYER}?\n\nJUAN is the Lord of the Long Night. "
            "He froze this crater when the last king died, and it has not thawed since.\n\n"
            "Every POKéMON in there is ICE-type. FIRE, FIGHTING, STEEL and ROCK moves shatter them.\n\n"
            "And, to get to JUAN, an icy floor will hamper your progress…\n\n"
            "The rest of the way, you have to go for it yourself!",
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
