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
INTENSITY = {'light': 20, 'medium': 40, 'chaos': 80}
BOSS_WORDS = ('ROXANNE', 'BRAWLY', 'WATTSON', 'FLANNERY', 'NORMAN', 'WINONA', 'TATE', 'JUAN', 'SIDNEY', 'PHOEBE',
              'GLACIA', 'DRAKE', 'WALLACE', 'MAXIE', 'ARCHIE', 'TABITHA', 'SHELLY', 'MATT', 'COURTNEY')


def map_files():
    files = sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc')))
    return [f for f in files if not os.path.basename(os.path.dirname(f)).endswith('_Frlg')]


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
    signs, battle, boss, questions = set(), set(), set(), set()
    lines = text.split('\n')
    for i, line in enumerate(lines):
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
            for a in args:
                if re.fullmatch(r'\w+_Text_\w+', a):
                    battle.add(a)
                    if any(w in b.group(2) for w in BOSS_WORDS):
                        boss.add(a)
    return signs, battle, boss, questions


# ---- the pack runner ----------------------------------------------------------------

def styles_for_areas(areas, opt, rng):
    chosen = [s for s in opt.get('styles', list(L.STYLES)) if s in L.STYLES] or list(L.STYLES)
    out = {}
    for a in sorted(areas):
        out[a] = rng.choice(chosen)
    return out


def apply(ov, opt, rng, report):
    packs = opt.get('packs', {})
    level = INTENSITY.get(opt.get('intensity', 'medium'), 35) / 100.0
    widths = textdb.char_widths()
    files = map_files()
    areas = {area_of(os.path.relpath(f, ROOT)) for f in files}
    mood = styles_for_areas(areas, opt, rng) if packs.get('moodRing') else {}
    samples = []
    touched = 0
    for path in files:
        rel = os.path.relpath(path, ROOT)
        text = ov.read(rel)
        signs, battle, boss, questions = classify(text)
        entries = textdb.parse_file(path, text)
        style = L.STYLES.get(mood.get(area_of(rel))) if mood else None
        lines = text.split('\n')
        changed = False
        for e in reversed(entries):
            if e.kind != 'asm' or not e.raw.endswith('$'):
                continue
            codes = set(re.findall(r'\{[^}]*\}', e.raw))
            if codes - SAFE_CODES or '\\v' in e.raw or '\\e' in e.raw:
                continue
            friendly = e.friendly
            if len(friendly.strip()) < 4:
                continue
            new = _transform(e.label, friendly, rng, level, packs, style,
                             is_sign=e.label in signs, is_battle=e.label in battle,
                             is_boss=e.label in boss, is_question=e.label in questions or friendly.rstrip().endswith('?'),
                             widths=widths)
            if new is None or new == friendly:
                continue
            raw = textdb.friendly_to_raw(new, True)
            lines[e.start:e.end] = ['\t.string "%s"' % chunk for chunk in textdb.split_string_lines(raw)]
            changed = True
            touched += 1
            if len(samples) < 80:
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
    report.add('Comedy dialogue', head + samples, count=touched)


def _transform(label, friendly, rng, level, packs, style, is_sign, is_battle, is_boss, is_question, widths):
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
        if packs.get('thrones') and is_boss and rng.random() < 0.8:
            extra.append(rng.choice(L.THRONES_BOSS))
        elif packs.get('thrones') and not is_battle and rng.random() < level * 0.3:
            extra.append(rng.choice(L.THRONES_NPC))
        if packs.get('chaos') and not is_battle and rng.random() < level * 0.3:
            extra.append(rng.choice(L.CHAOS))
        if packs.get('narrator') and rng.random() < level * 0.3:
            extra.append(rng.choice(L.NARRATOR))
        if packs.get('hero') and rng.random() < level * 0.4:
            extra.append(rng.choice(L.HERO))
        boxes += extra[:2]
    return _finish(boxes, orig, friendly, widths)


def _prefix(box, opener):
    """Put an opener after a speaker tag like 'KIRA:' rather than before it."""
    m = re.match(r'^([A-Z][A-Z .&]+:)\s+', box)
    if m:
        return m.group(1) + ' ' + opener + ' ' + box[m.end():]
    return opener + ' ' + box


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
