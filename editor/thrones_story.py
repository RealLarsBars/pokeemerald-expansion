"""Game of Thrones story events: new scenes and twists woven into the real story.

- Bend the knee: after each badge, the beaten house's herald arrives with a gift.
- The Iron Bank: Mr. Stone offers a loan in Rustboro. After the fifth badge, the collector
  shows up.
- The Red Wedding: Capt. Stern's feast at the Slateport museum, where his ship is wed to
  the sea, turns into Team Aqua's ambush.
- Hand of the King: the rival becomes your Hand on Route 110, gets shifty on Route 119,
  sells you out in Lilycove, and writes after after the seventh badge.
- After a white-out: a septa rings her bell in the Pokémon Center; at home, Mom speaks.
- More betrayals: Wally wants to serve Mauville's Master of Whispers and later swears
  himself to the Champion, Norman is not who he says he is, and the Gym Guide was a spy.

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
    1: ("A woman in grey robes waits at the GYM door. Grave dust clings to her hem.\n\n"
        "“House Rustboro bends the knee. Lady ROXANNE keeps the crypts beneath the school, and the dead "
        "there watched you climb. She sends you this, from the oldest tomb.”",
        'ITEM_SPELL_TAG', 1, ''),
    2: ("A reaver with salt-white hair blocks the cave mouth. He does not bow until BRAWLY's raven "
        "lands on his shoulder.\n\n“House Dewford bends the knee. For now. Take this. The sea gave it to us.”",
        'ITEM_MYSTIC_WATER', 1,
        "“A word, since you won fairly. CAPT. STERN is holding a feast at the OCEANIC MUSEUM in SLATEPORT. "
        "He weds his new ship to the sea, the old way, with bread and salt.\n\n"
        "Lord ARCHIE has accepted the invitation. So have a great many of his men.\n\n"
        "Guest right is sacred. Remember that, if you go. Remember who forgets it.”"),
    3: ("A thin man in a grey cloak is standing beside you. You did not hear him arrive.\n\n"
        "“House Wattson bends the knee. Lord WATTSON hears everything in MAUVILLE, and now he hears it for you.”",
        'ITEM_BLACK_GLASSES', 1,
        "“A gift, and a whisper. Your friend {RIVAL} has been seen on the coast roads, drinking with "
        "men in red, and with men in blue.\n\nPerhaps it means nothing. In my experience, it never does.”"),
    4: ("A priestess steps out of the steam. Her eyes are red from the springs.\n\n"
        "“House Lavaridge bends the knee. Lady FLANNERY dreamed of you three nights running. "
        "She saw a crown of water, a crown of fire, and a hand holding a knife.\n\n"
        "She does not know whose hand. She asked me to give you this.”",
        'ITEM_TWISTED_SPOON', 1,
        "A raven lands on the rail. The letter is from {RIVAL}, and it is very short.\n\n"
        "“Stay off the coast roads. I'll explain when I can. Burn this.”"),
    5: ("Your father waits until the GYM is empty. When he speaks, his voice is not quite his own.\n\n"
        "“House Petalburg bends the knee to you, my child. Now hear the truth.\n\n"
        "I was not born in PETALBURG. I was trained across the sea, by men who own no faces, and sent "
        "here to watch the THRONE. NORMAN was a name I wore. Then I met your mother, and I let it become mine.\n\n"
        "She knows. Now you do. Tell no one.”",
        'ITEM_SILK_SCARF', 1,
        "“Take this. It is the only thing I carried here from the old life. I have no more use for it.”"),
    6: ("A herald with burned hands kneels at the foot of the tree.\n\n"
        "“House Fortree bends the knee. The dragons would have come themselves, but the Lady will not "
        "let them near the town. Not yet. She sends this from their nest. It is still warm.”",
        'ITEM_CHARCOAL', 1,
        "A raven arrives. It is not from {RIVAL}. {RIVAL} has not written in weeks.\n\n"
        "There is no seal and no name. Three words: “Watch your Hand.”"),
    7: ("A herald in a dented helm kneels before you.\n\n"
        "“House Mossdeep bends the knee. The twins forged the first swords of the THRONE, a hundred years ago. "
        "They send you this, for the head that will one day carry the weight.”",
        'ITEM_KINGS_ROCK', 1,
        "A raven arrives. It is from {RIVAL}.\n\n"
        "“I won't ask you to forgive LILYCOVE. I told myself I was protecting you by picking a side "
        "before the sides picked us. I was protecting myself.\n\n"
        "If you still want a Hand, I'm here. If you don't, I'll understand.”"),
    8: ("A herald walks in out of the cold. There is frost in his beard, and he does not shiver.\n\n"
        "“House Sootopolis bends the knee. Not to you. To what must come after the war.\n\n"
        "The Lord JUAN asks that you remember who stood with you when the long night fell.”",
        'ITEM_NEVER_MELT_ICE', 1,
        "A raven from {RIVAL}: “All eight banners. The THRONE waits at EVER GRANDE.\n\n"
        "I'll be on the road behind you. Whatever you decide about me, I'll be there.”"),
}

IRON_BANK_OFFER = ("MR. STONE: One more matter. House Stone does not only hold the land. It holds the IRON BANK.\n\n"
                   "Wars are won with gold as much as with POKéMON. I can lend you 3000, today. "
                   "Will you take the loan?")
IRON_BANK_YES = ("MR. STONE: Very good.\n\n{PLAYER} received 3000 from the IRON BANK.\n\n"
                 "MR. STONE: The IRON BANK will have its due, {PLAYER}{KUN}. It always does. "
                 "Kings have learned that too late.")
IRON_BANK_NO = ("MR. STONE: A wise answer. Few lords give it. Fewer still are around long enough "
                "to be glad they did.")
COLLECTOR = ("A man in grey was standing behind your father the whole time. No one saw him come in.\n\n"
             "“I come from the IRON BANK. You owe 3000, and the interest has run for four badges. "
             "The debt is now 6000.”\n\n"
             "He counts it out of your purse, coin by coin. If you do not have enough, he takes what there is.\n\n"
             "“The IRON BANK will have its due.”")
SHAME_CENTER = ("A septa stands by the door of the POKéMON CENTER. As you pass, she rings her bell once.\n\n"
                "“Shame.”")
SHAME_MOM = ("MOM doesn't ask what happened. She can see it.\n\n"
             "“Every house loses battles. The ones that last are the ones that get up again. Rest now.”")

# Whole-text rewrites of existing scenes, by label. Codes and question endings are kept.
TEXT = {
    # The Red Wedding.
    'SlateportCity_OceanicMuseum_2F_Text_WellTakeThoseParts':
        "The musicians stop. Then they begin a different song: “The Rains of Slateport.”\n\n"
        "That's the signal! Bar the doors! We'll take those parts!",
    'SlateportCity_OceanicMuseum_2F_Text_SternWhoAreYou':
        "CAPT. STERN: Wh-what? You ate my bread! You took my salt! You're my guests! Why are you doing this?",
    'SlateportCity_OceanicMuseum_2F_Text_WereTeamAqua':
        "We're TEAM AQUA! We came for the parts, not the feast.\n\n"
        "Guest right is for lords who can afford it! Hand them over, old man!",
    'SlateportCity_OceanicMuseum_2F_Text_Grunt1Defeat':
        "Awaaaah! Beaten by a child, in front of the whole hall!",
    'SlateportCity_OceanicMuseum_2F_Text_BossGoingToBeFurious':
        "Oh, man, what a disaster… Lord ARCHIE planned this for months… He'll have my head on the gate…",
    'SlateportCity_OceanicMuseum_2F_Text_LetMeTakeCareOfThis':
        "Humph, sniveling wimp! No one leaves this hall until it's done! Let me take care of this!",
    'SlateportCity_OceanicMuseum_2F_Text_Grunt2Defeat':
        "What?! I lost, too! The doors were barred! Where did you even come from?",
    'SlateportCity_OceanicMuseum_2F_Text_MeddlingKid':
        "Now what? If we don't get the parts, we're in for it!\n\n"
        "Every guest was counted. Every door was watched. And one child still got through!",
    'SlateportCity_OceanicMuseum_2F_Text_CameToSeeWhatsTakingSoLong':
        "I came to see why the hall isn't taken yet, and I find you simps held up by a mere child?",
    'SlateportCity_OceanicMuseum_2F_Text_ArchieWarning':
        "We are TEAM AQUA, and the sea is ours!\n\n"
        "And I am ARCHIE, Lord of the Sea, and soon of everything it touches!\n\n"
        "What makes you interfere with us?\n\n"
        "…No! You can't be! You're not one of TEAM MAGMA?\n\n"
        "No. MAXIE's dogs don't come to feasts. They come after, to pick the bones.\n\n"
        "… … … … … …\n\n"
        "POKéMON, people… All life depends on the sea.\n\n"
        "CAPT. STERN would wed his ship to it, and keep it for DEVON and the THRONE. "
        "I will not let the sea be married off like a lord's daughter.\n\n"
        "You think I broke guest right? The sea has no guests. Only the drowned.\n\n"
        "But I warn you, don't even consider interfering with our plans again.\n\n"
        "The next time, there will be no feast and no doors left to bar.\n\n"
        "And don't you forget it!",
    'SlateportCity_OceanicMuseum_2F_Text_SternThankYouForSavingUs':
        "CAPT. STERN: You're… Ah, okay, you're {PLAYER}{KUN}…\n\n"
        "They ate at my table. They raised their cups to my ship. And then they barred the doors. "
        "Thank you for saving us! I won't forget who stood with me today.\n\n"
        "Oh, yes, I almost forgot that you even brought the parts from DEVON!",

    # Hand of the King: Route 110, the rival becomes your Hand.
    'Route110_Text_MayLetsBattle':
        "MAY: Hi, {PLAYER}{KUN}, long time no see!\n\n"
        "Everyone on the road is talking about you. The lords are starting to count your banners.\n\n"
        "Anyone who wants the THRONE needs a Hand. Someone who tells them the truth. "
        "I'd like that to be me.\n\n"
        "Winner rules, loser serves. So… How about a little battle?",
    'Route110_Text_MayDefeated':
        "Yikes! You're better than I expected! Then I'm your Hand.",
    'Route110_Text_MayTakeThis':
        "MAY: I swear to serve you, {PLAYER}{KUN}, and to tell you the truth even when you hate it.\n\n"
        "A Hand should have something to show for it. This is from me!",
    'Route110_Text_MayExplainItemfinder':
        "MAY: That's an ITEMFINDER.\n\n"
        "Try it out. If there is an item that's not visible, it emits a sound.\n\n"
        "A Hand's work is finding what people hide. Okay, {PLAYER}{KUN}, I'll send ravens!\n\n"
        "My first counsel: the lords are watching now. Train a lot harder for the next time.",
    'Route110_Text_BrendanLetsBattle':
        "BRENDAN: Hey, {PLAYER}. So this is where you were.\n\n"
        "People are saying your name in taverns now. That's how it starts.\n\n"
        "If you're going for the THRONE, you'll need a Hand. Let's see which of us should be serving.\n\n"
        "Have you been raising your POKéMON? I'll check for you.",
    'Route110_Text_BrendanDefeated':
        "Hmm… You're pretty good. All right. I'm your Hand.",
    'Route110_Text_BrendanTakeThis':
        "BRENDAN: {PLAYER}, you've trained without me noticing… That's the kind of thing I'm supposed to notice.\n\n"
        "A Hand needs a tool of office. Here, take this.",
    'Route110_Text_BrendanExplainItemfinder':
        "BRENDAN: That's an ITEMFINDER.\n\n"
        "Use it to root around for items that aren't visible.\n\n"
        "If it senses something, it emits a sound.\n\n"
        "A Hand finds the things people bury. I'm off to listen at some doors. I'll send ravens.",

    # Route 119: the Hand grows distant.
    'Route119_Text_MayIntro':
        "MAY: {PLAYER}{KUN}! Where were you? I was looking for you!\n\n"
        "I've been in LILYCOVE, mostly. Meetings. A Hand has to talk to everyone, even people you wouldn't like.\n\n"
        "Ready with your POKéMON? Of course you are! Go!",
    'Route119_Text_MayDefeat':
        "Achah! {PLAYER}{KUN}, you're strong! Stronger than they think.\n\n"
        "I was worried that you might be struggling with your training. Now I'm worried about something else.",
    'Route119_Text_BrendanIntro':
        "BRENDAN: {PLAYER}! So this is where you've been?\n\n"
        "I've been on the coast. Talking to people. Don't ask which ones.\n\n"
        "Let me see how good you got. I'll test you! Now! It's a battle, so battle!",
    'Route119_Text_BrendanDefeat':
        "Hmm… You've gotten pretty darn decent. They'll want to know that.",

    # Lilycove: the Hand betrays you.
    'LilycoveCity_Text_MayShoppingLetsBattle':
        "MAY: Oh, hey? {PLAYER}{KUN}, I hoped I wouldn't run into you here.\n\n"
        "I'll tell you myself, because you'd hear it anyway. I gave your plans to Lord MAXIE. "
        "Your team, your road, which towns are loyal.\n\n"
        "In return, LITTLEROOT will be spared when the fire comes. My father will be spared.\n\n"
        "You can't protect us, {PLAYER}{KUN}. Show me your POKéMON. Prove me wrong.",
    'LilycoveCity_Text_MayWontBeBeaten':
        "MAY: I know every move you'll make, {PLAYER}{KUN}. I helped you plan them.",
    'LilycoveCity_Text_MayDefeat':
        "… … … … … … … …\n\n"
        "I remember the battle I had with you, {PLAYER}{KUN}, on ROUTE 103. You were nobody then.\n\n"
        "I chose the wrong side, didn't I?",
    'LilycoveCity_Text_MayGoingBackToLittleroot':
        "MAY: I'm going back to LITTLEROOT.\n\n"
        "I have to tell my father what I did, and why. I don't know which part will hurt him more.",
    'LilycoveCity_Text_BrendanShoppingLetsBattle':
        "BRENDAN: Oh, hey, it's {PLAYER}.\n\n"
        "You'll hear it soon, so hear it from me. I sold your plans to Lord ARCHIE. "
        "Your team, your road, who's loyal to you.\n\n"
        "He promised LITTLEROOT won't drown when the sea comes. That was the price.\n\n"
        "Want to have a battle to see which of us was right?",
    'LilycoveCity_Text_BrendanWontBeBeaten':
        "BRENDAN: I know all your tricks. I'm not going to lose to my own king, {PLAYER}.",
    'LilycoveCity_Text_BrendanDefeat':
        "Humph… I knew every secret you had, and it still wasn't enough.\n\n"
        "That stings a bit. Maybe it should sting more.",
    'LilycoveCity_Text_BrendanGoingBackToLittleroot':
        "BRENDAN: I… I'm going home to LITTLEROOT.\n\n"
        "My dad trusted me with his work. Now I have to tell him what I did with yours.",

    # Wally wants to serve the Master of Whispers…
    'MauvilleCity_Text_WallyWantToChallengeGym':
        "WALLY: Aww, UNCLE, please?\n\n"
        "Lord WATTSON takes in sick boys and orphans and teaches them to listen. "
        "If I win, he'll take me. I won't be the boy in bed anymore.\n\n"
        "Please? May I, please?",
    'MauvilleCity_Text_WallyDefeat':
        "WALLY: … … … … … … …\n\n… … … … … … … …\n\nI lost… Nobody wants a weak spy…",
    'MauvilleCity_Text_WallyIllGoBackToVerdanturf':
        "WALLY: UNCLE… I'll go back to VERDANTURF…\n\n"
        "But someday someone powerful will see what I'm worth. I'll make sure of it.",
    # …and later swears himself to the Champion.
    'VictoryRoad_1F_Text_WallyNotGoingToLoseAnymore':
        "WALLY: Hi! {PLAYER}!\n\n"
        "I bet you're surprised to see me here! And in a white cloak.\n\n"
        "The CHAMPION saw what I'm worth. I've sworn my sword to him. I'm his Kingsguard now.\n\n"
        "{PLAYER}, you taught me how to catch my first POKéMON. That is why I had to be the one to stop you.\n\n"
        "But I'm not going to lose anymore!\n\n"
        "For the THRONE! For the CHAMPION!\n\nOkay… Here I come!",
    'VictoryRoad_1F_Text_WallyEntranceDefeat':
        "Wow! {PLAYER}, you are strong, after all! I've failed my oath already…",
    'VictoryRoad_1F_Text_WallyPostEntranceBattle':
        "WALLY: I swore to stop you, {PLAYER}, and I couldn't. A Kingsguard who can't keep the gate.\n\n"
        "Go on, then. He'll be waiting. He's always known you'd come.",

    # The Gym Guide was a spy all along.
    'SootopolisCity_Gym_1F_Text_GymGuidePostVictory':
        "Yow! You've beaten even JUAN, the lord of the long night himself!\n\n"
        "Okay! Check out your TRAINER CARD.\n\n"
        "If you've gotten all the BADGES, you're set for the POKéMON LEAGUE challenge!\n\n"
        "… … … … … …\n\n"
        "Before you go, you deserve the truth. Every word of advice I gave you, I also wrote down "
        "for someone else. The CHAMPION has known your road since RUSTBORO.\n\n"
        "I was paid to watch you, not to like you. I failed at the second part.\n\n"
        "Go carefully. He knows you're coming.",
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
          '\tcall Thrones_EventScript_ShameCenter', report, 'the septa after a white-out')
    _hook(ov, EVENT_SCRIPTS, r'^EventScript_AfterWhiteOutMomHeal::\n\tlockall$',
          '\tcall Thrones_EventScript_ShameMom', report, 'Mom after a white-out')
    report.insert(0, 'Story events: heralds after every badge, the Iron Bank, the Red Wedding, '
                     'your Hand (and their betrayal), Wally\'s oath, the spy, and the septa\'s bell.')
    return report
