"""Comedy dialogue packs for Fun Modes.

Rewrites what people say in map scripts: speech styles per town (mood
ring), modern slang, Mad Libs nouns, narrator asides, the hero's inner
voice, fake news on signs, and Game of Thrones-style politics. Text is
re-wrapped to fit the message box. Only plain dialogue is touched: texts
with special codes (colors, music, arrows) and questions that lead into a
Yes/No menu are left alone."""

import glob
import os
import re

import comedy_lines as L
import madlibs_live as ML
import textdb
from common import ROOT
from maps import BATTLE_RE

SAFE_CODES = {'{PLAYER}', '{RIVAL}', '{KUN}', '{STR_VAR_1}', '{STR_VAR_2}', '{STR_VAR_3}', '{POKEBLOCK}'}
CODE_WIDTH = {'{PLAYER}': 42, '{RIVAL}': 42, '{KUN}': 0, '{STR_VAR_1}': 48, '{STR_VAR_2}': 48, '{STR_VAR_3}': 48,
              '{POKEBLOCK}': 60}
INTENSITY = {'light': 20, 'medium': 40, 'chaos': 80, 'everything': 100}


SHARED_SKIP = ('braille', 'match_call', 'apprentice', 'secret_base_trainers', 'questionnaire', 'cable_club',
               'record_mix', 'trainer_card', 'fame_checker', 'new_game_intro', 'pokedex_rating')


def map_files():
    files = sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc')))
    return [f for f in files if not os.path.basename(os.path.dirname(f)).endswith('_Frlg')]


def shared_script_files():
    return [f for f in sorted(glob.glob(os.path.join(ROOT, 'data/scripts/*.inc')))
            if not re.search(r'frlg|braille|cable|record_mix|trainer_hill', os.path.basename(f))]


def shared_text_files():
    return [f for f in sorted(glob.glob(os.path.join(ROOT, 'data/text/*.inc')))
            if not any(k in os.path.basename(f) for k in SHARED_SKIP) and 'frlg' not in os.path.basename(f)]


def area_of(rel):
    folder = rel.split('/')[2]
    return re.split(r'_', folder)[0]


# ---- word wrapping -------------------------------------------------------------

def _width(word, widths):
    w = 0
    for part in re.split(r'(\{[^}]*\})', word):
        if part.startswith('{'):
            w += CODE_WIDTH.get(part, 40)
        else:
            w += sum(widths.get(c, 6) for c in part)
    return w


def wrap_box(text, widths, limit=textdb.TEXT_BOX_WIDTH):
    if '\n' in text:  # a forced line break, e.g. before the hero speaks
        return '\n'.join(wrap_box(part, widths, limit) for part in text.split('\n') if part.strip())
    words = text.split()
    lines, cur, cur_w = [], [], 0
    space = widths.get(' ', 4)
    for w in words:
        ww = _width(w, widths)
        if cur and cur_w + space + ww > limit:
            lines.append(' '.join(cur))
            cur, cur_w = [w], ww
        else:
            cur_w += (space if cur else 0) + ww
            cur.append(w)
    if cur:
        lines.append(' '.join(cur))
    # Like the original game, lines past the second one scroll up.
    return '\n'.join(lines)


# ---- transforms -------------------------------------------------------------------

def _match_case(src, repl):
    if src.isupper() and len(src) > 1:
        return repl.upper()
    if src[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def swap_words(text, mapping, rng, chance):
    keys = sorted(mapping, key=len, reverse=True)
    exact = [k for k in keys if k[:1].isupper()]
    loose = [k for k in keys if not k[:1].isupper()]
    def name_part(m):  # an all-caps word next to another one is part of a name (BATTLE TOWER)
        w = m.group(1)
        if not (w.isupper() and len(w) > 1):
            return False
        before = m.string[:m.start()].split()
        after = m.string[m.end():].split()
        caps = lambda t: len(t) > 1 and re.sub(r'[^A-Za-zé]', '', t).isupper()  # noqa: E731
        return bool(before and caps(before[-1]) or after and caps(after[0]))
    if exact:
        pat = re.compile(r'(?<![\w{])(' + '|'.join(re.escape(k) for k in exact) + r')(?![\w}])')
        def exact_sub(m):
            if name_part(m) or rng.random() >= chance:
                return m.group(1)
            rep = mapping[m.group(1)]
            if re.search(r'(^|[.!?…]\s+)$', m.string[:m.start()]):
                rep = rep[:1].upper() + rep[1:]  # still starts the sentence
            return rep
        text = pat.sub(exact_sub, text)
    if loose:
        pat = re.compile(r'(?<![\w{])(' + '|'.join(re.escape(k) for k in loose) + r')(?![\w}])', re.I)
        text = pat.sub(lambda m: _match_case(m.group(1), mapping[m.group(1).lower()])
                       if m.group(1).lower() in mapping and not name_part(m) and rng.random() < chance
                       else m.group(1), text)
    # 'a ASSOCIATE' -> 'an ASSOCIATE'
    return re.sub(r'(?<![\w{])([Aa]) (?=[AEIOUaeiou]\w)', lambda m: m.group(1) + 'n ', text)


DETERMINERS = {'a', 'an', 'the', 'my', 'your', 'his', 'her', 'our', 'their', 'this'}


def _plural(noun):
    for joint in (' of ', ' in '):
        if joint in noun:  # 'jar of mayonnaise' -> 'jars of mayonnaise'
            head, tail = noun.split(joint, 1)
            return _plural(head) + joint + tail
    if noun.endswith('sis'):
        return noun[:-2] + 'es'
    if noun.endswith(('s', 'sh', 'ch', 'x')):
        return noun + 'es'
    if noun.endswith('y') and noun[-2:-1] not in 'aeiou':
        return noun[:-1] + 'ies'
    return noun + 's'


PLURAL_NOUNS = {'dreams', 'friends', 'people'}


def madlibs(text, rng, chance):
    """Swap a noun for something absurd, but only right after a word like 'the' or 'my',
    so the sentence still reads right ('my house' -> 'my haunted toaster')."""
    nouns = {n.lower() for n in L.MADLIB_NOUNS}
    pat = re.compile(r"(?<![\w{'])((?i:" + '|'.join(sorted(DETERMINERS)) + r"))(\s+)([A-Za-z]+)(?![\w}'])(?!\s+[A-Z])")

    def sub(m):
        det, space, w = m.group(1), m.group(2), m.group(3)
        if w.lower() not in nouns or w.isupper() or rng.random() >= chance:
            return m.group(0)
        fill = rng.choice(L.MADLIB_FILL)
        if w.lower() in PLURAL_NOUNS:
            fill = _plural(fill)
        if det.lower() in ('a', 'an'):
            article = 'an' if fill[0].lower() in 'aeiou' else 'a'
            det = _match_case(det, article)
        return det + space + fill
    return pat.sub(sub, text)


def _boxes(friendly):
    return [b for b in re.split(r'\n\s*\n', friendly) if b.strip()]


def _join(box):
    return ' '.join(box.split())


# ---- finding what each text is ------------------------------------------------------

# Commands that may sit between a message and the end of the conversation.
QUIET_CMDS = {'closemessage', 'waitmessage', 'waitbuttonpress', 'setflag', 'clearflag', 'setvar', 'addvar', 'subvar',
              'applymovement', 'waitmovement', 'playse', 'waitse', 'delay', 'special', 'specialvar',
              'removeobject', 'addobject', 'fadescreen', 'playbgm', 'fadedefaultbgm', 'savebgm', 'setobjectxyperm',
              'turnobject', 'copyvar', 'incrementgamestat', 'hideobjectat', 'showobjectat', 'waitstate',
              'fadenewbgm', 'setrespawn', 'opendoor', 'closedoor', 'waitdooranim', 'playmoncry', 'waitmoncry'}


def _ends_talk(lines, i):
    """True when the conversation is over right after the message on line i."""
    for line in lines[i + 1:i + 14]:
        s = line.split('@')[0].strip()
        if not s:
            continue
        if s.endswith(':') or s.endswith('::'):
            return False
        cmd = s.split()[0]
        if cmd in ('release', 'releaseall', 'end'):
            return True
        if cmd not in QUIET_CMDS:
            return False
    return False


def classify(text):
    """What each text in one script file is used for.

    signs, questions, used: sets of labels. battle: label -> 'intro', 'defeat' or 'other'.
    boss: label -> that boss's line in the Game of Thrones storyline. final: label -> True when
    every use of the text ends the conversation. after: labels said by a trainer you already beat."""
    signs, questions, used, after, npc = set(), set(), set(), set(), set()
    facing = False  # inside a script where someone turned to talk to you
    battle, boss, final = {}, {}, {}
    lines = text.split('\n')
    pending_after = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.endswith(':'):
            pending_after = False
            facing = False
        if s == 'faceplayer':
            facing = True
        mm = re.match(r'\s*(?:msgbox|message|messageautoscroll|pokenavcall)\s+(\w+)\s*(?:,\s*(MSGBOX_\w+))?', line)
        if mm:
            label, kind = mm.group(1), mm.group(2)
            used.add(label)
            if facing or kind == 'MSGBOX_NPC':
                npc.add(label)
            if kind == 'MSGBOX_SIGN':
                signs.add(label)
            elif kind == 'MSGBOX_YESNO':
                questions.add(label)
            if not line.strip().startswith('msgbox') or kind in (None, 'MSGBOX_DEFAULT'):
                following = ' '.join(lines[i + 1:i + 4])
                if line.strip().startswith('message') and re.search(r'yesnobox|multichoice|dynmultichoice', following):
                    questions.add(label)
            ends = kind in ('MSGBOX_NPC', 'MSGBOX_SIGN', 'MSGBOX_AUTOCLOSE') or (
                kind != 'MSGBOX_YESNO' and _ends_talk(lines, i))
            final[label] = final.get(label, True) and ends
            if pending_after:
                after.add(label)
                pending_after = False
        b = BATTLE_RE.match(line)
        if b:
            pending_after = True
            args = [a.strip() for a in (b.group(3) or '').split(',')]
            texts = [a for a in args if re.fullmatch(r'\w+_Text_\w+', a)]
            roles = ['defeat'] if b.group(1) == 'trainerbattle_no_intro' else ['intro', 'defeat']
            for n, label in enumerate(texts):
                battle[label] = roles[n] if n < len(roles) else 'other'
            key = next((k for k in L.THRONES_LEADER_LINES if b.group(2)[len('TRAINER_'):].startswith(k)), None)
            if key:
                intro, defeat = L.THRONES_LEADER_LINES[key]
                for label, role in zip(texts, roles):
                    line_ = intro if role == 'intro' else defeat
                    if line_:
                        boss[label] = line_
    return {'signs': signs, 'questions': questions, 'used': used, 'after': after, 'npc': npc,
            'battle': battle, 'boss': boss, 'final': final}


def merge_ctx(acc, ctx):
    for k in ('signs', 'questions', 'used', 'after', 'npc'):
        acc[k] |= ctx[k]
    acc['battle'].update(ctx['battle'])
    acc['boss'].update(ctx['boss'])
    for label, ends in ctx['final'].items():
        acc['final'][label] = acc['final'].get(label, True) and ends


SPEECH_RE = re.compile(r"(?<![\w])(I|I'm|I'll|I've|I'd|me|my|mine|we|we're|our|us|you|you're|your|yours|"
                       r"let's|hey|oh|hi|hello|please|thanks)(?![\w])", re.I)
_SPECIES = None


def species_names():
    global _SPECIES
    if _SPECIES is None:
        try:
            import fundata
            _SPECIES = {i['name'].upper() for i in fundata.pool().values()}
        except Exception:  # noqa: BLE001 - the comedy still works without it
            _SPECIES = set()
    return _SPECIES


def kind_of(label, friendly, ctx):
    """What kind of moment a text is: sign, question, intro, defeat, other_battle, after,
    talk, thing (someone examines an object), system (you received an item...) or cry."""
    flat = _join(friendly)
    if label in ctx['questions'] or flat.rstrip().endswith('?') and label not in ctx['battle']:
        return 'question'
    role = ctx['battle'].get(label)
    if role:
        return role if role in ('intro', 'defeat') else 'other_battle'
    m = re.match(r'^([A-Z][A-Z .\'é]+):\s*(.*)$', flat)
    if m and m.group(1).strip() in species_names() and len(m.group(2).split()) <= 4:
        return 'cry'
    if flat.startswith('{PLAYER}') or re.search(r'\b(obtained|received)\b', flat, re.I):
        return 'system'
    if label in ctx['signs']:
        first = _boxes(friendly)[0].split('\n')[0]
        letters = [c for c in first if c.isalpha()]
        if letters and sum(c.isupper() for c in letters) >= 0.6 * len(letters) \
                and not re.search(r'\b(says|said|painted|written|label)\b', flat):
            return 'sign'
        return 'thing'  # a sign or an object, never a person
    if label in ctx['after']:
        return 'after'
    if label not in ctx['npc'] and not SPEECH_RE.search(flat) and '!' not in flat:
        return 'thing'
    return 'talk'


def topic_of(friendly):
    low = friendly.lower()
    for topic, words in L.TOPICS:
        for w in words:
            if re.search(r'(?<![a-zé])' + re.escape(w) + r'(?![a-zé])', low):
                return topic
    return None


def place_name(area):
    if not area:
        return 'Hoenn'
    name = re.sub(r'(?<=[a-z])(?=[A-Z0-9])', ' ', area)
    return re.sub(r'^Mt ', 'Mt. ', name)


# Battle Frontier facilities and the like: the staff repeat the same rules and prompts all
# day, so they get the town's voice but nobody adds lines to them.
STAFF_RE = re.compile(r'^(BattleFrontier_Battle|BattleFrontier_Exchange|BattleFrontier_Ranking|BattlePyramid|'
                      r'BattleDome|BattleTower|TrainerHill|ContestHall|BerryBlender|SecretBase|battle_frontier|'
                      r'battle_pyramid|battle_tent|trainer_hill|contest|berry_blender|secret_base|save|pc|lottery)')
INDOOR_RE = re.compile(r'_(\w*House\w*|\w*Apartment\w*)$')


# ---- the pack runner ----------------------------------------------------------------

def styles_for_areas(areas, opt, rng):
    chosen = [s for s in opt.get('styles', list(L.STYLES)) if s in L.STYLES] or list(L.STYLES)
    out = {}
    for a in sorted(areas):
        out[a] = rng.choice(chosen)
    return out


def apply(ov, opt, rng, report):
    packs = opt.get('packs', {})
    level = INTENSITY.get(opt.get('intensity', 'medium'), 40) / 100.0
    widths = textdb.char_widths()
    maps_ = map_files()
    scripts = shared_script_files()
    areas = {area_of(os.path.relpath(f, ROOT)) for f in maps_}
    mood = styles_for_areas(areas, opt, rng) if packs.get('moodRing') else {}
    chosen_styles = [s for s in opt.get('styles', list(L.STYLES)) if s in L.STYLES] or list(L.STYLES)

    # What each text is used for, across every script in the game.
    ctx = {'signs': set(), 'questions': set(), 'used': set(), 'after': set(), 'npc': set(), 'battle': {}, 'boss': {}, 'final': {}}
    for path in maps_ + scripts:
        merge_ctx(ctx, classify(ov.read(os.path.relpath(path, ROOT))))

    if packs.get('liveMadLibs'):
        # Each blank is as wide as its longest word, so text never runs off the box.
        for key, _, words in ML.SLOTS:
            CODE_WIDTH[ML.code(key)] = max(_width(w, widths) for w in words)
            SAFE_CODES.add(ML.code(key))
    samples = []
    touched = 0
    for path in maps_ + scripts + shared_text_files():
        rel = os.path.relpath(path, ROOT)
        shared = not rel.startswith('data/maps/')
        text = ov.read(rel)
        entries = textdb.parse_file(path, text)
        style = None
        if mood:
            # One voice per place. Shared scripts (the POKéMON CENTER, the MART...) keep one
            # voice per file, so a conversation never switches accent halfway.
            style = L.STYLES[rng.choice(chosen_styles)] if shared else L.STYLES.get(mood.get(area_of(rel)))
        place = {'town': 'Hoenn' if shared else place_name(area_of(rel)),
                 'indoor': not shared and bool(INDOOR_RE.search(rel.split('/')[2])),
                 'staff': bool(STAFF_RE.match(os.path.basename(rel) if shared else rel.split('/')[2]))}
        lines = text.split('\n')
        changed = False
        for e in reversed(entries):
            if e.kind != 'asm' or not e.raw.endswith('$'):
                continue
            if rel.startswith('data/text/') and e.label not in ctx['used']:
                continue  # shown by the game's own code in a special window
            codes = set(re.findall(r'\{[^}]*\}', e.raw))
            if codes - SAFE_CODES or '\\v' in e.raw or '\\e' in e.raw:
                continue
            friendly = e.friendly
            if len(friendly.strip()) < 4:
                continue
            new = _transform(e.label, friendly, rng, level, packs, style, ctx, place, widths)
            if new is None or new == friendly:
                continue
            raw = textdb.friendly_to_raw(new, True)
            lines[e.start:e.end] = ['\t.string "%s"' % chunk for chunk in textdb.split_string_lines(raw)]
            changed = True
            touched += 1
            if len(samples) < 80 and (shared or len(samples) < 60):
                samples.append('%s: %s' % (e.label, ' / '.join(new.split('\n'))[:220]))
        if changed:
            ov.write(rel, '\n'.join(lines))
    head = []
    if mood:
        counts = {}
        for a, s in mood.items():
            counts.setdefault(L.STYLES[s]['label'], []).append(a)
        head = ['Mood ring: %s talks %s' % (', '.join(sorted(v)[:6]) + ('...' if len(v) > 6 else ''), k)
                for k, v in sorted(counts.items())]
    if packs.get('liveMadLibs'):
        head = ML.install(ov) + head
    if packs.get('thrones'):
        head += thrones_storyline(ov, opt, rng, widths)
    if packs.get('battle'):
        head += battle_messages(ov, rng)
    report.add('Comedy dialogue', head + samples, count=touched)


EVENT_SCRIPTS = 'data/event_scripts.s'
GOSSIP_SHARE = {'light': 0.15, 'medium': 0.3, 'chaos': 0.6, 'everything': 1.0}
NPC_RE = re.compile(r'^(\w+)::\n\tmsgbox (\w+), MSGBOX_NPC\n\tend$', re.M)
# Highest progress first: chapter 9 is the Champion, chapters 1-8 follow the badges.
CHAPTER_FLAGS = ['FLAG_IS_CHAMPION'] + ['FLAG_BADGE%02d_GET' % n for n in range(8, 0, -1)]


def thrones_storyline(ov, opt, rng, widths):
    """Add the realm's gossip script, then let chosen townsfolk share it after their own line.
    What they say depends on your newest badge, so nobody gossips about something that
    hasn't happened yet."""
    out = ['', '@ ---- Fun Modes: Game of Thrones storyline (added by Emerald Editor) ----',
           'Thrones_EventScript_Gossip::']
    for chapter, flag in zip(range(9, 0, -1), CHAPTER_FLAGS):
        out.append('\tgoto_if_set %s, Thrones_EventScript_Chapter%d' % (flag, chapter))
    out.append('\tgoto Thrones_EventScript_Chapter0')
    texts = []
    for c, lines in enumerate(L.THRONES_CHAPTERS):
        out += ['', 'Thrones_EventScript_Chapter%d:' % c, '\trandom %d' % len(lines), '\tswitch VAR_RESULT']
        out += ['\tcase %d, Thrones_EventScript_C%d_%d' % (i, c, i) for i in range(len(lines))]
        out.append('\treturn')
        for i, line in enumerate(lines):
            out += ['Thrones_EventScript_C%d_%d:' % (c, i), '\tmsgbox Thrones_Text_C%d_%d, MSGBOX_DEFAULT' % (c, i), '\treturn']
            said = rng.choice(L.GOSSIP_LEADS) + ' ' + line  # they change the subject, then gossip
            raw = textdb.friendly_to_raw(wrap_box(said, widths), True)
            texts += ['', 'Thrones_Text_C%d_%d:' % (c, i)] + ['\t.string "%s"' % ch for ch in textdb.split_string_lines(raw)]
    text = ov.read(EVENT_SCRIPTS)
    if 'Thrones_EventScript_Gossip::' not in text:
        ov.write(EVENT_SCRIPTS, text.rstrip('\n') + '\n' + '\n'.join(out + texts) + '\n')

    share = GOSSIP_SHARE.get(opt.get('intensity', 'medium'), 0.3)
    empty = {'signs': set(), 'questions': set(), 'used': set(), 'after': set(), 'npc': set(), 'battle': {}, 'boss': {}, 'final': {}}
    hooked = 0
    for path in map_files():
        rel = os.path.relpath(path, ROOT)
        text = ov.read(rel)
        said = {e.label: e.friendly for e in textdb.parse_file(path, text) if e.kind == 'asm'}
        empty['npc'] = set(said)  # everyone hooked here turned to talk to you
        staff = bool(STAFF_RE.match(rel.split('/')[2]))  # Frontier staff stick to their job

        def hook(m):
            nonlocal hooked
            # Only people who are actually chatting: not POKéMON cries, notices or questions.
            if staff or m.group(2) not in said or kind_of(m.group(2), said[m.group(2)], empty) != 'talk':
                return m.group(0)
            if rng.random() >= share:
                return m.group(0)
            hooked += 1
            return ('%s::\n\tlock\n\tfaceplayer\n\tmsgbox %s, MSGBOX_DEFAULT\n'
                    '\tcall Thrones_EventScript_Gossip\n\trelease\n\tend' % (m.group(1), m.group(2)))
        new = NPC_RE.sub(hook, text)
        if new != text:
            ov.write(rel, new)
    return ['Game of Thrones: every Gym Leader, Elite Four member, Wallace, Maxie, Archie and their admins speak for their house',
            'Game of Thrones: %d people share realm gossip that follows your badges (%d chapters, %d lines)'
            % (hooked, len(L.THRONES_CHAPTERS), sum(len(c) for c in L.THRONES_CHAPTERS))]


BATTLE_FILE = 'src/battle_message.c'


def battle_messages(ov, rng):
    text = ov.read(BATTLE_FILE)
    done = []
    for orig, options in L.BATTLE.items():
        lit = '_("%s")' % orig
        lit2 = 'COMPOUND_STRING("%s")' % orig
        new = rng.choice(options)
        for old, rep in ((lit, '_("%s")' % new), (lit2, 'COMPOUND_STRING("%s")' % new)):
            if old in text:
                text = text.replace(old, rep)
                done.append('Battle: ' + new.replace('\\p', '').split('{WAIT_SE}')[0])
                break
    ov.write(BATTLE_FILE, text)
    return done


TOWN_WORDS = ('LITTLEROOT', 'OLDALE', 'PETALBURG', 'RUSTBORO', 'DEWFORD', 'SLATEPORT', 'MAUVILLE', 'VERDANTURF',
              'FALLARBOR', 'LAVARIDGE', 'FORTREE', 'LILYCOVE', 'MOSSDEEP', 'SOOTOPOLIS', 'PACIFIDLOG', 'EVER GRANDE',
              'ROUTE', 'MT.', 'LAVA', 'WALLACE', 'DEWFORD', 'WEATHER INSTITUTE', 'ABANDONED SHIP', 'MOSSDEEP')


def _news_for(town, topic):
    """Fake news that fits the sign: news about this town, then about the sign's topic
    (a Gym sign gets Gym news), then news that doesn't name some other place."""
    key = None
    if town.endswith(('Town', 'City')):
        key = town.upper().rsplit(' ', 1)[0]
    elif town.startswith('Route'):
        key = town.upper()
    local = [n for n in L.NEWS if key and key in n]
    if local:
        return local
    if topic in L.NEWS_TOPIC:
        return L.NEWS_TOPIC[topic]
    return [n for n in L.NEWS if not any(w in n for w in TOWN_WORDS)]


def _fill(line, place):
    return line.replace('{TOWN}', place['town'])


def _pick(rng, pools, place):
    """Pick from the first pool that has lines (a topic pool, then the general one).
    Lines that name the town are only used in a town or city."""
    in_town = place['town'].endswith(('Town', 'City'))
    for p in pools:
        p = [x for x in (p or []) if in_town or '{TOWN}' not in x]
        if p:
            return rng.choice(p)
    return None


LIVE_SHARE = 0.4  # how often an added line is one built around the player's own words


def _live_pool(rng, packs, who, moment):
    """With in-game Mad Libs on, sometimes use a line built around the player's words."""
    if not packs.get('liveMadLibs') or rng.random() >= LIVE_SHARE:
        return None
    pool = L.MADLIB_LINES[who]
    return pool if isinstance(pool, list) else pool.get(moment)


def _live(rng, packs, who, moment):
    pool = _live_pool(rng, packs, who, moment)
    return rng.choice(pool) if pool else None


def _chaos(rng, topic, place):
    """The person keeps talking: about the same thing if we have a line for it, otherwise
    they admit they're changing the subject."""
    if L.TOPIC_CHAOS.get(topic):
        return rng.choice(L.TOPIC_CHAOS[topic])
    return _prefix(_pick(rng, [L.CHAOS], place), rng.choice(L.CHAOS_LEADS))


def _starts_sentence(box):
    m = re.match(r'^(?:[A-Z][A-Z .&]+:\s+)?(.)', box)
    return bool(m) and (m.group(1).isupper() or m.group(1) == '{')


def _transform(label, friendly, rng, level, packs, style, ctx, place, widths):
    boxes = [_join(b) for b in _boxes(friendly)]
    if not boxes:
        return None
    orig = list(boxes)
    kind = kind_of(label, friendly, ctx)
    if kind in ('system', 'cry'):
        return friendly  # item jingles and POKéMON cries stay as they are
    if kind == 'sign':
        if packs.get('fakeNews') and rng.random() < max(level * 1.5, 0.3):
            boxes.append('BREAKING NEWS: ' + rng.choice(_news_for(place['town'], topic_of(friendly))))
        return _finish(boxes, orig, friendly, widths)

    talking = kind != 'thing'  # a person is speaking (not a description of an object)
    topic = topic_of(friendly) if kind in ('talk', 'after') else None
    final = ctx['final'].get(label, False) or kind in ('intro', 'defeat')

    # 1. Mad Libs first, on the original words only.
    if packs.get('madlibs') and rng.random() < level * 0.7:
        boxes = [madlibs(b, rng, 0.6) for b in boxes]
    # 1b. In-game Mad Libs: some words become blanks the player fills in inside the game.
    if packs.get('liveMadLibs') and rng.random() < min(1.0, 0.25 + level * 0.6):
        left = 2
        for i, b in enumerate(boxes):
            nb = ML.fill_blanks(b, rng, 0.6, limit=left)
            left -= nb.count('{MADLIB_') - b.count('{MADLIB_')
            boxes[i] = nb
            if left <= 0:
                break
    # 2. Word swaps: the town's voice, then slang. Only people talk in a voice.
    use_style = talking and style and rng.random() < level
    use_slang = talking and packs.get('slang') and rng.random() < level
    if use_style:
        boxes = [swap_words(b, style['words'], rng, 0.9) for b in boxes]
    if use_style and style.get('label') == 'Shakespeare':
        boxes = [_thee(b) for b in boxes]
    if use_slang:
        boxes = [swap_words(b, L.SLANG_WORDS, rng, 0.8) for b in boxes]
    # 3. At most one opener and one closer, so they never pile up.
    # (Never on a question, and never when the text picks up mid-sentence from the last one.)
    if use_style and kind != 'question' and _starts_sentence(boxes[0]) and rng.random() < 0.4:
        boxes[0] = _prefix(boxes[0], rng.choice(style['open']))
    if kind != 'question':
        tags = L.SLANG_BATTLE.get(kind, L.SLANG_TAGS)
        if use_style and rng.random() < 0.6:
            closers = tags if style['close'] is L.SLANG_TAGS else style['close']
            boxes[-1] = boxes[-1] + ' ' + rng.choice(closers)
        elif use_slang and rng.random() < 0.5:
            boxes[-1] = boxes[-1] + ' ' + rng.choice(tags)

    if kind in ('question', 'other_battle') or not final or (place['staff'] and kind in ('talk', 'thing')):
        # Mid-conversation: nothing is added, so nobody talks over the next line.
        return _finish(boxes, orig, friendly, widths)

    # 4. What gets added at the end, in the order people would say it.
    moment = 'house' if kind == 'talk' and place['indoor'] else kind
    said, hero_line, narrator = [], None, None
    if packs.get('thrones') and ctx['boss'].get(label):
        said.append(ctx['boss'][label])  # the boss speaks for their house
    if packs.get('chaos') and kind == 'talk' and rng.random() < level * 0.3:
        said.append(_live(rng, packs, 'chaos', moment) or _chaos(rng, topic if rng.random() < 0.7 else None, place))
    if packs.get('hero') and rng.random() < level * 0.4:
        hero_line = _pick(rng, [_live_pool(rng, packs, 'hero', moment),
                                L.TOPIC_HERO.get(topic) if rng.random() < 0.6 else None,
                                L.HERO[moment] if moment == 'house' and rng.random() < 0.5 else None,
                                L.HERO['talk' if moment == 'house' else moment]], place)
    if packs.get('narrator') and rng.random() < level * 0.3:
        narrator = _pick(rng, [_live_pool(rng, packs, 'narrator', moment),
                               L.TOPIC_NARRATOR.get(topic) if rng.random() < 0.6 else None, L.NARRATOR[moment]], place)
    if not said and not hero_line and not narrator and boxes == orig and level >= 1:
        # Everything: every line gets something that fits it.
        options = (['hero'] * bool(packs.get('hero')) + ['narrator'] * bool(packs.get('narrator'))
                   + ['chaos'] * bool(packs.get('chaos') and kind == 'talk'))
        pick = rng.choice(options) if options else None
        if pick == 'hero':
            hero_line = _pick(rng, [_live_pool(rng, packs, 'hero', moment), L.TOPIC_HERO.get(topic),
                                    L.HERO['talk' if moment == 'house' else moment]], place)
        elif pick == 'narrator':
            narrator = _pick(rng, [_live_pool(rng, packs, 'narrator', moment), L.TOPIC_NARRATOR.get(topic),
                                   L.NARRATOR[moment]], place)
        elif pick == 'chaos':
            said.append(_live(rng, packs, 'chaos', moment) or _chaos(rng, topic, place))
    boxes += [_fill(s, place) for s in said[:2]]
    if hero_line:
        # The hero answers right there, on new lines of the same text box.
        boxes[-1] = boxes[-1] + '\n' + _fill(hero_line, place)
    if narrator and len(said) < 2:
        boxes.append(_fill(narrator, place))
    return _finish(boxes, orig, friendly, widths)


OBJECT_BEFORE = r'(?:to|for|with|at|about|on|of|from|know|see|tell|give|thank|beat|help|meet|show|ask|need|want|like|love|let)'


def _thee(box):
    """'thou' as an object is 'thee': 'I want to see thou!' -> 'I want to see thee!'"""
    box = re.sub(r'\bthou(?=\s*[.!?,…]|\s*$)', 'thee', box)
    return re.sub(r'(?<=\b)(' + OBJECT_BEFORE + r') thou\b(?! (?:art|hast|wouldst|wilt|dost))', r'\1 thee', box)


COMMON_STARTS = set('''the a an it it's its this that there there's these those my we we're our you you're your
if when what why how so but and all some every everyone nobody don't do did does is are was were can could would
should will let let's hey oh ah well yes no okay please here he she they their his her hmm huh wow whoa um uh
hehe heh haha hahaha one just now then maybe even also anyway sorry thanks thank welcome come go look listen wait
get take have see try don't'''.split())


def _prefix(box, opener):
    """Put an opener after a speaker tag like 'KIRA:' rather than before it."""
    m = re.match(r'^([A-Z][A-Z .&]+:)\s+', box)
    head, rest = (m.group(1) + ' ', box[m.end():]) if m else ('', box)
    if not opener.endswith(('.', '!', '?', '…', ':')):  # the sentence carries on after it
        w = re.sub(r"[^A-Za-z']", '', rest.split(' ', 1)[0])
        if w.lower() in COMMON_STARTS and w[:1].isupper():  # never lowercase a name
            rest = rest[0].lower() + rest[1:]
    return head + opener + ' ' + rest


def _finish(boxes, orig, friendly, widths):
    if boxes == orig:
        return friendly
    old = _boxes(friendly)
    out = []
    for i, b in enumerate(boxes):
        if i < len(orig) and b == orig[i]:
            out.append(old[i])  # unchanged box keeps its original line breaks
        else:
            out.append(wrap_box(b, widths))
    return '\n\n'.join(out)
