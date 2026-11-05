"""Writing for the comedy dialogue packs.

Only characters the game's font has: plain letters, digits, é, and
! ? . , ' - : ; ( ) & + = % / ~ and the ellipsis. No double quotes.
{PLAYER} and {RIVAL} are filled in by the game. {TOWN} is filled in by the
editor with the name of the place where the line is said.

Every line is written for a moment, so it makes sense where it lands:
- talk:   after someone finishes talking to you
- house:  after someone talks to you inside their own house
- thing:  after you examine an object (a bookshelf, a locked door...)
- intro:  after a trainer challenges you, right before the battle
- defeat: after a trainer loses to you
- after:  when you talk to a trainer you already beat
Lines about a topic (shops, Gyms, the sea...) are used when the text is
about that topic. Nothing here assumes the player's age or gender."""

# ---- the hero finally says something (out loud, on the last lines) -----------
HERO = {
    'talk': [
        "{PLAYER}: Cool. Cool cool cool. Anyway.",
        "{PLAYER}: I'm going to pretend that made sense.",
        "{PLAYER}: Respectfully, what?",
        "{PLAYER}: Noted. Ignored. Archived.",
        "{PLAYER}: You said that with your whole chest.",
        "{PLAYER}: I nodded. Nodding is all I can do. I am trapped in nodding.",
        "{PLAYER}: That's the most normal thing I've heard all week, which is concerning.",
        "{PLAYER}: I'm putting this conversation in the PC and never taking it out.",
        "{PLAYER}: Wow. Okay. Unpacking that in therapy later.",
        "{PLAYER}: Love that for you. Truly. Bye.",
        "{PLAYER}: Why does everyone here talk to me like I'm a quest board?",
        "{PLAYER}: I've heard that exact sentence from three different people today.",
        "{PLAYER}: Do you just stand there all day waiting to tell someone that?",
        "{PLAYER}: Was that advice or a threat? Blink twice.",
        "{PLAYER}: I'm going to remember that and bring it up at the worst moment.",
        "{PLAYER}: I could just leave. I could go home. I won't, but I could.",
        "{PLAYER}: Nobody in {TOWN} has a normal job, huh?",
        "{PLAYER}: I think I'm the only sane person in {TOWN}, and I keep a bird in a ball.",
    ],
    'house': [
        "{PLAYER}: I just walked into your house uninvited and you started chatting. Nobody here locks a door.",
        "{PLAYER}: I'm a total stranger standing in your living room and your move is small talk?",
        "{PLAYER}: Nice place. I'm going to check your bookshelf and your PC now, and then leave without a word.",
        "{PLAYER}: You don't know my name and I'm standing in your kitchen. Hoenn is wild.",
        "{PLAYER}: I'm going to check every pot in this house for items. That's normal here, right?",
    ],
    'thing': [
        "{PLAYER}: Riveting.",
        "{PLAYER}: Yep. That's a thing alright.",
        "{PLAYER}: Five stars. Would examine again.",
        "{PLAYER}: I'm leaving a review.",
        "{PLAYER}: Nobody saw me do that. Good.",
        "{PLAYER}: Pressing A on everything is my whole personality now.",
        "{PLAYER}: I was hoping for an item. I'm always hoping for an item.",
    ],
    'intro': [
        "{PLAYER}: We made eye contact for one second. Apparently that's a legal contract here.",
        "{PLAYER}: You've been standing in that exact spot all day waiting for someone to look at you, huh?",
        "{PLAYER}: Fine. But I'm taking your money and I'm not saying sorry.",
        "{PLAYER}: I've beaten ten people like you today. I counted. I'm counting you now.",
        "{PLAYER}: Can I just walk past? No? Cool.",
        "{PLAYER}: Okay, but if I win, you have to stop talking.",
        "{PLAYER}: Big speech for someone about to lose to a kid with a backpack.",
    ],
    'defeat': [
        "{PLAYER}: I'll take my prize money in cash, thanks.",
        "{PLAYER}: You lost to a kid with a backpack. Take a minute.",
        "{PLAYER}: Good game. I mean that. No I don't.",
        "{PLAYER}: Okay, now go stand in your spot and think about what you did.",
        "{PLAYER}: Same time tomorrow? I'll bring a bigger wallet.",
        "{PLAYER}: My POKéMON say gg. They're lying.",
    ],
    'after': [
        "{PLAYER}: You lost to me five minutes ago and you're giving me advice?",
        "{PLAYER}: Bold of you to keep talking after that.",
        "{PLAYER}: I'd love to stay and chat, but I'm going to go beat up your neighbors.",
        "{PLAYER}: You're still standing in the exact same spot. Do you live here?",
        "{PLAYER}: I already took your money. What else do you want from me?",
    ],
}

# ---- narrator asides ------------------------------------------------------------
NARRATOR = {
    'talk': [
        "(Narrator: They had been rehearsing that line for weeks.)",
        "(Narrator: Nobody clapped.)",
        "(Narrator: That was a lie. Everyone could tell.)",
        "(Narrator: This person would later be arrested for something unrelated.)",
        "(Narrator: They meant every word. That was the scary part.)",
        "(Narrator: {PLAYER} would think about this every night for a week.)",
        "(Narrator: This would come up again. It would be worse.)",
        "(Narrator: The conversation lasted exactly as long as it needed to. Too long.)",
        "(Narrator: They went right back to staring at nothing.)",
        "(Narrator: {TOWN} has a population of about nine, and all of them have opinions.)",
        "(Narrator: Meanwhile, the rest of {TOWN} pretended not to listen. Badly.)",
        "(Narrator: Somewhere, a Wingull laughed.)",
    ],
    'thing': [
        "(Narrator: It was, in every way, exactly that.)",
        "(Narrator: {PLAYER} stared at it for an uncomfortable amount of time.)",
        "(Narrator: Behind it, there was nothing. There is never anything.)",
        "(Narrator: This was the most interesting thing for miles.)",
        "(Narrator: A lesser hero would have walked past. {PLAYER} pressed A.)",
        "(Narrator: Somewhere, a hidden item was watching and judging.)",
    ],
    'intro': [
        "(Narrator: This person had not won a battle since the last game.)",
        "(Narrator: Their POKéMON already looked embarrassed.)",
        "(Narrator: They had been waiting in that exact spot since the game came out.)",
        "(Narrator: The music changed. Things were about to get loud.)",
        "(Narrator: {PLAYER} chose violence.)",
    ],
    'defeat': [
        "(Narrator: They would tell everyone it was close. It was not close.)",
        "(Narrator: Their POKéMON were already looking for a new trainer.)",
        "(Narrator: That prize money was the last of their savings.)",
        "(Narrator: Nobody learned anything.)",
    ],
    'after': [
        "(Narrator: They would stand there, defeated, until the end of time.)",
        "(Narrator: Their POKéMON were still not speaking to them.)",
        "(Narrator: They had told their whole family they won.)",
    ],
}
NARRATOR['house'] = NARRATOR['talk']

# ---- the person keeps talking and overshares (sitcom energy) --------------------
CHAOS = [
    "I've been standing in this exact spot for eleven years. Nobody has ever asked why.",
    "My Wingull does my taxes. He's not good at it, but he's cheap.",
    "Don't look in my basement. There's no basement. Stop looking for the basement.",
    "I put all my savings into Poké Ball futures. Now I just say stuff to strangers.",
    "I'm in a feud with my neighbor. They don't know. That's the power move.",
    "Every night I hear the Wurmple singing. Every night the song gets longer.",
    "I'm technically the mayor of {TOWN}. Nobody voted. I just started wearing a sash.",
    "My therapist is a Chimecho. Sessions are mostly ringing.",
    "If you see someone in a Wailord costume, no you didn't.",
    "I'm not crying, my Lotad is just leaking again.",
    "I licked a Grimer once. On a dare. I still taste it on Tuesdays.",
    "Do you ever stare at a Spinda and think, that's what I look like inside?",
    "Want to buy a Shuckle? It's been in my family for nine generations. It's the same Shuckle.",
    "I'm not supposed to tell you this, but I'm three Zigzagoon in a coat.",
]

# How someone changes the subject before oversharing.
CHAOS_LEADS = ['Also, unrelated:', 'Random, but', 'Anyway, fun fact:', 'Oh, and', 'Not that you asked, but']

# ---- lines about what the text is about --------------------------------------------
# Checked in order; the first topic whose words appear in a text wins.
TOPICS = [
    ('villain', ['team aqua', 'team magma', 'aqua', 'magma', 'maxie', 'archie', 'grunt']),
    ('rival', ['{rival}']),
    ('gym', ['gym', 'badge']),
    ('center', ['pokémon center', 'heal', 'nurse', 'potion']),
    ('shop', ['buy', 'sell', 'shop', 'mart', 'money', '¥', 'price', 'customer']),
    ('contest', ['contest', 'pokéblock', 'ribbon']),
    ('science', ['prof.', 'professor', 'research', 'pokédex', 'devon', 'scientist']),
    ('family', ['mom', 'dad', 'mother', 'father', 'grandpa', 'grandma', 'son', 'daughter', 'husband', 'wife',
                'brother', 'sister']),
    ('sea', ['sea', 'ocean', 'boat', 'ship', 'surf', 'beach', 'swim', 'sail', 'fish']),
    ('nature', ['berry', 'berries', 'flower', 'tree', 'plant', 'grass', 'bug']),
    ('battle', ['battle', 'strong', 'train']),
]
TOPIC_HERO = {
    'villain': ["{PLAYER}: Your whole plan is to change the planet's geography, and you dress alike for it.",
                "{PLAYER}: Why are the evil teams always hiring? Is the pay good? Asking for a friend.",
                "{PLAYER}: Hoenn's entire police strategy is: let the kid handle it."],
    'rival': ["{PLAYER}: Wherever I go, {RIVAL} was there five minutes earlier. Are they following me from the front?",
              "{PLAYER}: {RIVAL} keeps saying we're rivals. I keep winning. That's not a rivalry, that's a routine."],
    'gym': ["{PLAYER}: So the plan is I beat up the local government and they give me jewelry.",
            "{PLAYER}: Who designs these Gyms? Why is there always a puzzle? I just want to fight.",
            "{PLAYER}: The badges don't do anything. They just make strangers nervous. I love them."],
    'center': ["{PLAYER}: Free healing, free PC, free counter to lean on. Only working institution in Hoenn.",
               "{PLAYER}: My POKéMON were on fire five seconds ago. Now they're fine. Nobody asks questions.",
               "{PLAYER}: I've slept in more POKéMON CENTERS than at home. Mom thinks I'm at camp."],
    'shop': ["{PLAYER}: Why does every shop in Hoenn sell the same twelve things?",
             "{PLAYER}: I have 99 Potions and I'm still going to buy more. This is an illness.",
             "{PLAYER}: I pay for all this by fighting strangers. Hoenn has one job and it's that."],
    'contest': ["{PLAYER}: Judges rating how pretty my POKéMON are? We fight in the dirt. We are not pretty.",
                "{PLAYER}: Blending Berries into candy for a ribbon. This region has hobbies, I'll give it that.",
                "{PLAYER}: My POKéMON's Cool stat is low because it has seen things."],
    'science': ["{PLAYER}: Every scientist here hands important stuff to strangers. Do you guys have security?",
                "{PLAYER}: Professor Birch still owes me for saving his life in a bush.",
                "{PLAYER}: I'm filling a whole encyclopedia for free, for a guy who hides in tall grass."],
    'family': ["{PLAYER}: Everybody in Hoenn has a family member who's a problem. I'm starting to think mine is me.",
               "{PLAYER}: My dad runs a Gym and never calls. I don't need your family drama too.",
               "{PLAYER}: Tell your family I said hi. Or don't. I won't remember them."],
    'sea': ["{PLAYER}: My POKéMON is going to carry me across the ocean on its back and everyone's fine with that.",
            "{PLAYER}: Most of Hoenn is water, and most of the water is Tentacool.",
            "{PLAYER}: I'm not getting on a boat with you. I've seen what happens on boats here."],
    'nature': ["{PLAYER}: I'm not eating anything that grew in this region. I've seen the soil.",
               "{PLAYER}: Hoenn has a plant for every problem and a POKéMON hiding in every plant."],
    'battle': ["{PLAYER}: Everybody here wants to fight me. Is it the hat?",
               "{PLAYER}: I've had more fights than conversations this week. Wait, this is a conversation. Close one."],
}
TOPIC_NARRATOR = {
    'villain': ["(Narrator: Team Aqua and Team Magma once shared an office. It ended badly.)",
                "(Narrator: The grunts were paid in exposure.)",
                "(Narrator: Nobody on either team has ever opened a geography book.)"],
    'rival': ["(Narrator: {RIVAL} was, at that exact moment, losing to a Bug Catcher.)",
              "(Narrator: {RIVAL} had practiced all of this in a mirror.)"],
    'gym': ["(Narrator: Every Gym in Hoenn is required by law to have one guy at the door giving advice.)",
            "(Narrator: The Gym's insurance did not cover any of what was about to happen.)",
            "(Narrator: The Leader was, at that moment, striking a dramatic pose in an empty room.)"],
    'center': ["(Narrator: The nurse's smile did not move. It has never moved.)",
               "(Narrator: Nobody has ever seen the back room. Nobody ever will.)",
               "(Narrator: The healing jingle is the only song everyone in Hoenn knows by heart.)"],
    'shop': ["(Narrator: {PLAYER} would later sell a Nugget here for way less than it was worth.)",
             "(Narrator: Capitalism, but make it POKéMON.)"],
    'contest': ["(Narrator: The judges had been bribed with Pokéblocks. All of them. By each other.)",
                "(Narrator: Contest Halls run on glitter, spite and hope.)"],
    'science': ["(Narrator: This research was funded by Devon. Devon would be taking all of it.)",
                "(Narrator: Science in Hoenn is mostly shouting at birds.)"],
    'family': ["(Narrator: The next family dinner would be a bloodbath.)",
               "(Narrator: The family group chat was already blowing up about this.)",
               "(Narrator: Somewhere, a grandparent sensed they were being talked about.)"],
    'sea': ["(Narrator: Out at sea, a Wailmer did a flip. Nobody saw. It was very sad about that.)",
            "(Narrator: The sea had heard all this before. The sea did not care.)"],
    'nature': ["(Narrator: The tall grass rustled with judgment.)",
               "(Narrator: Somewhere, a Berry tree grew one Oran Berry out of spite.)"],
    'battle': ["(Narrator: They talked a big game. The game, it turned out, was small.)"],
}
TOPIC_CHAOS = {
    'villain': ["I joined Team Magma for the hoodie and stayed for the dental. Then I left. The hoodie stayed.",
                "My cousin's in Team Aqua. He doesn't know what they do either. He just likes saying yo ho."],
    'gym': ["I failed the Gym puzzle so many times they gave me a chair.",
            "I trained nine years to beat that Gym. Yesterday I found out there's a type chart."],
    'center': ["I come here to sit in the lobby. I'm not hurt. I just like the jingle.",
               "I asked the nurse to heal my emotional damage. She put me in a Poké Ball for six seconds. It helped."],
    'shop': ["I bought a Repel once. Now nothing comes near me. Not POKéMON. Not people. Not love.",
             "My whole business plan is selling Potions to kids who just got free Potions."],
    'contest': ["I lost a Beauty Contest to a Feebas once. I still wake up screaming.",
                "My Pokéblock recipe is a family secret. The secret is it's just one Pecha Berry."],
    'science': ["I'm doing research. Mostly I write down what Zigzagoon eat. It's everything. They eat everything.",
                "My thesis says Magikarp is secretly the strongest POKéMON. I've been fired from four labs."],
    'family': ["My grandpa says when he was young there were only 151 POKéMON, and they were all angrier.",
               "My family has a cursed heirloom. It's a Poké Ball. It's always empty. It's always warm."],
    'sea': ["I tried to Surf on a Magikarp once. It went badly for both of us.",
            "I've fished here for twenty years. I've caught 4,000 Tentacool. I named them all Greg."],
    'nature': ["I talk to my Berry plants every day. Yesterday one talked back. It was a Lotad.",
               "Ever eaten a Pecha Berry so fast you saw the future? I have. The future is bad."],
    'battle': ["I trained my Zigzagoon to steal. Now it steals FROM me. Circle of life.",
               "I invented a new kind of battle. It's the same, but everyone's angrier."],
}

# ---- Game of Thrones gossip: how someone changes the subject ------------------------
GOSSIP_LEADS = ['Anyway. Realm news:', 'Oh, and keep this between us:', 'Also, have you heard?',
                'Unrelated, but huge:', "Don't tell anyone I told you this, but:"]

# ---- fake news (added to signs) --------------------------------------------------
NEWS = [
    "LOCAL ZIGZAGOON ELECTED MAYOR. PROMISES MORE ZIGZAGS.",
    "PROFESSOR BIRCH STILL BEING CHASED. DAY 4,012.",
    "SCIENTISTS CONFIRM: MAGIKARP HAS BEEN SPLASHING ON PURPOSE.",
    "MAN FOUND LIVING IN TALL GRASS FOR 30 YEARS. SAYS IT'S FINE.",
    "TEAM AQUA, TEAM MAGMA AGREE TO SPLIT OCEAN AND LAND. NOBODY TELLS SKY.",
    "SLAKING DECLARED MOST PRODUCTIVE EMPLOYEE AT DEVON CORP.",
    "WINGULL CAUGHT RUNNING UNLICENSED TAXI SERVICE.",
    "MYSTERY GIFT REVEALED TO BE MORE MYSTERY.",
    "LAVARIDGE HOT SPRINGS: NOW 40% LAVA.",
    "STUDY: 9 OUT OF 10 YOUNGSTERS STILL LOVE THEIR SHORTS.",
    "LOCAL CHILD BEATS GYM LEADER, OWNS 900 POTIONS. EXPERTS ALARMED.",
    "FORTREE CITY TREEHOUSES RATED SUS BY HOUSING BOARD.",
    "SECRET BASE CRAZE: CITIZENS NOW LIVE INSIDE BUSHES.",
    "ROUTE 113 ASH NOT BAD FOR LUNGS, SAYS MAN MADE OF ASH.",
    "WALLACE HAIR BUDGET EXCEEDS SOOTOPOLIS GDP.",
    "DEWFORD BRAWLERS WIN FIGHT AGAINST CAVE. CAVE DISAGREES.",
    "MOSSDEEP SPACE CENTER LAUNCHES ROCKET. ROCKET COMES BACK, CONFUSED.",
    "SPINDA SPOTS FOUND TO SPELL OUT A MESSAGE. MESSAGE IS RUDE.",
    "MAUVILLE GAME CORNER COMPLAINT: GAMES TOO GAME-Y.",
    "RAYQUAZA SIGHTED. EXPERTS SAY GO INSIDE. EXPERTS ALSO GO INSIDE.",
    "STEVEN STONE ADDS 400TH ROCK TO COLLECTION. RELATIONSHIPS STRUGGLE.",
    "NURSE JOY QUESTIONED ABOUT IDENTICAL COUSINS. REFUSES TO ELABORATE.",
    "SHEDINJA DECLARED LEGALLY ALIVE. BARELY.",
    "PETALBURG DAD SPENDS ANOTHER YEAR AT WORK. KID NOW TALLER.",
    "WEATHER INSTITUTE PREDICTS WEATHER. IS WRONG. IS HAPPY.",
    "ABANDONED SHIP NOT ABANDONED. JUST SHY.",
    "OLDALE TOWN STILL NOT OLD. RESIDENTS DEMAND NAME CHANGE.",
    "LILYCOVE MUSEUM ADDS PAINTING OF A WALL. CRITICS: IT'S GIVING WALL.",
    "MAN WITH 6 ZUBAT IN CAVE SAYS HE'S JUST VIBING.",
    "SLATEPORT MARKET SELLS FAKE DOLLS. REAL DOLLS FURIOUS.",
    "HOENN REPORTS RECORD RAINFALL, ALL OF IT ON ROUTE 119.",
    "POLL: HOENN PREFERS BREAD TO SECRET POWER BY NARROW MARGIN.",
    "LOCAL KID BATTLES EVERYONE, SPEAKS TO NO ONE. HERO OR MENACE?",
    "TEAM MAGMA RECRUITMENT DRIVE OFFERS FREE HOODIES, CAUSES HEATSTROKE.",
    "EVER GRANDE CITY: THE CHAMPION WILL SEE YOU NOW (IN 6-8 WEEKS).",
    "BREAKING: GRASS STILL TALL.",
    "AREA MAN WALKS INTO 40 STRANGERS' HOMES IN ONE DAY. NOBODY CALLS POLICE. HOENN HAS NO POLICE.",
    "STUDY: ROUTE TRAINERS HAVE NOT MOVED IN 20 YEARS. SCIENTISTS AFRAID TO ASK.",
    "POTION PRICES UP 300%. EXPERTS BLAME CHILDREN WITH 900 POTIONS.",
    "MAN STILL WAITING FOR SOMEONE TO MAKE EYE CONTACT SO HE CAN BATTLE. DAY 6.",
    "HM SLAVE INDUSTRY UNDER FIRE. BIBAREL UNION DEMANDS ANSWERS.",
    "LOCAL BIKE SHOP GIVES AWAY FREE BIKE. ECONOMISTS STILL CONFUSED.",
    "POLL: 0% OF HOENN READ THE SIGNS. YOU ARE READING THIS ONE. WEIRD.",
    "CHILD SEEN RUNNING INDOORS WITH SHOES. MOMS ACROSS HOENN SPEECHLESS.",
    "PC STORAGE SYSTEM NOW HOLDS 420 POKéMON. NOBODY KNOWS WHERE THEY PHYSICALLY ARE.",
    "WILD POKéMON ATTACK RATE IN TALL GRASS: 100%. TALL GRASS ATTENDANCE: ALSO 100%.",
]
# Fake news that fits the sign: a Gym sign gets Gym news, and so on.
NEWS_TOPIC = {
    'gym': ["GYM LEADER HAS NOT LEFT GYM IN 9 YEARS. CALLS IT DEDICATION.",
            "GYM PUZZLE DESIGNER ARRESTED. CHARGES: BEING LIKE THIS.",
            "LEADER LOSES TO CHILD, GIVES CHILD A BADGE AND A TM. CHILD WANTS MORE.",
            "GYM GUIDE GIVES SAME ADVICE FOR 30 YEARS. NOBODY HAS EVER LISTENED."],
    'center': ["POKéMON CENTER HEALS FOR FREE. HOSPITALS IN SHAMBLES.",
               "NURSE SAYS WE HOPE TO SEE YOU AGAIN 10,000 TIMES IN ONE DAY. VOICE HOLDS UP."],
    'shop': ["POKé MART STILL ONLY SELLS 12 THINGS. CUSTOMERS STILL BUY ALL 12.",
             "CLERK SAYS IS THERE ANYTHING ELSE I MAY DO FOR YOU. THERE IS NOT."],
    'battle': ["TRAINER TIPS SIGN STILL GIVING TIPS. NOBODY ASKED.",
               "LOCAL KID BATTLES EVERYONE, SPEAKS TO NO ONE. HERO OR MENACE?"],
}


# ---- Mad Libs ----------------------------------------------------------------------
MADLIB_NOUNS = ['house', 'home', 'town', 'city', 'forest', 'road', 'boat', 'ship', 'cave', 'mountain', 'island',
                'dream', 'dreams', 'heart', 'world', 'friend', 'friends', 'brother', 'sister', 'dad', 'mom',
                'grandpa', 'grandma', 'father', 'mother', 'store', 'shop', 'bike', 'Gym', 'girlfriend', 'boyfriend',
                'secret', 'treasure', 'tower', 'beach', 'route', 'family', 'child', 'kid', 'man', 'woman',
                'person', 'people', 'life']
MADLIB_FILL = ['haunted toaster', 'emotional support Wailord', 'cursed spoon', 'tax return', 'damp sandwich',
               'secret third cousin', 'ex-roommate', 'mortgage', 'sentient bush', 'cardboard throne', 'Magikarp lawyer',
               'business plan', 'garden gnome', 'timeshare', 'jar of mayonnaise', 'side hustle', 'beef jerky statue',
               'midlife crisis', 'karaoke machine', 'wet sock', 'conspiracy board', 'nemesis', 'pyramid scheme',
               'Slakoth in a trenchcoat', 'podcast', 'crypto wallet', 'cursed VHS tape', 'suitcase of regrets',
               'weird extra toe', 'hot tub', 'raccoon gang', 'divorce lawyer', 'decorative sword']

# ---- modern slang ------------------------------------------------------------------
SLANG_WORDS = {
    'very': 'lowkey', 'really': 'fr', 'good': 'bussin', 'great': 'goated', 'cool': 'drippy', 'amazing': 'goated',
    'awesome': 'goated', 'strong': 'cracked', 'stronger': 'more cracked', 'strongest': 'most cracked', 'weak': 'mid',
    'friend': 'bestie', 'friends': 'besties', 'angry': 'pressed', 'mad': 'pressed', 'lying': 'capping',
    'cute': 'adorbs', 'suspicious': 'sus', 'strange': 'sus', 'weird': 'sus', 'talk': 'yap',
    'talking': 'yapping', 'boring': 'mid', 'impressive': 'built different', 'excited': 'hyped', 
    
    'serious': 'deadass', 'seriously': 'deadass', 'tired': 'cooked', 'finished': 'cooked',
    'charm': 'rizz', 'charming': 'rizzy',
    'Hello': 'Yo', 'Hi': 'Ayo', 'Yes': 'Bet', 'Wow': 'Sheesh', 'Oh': 'Bruh', 'Hey': 'Ayo',
}
# Said at the end of someone's line. The ones for battles fit who is winning.
SLANG_TAGS = ['No cap.', 'Fr fr.', 'Respectfully.', 'Say less.', 'That is so real.', 'Just saying.', 'Periodt.',
              'Lowkey.', "And that's on everything.", 'Hits different.', 'Not me being honest rn.', 'Deadass.']
SLANG_BATTLE = {
    'intro': ["Let's get it.", "It's on, bestie.", 'Prepare to get cooked.', 'Run it.', 'No cap.',
              "You're about to take the L."],
    'defeat': ["I'm cooked.", 'Big L.', 'Down bad.', 'This is so not bussin.', 'I fumbled.', 'Rip bozo. Me. I\'m bozo.'],
    'after': ['Still cooked btw.', "I'm healing.", "We don't talk about it.", 'Respectfully, rematch.'],
}

# ---- mood ring speech styles (one per town/route) ----------------------------------
STYLES = {
    'pirate': {
        'label': 'Pirate',
        'words': {'you': 'ye', 'your': 'yer', 'my': 'me', 'is': 'be', 'are': 'be', 'Hello': 'Ahoy', 'Hi': 'Ahoy',
                  'yes': 'aye', 'Yes': 'Aye', 'friend': 'matey', 'friends': 'mateys', 'money': 'doubloons',
                  'treasure': 'booty', 'stop': 'avast', 'boy': 'lad', 'girl': 'lass', 'the sea': 'the briny deep',
                  'Hey': 'Oi', 'there': 'thar'},
        'open': ['Arr!', 'Yo ho!', 'Shiver me timbers!', 'Avast!'],
        'close': ['Arr.', 'Yarr.', 'Walk the plank, ye scallywag.', 'Savvy.'],
    },
    'genz': {
        'label': 'Gen Z',
        'words': SLANG_WORDS,
        'open': ['Bro.', 'Ngl,', 'Okay so like,', 'Bestie,'],
        'close': SLANG_TAGS,
    },
    'shakespeare': {
        'label': 'Shakespeare',
        'words': {'you': 'thou', 'your': 'thy', 'you are': 'thou art', 'are you': 'art thou', 'Yes': 'Aye',
                  'Hello': 'Good morrow', 'Hi': 'Hail', 'Hey': 'Hark', 'before': 'ere', 'often': 'oft',
                  'does': 'doth', 'has': 'hath', 'do you': 'dost thou', 'you do': 'thou dost', 'have you': 'hast thou',
                  'you have': 'thou hast', 'you will': 'thou wilt', 'you would': 'thou wouldst', 'you can': 'thou canst',
                  'can you': 'canst thou', 'you may': 'thou mayst', 'will you': 'wilt thou', 'would you': 'wouldst thou',
                  "you're": 'thou art', "you've": 'thou hast', "you'd": 'thou wouldst', "you'll": 'thou wilt',
                  'why': 'wherefore'},
        'open': ['Hark!', 'Forsooth,', 'Prithee, listen.', 'Alas!'],
        'close': ['Verily.', 'Huzzah.', 'Fare thee well.', 'Such is the tragedy of Hoenn.'],
    },
    'corporate': {
        'label': 'Corporate',
        'words': {'problem': 'challenge', 'problems': 'challenges', 'help': 'support', 'fight': 'alignment meeting', 'talk': 'circle back', 'idea': 'value-add',
                  'friend': 'stakeholder', 'friends': 'stakeholders', 'money': 'budget', 'win': 'deliver',
                  'lose': 'miss targets', 'POKéMON': 'assets', 'Trainer': 'associate',
                  'TRAINER': 'ASSOCIATE', 'goal': 'KPI', 'dream': 'roadmap'},
        'open': ['Per my last message,', 'Quick sync:', 'Just looping you in:', 'Hope this finds you well.'],
        'close': ["Let's take this offline.", 'Thanks in advance.', 'Circling back later.', 'Per HR, this is fine.'],
    },
    'conspiracy': {
        'label': 'Conspiracy theorist',
        'words': {'bird': 'drone', 'birds': 'drones', 'Wingull': 'Wingull (drone)', 'Professor': 'so-called Professor',
                  'truth': 'TRUTH', 'they': 'THEY', 'government': 'Elite Four'},
        'open': ['Wake up.', "Don't tell anyone, but", 'Listen closely.', 'They are listening, so quickly:'],
        'close': ['Do your own research.', 'The Wingulls are drones.', 'Birch knows.', "It's all connected.",
                  'Follow the Berries.', 'Rayquaza is a weather balloon.'],
    },
    'noir': {
        'label': 'Detective noir',
        'words': {'town': 'rotten little town', 'city': 'city of broken dreams', 'kid': 'gumshoe',
                  'girl': 'dame', 'boy': 'kid', 'money': 'dough', 'police': 'the bulls'},
        'open': ['Listen, kid.', "I've seen things, kid.", 'Another day, another Zigzagoon.',
                 'The rain never stops around here.'],
        'close': ['Hoenn never sleeps.', "That's how it goes in this business.", 'Trust no one, kid.',
                  'The rain kept falling.'],
    },
    'surfer': {
        'label': 'Surfer',
        'words': {'very': 'totally', 'really': 'radically', 'good': 'gnarly', 'great': 'tubular', 'friend': 'bro',
                  'friends': 'bros', 'man': 'brah', 'cool': 'rad', 'scary': 'heavy', 'Hello': 'Duuude', 'Hi': 'Sup'},
        'open': ['Duuude.', 'Whoa.', 'Brah.', 'Cowabunga.'],
        'close': ['Hang ten.', 'Totally.', "Catch ya on the next wave.", 'Stay salty.'],
    },
    'dramatic': {
        'label': 'Soap opera',
        'words': {'friend': 'secret twin', 'mom': 'birth mother', 'dad': 'estranged father', 'brother': 'evil brother',
                  'sister': 'secret sister'},
        'open': ['GASP!', 'Oh, the drama!', 'Brace yourself.'],
        'close': ['Dun dun DUNNN.', 'To be continued.', 'Cue the dramatic music.', 'Nobody move.'],
    },
}

# ---- battle messages (src/battle_message.c) -------------------------------------
# Original text -> funny versions. The game wraps battle text by itself; every
# {CODE} from the original is kept.
BATTLE = {
    'You encountered a wild {B_OPPONENT_MON1_NAME}!\\p': [
        'A wild {B_OPPONENT_MON1_NAME} appeared! It looks like it owes you money.\\p',
        'A wild {B_OPPONENT_MON1_NAME} jumped out of the bushes like it pays rent there.\\p',
        'A wild {B_OPPONENT_MON1_NAME} appeared! It has chosen violence.\\p',
    ],
    'Oh! A wild {B_OPPONENT_MON1_NAME} and {B_OPPONENT_MON2_NAME} appeared!\\p': [
        'A wild {B_OPPONENT_MON1_NAME} and {B_OPPONENT_MON2_NAME} appeared! They brought backup. Rude.\\p',
    ],
    'You are challenged by {B_TRAINER1_NAME_WITH_CLASS}!\\p': [
        '{B_TRAINER1_NAME_WITH_CLASS} wants to fight! Nobody asked them to.\\p',
        '{B_TRAINER1_NAME_WITH_CLASS} locked eyes with you. Now it is legally binding.\\p',
        '{B_TRAINER1_NAME_WITH_CLASS} has been waiting all day for this. All. Day.\\p',
    ],
    '{PLAY_SE SE_FLEE}You got away safely!\\p': [
        '{PLAY_SE SE_FLEE}You ran away. Coward. (Safely, though.)\\p',
        '{PLAY_SE SE_FLEE}You got away! The tall grass will remember this.\\p',
    ],
    'Go! {B_PLAYER_MON1_NAME}!': ['Go! {B_PLAYER_MON1_NAME}! Do crimes!', 'Go! {B_PLAYER_MON1_NAME}! Make Mom proud!',
                                  'Go! {B_PLAYER_MON1_NAME}! Remember the plan! There is no plan!'],
    '{B_BUFF1}, come back!': ['{B_BUFF1}, come back! You are embarrassing me!', '{B_BUFF1}, get back in the ball. We will talk later.'],
    'Good job, {B_BUFF1}! Come back!': ['Good job, {B_BUFF1}! Come back! Snacks are in the ball!'],
    '{B_BUFF1} gained{B_BUFF2} {B_BUFF3} Exp. Points!\\p': [
        '{B_BUFF1} gained{B_BUFF2} {B_BUFF3} Exp. Points! Character development!\\p',
        '{B_BUFF1} gained{B_BUFF2} {B_BUFF3} Exp. Points and a little bit of trauma!\\p',
    ],
    '{B_BUFF1} grew to Lv. {B_BUFF2}!{WAIT_SE}\\p': [
        '{B_BUFF1} grew to Lv. {B_BUFF2}! Puberty hits different.{WAIT_SE}\\p',
        '{B_BUFF1} grew to Lv. {B_BUFF2}! The aura is growing.{WAIT_SE}\\p',
    ],
    '{B_BUFF1} learned {B_BUFF2}!{WAIT_SE}\\p': ['{B_BUFF1} learned {B_BUFF2}! It watched one tutorial online.{WAIT_SE}\\p'],
    '{B_SCR_NAME_WITH_PREFIX} fainted!\\p': [
        '{B_SCR_NAME_WITH_PREFIX} fainted! Dramatically!\\p',
        '{B_SCR_NAME_WITH_PREFIX} fainted! Somebody call its mom.\\p',
        '{B_SCR_NAME_WITH_PREFIX} has left the chat.\\p',
    ],
    'It doesn\'t affect {B_DEF_NAME_WITH_PREFIX2}…': ['It doesn\'t affect {B_DEF_NAME_WITH_PREFIX2}… Awkward.'],
    'A critical hit!': ['A critical hit! Emotional damage!', 'A critical hit! That one was personal!'],
    'It\'s not very effective…': ['It\'s not very effective… That was mid.', 'It\'s not very effective… Embarrassing, honestly.'],
    'It\'s super effective!': ['It\'s super effective! Absolutely cooked!', 'It\'s super effective! Somebody check on them!'],
    'You can\'t escape!\\p': ['You can\'t escape! This is your life now!\\p'],
    'Oh no! The Pokémon broke free!': ['Oh no! The Pokémon broke free! It has trust issues.'],
    'Gotcha! {B_DEF_NAME} was caught!{WAIT_SE}{PLAY_BGM MUS_CAUGHT}\\p': [
        'Gotcha! {B_DEF_NAME} was caught! It did not read the terms and conditions.{WAIT_SE}{PLAY_BGM MUS_CAUGHT}\\p',
    ],
    'You got ¥{B_BUFF1} for winning!\\p': ['You took ¥{B_BUFF1} from a stranger for winning. Normal Hoenn stuff.\\p'],
    'You have no more Pokémon that can fight!\\p': ['You have no more Pokémon that can fight! Skill issue.\\p'],
}

# ---- Game of Thrones storyline ------------------------------------------------------
# Gossip follows your progress: one chapter per badge, so people only talk
# about what has already happened. 0: no badges. 1: Roxanne. 2: Brawly.
# 3: Wattson. 4: Flannery. 5: Norman. 6: Winona. 7: Tate & Liza. 8: Juan.
# 9: Champion.
THRONES_CHAPTERS = [
    [  # 0 - nobody yet
        "Eight Great Houses hold the Gyms of Hoenn. Each one swears loyalty to the Poké Ball Throne at Ever Grande. Each one is lying.",
        "Lord Maxie claims the land. Lord Archie claims the sea. Both claims were written on napkins.",
        "The Throne sits empty half the year. Wallace keeps leaving to get his hair done.",
        "House Stone runs Devon, the banks, and the rocks. Mostly the rocks. Never insult a rock in Rustboro.",
        "The Small Council rules Hoenn. It's four Gym Leaders and a Slakoth. The Slakoth has the most power. Nobody knows how.",
        "Whoever wins all eight badges may challenge for the Throne. Nobody's done it in years. Mostly because of the paperwork.",
        "Some kid from Littleroot just got a POKéMON from Professor Birch. The lords don't care. Lords never care about kids. Until they do.",
    ],
    [  # 1 - Roxanne
        "Word from Rustboro: a kid from Littleroot beat Lady Roxanne. House Stone says it isn't worried. House Stone is buying a lot of rocks.",
        "They're calling you the Littleroot Pretender, {PLAYER}. It isn't a compliment. It isn't NOT a compliment.",
        "Brawly of Dewford heard about you. He's been punching the ocean to get ready. The ocean is winning.",
        "Lord Maxie sent spies to watch the Pretender. They wear bright red hoodies. Stealth is not the brand.",
        "Somebody painted LONG LIVE THE PRETENDER on a fence in Petalburg. Somebody else painted WHO? under it.",
        "The Small Council met about you. The Slakoth took notes. The notes are a drawing of a Slakoth.",
    ],
    [  # 2 - Brawly
        "Two badges. Brawly says he went easy on you. His Makuhita says otherwise. His Makuhita has never lied.",
        "Team Aqua tried to rob the Slateport Museum. The plan was to walk in. That's it. That was the plan.",
        "Steven Stone, heir of House Stone, got a letter in a cave. He wrote back one word: rocks.",
        "Lord Wattson of Mauville runs the power grid. He swears the Pretender will never take his badge. Then he laughed for six minutes.",
        "Archie's sailors mutiny every Tuesday. He calls it team building.",
        "The bards are writing songs about you, {PLAYER}. They don't know your name. They rhymed Pretender with blender.",
    ],
    [  # 3 - Wattson
        "The lights in Mauville went out the day you beat Wattson. He says that's unrelated. He's been laughing about it nervously ever since.",
        "Three badges. The lords stopped calling you the Pretender. Now they call you That Problem.",
        "Lord Maxie is marching his army up Mt. Chimney. Nobody knows why. Nobody has ever known why, with Maxie.",
        "Lady Flannery of House Lavaridge just inherited her Gym. She's been practicing her scary voice. It's going okay.",
        "A Swablu from Fortree brought a message: Winona is watching. Then it pooped on my roof. Message received.",
        "House Petalburg has gone very quiet. Lord Norman knows who's coming for his seat. Family dinners are about to get tense.",
    ],
    [  # 4 - Flannery
        "They're calling Mt. Chimney the Ash Wedding. Nobody got married. Everybody got ash in their shoes.",
        "Lady Flannery lost a badge in her first month on the job. She's taking it well. By that I mean the Gym is on fire.",
        "Four badges. Next on the road is Petalburg. You know who's in Petalburg. Bring a card. Maybe flowers.",
        "Maxie and Archie both offered you an alliance. You said no. Correctly. Their benefits package is terrible.",
        "The Small Council voted to stop you. Three votes yes, one vote no. The Slakoth abstained by being asleep.",
        "There's a betting pool on the Pretender versus Petalburg. The odds are terrible. For your dad.",
    ],
    [  # 5 - Norman
        "You beat your own father in his own hall. The whole realm is talking. Mostly about how awkward dinner is going to be.",
        "Lord Norman sent a raven: I'm proud of you. Also, you're grounded. Both are binding by law.",
        "Five badges, {PLAYER}. They call this stretch the Usurper's Road now. The tourism board loves it.",
        "Team Aqua is circling the Weather Institute. If they control the weather it rains forever. Route 119 won't even notice.",
        "Lady Winona of the High Skies has heard of you. She hasn't decided if that's good. Her birds have decided it's bad.",
        "Wally from Petalburg has been training. Nobody's worried about Wally. Somebody should be worried about Wally.",
    ],
    [  # 6 - Winona
        "Lady Winona has declared for you. Her house words are: Our Wings Are Higher. It's mostly a threat.",
        "Six badges. The Kingsguard of the Elite Four started looking up your stats. One of them made a spreadsheet.",
        "Team Magma and Team Aqua are both heading for Mt. Pyre. It's a graveyard. Nothing good ever started in a graveyard.",
        "The old gods sleep beneath Hoenn. One in the sea, one in the land, one in the sky. Maxie and Archie keep trying to wake them like it's a sleepover.",
        "The Twin House of Mossdeep has a succession crisis. Tate says he's the heir. Liza says she's the heir. The house cat is acting regent.",
        "Lilycove's department store has five floors and no exit strategy. That's not political. I just think about it a lot.",
    ],
    [  # 7 - Tate & Liza
        "You beat both Mossdeep heirs at once. The succession crisis is over. The house cat is still regent. Nobody wants to tell it.",
        "Maxie really did wake Groudon. It ran off. Now Archie wants Kyogre. Two grown men are about to ruin the weather for everyone.",
        "Seven badges, {PLAYER}. Every lord in Hoenn has your poster up. Half of them are dartboards.",
        "Steven Stone is back from the rock wilderness. He supports your claim. He also has 400 rocks to show you.",
        "Lord Juan of Sootopolis says beauty is a weapon. He's very calm about it. Too calm.",
        "The Small Council called an emergency meeting about the gods. The Slakoth came. First time anyone's seen it move.",
    ],
    [  # 8 - Juan
        "Eight badges. By the ancient law you may now march on Ever Grande. Bring snacks. Victory Road is long and full of rude people.",
        "Rayquaza came down from the sky and told Groudon and Kyogre to knock it off. Like a parent. It was humiliating for everyone.",
        "Maxie and Archie lost everything, and now they're kind of friends? They get lunch. The realm is confused.",
        "Lord Juan lost to you and called it beautiful. He calls everything beautiful. He called his parking ticket beautiful.",
        "The Kingsguard are sharpening their POKéMON. Sidney says he isn't scared. He's scared.",
        "Wallace has been practicing his I-am-not-nervous face in the mirror. The mirror is nervous.",
    ],
    [  # 9 - Champion
        "All hail {PLAYER}, First of Their Name, Champion of Hoenn, Breaker of Gyms, Haver of Way Too Many Potions.",
        "Wallace bent the knee. Then he asked if you'd seen his comb. It's in your bag, {PLAYER}. Give it back.",
        "The Small Council is yours now. It's still four Gym Leaders and a Slakoth. The Slakoth got a raise.",
        "House Petalburg is the most powerful house in the realm. Lord Norman is unbearable about it at the grocery store.",
        "Every lord in Hoenn wants a favor from the new Champion. Roxanne wants her homework due dates moved.",
        "Uneasy lies the head that wears the cap. You're going to need a bigger cap.",
    ],
]
THRONES_LEADER_LINES = {
    'ROXANNE': ("I am Roxanne of House Rustboro, sworn to House Stone. Our words are: We Did The Reading.",
                "You beat me, so by law my rocks are... still mine. But my respect is yours. Mostly."),
    'BRAWLY': ("I'm Brawly of the Dewford Tide! Our words are: Hit First, Ask Never!",
               "The Tide pledges its fists to you, little ruler. Don't make it weird."),
    'WATTSON': ("Wahahaha! House Wattson keeps the lights on in Mauville! Our words: The Bills Are Paid!",
                "My house yields! Do NOT tell the power company."),
    'FLANNERY': ("I'm Flannery of House Lavaridge, and I've been a lady for one week! Our words: The Floor Is Lava!",
                 "My grandfather would have beaten you. Probably. He's in a hot spring. Don't wake him."),
    'NORMAN': ("You've come for the seat of House Petalburg, my own child? Our words are: Family Is Complicated.",
               "...Fine. You win the seat. You're still doing the dishes, by order of the head of the household."),
    'WINONA': ("I am Winona of the High Skies. Our words are: Our Wings Are Higher. Kneel, or be pooped on.",
               "The High Skies declare for you. Our birds will follow your banners. And your hat."),
    'TATE': ("We are the Twin House of Mossdeep! Our words are: Two Heirs, No Answers!",
             "We both lose... equally. That's the most fair thing that has ever happened in this family."),
    'JUAN': ("I am Juan of House Sootopolis. Our words: Beauty Is A Weapon. Prepare to be... beautified.",
             "You have won all eight banners. Ever Grande awaits you. Do something about your hair first."),
    'SIDNEY': ("", "Fine, Kingsguard steps aside. Don't tell the others I liked you."),
    'PHOEBE': ("", "The ghosts of the old kings approve of you. They want you to know they're watching. Always."),
    'GLACIA': ("", "Cold is the throne, little ruler. Cold, and very uncomfortable. Bring a cushion."),
    'DRAKE': ("", "The last of the Kingsguard falls! Go on. The Champion is waiting, and he's nervous."),
    'WALLACE': ("So the Usurper finally comes to the Poké Ball Throne. Our words: Fabulous Until The End.",
                "The Throne is yours. It has a squeaky leg. I never told anyone. Now it's your problem."),
    'MAXIE': ("I am Maxie, rightful Lord of the Land! The seas will dry, the realm will kneel, and you will move!",
              "My claim... is dust. Literally. There's dust everywhere. I need a nap."),
    'ARCHIE': ("I'm Archie, true Lord of the Sea! Every drop of water bows to me! Except the drinking fountain.",
               "Ahoy... the sea rejects my claim. Probably because I never asked it."),
    'TABITHA': ("For Lord Maxie and the Land! Also for the dental plan.", "I'll be demoted to Lord of a Small Rock for this."),
    'SHELLY': ("For Lord Archie and the Sea! Hand over your lunch money in his name!", "Archie's going to make me swab the deck again."),
    'MATT': ("Hah! Lord Archie's sworn shield stands before you! Hah!", "Hah... my shield has a hole in it."),
    'COURTNEY': ("...Lord Maxie's will. ...Analyzing. ...You are a threat. ...Fun.", "...Recalculating my loyalty. ...Recalculating."),
}


# ---- in-game Mad Libs: lines built around the player's own words --------------------
# {MADLIB_...} blanks show the words the player picked in the game. Never put 'a' or 'an'
# right before a blank: the word could start with any letter.
MADLIB_LINES = {
    'hero': {
        'talk': ["{PLAYER}: Cool story. Has anyone seen my {MADLIB_CLOTHING}? I left it at the {MADLIB_PLACE}.",
                 "{PLAYER}: I'd trade every badge I own for the last {MADLIB_FOOD} at the food court.",
                 "{PLAYER}: That's the most {MADLIB_ADJ} thing I've heard since {MADLIB_NAME} fell into the {MADLIB_PLACE}.",
                 "{PLAYER}: {MADLIB_SHOUT}. I need to go sit in the {MADLIB_PLACE} and think about that.",
                 "{PLAYER}: Hearing that made my {MADLIB_BODYPART} feel {MADLIB_FEELING}.",
                 "{PLAYER}: Okay, but have you tried {MADLIB_ACTIVITY}? Changed my life.",
                 "{PLAYER}: You sound exactly like my {MADLIB_PERSON}. That's not a compliment."],
        'thing': ["{PLAYER}: Still no {MADLIB_THING}. The search continues.",
                  "{PLAYER}: Smells like {MADLIB_DRINK} over here. Why does everything smell like {MADLIB_DRINK}?",
                  "{PLAYER}: I was hoping to find my {MADLIB_CREATURE} back here."],
        'intro': ["{PLAYER}: Fine. Loser has to say {MADLIB_SOUND} in front of everyone.",
                  "{PLAYER}: My {MADLIB_CREATURE} could beat you, and it's not even here.",
                  "{PLAYER}: Bold move, challenging someone in this {MADLIB_CLOTHING}."],
        'defeat': ["{PLAYER}: {MADLIB_SHOUT}! Go cry to {MADLIB_NAME} about it.",
                   "{PLAYER}: I'm celebrating with some {MADLIB_DRINK}. You're not invited.",
                   "{PLAYER}: That was {MADLIB_ADJ}. For you, I mean. I was great."],
        'after': ["{PLAYER}: Still {MADLIB_FEELING} about losing? Go eat the {MADLIB_FOOD} you brought. Feel better.",
                  "{PLAYER}: You lost to me AND you smell like {MADLIB_DRINK}. Rough week."],
    },
    'narrator': {
        'talk': ["(Narrator: Somewhere, {MADLIB_NAME} was {MADLIB_ACTIVITY} in the {MADLIB_PLACE}.)",
                 "(Narrator: Their {MADLIB_BODYPART} twitched. That meant they were {MADLIB_FEELING}.)",
                 "(Narrator: Nobody mentioned the {MADLIB_CREATURE} wearing the {MADLIB_CLOTHING}. Nobody ever does.)",
                 "(Narrator: This conversation was brought to you by the {MADLIB_FOOD} industry.)",
                 "(Narrator: In the distance, someone yelled {MADLIB_SHOUT}. It felt right.)"],
        'thing': ["(Narrator: It smelled faintly like the {MADLIB_FOOD} from last week.)",
                  "(Narrator: It was painted {MADLIB_COLOR}. Nobody knows who did that.)",
                  "(Narrator: A single {MADLIB_SOUND} echoed. Then nothing.)"],
        'intro': ["(Narrator: The battle music was briefly replaced by {MADLIB_SOUND}.)",
                  "(Narrator: They had trained for this by {MADLIB_ACTIVITY}. It would not be enough.)"],
        'defeat': ["(Narrator: They left on their {MADLIB_VEHICLE}. Emotionally.)",
                   "(Narrator: Their {MADLIB_BODYPART} would never be the same.)"],
        'after': ["(Narrator: They had spent their prize money on {MADLIB_DRINK}.)"],
    },
    'chaos': ["My {MADLIB_CREATURE}, {MADLIB_NAME}, runs the {MADLIB_PLACE} now. I just work there.",
              "I keep {MADLIB_DRINK} in my {MADLIB_CLOTHING}. For emergencies.",
              "Every night I hear {MADLIB_SOUND} from the {MADLIB_PLACE}. Every night it gets closer.",
              "{MADLIB_SHOUT}! Sorry. I do that whenever I think about the {MADLIB_FOOD} I dropped in 2019.",
              "I've been {MADLIB_ACTIVITY} since sunrise. My {MADLIB_BODYPART} is gone. I feel {MADLIB_FEELING}.",
              "I'm saving up for my own {MADLIB_VEHICLE}. Painted {MADLIB_COLOR}. Don't laugh.",
              "My cousin quit being a Trainer. Now they're the {MADLIB_PERSON} at the {MADLIB_PLACE}.",
              "Some {MADLIB_PERSON} sold me this {MADLIB_THING}. It doesn't do anything. I love it."],
}
MADLIB_LINES['narrator']['house'] = MADLIB_LINES['narrator']['talk']
MADLIB_LINES['hero']['house'] = MADLIB_LINES['hero']['talk']
