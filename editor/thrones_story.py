"""Game of Thrones story events: new scenes and twists woven into the real story.

- Bend the knee: after each badge, the beaten house's herald arrives with a gift.
- The Iron Bank: Mr. Stone offers a loan in Rustboro. After the fifth badge, the collector
  shows up.
- The Red Wedding: Capt. Stern's "wedding to the sea" at the Slateport museum turns into
  Team Aqua's ambush.
- Hand of the King: the rival becomes your Hand on Route 110, gets shifty on Route 119,
  betrays you in Lilycove, and says sorry by raven after the seventh badge.
- Walk of shame: after a white-out, someone rings a bell and says "Shame."
- More betrayals: Wally tries to join the Thieves' Guild and later swears himself to the
  Champion, Norman is not who he says he is, and the Gym Guide was a spy all along.

New scenes are scripts added to data/event_scripts.s, called from small hooks in the
existing scripts. Changed lines in existing scenes are whole-text rewrites (TEXT), which
comedy.py uses like the hand-written rewrite files. Uses FLAG_UNUSED_0x020 (took the loan)
and FLAG_UNUSED_0x021 (the loan is paid).
"""
import re

EVENT_SCRIPTS = 'data/event_scripts.s'
LOAN = 'FLAG_UNUSED_0x020'
PAID = 'FLAG_UNUSED_0x021'

# Gym map, badge number. The herald arrives right after the badge is given.
GYMS = [('RustboroCity_Gym', 1), ('DewfordTown_Gym', 2), ('MauvilleCity_Gym', 3), ('LavaridgeTown_Gym_1F', 4),
        ('PetalburgCity_Gym', 5), ('FortreeCity_Gym', 6), ('MossdeepCity_Gym', 7), ('SootopolisCity_Gym_1F', 8)]

# Herald n: (what is said, gift, how many, what is said after the gift or '').
HERALDS = {
    1: ("A ghost floats out of the GYM wall. It's wearing tiny glasses.\n\n"
        "“Ooooo… House Rustboro bends the knee… Lady ROXANNE sends a gift… Your library card… It's overdue… "
        "Since before you were born… Ooooo…”",
        'ITEM_SPELL_TAG', 1, ''),
    2: ("A waiter in a cave-stained apron bows very low. Too low. He's stuck.\n\n"
        "“House Dewford bends the knee. Here's your doggy bag.”",
        'ITEM_LEFTOVERS', 1,
        "“Oh! And an invitation! CAPT. STERN is marrying the sea at the OCEANIC MUSEUM in SLATEPORT. "
        "Everyone's invited. Even the pirates. ESPECIALLY the pirates. They seem really excited. Weirdly excited.”"),
    3: ("A man in a hood melts out of the shadows.\n\n"
        "“The Thieves' Guild bends the knee. Here's a gift. We stole it from you earlier. You're welcome.”",
        'ITEM_AMULET_COIN', 1,
        "“And now, for old times' sake…”\n\nHe hugs you. It's a long hug. Way too long.\n\n"
        "When he lets go, your wallet is 1000 lighter. The Guild always gets a tip."),
    4: ("A man in a bathrobe shuffles in with his eyes closed.\n\n"
        "“Zzz… House Lavaridge bends the… zzz… knee… here…”\n\n"
        "He hands you something and lies down on the floor. He's asleep. He was asleep the whole time.",
        'ITEM_CHESTO_BERRY', 3,
        "A raven lands on the sleeping man. It carries a note from your Hand, {RIVAL}.\n\n"
        "“Hand's advice: drink water. And trust nobody. Except me. ESPECIALLY me.”"),
    5: ("Your father takes off his face. Under it is another face. It's also your father.\n\n"
        "“House Petalburg bends the knee, my child. I have a confession. I am not your father. I'm your father's "
        "brother. Who is also your father. A Dad Has No Name. Don't tell your mother. She knows.”",
        'ITEM_SILK_SCARF', 1, "“Take my tie. A Faceless Dad doesn't need a tie. He needs a thousand ties.”"),
    6: ("A herald in a fireproof suit marches in. He is slightly on fire.\n\n"
        "“House Fortree bends the knee! The dragons wanted to come! They don't fit through the door! "
        "One of them left you this. It's warm. Don't ask why it's warm.”",
        'ITEM_CHARCOAL', 1,
        "A raven arrives. It's not from {RIVAL}. {RIVAL} hasn't written in weeks.\n\n"
        "It's signed “A Friend.” It only says: “Watch your Hand.”"),
    7: ("A herald covered in bandages limps in.\n\n"
        "“House Mossdeep bends the knee. Carefully. We've been sitting on swords. For a year. Here. A crown for "
        "the future king. Do NOT sit on anything.”",
        'ITEM_KINGS_ROCK', 1,
        "A raven arrives. It's from {RIVAL}.\n\n"
        "“Sorry about LILYCOVE. I returned the crown. I kept the snacks. I'm still your Hand, if you'll have me. "
        "Write back. Or don't. I'll know either way. I'm your Hand. Sorry. Old habits.”"),
    8: ("A herald made of ice walks in. He's already melting.\n\n"
        "“House Sootopolis… bends… the kn…”\n\nHe's a puddle now. The puddle hands you something.",
        'ITEM_NEVER_MELT_ICE', 1,
        "A raven from {RIVAL}: “All eight banners! The THRONE waits at EVER GRANDE! I'm proud of you! "
        "I'm only a little jealous! Bring snacks!”"),
}

IRON_BANK_OFFER = ("MR. STONE: Oh, and one more thing. House Stone also runs the IRON BANK.\n\n"
                   "A young TRAINER needs gold. 3000, right now. Low interest. Practically no interest. "
                   "Some interest. Will you take the loan?")
IRON_BANK_YES = ("MR. STONE: Wonderful! Here you go!\n\n{PLAYER} received 3000 from the IRON BANK.\n\n"
                 "MR. STONE: The IRON BANK will be in touch. The IRON BANK is always in touch. "
                 "Even when you don't want it to be.")
IRON_BANK_NO = "MR. STONE: Smart. Very smart. My son said the same thing. He still owes me forty rocks."
COLLECTOR = ("A man in a gray suit was waiting behind your father this whole time.\n\n"
             "“The IRON BANK sends its regards. You owe 3000. Plus interest. Plus a fee for the interest. "
             "Plus a fee for this conversation.”\n\n"
             "He takes 6000 from your wallet. If you didn't have that much, he takes all of it, and a sock.\n\n"
             "“The IRON BANK always gets paid.”")
SHAME_CENTER = ("A nun in the corner of the POKéMON CENTER rings a bell.\n\n“Shame.”\n\n"
                "She follows you all the way to the counter. “Shame.” “Shame.” She's very committed.")
SHAME_MOM = ("MOM rings a little bell.\n\n“Shame.” “Shame.”\n\n"
             "Then she makes you a sandwich. “Shame.”")

# Whole-text rewrites of existing scenes, by label. Codes and question endings are kept.
TEXT = {
    # The Red Wedding.
    'SlateportCity_OceanicMuseum_2F_Text_WellTakeThoseParts':
        "Hehehe, hold it! The band is playing “The Rains of Slateport.” That's the signal!\n\nWe'll take those parts!",
    'SlateportCity_OceanicMuseum_2F_Text_SternWhoAreYou':
        "CAPT. STERN: Wh-what? You're my wedding guests! You brought a gift! Why are you people doing this?",
    'SlateportCity_OceanicMuseum_2F_Text_WereTeamAqua':
        "We're TEAM AQUA! We were never here for the cake!\n\nOur BOSS wants those parts! And the cake! Fork them over!",
    'SlateportCity_OceanicMuseum_2F_Text_Grunt1Defeat':
        "Awaaaah! A kid beat me! At a wedding! I'm going to cry into the cake!",
    'SlateportCity_OceanicMuseum_2F_Text_BossGoingToBeFurious':
        "Oh, man, what a disaster… The BOSS planned this ambush for six months… He picked the napkins himself…",
    'SlateportCity_OceanicMuseum_2F_Text_LetMeTakeCareOfThis':
        "Humph, sniveling wimp! Nobody leaves the Red Wedding! Let me take care of this!",
    'SlateportCity_OceanicMuseum_2F_Text_Grunt2Defeat':
        "What?! I lost, too! I didn't even get to give my speech! It had jokes!",
    'SlateportCity_OceanicMuseum_2F_Text_MeddlingKid':
        "Now what? If we don't get the parts, we're in for it! The BOSS paid for the open bar!\n\n"
        "Arrgh, the one guest who skipped the soup! The soup was the whole plan!",
    'SlateportCity_OceanicMuseum_2F_Text_CameToSeeWhatsTakingSoLong':
        "I came to see why my wedding ambush is taking so long, and you simps are held up by a mere child?",
    'SlateportCity_OceanicMuseum_2F_Text_ArchieWarning':
        "We are TEAM AQUA, and we love the sea!\n\n"
        "And I am ARCHIE, Lord of the Sea, and the wedding planner!\n\n"
        "What makes you interfere with us?\n\n"
        "…No! You can't be! You're not one of TEAM MAGMA?\n\n"
        "Wait, that can't be right. You were on the guest list. I wrote it. I'd remember.\n\n"
        "… … … … … …\n\n"
        "POKéMON, people… All life depends on the sea.\n\n"
        "And today, the sea got married. Whoever marries the sea owns everything in it. That's the law. I think. "
        "I read it on a napkin.\n\n"
        "Ah, fine… You're too young to understand marriage law.\n\n"
        "But I warn you, don't even consider interfering with our plans again.\n\n"
        "The Lord of the Sea doesn't send a second invitation!\n\n"
        "And don't you forget it!",
    'SlateportCity_OceanicMuseum_2F_Text_SternThankYouForSavingUs':
        "CAPT. STERN: You're… Ah, okay, you're {PLAYER}{KUN}… The only guest who didn't betray me!\n\n"
        "That was a tense wedding! Thank you for saving us! I'm still married to the sea, though. "
        "It's very cold in bed.\n\n"
        "Oh, yes, I almost forgot that you even brought the parts from DEVON!",

    # Hand of the King: Route 110, the rival becomes your Hand.
    'Route110_Text_MayLetsBattle':
        "MAY: Hi, {PLAYER}{KUN}, long time no see!\n\n"
        "I've been thinking. Every ruler needs a Hand. Someone loyal. Someone honest. Someone who is me.\n\n"
        "Winner is the king. Loser is the Hand. So… How about a little battle?",
    'Route110_Text_MayDefeated':
        "Yikes! You're the king, then! Fine! I'll be your Hand! I'm great at it! I have two of them!",
    'Route110_Text_MayTakeThis':
        "MAY: As your Hand, I swear to serve you, {PLAYER}{KUN}! Probably! Mostly!\n\n"
        "Every Hand gets a badge of office! This is from me!",
    'Route110_Text_MayExplainItemfinder':
        "MAY: That's an ITEMFINDER.\n\n"
        "Try it out. If there is an item that's not visible, it beeps.\n\n"
        "A good Hand finds hidden things. Treasure. Secrets. Your diary. Okay, {PLAYER}{KUN}, I'll send ravens!\n\n"
        "My first advice as your Hand: train a lot harder for the next time. That's also my only advice.",
    'Route110_Text_BrendanLetsBattle':
        "BRENDAN: Hey, {PLAYER}. So this is where you were.\n\n"
        "Listen. Every king needs a Hand. I've decided I'm yours. Or you're mine. Let's settle it.\n\n"
        "Have you been raising your POKéMON? I'll check for you.",
    'Route110_Text_BrendanDefeated':
        "Hmm… You're the king. Fine. I'm the Hand. I already made a little hat for it.",
    'Route110_Text_BrendanTakeThis':
        "BRENDAN: {PLAYER}, you've been training behind my back… That's very kingly.\n\n"
        "As your Hand, here's my sacred tool of office. Take this.",
    'Route110_Text_BrendanExplainItemfinder':
        "BRENDAN: That's an ITEMFINDER.\n\n"
        "Use it to root around for items that aren't visible.\n\n"
        "If it senses something, it beeps.\n\n"
        "A Hand finds everything. Traitors. Treasure. Snacks. Anyway, I'm off to do Hand stuff. I'll send ravens.",

    # Route 119: the Hand gets shifty.
    'Route119_Text_MayIntro':
        "MAY: {PLAYER}{KUN}! Where were you? Your Hand was looking for you!\n\n"
        "I've been having very normal meetings. With very normal people. Nobody you know. Don't check.\n\n"
        "Ready with your POKéMON? Of course you are! Go!",
    'Route119_Text_MayDefeat':
        "Achah! {PLAYER}{KUN}, you're strong! Too strong. That's… useful information. For me. Your loyal Hand.\n\n"
        "I was worried that you might be struggling with your training. Very worried. For normal reasons.",
    'Route119_Text_BrendanIntro':
        "BRENDAN: {PLAYER}! So this is where you've been?\n\n"
        "I've been… around. At meetings. Hand stuff. Don't read my ravens.\n\n"
        "Let me see how good you got. I'll test you! Now! It's a battle, so battle!",
    'Route119_Text_BrendanDefeat':
        "Hmm… You've gotten pretty darn decent. I'm writing that down. For no reason. Forget I said that.",

    # Lilycove: the Hand betrays you.
    'LilycoveCity_Text_MayShoppingLetsBattle':
        "MAY: Oh, hey? {PLAYER}{KUN}, are you shopping, too? I'm buying a crown. For me. Don't look at the crown.\n\n"
        "I've been your Hand for a while now. I've learned all your secrets. Your team. Your weaknesses. "
        "Your shoe size.\n\n"
        "So I sold them. To everyone. I'm the Queen of LITTLEROOT now. I declared it this morning.\n\n"
        "Show me your POKéMON, {PLAYER}{KUN}. The throne is mine.",
    'LilycoveCity_Text_MayWontBeBeaten':
        "MAY: I know every move you'll make, {PLAYER}{KUN}! I read your diary! Twice!",
    'LilycoveCity_Text_MayDefeat':
        "… … … … … … … …\n\n"
        "I knew all your secrets, {PLAYER}{KUN}, and I still lost. Just like on ROUTE 103.\n\n"
        "I should have stayed loyal, shouldn't I?",
    'LilycoveCity_Text_MayGoingBackToLittleroot':
        "MAY: I'm going back to LITTLEROOT. I'll return the crown. It was on sale.\n\n"
        "I have to tell my dad I betrayed the realm for a discount crown. He's going to make the face.",
    'LilycoveCity_Text_BrendanShoppingLetsBattle':
        "BRENDAN: Oh, hey, it's {PLAYER}.\n\n"
        "I've been your Hand for a while. I know your team, your tricks, and where you hide your snacks.\n\n"
        "So I sold it all. To TEAM AQUA. And TEAM MAGMA. And a man in a hat. Nothing personal. "
        "The crown was on sale.\n\n"
        "Want to have a battle to see who really deserves the throne?",
    'LilycoveCity_Text_BrendanWontBeBeaten':
        "BRENDAN: I know every move you'll make. You're not beating your own Hand, {PLAYER}.",
    'LilycoveCity_Text_BrendanDefeat':
        "Humph… I knew all your secrets and still lost.\n\n"
        "That stings a bit. Betrayal is way harder than it looks…",
    'LilycoveCity_Text_BrendanGoingBackToLittleroot':
        "BRENDAN: I… I'm going home to LITTLEROOT. I'll return the crown. And the snacks. Most of the snacks.\n\n"
        "My dad's going to make me apologize in front of the whole town. With a bell.",

    # Wally tries to join the Thieves' Guild…
    'MauvilleCity_Text_WallyWantToChallengeGym':
        "WALLY: Aww, UNCLE, please?\n\n"
        "I want to join the Thieves' Guild! They have capes! And a secret knock! And snacks!\n\n"
        "Please? May I, please?",
    'MauvilleCity_Text_WallyDefeat':
        "WALLY: … … … … … … …\n\n… … … … … … … …\n\n"
        "I lost… The Guild doesn't take losers… They took my wallet anyway…",
    'MauvilleCity_Text_WallyIllGoBackToVerdanturf':
        "WALLY: UNCLE… I'll go back to VERDANTURF…\n\n"
        "But one day, someone powerful will see my worth. Someone with a cape. A really good cape.",
    # …and later swears himself to the Champion.
    'VictoryRoad_1F_Text_WallyNotGoingToLoseAnymore':
        "WALLY: Hi! {PLAYER}!\n\n"
        "I bet you're surprised to see me here! And in a white cape!\n\n"
        "I've sworn myself to the CHAMPION. I'm his Kingsguard now. He saw my worth. And my cape size.\n\n"
        "{PLAYER}, you taught me how to catch my first POKéMON. That's why this hurts.\n\n"
        "But I'm not going to lose anymore!\n\n"
        "For the Throne! For the CHAMPION! For the cape!\n\n"
        "Okay… Here I come!",
    'VictoryRoad_1F_Text_WallyEntranceDefeat':
        "Wow! {PLAYER}, you are strong, after all! The CHAMPION is going to take the cape back…",
    'VictoryRoad_1F_Text_WallyPostEntranceBattle':
        "WALLY: I betrayed you, {PLAYER}, and I still lost. That's the worst of both worlds.\n\n"
        "Can we pretend this never happened? I'm keeping the cape.",

    # The Gym Guide was a spy all along.
    'SootopolisCity_Gym_1F_Text_GymGuidePostVictory':
        "Yow! You've beaten even JUAN, the Night King himself!\n\n"
        "Okay! Check out your TRAINER CARD.\n\n"
        "If you've gotten all the BADGES, you're set for the POKéMON LEAGUE challenge!\n\n"
        "… … … … … …\n\n"
        "I have a confession. I've been spying for the Night King. The whole time. In every GYM.\n\n"
        "I counseled six kings, remember? I betrayed five of them. You were the sixth. "
        "I just couldn't do it. You always said hi.\n\n"
        "Please don't tell anyone. Except him. He already knows.",
}


def _lines(label, friendly, widths):
    import comedy
    import textdb
    boxes = [comedy.wrap_box(comedy._join(b), widths) for b in comedy._boxes(friendly)]
    raw = textdb.friendly_to_raw('\n\n'.join(boxes), True)
    return ['', label + ':'] + ['\t.string "%s"' % s for s in textdb.split_string_lines(raw)]


def scripts(widths):
    """The new scripts and their texts, as lines for data/event_scripts.s."""
    out = ['', '@ ---- Fun Modes: Game of Thrones story events (added by Emerald Editor) ----']
    texts = []
    for n in sorted(HERALDS):
        said, item, count, after = HERALDS[n]
        out += ['Thrones_EventScript_Herald%d::' % n,
                '\tmsgbox Thrones_Text_Herald%d, MSGBOX_DEFAULT' % n,
                '\tgiveitem %s, %d' % (item, count)]
        texts += _lines('Thrones_Text_Herald%d' % n, said, widths)
        if n == 3:
            out.append('\tremovemoney 1000')
        if after:
            out.append('\tmsgbox Thrones_Text_Herald%dAfter, MSGBOX_DEFAULT' % n)
            texts += _lines('Thrones_Text_Herald%dAfter' % n, after, widths)
        if n == 5:
            out.append('\tcall_if_set %s, Thrones_EventScript_IronBankCollector' % LOAN)
        out += ['\treturn', '']
    out += ['Thrones_EventScript_IronBankLoan::',
            '\tmsgbox Thrones_Text_IronBankOffer, MSGBOX_YESNO',
            '\tgoto_if_eq VAR_RESULT, NO, Thrones_EventScript_IronBankNo',
            '\taddmoney 3000',
            '\tsetflag ' + LOAN,
            '\tmsgbox Thrones_Text_IronBankYes, MSGBOX_DEFAULT',
            '\treturn',
            'Thrones_EventScript_IronBankNo:',
            '\tmsgbox Thrones_Text_IronBankNo, MSGBOX_DEFAULT',
            '\treturn',
            '',
            'Thrones_EventScript_IronBankCollector::',
            '\tgoto_if_set %s, Thrones_EventScript_Return' % PAID,
            '\tmsgbox Thrones_Text_Collector, MSGBOX_DEFAULT',
            '\tremovemoney 6000',
            '\tsetflag ' + PAID,
            'Thrones_EventScript_Return:',
            '\treturn',
            '',
            'Thrones_EventScript_ShameCenter::',
            '\tmsgbox Thrones_Text_ShameCenter, MSGBOX_DEFAULT',
            '\treturn',
            '',
            'Thrones_EventScript_ShameMom::',
            '\tmsgbox Thrones_Text_ShameMom, MSGBOX_DEFAULT',
            '\treturn']
    for label, friendly in [('Thrones_Text_IronBankOffer', IRON_BANK_OFFER), ('Thrones_Text_IronBankYes', IRON_BANK_YES),
                            ('Thrones_Text_IronBankNo', IRON_BANK_NO), ('Thrones_Text_Collector', COLLECTOR),
                            ('Thrones_Text_ShameCenter', SHAME_CENTER), ('Thrones_Text_ShameMom', SHAME_MOM)]:
        texts += _lines(label, friendly, widths)
    return out + texts


def _hook(ov, rel, after_re, line, report, what):
    text = ov.read(rel)
    if line.strip() in text:
        return
    new, n = re.subn(after_re, lambda m: m.group(0) + '\n' + line, text, count=1, flags=re.M)
    if n:
        ov.write(rel, new)
    else:
        report.append('Could not find the spot for ' + what + ' in ' + rel)


def apply(ov, widths):
    """Adds the new scenes and hooks them in. Returns report lines."""
    report = []
    text = ov.read(EVENT_SCRIPTS)
    if 'Thrones_EventScript_Herald1::' not in text:
        ov.write(EVENT_SCRIPTS, text.rstrip('\n') + '\n' + '\n'.join(scripts(widths)) + '\n')
    for folder, n in GYMS:
        _hook(ov, 'data/maps/%s/scripts.inc' % folder, r'^\tsetflag FLAG_BADGE%02d_GET$' % n,
              '\tcall Thrones_EventScript_Herald%d' % n, report, 'herald %d' % n)
    _hook(ov, 'data/maps/RustboroCity_DevonCorp_3F/scripts.inc',
          r'^\tmsgbox RustboroCity_DevonCorp_3F_Text_MrStoneExplainPokenavRestUp, MSGBOX_DEFAULT$',
          '\tcall Thrones_EventScript_IronBankLoan', report, 'the Iron Bank')
    _hook(ov, EVENT_SCRIPTS, r'^EventScript_AfterWhiteOutHeal::\n\tlockall$',
          '\tcall Thrones_EventScript_ShameCenter', report, 'the walk of shame')
    _hook(ov, EVENT_SCRIPTS, r'^EventScript_AfterWhiteOutMomHeal::\n\tlockall$',
          '\tcall Thrones_EventScript_ShameMom', report, 'the walk of shame at home')
    report.insert(0, 'Story events: heralds after every badge, the Iron Bank, the Red Wedding, '
                     'your Hand (and their betrayal), Wally\'s cape, the spy, and the walk of shame.')
    return report
