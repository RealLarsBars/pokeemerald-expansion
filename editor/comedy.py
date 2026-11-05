"""Comedy dialogue for Fun Modes: pick one theme and the whole game goes all in on it.

Themes (editor/comedy_themes.py): Game of Thrones and Mad Libs. Switches that work
with either: Hero talks back, Adult humor, Fake news signs, Battle commentary.

How it reads in the game:
- Everyone who talks gets the theme's voice: Thrones word swaps, or Mad Libs blanks
  filled with the player's own words.
- A conversation can start with a short opener and end with a short sign-off.
- At most one joke is added per conversation: a line from the speaker, or the hero
  talking back. Every joke is used once per game at most; when a pool runs out,
  the rest of the game keeps the voice without extra lines.
- Game of Thrones also has the realm's gossip (one person in towns all over Hoenn,
  a new line after every badge) and every boss speaking for their house.

Only plain dialogue is touched: texts with special codes (colors, music, arrows) are
left alone, and nothing is added to a question that leads into a Yes/No menu."""

import glob
import json
import os
import re

import comedy_lines as L
import comedy_themes as T
import madlibs_live as ML
import textdb
from common import ROOT
from maps import BATTLE_RE
import title_screen
import house_gyms
import house_sigils
import thrones_sprites
import thrones_story

SAFE_CODES = {'{PLAYER}', '{RIVAL}', '{KUN}', '{STR_VAR_1}', '{STR_VAR_2}', '{STR_VAR_3}', '{POKEBLOCK}'}
CODE_WIDTH = {'{PLAYER}': 42, '{RIVAL}': 42, '{KUN}': 0, '{STR_VAR_1}': 48, '{STR_VAR_2}': 48, '{STR_VAR_3}': 48,
              '{POKEBLOCK}': 60}

SHARED_SKIP = ('braille', 'match_call', 'apprentice', 'secret_base_trainers', 'questionnaire', 'cable_club',
               'record_mix', 'trainer_card', 'fame_checker', 'new_game_intro', 'pokedex_rating')

TIC_USES = 3  # each short opener or sign-off shows up at most this many times per game


def map_files():
    files = sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc')))
    return [f for f in files if not os.path.basename(os.path.dirname(f)).endswith('_Frlg')]


def shared_script_files():
    return [f for f in sorted(glob.glob(os.path.join(ROOT, 'data/scripts/*.inc')))
            if not re.search(r'frlg|braille|cable|record_mix|trainer_hill|mad_libs', os.path.basename(f))]


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


# ---- word swaps -------------------------------------------------------------------

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


def _boxes(friendly):
    return [b for b in re.split(r'\n\s*\n', friendly) if b.strip()]


def _join(box):
    return ' '.join(box.split())


# ---- who is talking --------------------------------------------------------------

# Grown-ups, by sprite. Anyone else (kids, twins, unknown speakers) never gets an adult line.
ADULT_GFX = re.compile(r'MAN|WOMAN|GENTLEMAN|OLD|SCIENTIST|EXPERT|SAILOR|HIKER|FISHERMAN|BLACK_BELT|BIKER|ROCKER|'
                       r'BEAUTY|WORKER|POKEFAN|MANIAC|MEMBER|NURSE|CLERK|ARTIST|COOK|REPORTER|TEALA|LADY|MOM|DAD|'
                       r'NORMAN|STEVEN|WALLACE|ARCHIE|MAXIE|BIRCH|GUITARIST|HEX|ROXANNE|BRAWLY|WATTSON|FLANNERY|'
                       r'WINONA|JUAN|SIDNEY|PHOEBE|GLACIA|DRAKE|TABITHA|SHELLY|MATT|COURTNEY|COZMO|STERN|ADMIN')
KID_GFX = re.compile(r'BOY|GIRL|KID|TWIN|LITTLE|YOUNGSTER|LASS|TUBER|BUG_CATCHER|WALLY|BRENDAN|MAY|RIVAL|SCHOOL|'
                     r'PICNICKER|CAMPER|TATE|LIZA|PSYCHIC')


def speakers(rel):
    """script label -> sprite of the person who runs it ('' for triggers and signs)."""
    out = {}
    path = os.path.join(ROOT, os.path.dirname(rel), 'map.json')
    if not rel.startswith('data/maps/') or not os.path.exists(path):
        return out
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        return out
    for o in data.get('object_events') or []:
        if o.get('script') and o['script'] != '0x0':
            out[o['script']] = o.get('graphics_id', '')
    for key in ('coord_events', 'bg_events'):
        for o in data.get(key) or []:
            if o.get('script'):
                out.setdefault(o['script'], '')
    return out


def is_adult(gfx):
    return bool(gfx) and bool(ADULT_GFX.search(gfx)) and not KID_GFX.search(gfx)


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


def new_ctx():
    return {'signs': set(), 'questions': set(), 'used': set(), 'after': set(), 'npc': set(), 'battle': {},
            'boss': {}, 'final': {}, 'first': {}, 'adult': {}}


def classify(text, gfx=None):
    """What each text in one script file is used for.

    signs, questions, used: sets of labels. battle: label -> 'intro', 'defeat' or 'other'.
    boss: label -> that boss's line in the Game of Thrones storyline. final: label -> True when
    every use of the text ends the conversation. first: label -> True when every use starts one.
    adult: label -> True when a grown-up always says it. after: labels said by a trainer you
    already beat."""
    gfx = gfx or {}
    ctx = new_ctx()
    facing = False  # inside a script where someone turned to talk to you
    fresh = False   # nothing said yet since they turned to you
    owner = None
    lines = text.split('\n')
    pending_after = False
    for i, line in enumerate(lines):
        s = line.strip()
        if s.endswith(':'):
            pending_after = False
            facing = fresh = False
            name = s.rstrip(':')
            if name in gfx:
                owner = gfx[name]
        if s == 'faceplayer':
            facing = fresh = True
        mm = re.match(r'\s*(?:msgbox|message|messageautoscroll|pokenavcall)\s+(\w+)\s*(?:,\s*(MSGBOX_\w+))?', line)
        if mm:
            label, kind = mm.group(1), mm.group(2)
            ctx['used'].add(label)
            if facing or kind == 'MSGBOX_NPC':
                ctx['npc'].add(label)
            if kind == 'MSGBOX_SIGN':
                ctx['signs'].add(label)
            elif kind == 'MSGBOX_YESNO':
                ctx['questions'].add(label)
            if not line.strip().startswith('msgbox') or kind in (None, 'MSGBOX_DEFAULT'):
                following = ' '.join(lines[i + 1:i + 4])
                if line.strip().startswith('message') and re.search(r'yesnobox|multichoice|dynmultichoice', following):
                    ctx['questions'].add(label)
            ends = kind in ('MSGBOX_NPC', 'MSGBOX_SIGN', 'MSGBOX_AUTOCLOSE') or (
                kind != 'MSGBOX_YESNO' and _ends_talk(lines, i))
            ctx['final'][label] = ctx['final'].get(label, True) and ends
            starts = fresh or kind == 'MSGBOX_NPC'
            ctx['first'][label] = ctx['first'].get(label, True) and starts
            fresh = False
            ctx['adult'][label] = ctx['adult'].get(label, True) and is_adult(owner)
            if pending_after:
                ctx['after'].add(label)
                pending_after = False
        b = BATTLE_RE.match(line)
        if b:
            pending_after = True
            args = [a.strip() for a in (b.group(3) or '').split(',')]
            texts = [a for a in args if re.fullmatch(r'\w+_Text_\w+', a)]
            roles = ['defeat'] if b.group(1) == 'trainerbattle_no_intro' else ['intro', 'defeat']
            for n, label in enumerate(texts):
                ctx['battle'][label] = roles[n] if n < len(roles) else 'other'
                ctx['used'].add(label)
                ctx['adult'][label] = ctx['adult'].get(label, True) and is_adult(owner)
            key = next((k for k in L.THRONES_LEADER_LINES if b.group(2)[len('TRAINER_'):].startswith(k)), None)
            if key:
                intro, defeat = L.THRONES_LEADER_LINES[key]
                for label, role in zip(texts, roles):
                    line_ = intro if role == 'intro' else defeat
                    if line_:
                        ctx['boss'][label] = line_
    return ctx


def merge_ctx(acc, ctx):
    for k in ('signs', 'questions', 'used', 'after', 'npc'):
        acc[k] |= ctx[k]
    acc['battle'].update(ctx['battle'])
    acc['boss'].update(ctx['boss'])
    for k in ('final', 'first', 'adult'):
        for label, v in ctx[k].items():
            acc[k][label] = acc[k].get(label, True) and v


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
    speech = SPEECH_RE.search(flat)
    if len(flat.split()) <= 3 and not speech:
        return 'cry'  # 'Bow! Bowwow!'
    if not speech and re.match(r"^[A-Z][A-Zé .']+ (looks|is|seems|appears|stares|gazes|gives|won't|doesn't|cries|"
                               r"barks|growls|let out|lets out)\b", flat):
        return 'thing'  # 'ZIGZAGOON looks vacant…' describes a POKéMON, nobody is talking
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


# Battle Frontier facilities and the like: the staff repeat the same rules and prompts all
# day, so they get the theme's voice but nobody adds lines to them.
STAFF_RE = re.compile(r'^(BattleFrontier_Battle|BattleFrontier_Exchange|BattleFrontier_Ranking|BattlePyramid|'
                      r'BattleDome|BattleTower|TrainerHill|ContestHall|BerryBlender|SecretBase|battle_frontier|'
                      r'battle_pyramid|battle_tent|trainer_hill|contest|berry_blender|secret_base|save|pc|lottery)')
TALKING = ('talk', 'after', 'intro', 'defeat', 'other_battle', 'question')


# ---- the theme runner -------------------------------------------------------------------

# Birch's opening speech is shown by the game's own code. It changes only when a theme has
# a hand-written version, and the hero (who has no name yet) never answers it.
INTRO_FILE = 'data/text/birch_speech.inc'
REWRITES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fun', 'rewrites')


def load_rewrites(key):
    """Hand-written versions of whole texts for one theme: editor/fun/rewrites/<theme>/*.txt.

    Each entry starts with a line '@ Label' and holds the new text. A blank line starts a
    new text box; lines are wrapped to fit by the editor."""
    out = {}
    for path in sorted(glob.glob(os.path.join(REWRITES_DIR, key, '*.txt'))):
        with open(path, encoding='utf-8') as f:
            label, body = None, []
            for line in f.read().split('\n') + ['@ ']:
                if line.startswith('@ '):
                    if label:
                        out[label] = '\n'.join(body).strip()
                    label, body = line[2:].strip(), []
                elif not line.startswith('#'):
                    body.append(line)
    return out


def rewrite_ok(old, new):
    """A rewrite keeps every code the game fills in, and a question stays a question."""
    need = set(re.findall(r'\{(?:STR_VAR_\d|PLAYER|RIVAL|POKEBLOCK)\}', old))
    have = set(re.findall(r'\{[^}]*\}', new))
    if not need <= have or have - SAFE_CODES:
        return False
    return not old.rstrip().endswith('?') or new.rstrip().endswith('?')


def theme_of(opt):
    return opt.get('theme') if opt.get('theme') in T.THEMES else 'thrones'


def apply(ov, opt, rng, report):
    key = theme_of(opt)
    th = T.THEMES[key]
    adult = bool(opt.get('adult'))
    widths = textdb.char_widths()
    maps_ = map_files()
    scripts = shared_script_files()

    # What each text is used for, across every script in the game.
    ctx = new_ctx()
    for path in maps_ + scripts:
        rel = os.path.relpath(path, ROOT)
        merge_ctx(ctx, classify(ov.read(rel), speakers(rel)))

    head = []
    if key == 'madlibs':
        slots = ML.with_words(th['adult_words']) if adult else ML.SLOTS
        # Each blank is as wide as its longest word, so text never runs off the box.
        for k, _, words in slots:
            CODE_WIDTH[ML.code(k)] = max(_width(w, widths) for w in words)
            SAFE_CODES.add(ML.code(k))
        head += ML.install(ov, slots)
    # Game of Thrones is a straight story: only hand-written lines, the story events and the
    # House Gyms change text. No random add-ons (hero lines, gossip, signs, battle jokes, tics).
    story_only = key == 'thrones'
    gossip = {}
    rewrites = load_rewrites(key)
    head += title_screen.apply(ov, key)
    if key == 'thrones' and opt.get('houseGyms', True):
        head += ['Gyms: ' + line for line in house_gyms.apply(ov, rng)]
        # The Gyms changed, so the Gym Guides' advice and the leaders' house lines change too.
        rewrites.update(house_gyms.text_overrides())
        head += house_sigils.apply(ov)
        swap = {}
        for k, new_lines in house_gyms.boss_lines().items():
            swap.update(zip(L.THRONES_LEADER_LINES[k], new_lines))
        ctx['boss'] = {label: swap.get(line_, line_) for label, line_ in ctx['boss'].items()}
    if key == 'thrones' and opt.get('sprites', True):
        head += thrones_sprites.apply(ov)
    if key == 'thrones' and opt.get('story', True):
        rewrites.update(thrones_story.TEXT)
        head += thrones_story.apply(ov, widths)

    # Pass 1: every text the theme can touch.
    files, items = [], []
    for path in maps_ + scripts + shared_text_files():
        rel = os.path.relpath(path, ROOT)
        shared = not rel.startswith('data/maps/')
        text = ov.read(rel)
        staff = bool(STAFF_RE.match(os.path.basename(rel) if shared else rel.split('/')[2]))
        mine = []
        for e in textdb.parse_file(path, text):
            if e.kind != 'asm' or not e.raw.endswith('$'):
                continue
            intro = rel == INTRO_FILE and e.label in rewrites
            if rel.startswith('data/text/') and e.label not in ctx['used'] and not intro:
                continue  # shown by the game's own code in a special window
            codes = set(re.findall(r'\{[^}]*\}', e.raw))
            if codes - SAFE_CODES or '\\v' in e.raw or '\\e' in e.raw or len(e.friendly.strip()) < 4:
                continue
            kind = kind_of(e.label, e.friendly, ctx)
            if kind in ('system', 'cry'):
                continue  # item jingles and POKéMON cries stay as they are
            it = {'e': e, 'rel': rel, 'kind': kind, 'staff': staff or intro, 'adult': ctx['adult'].get(e.label, False),
                  'final': ctx['final'].get(e.label, False) or kind in ('intro', 'defeat'),
                  'first': ctx['first'].get(e.label, False) or kind == 'intro',
                  'boss': ctx['boss'].get(e.label) if key == 'thrones' else None,
                  'gossip': e.label in gossip['labels'] if gossip else False}
            rw = rewrites.get(e.label)
            if rw and rewrite_ok(e.friendly, rw):
                it['rw'] = rw
            mine.append(it)
            items.append(it)
        files.append((rel, text, mine))

    counts = plan(items, th, opt, rng, story_only)

    # Pass 2: write it.
    touched = 0
    samples = []
    for rel, text, mine in files:
        lines = text.split('\n')
        changed = False
        for it in reversed(mine):  # from the bottom, so line numbers stay right
            e = it['e']
            new = _transform(it, th, key, rng, widths)
            if new is None or new == e.friendly:
                continue
            raw = textdb.friendly_to_raw(new, True)
            if e.raw.endswith('\\p$') and not raw.endswith('\\p$'):
                raw = raw[:-1] + '\\p$'  # the game waits on that last empty page (Birch's speech)
            lines[e.start:e.end] = ['\t.string "%s"' % chunk for chunk in textdb.split_string_lines(raw)]
            changed = True
            touched += 1
            if len(samples) < 80 and (it.get('add') or len(samples) < 40):
                samples.append('%s: %s' % (e.label, ' / '.join(new.split('\n'))[:240]))
        if changed:
            ov.write(rel, '\n'.join(lines))

    head.insert(0, 'Theme: %s. Every joke below is used once at most: %s' % (
        th['label'], ', '.join('%d %s' % (n, what) for what, n in counts.items() if n)))
    if gossip:
        head += thrones_storyline(ov, gossip, adult, widths)
    if opt.get('battle', True) and not story_only:
        head += battle_messages(ov, rng)
    report.add('Comedy dialogue', head + samples, count=touched)


def _tics(cands, lines, rng, field):
    """Short openers and sign-offs: each used at most TIC_USES times, on texts spread
    over the whole game."""
    cands = [c for c in cands if field not in c]
    rng.shuffle(cands)
    pool = []
    for _ in range(TIC_USES):
        more = list(lines)
        rng.shuffle(more)
        pool += more
    for line, c in zip(pool, cands):
        c[field] = line
    return min(len(pool), len(cands))


def plan(items, th, opt, rng, story_only=False):
    """Decide, for the whole game at once, which text gets which line. Jokes are dealt out
    without putting any back, so none repeats; adult lines only go to grown-ups."""
    hero_on = opt.get('hero', True)
    adult = bool(opt.get('adult'))
    news_on = opt.get('fakeNews', True)
    ad = th['adult'] if adult else {}
    counts = {}

    def deal(cands, lines, slot, label, adult_lines=(), adult_only=True):
        free = [c for c in cands if 'add' not in c]
        rng.shuffle(free)
        n = 0
        extra = list(adult_lines)
        rng.shuffle(extra)
        for line in extra:
            pick = next((c for c in free if c['adult'] or not adult_only), None)
            if pick is None:
                break
            free.remove(pick)
            pick['add'] = (slot, line)
            n += 1
        lines = list(lines)
        rng.shuffle(lines)
        for line, c in zip(lines, free):
            c['add'] = (slot, line)
            n += 1
        counts[label] = counts.get(label, 0) + n

    for it in items:
        if it['boss'] and it['kind'] in ('intro', 'defeat') and (not story_only or opt.get('houseGyms', True)):
            it['add'] = ('boss', it['boss'])  # the boss speaks for their house
    ends = lambda it: it['final'] and not it['staff'] and not it['gossip']  # noqa: E731
    by_kind = {k: [it for it in items if it['kind'] == k and ends(it)] for k in ('talk', 'thing', 'intro', 'defeat', 'after')}
    counts['hand-written lines'] = sum(1 for it in items if 'rw' in it)
    if story_only:
        counts['Gym Leader house lines'] = sum(1 for it in items if it.get('add'))
        return counts

    if hero_on:
        for moment, cands in by_kind.items():
            # The hero swears now and then with Adult humor on; never anything sexual (they're a kid).
            deal(cands, th['hero'][moment], 'hero', 'hero lines',
                 ad.get('hero', []) if moment == 'talk' else (), adult_only=False)
    # A hand-written line is already new: the hero may answer it, but nothing else is added.
    by_kind = {k: [it for it in v if 'rw' not in it] for k, v in by_kind.items()}
    deal(by_kind['talk'], th['end'], 'say', 'lines from townsfolk', ad.get('end', []))
    deal(by_kind['intro'], th['intro'], 'say', 'trainer challenges', ad.get('intro', []))
    deal(by_kind['defeat'], th['defeat'], 'say', 'trainer defeats', ad.get('defeat', []))
    deal(by_kind['after'], th['after'], 'say', 'lines from beaten trainers')
    if news_on:
        signs = [it for it in items if it['kind'] == 'sign']
        deal(signs, th['sign'], 'news', 'signs', ad.get('sign', []), adult_only=False)

    # Openers and sign-offs: the theme's voice, at the start and end of more conversations.
    chat = lambda it: it['kind'] in ('talk', 'after') and not it['staff'] and 'rw' not in it  # noqa: E731
    n = _tics([it for it in items if chat(it) and it['first']], th['open'], rng, 'open')
    quiet = [it for it in items if 'add' not in it and it['final'] and not it['staff'] and not it['gossip']
             and 'rw' not in it]
    n += _tics([it for it in quiet if chat(it)], th['close'], rng, 'close')
    n += _tics([it for it in quiet if it['kind'] == 'intro'], th['close_intro'], rng, 'close')
    n += _tics([it for it in quiet if it['kind'] == 'defeat'], th['close_defeat'], rng, 'close')
    counts['short openers and sign-offs (each 3 times at most)'] = n
    return counts


def _transform(it, th, key, rng, widths):
    friendly = it['e'].friendly
    boxes = [_join(b) for b in _boxes(friendly)]
    if not boxes:
        return None
    orig = list(boxes)
    kind = it['kind']
    add = it.get('add')
    if 'rw' in it:
        boxes = [_join(b) for b in _boxes(it['rw'])]
        orig = []  # every box is new, so every box is wrapped
    elif kind == 'sign':
        if add:
            boxes.append(add[1])
        return _finish(boxes, orig, friendly, widths)

    elif kind in TALKING:
        # The voice: Mad Libs blanks with the player's words, or the realm's way of talking.
        if key == 'madlibs' and not it['staff']:
            left = 2
            for i, b in enumerate(boxes):
                nb = ML.fill_blanks(b, rng, 1.0, limit=left)
                left -= nb.count('{MADLIB_') - b.count('{MADLIB_')
                boxes[i] = nb
                if left <= 0:
                    break
        if th['words'] and key != 'thrones':  # Thrones changes only hand-written texts
            boxes = [swap_words(b, th['words'], rng, 1.0) for b in boxes]
    if it.get('open') and _starts_sentence(boxes[0]):
        boxes[0] = _prefix(boxes[0], it['open'])
    if it.get('close'):
        boxes[-1] = boxes[-1] + ' ' + it['close']
    if add:
        slot, line = add
        if slot == 'hero':
            # The hero answers right there, on new lines of the same text box.
            boxes[-1] = boxes[-1] + '\n' + line
        else:
            boxes.append(line)  # the same person keeps talking, in a box of its own
    return _finish(boxes, orig, friendly, widths)


def _starts_sentence(box):
    m = re.match(r'^(?:[A-Z][A-Z .&]+:\s+)?(.)', box)
    return bool(m) and (m.group(1).isupper() or m.group(1) == '{')


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


# ---- Game of Thrones: the realm's gossip ------------------------------------------------

EVENT_SCRIPTS = 'data/event_scripts.s'
NPC_RE = re.compile(r'^(\w+)::\n\tmsgbox (\w+), MSGBOX_NPC\n\tend$', re.M)
# Highest progress first: chapter 9 is the Champion, chapters 1-8 follow the badges.
CHAPTER_FLAGS = ['FLAG_IS_CHAMPION'] + ['FLAG_BADGE%02d_GET' % n for n in range(8, 0, -1)]


def gossip_chapters(adult):
    if not adult:
        return T.THRONES_GOSSIP
    return [c + a for c, a in zip(T.THRONES_GOSSIP, T.THRONES_GOSSIP_ADULT)]


def pick_gossipers(ov, ctx, rng, adult):
    """One chatty grown-up per place, all over Hoenn, until every gossip line has someone
    to say it. Towns and cities first."""
    need = max(len(c) for c in gossip_chapters(adult))
    by_area = {}
    for path in map_files():
        rel = os.path.relpath(path, ROOT)
        folder = rel.split('/')[2]
        if STAFF_RE.match(folder):
            continue
        text = ov.read(rel)
        said = {e.label: e.friendly for e in textdb.parse_file(path, text) if e.kind == 'asm'}
        for m in NPC_RE.finditer(text):
            script, label = m.group(1), m.group(2)
            if label not in said or label in ctx['boss'] or not ctx['adult'].get(label):
                continue
            if kind_of(label, said[label], ctx) != 'talk':
                continue
            by_area.setdefault(area_of(rel), []).append((rel, script, label))
    towns = [a for a in by_area if a.endswith(('Town', 'City'))]
    others = [a for a in by_area if a not in towns]
    rng.shuffle(towns)
    rng.shuffle(others)
    chosen = []
    for a in towns + others:
        if len(chosen) >= need:
            break
        chosen.append(rng.choice(by_area[a]))
    return {'people': chosen, 'labels': {label for _, _, label in chosen}}


def thrones_storyline(ov, gossip, adult, widths):
    """Add the gossip script, then hook the chosen people into it. Each person says their own
    line for your newest badge, so nobody repeats anybody, and nobody gossips about
    something that hasn't happened yet."""
    chapters = gossip_chapters(adult)
    out = ['', '@ ---- Fun Modes: Game of Thrones storyline (added by Emerald Editor) ----',
           '@ VAR_0x8004: which gossiper is talking.',
           'Thrones_EventScript_Gossip::']
    for chapter, flag in zip(range(9, 0, -1), CHAPTER_FLAGS):
        out.append('\tgoto_if_set %s, Thrones_EventScript_Chapter%d' % (flag, chapter))
    out.append('\tgoto Thrones_EventScript_Chapter0')
    texts = []
    for c, lines in enumerate(chapters):
        out += ['', 'Thrones_EventScript_Chapter%d:' % c, '\tswitch VAR_0x8004']
        out += ['\tcase %d, Thrones_EventScript_C%d_%d' % (i, c, i) for i in range(len(lines))]
        out.append('\treturn')
        for i, line in enumerate(lines):
            out += ['Thrones_EventScript_C%d_%d:' % (c, i), '\tmsgbox Thrones_Text_C%d_%d, MSGBOX_DEFAULT' % (c, i),
                    '\treturn']
            said = T.THRONES_LEADS[i % len(T.THRONES_LEADS)] + ' ' + line  # each person has their own way in
            raw = textdb.friendly_to_raw(wrap_box(said, widths), True)
            texts += ['', 'Thrones_Text_C%d_%d:' % (c, i)] + ['\t.string "%s"' % ch for ch in textdb.split_string_lines(raw)]
    text = ov.read(EVENT_SCRIPTS)
    if 'Thrones_EventScript_Gossip::' not in text:
        ov.write(EVENT_SCRIPTS, text.rstrip('\n') + '\n' + '\n'.join(out + texts) + '\n')

    places = []
    for n, (rel, script, label) in enumerate(gossip['people']):
        text = ov.read(rel)
        old = '%s::\n\tmsgbox %s, MSGBOX_NPC\n\tend' % (script, label)
        new = ('%s::\n\tlock\n\tfaceplayer\n\tmsgbox %s, MSGBOX_DEFAULT\n\tsetvar VAR_0x8004, %d\n'
               '\tcall Thrones_EventScript_Gossip\n\trelease\n\tend' % (script, label, n))
        if old in text:
            ov.write(rel, text.replace(old, new, 1))
            places.append(re.sub(r'(?<=[a-z])(?=[A-Z0-9])', ' ', area_of(rel)))
    return ['Game of Thrones: every Gym Leader, Elite Four member, Wallace, Maxie, Archie and their admins speak for their house',
            'Game of Thrones: %d people keep you up on realm news, with a new line from each after every badge '
            '(%d lines in all). Find them in: %s' % (len(places), sum(min(len(c), len(places)) for c in chapters),
                                                    ', '.join(sorted(places)))]


# ---- battle commentary ------------------------------------------------------------------

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
