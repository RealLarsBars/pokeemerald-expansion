"""In-game Mad Libs: the player fills in 16 blanks from menus inside the game.

Dialogue shows a blank as a code like {MADLIB_FOOD}; the game prints the word
the player picked for it (GetMadLibWord in src/string_util.c). Picks are kept in
16 save variables, so they last all game. The player fills them in at the start
and, after each badge, can keep them or pick new ones.

This file holds the blanks and their word lists, writes the game files that
use them (src/data/mad_libs.h, data/scripts/mad_libs.inc) and knows which words
in normal dialogue a blank can stand in for."""

import os
import re

from common import ROOT

HEADER = 'src/data/mad_libs.h'
SCRIPT = 'data/scripts/mad_libs.inc'

# key, what the menu asks for, words (max 14 letters so the menu fits;
# only characters the game's font has).
SLOTS = [
    ('THING', 'a THING', [
        'rizz', 'side quest', 'burrito', 'mixtape', 'group chat', 'podcast', 'fanny pack', 'hot tub', 'beanbag chair',
        'fidget spinner', 'NFT', 'gold star', 'ring light', 'air fryer', 'lava lamp', 'vision board', 'stress ball',
        'karaoke mic', 'rubber duck', 'crypto wallet']),
    ('PLACE', 'a PLACE', [
        'food court', 'basement', 'swamp', 'laundromat', 'bouncy castle', 'skate park', 'gas station', 'parking lot',
        'Discord server', 'escape room', 'ball pit', 'airport', 'DMV', 'water park', 'mall', 'backrooms',
        'dentist office', 'thrift store', 'arcade', 'drive-thru']),
    ('ADJ', 'a DESCRIBING WORD', [
        'unhinged', 'feral', 'soggy', 'bussin', 'mid', 'sus', 'cursed', 'delulu', 'goated', 'crusty', 'moist',
        'chaotic', 'iconic', 'cringe', 'extra', 'based', 'salty', 'sketchy', 'crunchy', 'spicy']),
    ('SHOUT', 'something to SHOUT', [
        'Sheesh', 'Bruh', 'Yeehaw', 'Holy moly', 'Good grief', 'Bazinga', 'Oh my Arceus', 'Big yikes', 'Slay',
        'Let him cook', 'No way', 'Ayo', 'Skibidi', 'Cowabunga', 'Bonjour', 'Hot dog', 'Jeepers', 'Gadzooks',
        'Mamma mia', 'Oh snap']),
    ('FOOD', 'a FOOD', [
        'chicken nugget', 'avocado toast', 'chili dog', 'ramen', 'corn dog', 'boba', 'taco', 'pickle', 'mystery meat',
        'pizza roll', 'cereal', 'spaghetti', 'burrito bowl', 'cheese puff', 'mac and cheese', 'burnt toast',
        'hot sauce', 'sourdough', 'noodle cup', 'meatball']),
    ('DRINK', 'a DRINK', [
        'energy drink', 'oat milk latte', 'pickle juice', 'warm soda', 'protein shake', 'iced coffee', 'swamp water',
        'kombucha', 'tap water', 'bubble tea', 'chocolate milk', 'lemonade', 'slushie', 'hot cocoa', 'smoothie',
        'gravy', 'root beer', 'seltzer', 'orange juice', 'sweet tea']),
    ('PERSON', 'a KIND OF PERSON', [
        'influencer', 'life coach', 'podcaster', 'mall cop', 'crypto bro', 'streamer', 'theater kid', 'HOA president',
        'landlord', 'gym bro', 'substitute', 'lifeguard', 'middle manager', 'vlogger', 'DJ', 'magician', 'barista',
        'cowboy', 'mime', 'tour guide']),
    ('BODYPART', 'a BODY PART', [
        'left elbow', 'pinky toe', 'eyebrow', 'kneecap', 'belly button', 'armpit', 'forehead', 'earlobe', 'spine',
        'nostril', 'funny bone', 'chin', 'ankle', 'big toe', 'shoulder blade', 'knuckle', 'uvula', 'eyelid', 'tongue',
        'back molar']),
    ('ACTIVITY', 'an ACTIVITY (-ing)', [
        'yodeling', 'doomscrolling', 'mewing', 'napping', 'gatekeeping', 'yapping', 'speedrunning', 'moonwalking',
        'manifesting', 'vibing', 'jazzercising', 'tap dancing', 'beatboxing', 'ghosting', 'glazing', 'crying',
        'flossing', 'rage quitting', 'cosplaying', 'meal prepping']),
    ('FEELING', 'a FEELING', [
        'unwell', 'so seen', 'hangry', 'shook', 'big mad', 'lowkey sad', 'at peace', 'cooked', 'blessed', 'unbothered',
        'spooked', 'emotional', 'giddy', 'betrayed', 'sleepy', 'chill', 'pressed', 'crushed', 'smug', 'confused']),
    ('VEHICLE', 'a VEHICLE', [
        'shopping cart', 'scooter', 'unicycle', 'monster truck', 'party bus', 'hoverboard', 'golf cart', 'tractor',
        'canoe', 'school bus', 'pogo stick', 'jet ski', 'blimp', 'tricycle', 'go-kart', 'food truck', 'wheelbarrow',
        'roller skate', 'limo', 'rowboat']),
    ('CLOTHING', 'something to WEAR', [
        'foam clog', 'fedora', 'cowboy hat', 'onesie', 'tutu', 'beanie', 'hoodie', 'cape', 'toga', 'bucket hat',
        'crop top', 'tracksuit', 'tiara', 'bow tie', 'sombrero', 'trench coat', 'ugly sweater', 'lucky sock',
        'bathrobe', 'tuxedo']),
    ('CREATURE', 'an ANIMAL', [
        'raccoon', 'goose', 'possum', 'capybara', 'axolotl', 'frog', 'llama', 'hamster', 'pigeon', 'seagull',
        'squirrel', 'goat', 'sloth', 'corgi', 'ferret', 'crab', 'alpaca', 'moth', 'duck', 'hedgehog']),
    ('NAME', 'a NAME', [
        'Kevin', 'Big Steve', 'Grandma Linda', 'Brenda', 'Chad', 'Lil Nugget', 'Doug', 'Gary', 'Sir Reginald',
        'Uncle Rick', 'DJ Toast', 'Barbara', 'Todd', 'Coach Dave', 'Becky', 'Mr. Pickles', 'Tiffany', 'Gerald',
        'Aunt Deb', 'Captain Bob']),
    ('SOUND', 'a SOUND', [
        'bonk', 'vine boom', 'honk', 'oof', 'yeet', 'boing', 'skrrt', 'kaboom', 'beep boop', 'sad trombone',
        'womp womp', 'ding', 'splat', 'bloop', 'airhorn', 'kazoo', 'quack', 'pew pew', 'ka-ching', 'dun dun dun']),
    ('COLOR', 'a COLOR', [
        'beige', 'neon green', 'hot pink', 'salmon', 'mustard', 'teal', 'chartreuse', 'ketchup red', 'glitter', 'lime',
        'lavender', 'sky blue', 'burnt orange', 'gold', 'camo', 'rainbow', 'periwinkle', 'maroon', 'mint', 'tie-dye']),
]
WORD_COUNT = 20  # words per blank (the game keeps up to 30), plus Surprise me!
# Four blanks get another word after each Gym, so every blank ends up with 3 words.
BADGE_SLOTS = [['THING', 'PLACE', 'FOOD', 'NAME'], ['ADJ', 'SHOUT', 'PERSON', 'SOUND'],
               ['DRINK', 'BODYPART', 'ACTIVITY', 'FEELING'], ['VEHICLE', 'CLOTHING', 'CREATURE', 'COLOR']] * 2
FIRST_CODE = 0x0F  # {MADLIB_THING} is FD 0F in charmap.txt, the next blank FD 10, ...


def code(key):
    return '{MADLIB_%s}' % key


def var_name(key):
    return 'VAR_MADLIB_%s' % key


# ---- where blanks go in normal dialogue --------------------------------------------
# Nouns are only swapped right after one of these, so 'my hat' -> 'my {MADLIB_CLOTHING}'
# always reads right, whatever word was picked (no 'a'/'an' to get wrong).
NOUN_AFTER = r'(?:the|The|my|My|your|Your|our|Our|their|Their|his|His|her|Her|this|This)'
NOUNS = {
    'PLACE': 'house home town city forest cave mountain island beach tower store shop village',
    'FOOD': 'lunch dinner breakfast snack food meal cake cookie sandwich candy',
    'DRINK': 'tea coffee juice soda milk',
    'PERSON': 'man woman guy lady person kid boy girl gentleman',
    'BODYPART': 'heart head face hair hand back',
    'VEHICLE': 'boat ship bike car truck ferry bicycle',
    'CLOTHING': 'hat shirt cap dress jacket outfit clothes',
    'CREATURE': 'dog cat bird puppy kitty pet',
    'THING': 'secret treasure dream gift present prize plan idea stuff thing',
}
# Words swapped anywhere (lowercase only), unless right after 'a' or 'an'.
WORDS = {
    'ADJ': 'strong tough cool cute great amazing wonderful beautiful scary weird nice pretty awesome incredible '
           'powerful impressive fantastic terrific',
    'FEELING': 'happy sad angry scared excited nervous lonely bored worried glad',
    'ACTIVITY': 'training battling fishing swimming walking running cycling dancing shopping hiking sleeping '
                'exploring studying singing',
    'COLOR': 'red blue green yellow pink black white purple brown',
}
# 'running the TOWER' is a verb with an object, not an activity: leave those alone.
OBJECTS = r'(?!\s+(?:the|my|your|a|an|it|them|him|her|this|that|these|those|POKéMON|[A-Z]{2,})\b)'
SHOUTS = r'(?:Wow|Whoa|Whoah|Oh|Yay|Hooray|Gosh|Wahahaha|Hey)'


def fill_blanks(text, rng, chance, limit=2):
    """Put up to `limit` blanks into one box of dialogue."""
    done = 0
    spots = []
    for key, words in NOUNS.items():
        for m in re.finditer(r'(?<![\w{-])%s (%s)(?![\w}-])' % (NOUN_AFTER, '|'.join(words.split())), text):
            spots.append((m.start(1), m.end(1), code(key)))
    for key, words in WORDS.items():
        after = OBJECTS if key == 'ACTIVITY' else ''
        for m in re.finditer(r'(?<![\w{-])(%s)(?![\w}-])%s' % ('|'.join(words.split()), after), text):
            if not re.search(r'(?:^|\s)(?:a|an|A|An)\s+$', text[:m.start()]):
                spots.append((m.start(1), m.end(1), code(key)))
    for m in re.finditer(r'(?:^|(?<=[.!?…] ))(%s)(?=[!,])' % SHOUTS, text):
        spots.append((m.start(1), m.end(1), code('SHOUT')))
    rng.shuffle(spots)
    taken = []
    for s, e, c in spots:
        if done >= limit:
            break
        if any(s < te and ts < e for ts, te, _ in taken) or rng.random() >= chance:
            continue
        taken.append((s, e, c))
        done += 1
    for s, e, c in sorted(taken, reverse=True):
        text = text[:s] + c + text[e:]
    return text


# ---- game files ------------------------------------------------------------------

def word_count(slots):
    return min(len(words) for _, _, words in slots)


def with_words(extra):
    """SLOTS with extra answers added to each blank, e.g. the Adult humor words."""
    return [(key, ask, words + list(extra.get(key, []))) for key, ask, words in SLOTS]


def header_text(slots=SLOTS):
    count = word_count(slots)
    out = ['// In-game Mad Libs words. Written by the Emerald Editor (editor/madlibs_live.py).',
           '// The player picks words in data/scripts/mad_libs.inc; src/mad_libs.c shows them.', '',
           '#ifndef GUARD_DATA_MAD_LIBS_H', '#define GUARD_DATA_MAD_LIBS_H', '',
           '#define MADLIB_SLOT_COUNT %d' % len(slots), '#define MADLIB_WORD_COUNT %d' % count, '',
           'static const u16 sMadLibVars[MADLIB_SLOT_COUNT] =', '{']
    out += ['    %s,' % var_name(key) for key, *_ in slots]
    out += ['};', '', 'static const u8 *const sMadLibWords[MADLIB_SLOT_COUNT][MADLIB_WORD_COUNT] =', '{']
    for key, _, words in slots:
        out.append('    { // %s' % key)
        for k in range(0, count, 5):
            out.append('        ' + ' '.join('COMPOUND_STRING("%s"),' % w for w in words[k:k + 5]))
        out.append('    },')
    out += ['};', '', '#endif // GUARD_DATA_MAD_LIBS_H', '']
    return '\n'.join(out)


def script_text(slots=SLOTS):
    """MadLibs_EventScript_Start fills every blank; MadLibs_EventScript_Badge1..8 add four words.
    Each asks first whether the player picks the words or lets the game surprise them."""
    index = {key: i for i, (key, *_) in enumerate(slots)}
    out = ['@ In-game Mad Libs menus. Written by the Emerald Editor (editor/madlibs_live.py).', '',
           'MadLibs_EventScript_Start::',
           '\tmsgbox MadLibs_Text_Intro, MSGBOX_DEFAULT',
           '\tcall MadLibs_EventScript_AskHow']
    for key, *_ in slots:
        out.append('\tcall MadLibs_EventScript_Pick%s' % key.title())
    out += ['\tgoto MadLibs_EventScript_Finish', '']
    for n, keys in enumerate(BADGE_SLOTS, 1):
        out += ['MadLibs_EventScript_Badge%d::' % n,
                '\tmsgbox MadLibs_Text_Badge%d, MSGBOX_DEFAULT' % n,
                '\tcall MadLibs_EventScript_AskHow']
        out += ['\tcall MadLibs_EventScript_Pick%s' % key.title() for key in keys]
        out += ['\tgoto MadLibs_EventScript_Finish', '']
    out += ['@ VAR_0x8005: YES = the player picks, NO = surprise',
            'MadLibs_EventScript_AskHow::',
            '\tmsgbox MadLibs_Text_PickOrSurprise, MSGBOX_YESNO',
            '\tcopyvar VAR_0x8005, VAR_RESULT',
            '\treturn', '',
            'MadLibs_EventScript_Finish::',
            '\tgoto_if_eq VAR_0x8005, NO, MadLibs_EventScript_FinishSurprise',
            '\tmsgbox MadLibs_Text_Done, MSGBOX_DEFAULT',
            '\treturn', '',
            'MadLibs_EventScript_FinishSurprise::',
            '\tmsgbox MadLibs_Text_Surprised, MSGBOX_DEFAULT',
            '\treturn', '',
            'MadLibs_EventScript_Random::',
            '\tsetvar VAR_RESULT, 255',
            '\tspecial MadLibs_AddWord',
            '\treturn', '']
    texts = []
    for key, ask, words in slots:
        name = key.title()
        words = words[:word_count(slots)]
        out += ['MadLibs_EventScript_Pick%s::' % name,
                '\tsetvar VAR_0x8004, %d' % index[key],
                '\tgoto_if_eq VAR_0x8005, NO, MadLibs_EventScript_Random',
                '\tmessage MadLibs_Text_Pick%s' % name,
                '\twaitmessage',
                '\tdynmultichoice 0, 0, TRUE, 6, 0, DYN_MULTICHOICE_CB_NONE, %s' % ', '.join(
                    ['MadLibs_Text_%s%d' % (name, i) for i in range(len(words))] + ['MadLibs_Text_Surprise']),
                '\tclosemessage',
                '\tspecial MadLibs_AddWord',
                '\treturn', '']
        texts += ['MadLibs_Text_Pick%s:' % name, '\t.string "Pick %s!$"' % ask, '']
        for i, w in enumerate(words):
            texts += ['MadLibs_Text_%s%d:' % (name, i), '\t.string "%s$"' % w, '']
    texts += ['MadLibs_Text_Surprise:', '\t.string "Surprise me!$"', '',
              'MadLibs_Text_Intro:',
              '\t.string "Before this adventure starts, the\\n"',
              '\t.string "story has %d blanks to fill in.\\p"' % len(slots),
              '\t.string "Everyone in HOENN will use your words\\n"',
              '\t.string "for the rest of the game.\\p"',
              '\t.string "Every GYM BADGE adds 4 more.$"', '',
              'MadLibs_Text_PickOrSurprise:',
              '\t.string "Pick the words yourself?\\n"',
              '\t.string "(NO lets the game surprise you.)$"', '',
              'MadLibs_Text_Done:',
              '\t.string "Your words are locked in.\\n"',
              '\t.string "Go see what people do with them.$"', '',
              'MadLibs_Text_Surprised:',
              '\t.string "Your words are picked. You don\'t get\\n"',
              '\t.string "to know them. Good luck out there.$"', '']
    for n, keys in enumerate(BADGE_SLOTS, 1):
        texts += ['MadLibs_Text_Badge%d:' % n,
                  '\t.string "New badge, new words!\\n"',
                  '\t.string "4 more blanks to fill in.$"', '']
    return '\n'.join(out + texts)


START_HOOK = ('\tmsgbox PlayersHouse_2F_Text_ClockIsStopped, MSGBOX_DEFAULT\n'
              '\tcall PlayersHouse_2F_EventScript_SetWallClock\n')
START_FILE = 'data/scripts/players_house.inc'


def install(ov, slots=SLOTS):
    """Write the words and menus, then show the menus right after you set the clock at
    home, and after each of the 8 Gym badges."""
    import glob
    ov.write(HEADER, header_text(slots))
    ov.write(SCRIPT, script_text(slots))
    text = ov.read(START_FILE)
    if 'MadLibs_EventScript_Start' not in text and START_HOOK in text:
        ov.write(START_FILE, text.replace(START_HOOK, START_HOOK + '\tcall MadLibs_EventScript_Start\n', 1))
    badges = 0
    for path in sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc'))):
        rel = os.path.relpath(path, ROOT)
        if rel.split('/')[2].endswith('_Frlg'):
            continue
        text = ov.read(rel)
        new = text
        for n in range(1, 9):
            flag = '\tsetflag FLAG_BADGE%02d_GET\n' % n
            call = '\tcall MadLibs_EventScript_Badge%d\n' % n
            if flag in new and call not in new:
                new = new.replace(flag, flag + call, 1)
                badges += 1
        if new != text:
            ov.write(rel, new)
    return ['In-game Mad Libs: you fill in %d blanks after setting the clock at home, and 4 more after each of %d '
            'Gym badges (%d answers each, or Surprise me)' % (len(slots), badges, word_count(slots))]


def write_defaults():
    for rel, text in ((HEADER, header_text()), (SCRIPT, script_text())):
        with open(os.path.join(ROOT, rel), 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)


if __name__ == '__main__':
    write_defaults()
