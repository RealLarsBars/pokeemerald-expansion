"""Finds, shows and edits the game's dialogue.

Dialogue lives in assembly files as a label followed by .string lines:

    Route102_Text_CalvinIntro:
        .string "If you have POKeMON with you, then\\n"
        .string "you're an official POKeMON TRAINER!\\l"
        .string "You can't say no to my challenge!$"

In the editor this is shown as plain text: a line break is a new line, and
a blank line starts a new text box (\\p). When saving, the first line break
of each box becomes \\n and the rest become \\l (scroll), like the original
game. Text that you do not change is never rewritten.
"""

import glob
import os
import re

from common import ROOT, read_text, write_text

LABEL_RE = re.compile(r'^([A-Za-z_]\w*)::?\s*(?:@.*)?$')
STRING_RE = re.compile(r'^\s*\.string\s+"((?:[^"\\]|\\.)*)"\s*(?:@.*)?$')
C_STRING_RE = re.compile(r'^(\s*(?:static\s+)?(?:ALIGNED\(\d+\)\s+)?const\s+u8\s+(\w+)\[\]\s*=\s*_\(")((?:[^"\\]|\\.)*)("\);.*)$')

TEXT_BOX_WIDTH = 208  # pixels available on one line of the normal message box


def text_files():
    files = sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc')))
    files += sorted(glob.glob(os.path.join(ROOT, 'data/scripts/*.inc')))
    files += sorted(glob.glob(os.path.join(ROOT, 'data/text/*.inc')))
    files += [os.path.join(ROOT, 'src/strings.c')]
    return [f for f in files if os.path.exists(f)]


def raw_to_friendly(raw):
    s = raw[:-1] if raw.endswith('$') else raw
    s = s.replace('\\p', '\n\n').replace('\\n', '\n').replace('\\l', '\n')
    return s


def curly_quotes(text):
    """The game's font has no straight double quote, only “ and ”."""
    return re.sub(r'(^|(?<=[\s(\[{]))"', '“', text).replace('"', '”')


def friendly_to_raw(text, terminated=True):
    text = curly_quotes(text.replace('\r', '').strip('\n'))
    boxes = re.split(r'\n\s*\n', text)
    out = []
    for box in boxes:
        lines = box.split('\n')
        s = lines[0]
        for i, line in enumerate(lines[1:]):
            s += ('\\n' if i == 0 else '\\l') + line
        out.append(s)
    raw = '\\p'.join(out)
    return raw + ('$' if terminated else '')


def split_string_lines(raw):
    """Split raw text into .string chunks after each \\n, \\l and \\p, like the original files."""
    parts = re.split(r'(?<=\\[nlp])', raw)
    return [p for p in parts if p]


class Entry:
    __slots__ = ('file', 'label', 'start', 'end', 'raw', 'kind')

    def __init__(self, file, label, start, end, raw, kind):
        self.file, self.label, self.start, self.end, self.raw, self.kind = file, label, start, end, raw, kind

    @property
    def friendly(self):
        return raw_to_friendly(self.raw)

    def to_json(self):
        return {'file': os.path.relpath(self.file, ROOT), 'label': self.label, 'text': self.friendly,
                'line': self.start + 1}


def parse_file(path, text=None):
    lines = (read_text(path) if text is None else text).split('\n')
    entries = []
    if path.endswith('.c'):
        for i, line in enumerate(lines):
            m = C_STRING_RE.match(line)
            if m:
                entries.append(Entry(path, m.group(2), i, i + 1, m.group(3), 'c'))
        return entries
    i = 0
    while i < len(lines):
        m = LABEL_RE.match(lines[i])
        if m:
            j = i + 1
            parts = []
            while j < len(lines):
                sm = STRING_RE.match(lines[j])
                if not sm:
                    break
                parts.append(sm.group(1))
                j += 1
            if parts:
                entries.append(Entry(path, m.group(1), i + 1, j, ''.join(parts), 'asm'))
                i = j
                continue
        i += 1
    return entries


class TextDB:
    def __init__(self):
        self.cache = {}  # path -> (mtime, entries)

    def entries(self, path):
        mtime = os.path.getmtime(path)
        cached = self.cache.get(path)
        if not cached or cached[0] != mtime:
            cached = (mtime, parse_file(path))
            self.cache[path] = cached
        return cached[1]

    def all(self):
        for f in text_files():
            yield from self.entries(f)

    def find_label(self, label, file=None):
        files = [os.path.join(ROOT, file)] if file else text_files()
        for f in files:
            for e in self.entries(f):
                if e.label == label:
                    return e
        return None

    def search(self, query, match_case=False, limit=500):
        results = []
        total = 0
        q = query if match_case else query.lower()
        for e in self.all():
            text = e.friendly
            hay = text if match_case else text.lower()
            if not q or q in hay or q == e.label.lower() or (q in e.label.lower() and len(q) > 3):
                total += 1
                if len(results) < limit:
                    results.append(e.to_json())
        return {'results': results, 'total': total}

    def save(self, file, label, friendly):
        e = self.find_label(label, file)
        if e is None:
            raise KeyError(label)
        if friendly.replace('\r', '') == e.friendly:
            return False
        terminated = e.raw.endswith('$')
        raw = friendly_to_raw(friendly, terminated)
        raw = raw.replace('"', '\\"').replace('\\\\"', '\\"')
        lines = read_text(e.file).split('\n')
        if e.kind == 'c':
            m = C_STRING_RE.match(lines[e.start])
            new = [m.group(1) + (raw[:-1] if raw.endswith('$') and not e.raw.endswith('$') else raw) + m.group(4)]
        else:
            new = ['\t.string "%s"' % chunk for chunk in split_string_lines(raw)]
        lines[e.start:e.end] = new
        write_text(e.file, '\n'.join(lines))
        return True

    def replace_all(self, find, replace, match_case, targets):
        """targets: list of {file, label}. Returns number of texts changed."""
        flags = 0 if match_case else re.I
        pattern = re.compile(re.escape(find), flags)
        changed = 0
        # group by file and process bottom-up so line numbers stay valid
        for t in targets:
            e = self.find_label(t['label'], t['file'])
            if e is None:
                continue
            new = pattern.sub(lambda m: replace, e.friendly)
            if new != e.friendly and self.save(t['file'], t['label'], new):
                changed += 1
        return changed


# ---- text box width preview -------------------------------------------------

_WIDTHS = None


def char_widths():
    """Pixel width of each character in the normal font, from charmap.txt and src/fonts.c."""
    global _WIDTHS
    if _WIDTHS is not None:
        return _WIDTHS
    widths = {}
    try:
        fonts = read_text(os.path.join(ROOT, 'src/fonts.c'))
        m = re.search(r'gFontNormalLatinGlyphWidths\[\]\s*=\s*\{(.*?)\};', fonts, re.S)
        table = [int(x) for x in re.findall(r'\d+', m.group(1))]
        for line in read_text(os.path.join(ROOT, 'charmap.txt')).splitlines():
            cm = re.match(r"^'(.+)'\s*=\s*([0-9A-Fa-f]{2})\s*$", line)
            if cm:
                ch = cm.group(1).replace("\\'", "'")
                code = int(cm.group(2), 16)
                if len(ch) == 1 and code < len(table) and ch not in widths:
                    widths[ch] = table[code]
    except (OSError, AttributeError):
        pass
    _WIDTHS = widths
    return widths
