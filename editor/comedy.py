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
    if exact:
        pat = re.compile(r'(?<![\w{])(' + '|'.join(re.escape(k) for k in exact) + r')(?![\w}])')
        text = pat.sub(lambda m: mapping[m.group(1)] if rng.random() < chance else m.group(1), text)
    if loose:
        pat = re.compile(r'(?<![\w{])(' + '|'.join(re.escape(k) for k in loose) + r')(?![\w}])', re.I)
        text = pat.sub(lambda m: _match_case(m.group(1), mapping[m.group(1).lower()])
                       if m.group(1).lower() in mapping and rng.random() < chance else m.group(1), text)
    return text


def madlibs(text, rng, chance):
    nouns = {n.lower() for n in L.MADLIB_NOUNS}
    pat = re.compile(r'(?<![\w{])([A-Za-z]+)(?![\w}])')

    def sub(m):
        w = m.group(1)
        if w.lower() in nouns and rng.random() < chance:
            return _match_case(w, rng.choice(L.MADLIB_FILL))
        return w
    return pat.sub(sub, text)


def _boxes(friendly):
    return [b for b in re.split(r'\n\s*\n', friendly) if b.strip()]


def _join(box):
    return ' '.join(box.split())


# ---- finding what each text is ------------------------------------------------------

def classify(text):
    """Labels used as signs, battle texts, boss texts and Yes/No questions in one script file."""
    signs, battle, questions, used = set(), set(), set(), set()
    boss = {}  # text label -> what that boss adds in the Game of Thrones storyline
    lines = text.split('\n')
    for i, line in enumerate(lines):
        mm = re.match(r'\s*(?:msgbox|message|messageautoscroll|pokenavcall)\s+(\w+)', line)
        if mm:
            used.add(mm.group(1))
        mm = re.match(r'\s*msgbox\s+(\w+)\s*,\s*(MSGBOX_\w+)', line)
        if mm:
            if mm.group(2) == 'MSGBOX_SIGN':
                signs.add(mm.group(1))
            elif mm.group(2) == 'MSGBOX_YESNO':
                questions.add(mm.group(1))
        mm = re.match(r'\s*message\s+(\w+)', line)
        if mm:
            following = ' '.join(lines[i + 1:i + 4])
            if re.search(r'yesnobox|multichoice|dynmultichoice', following):
                questions.add(mm.group(1))
        b = BATTLE_RE.match(line)
        if b:
            args = [a.strip() for a in (b.group(3) or '').split(',')]
            texts = [a for a in args if re.fullmatch(r'\w+_Text_\w+', a)]
            battle.update(texts)
            key = next((k for k in L.THRONES_LEADER_LINES if b.group(2)[len('TRAINER_'):].startswith(k)), None)
            if key:
                intro, defeat = L.THRONES_LEADER_LINES[key]
                roles = [defeat] if b.group(1) == 'trainerbattle_no_intro' else [intro, defeat]
                for label, line in zip(texts, roles):
                    if line:
                        boss[label] = line
    return signs, battle, boss, questions, used


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
    signs, battle, boss, questions, used = set(), set(), {}, set(), set()
    for path in maps_ + scripts:
        for acc, found in zip((signs, battle, boss, questions, used), classify(ov.read(os.path.relpath(path, ROOT)))):
            acc.update(found)

    samples = []
    touched = 0
    for path in maps_ + scripts + shared_text_files():
        rel = os.path.relpath(path, ROOT)
        shared = not rel.startswith('data/maps/')
        text = ov.read(rel)
        entries = textdb.parse_file(path, text)
        area_style = L.STYLES.get(mood.get(area_of(rel))) if mood and not shared else None
        lines = text.split('\n')
        changed = False
        for e in reversed(entries):
            if e.kind != 'asm' or not e.raw.endswith('$'):
                continue
            if rel.startswith('data/text/') and e.label not in used:
                continue  # shown by the game's own code in a special window
            codes = set(re.findall(r'\{[^}]*\}', e.raw))
            if codes - SAFE_CODES or '\\v' in e.raw or '\\e' in e.raw:
                continue
            friendly = e.friendly
            if len(friendly.strip()) < 4:
                continue
            style = area_style
            if mood and shared:
                style = L.STYLES[rng.choice(chosen_styles)]
            new = _transform(e.label, friendly, rng, level, packs, style,
                             is_sign=e.label in signs, is_battle=e.label in battle,
                             boss_line=boss.get(e.label), is_question=e.label in questions or friendly.rstrip().endswith('?'),
                             widths=widths)
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
    if packs.get('thrones'):
        head += thrones_storyline(ov, opt, rng, widths)
    if packs.get('battle'):
        head += battle_messages(ov, rng)
    report.add('Comedy dialogue', head + samples, count=touched)


EVENT_SCRIPTS = 'data/event_scripts.s'
GOSSIP_SHARE = {'light': 0.15, 'medium': 0.3, 'chaos': 0.6, 'everything': 1.0}
NPC_RE = re.compile(r'^(\w+)::\n\tmsgbox (\w+), MSGBOX_NPC\n\tend$', re.M)
CHAPTER_FLAGS = ['FLAG_IS_CHAMPION', 'FLAG_BADGE07_GET', 'FLAG_BADGE05_GET', 'FLAG_BADGE03_GET', 'FLAG_BADGE01_GET']


def thrones_storyline(ov, opt, rng, widths):
    """Add the realm's gossip script, then let chosen townsfolk share it after their own line.
    What they say depends on how many badges you have."""
    out = ['', '@ ---- Fun Modes: Game of Thrones storyline (added by Emerald Editor) ----',
           'Thrones_EventScript_Gossip::']
    for chapter, flag in zip((5, 4, 3, 2, 1), CHAPTER_FLAGS):
        out.append('\tgoto_if_set %s, Thrones_EventScript_Chapter%d' % (flag, chapter))
    out.append('\tgoto Thrones_EventScript_Chapter0')
    texts = []
    for c, lines in enumerate(L.THRONES_CHAPTERS):
        out += ['', 'Thrones_EventScript_Chapter%d:' % c, '\trandom %d' % len(lines), '\tswitch VAR_RESULT']
        out += ['\tcase %d, Thrones_EventScript_C%d_%d' % (i, c, i) for i in range(len(lines))]
        out.append('\treturn')
        for i, line in enumerate(lines):
            out += ['Thrones_EventScript_C%d_%d:' % (c, i), '\tmsgbox Thrones_Text_C%d_%d, MSGBOX_DEFAULT' % (c, i), '\treturn']
            raw = textdb.friendly_to_raw(wrap_box(line, widths), True)
            texts += ['', 'Thrones_Text_C%d_%d:' % (c, i)] + ['\t.string "%s"' % ch for ch in textdb.split_string_lines(raw)]
    text = ov.read(EVENT_SCRIPTS)
    if 'Thrones_EventScript_Gossip::' not in text:
        ov.write(EVENT_SCRIPTS, text.rstrip('\n') + '\n' + '\n'.join(out + texts) + '\n')

    share = GOSSIP_SHARE.get(opt.get('intensity', 'medium'), 0.3)
    hooked = 0
    for path in map_files():
        rel = os.path.relpath(path, ROOT)
        text = ov.read(rel)

        def hook(m):
            nonlocal hooked
            if rng.random() >= share:
                return m.group(0)
            hooked += 1
            return ('%s::\n\tlock\n\tfaceplayer\n\tmsgbox %s, MSGBOX_DEFAULT\n'
                    '\tcall Thrones_EventScript_Gossip\n\trelease\n\tend' % (m.group(1), m.group(2)))
        new = NPC_RE.sub(hook, text)
        if new != text:
            ov.write(rel, new)
    return ['Game of Thrones: every Gym Leader, Elite Four member, Wallace, Maxie, Archie and their admins speak for their house',
            'Game of Thrones: %d people share realm gossip that changes as you earn badges (6 chapters, %d lines)'
            % (hooked, sum(len(c) for c in L.THRONES_CHAPTERS))]


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


def _transform(label, friendly, rng, level, packs, style, is_sign, is_battle, boss_line, is_question, widths):
    boxes = [_join(b) for b in _boxes(friendly)]
    if not boxes:
        return None
    orig = list(boxes)
    if is_sign:
        if packs.get('fakeNews') and rng.random() < max(level * 1.5, 0.3):
            boxes.append('BREAKING NEWS: ' + rng.choice(L.NEWS))
        return _finish(boxes, orig, friendly, widths)

    # word-level changes
    if style and rng.random() < level:
        boxes = [swap_words(b, style['words'], rng, 0.9) for b in boxes]
        if rng.random() < 0.5:
            boxes[0] = _prefix(boxes[0], rng.choice(style['open']))
        if not is_question and rng.random() < 0.6:
            boxes[-1] = boxes[-1] + ' ' + rng.choice(style['close'])
    if packs.get('slang') and rng.random() < level:
        boxes = [swap_words(b, L.SLANG_WORDS, rng, 0.8) for b in boxes]
        if not is_question and rng.random() < 0.5:
            boxes[-1] = boxes[-1] + ' ' + rng.choice(L.SLANG_TAGS)
    if packs.get('madlibs') and rng.random() < level * 0.7:
        boxes = [madlibs(b, rng, 0.5) for b in boxes]

    # extra boxes, never after a question (it would hide the Yes/No prompt)
    if not is_question:
        extra = []
        hero_line = None
        if packs.get('thrones') and boss_line:
            extra.append(boss_line)  # the storyline: each house has its own words
        if packs.get('chaos') and not is_battle and rng.random() < level * 0.3:
            extra.append(rng.choice(L.CHAOS))
        if packs.get('narrator') and rng.random() < level * 0.3:
            extra.append(rng.choice(L.NARRATOR))
        if packs.get('hero') and rng.random() < level * 0.4:
            hero_line = rng.choice(L.HERO)
        if not extra and not hero_line and boxes == orig and level >= 1:
            pool = [L.NARRATOR] * bool(packs.get('narrator')) + [L.HERO] * bool(packs.get('hero')) \
                + [L.CHAOS] * bool(packs.get('chaos') and not is_battle) \
                + [L.SLANG_TAGS] * bool(packs.get('slang'))
            if pool:
                picked = rng.choice(pool)
                if picked is L.HERO:
                    hero_line = rng.choice(L.HERO)
                else:
                    extra.append(rng.choice(picked))
        boxes += extra[:2]
        if hero_line:
            # The hero answers right there, on new lines of the same text box.
            boxes[-1] = boxes[-1] + '\n' + hero_line
    elif boxes == orig and level >= 1:
        # questions: change the wording, never add a box after them
        if style:
            boxes[0] = _prefix(boxes[0], rng.choice(style['open']))
        elif packs.get('slang'):
            boxes[0] = _prefix(boxes[0], rng.choice(L.STYLES['genz']['open']))
    return _finish(boxes, orig, friendly, widths)


def _prefix(box, opener):
    """Put an opener after a speaker tag like 'KIRA:' rather than before it."""
    m = re.match(r'^([A-Z][A-Z .&]+:)\s+', box)
    head, rest = (m.group(1) + ' ', box[m.end():]) if m else ('', box)
    if opener.endswith((',', ':')) or opener.endswith('like,'):
        w = rest.split(' ', 1)[0]
        if len(w) > 1 and w[0].isupper() and w[1:].islower() and w not in ('I', "I'm", "I'll", "I've", "I'd"):
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
