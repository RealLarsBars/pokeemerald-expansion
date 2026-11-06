"""What one person on a map does when you talk to them.

The Maps tab uses this when you click someone: it finds their script, the
smaller scripts it jumps to in the same file, and every text they can say,
so all of it can be edited in one place.
"""

import json
import os
import re

from common import ROOT, project_path, read_text, write_text
from maps import script_files
from mapview import load_map
from textdb import LABEL_RE

TOKEN_RE = re.compile(r'[A-Za-z_]\w*')
MAX_SCRIPTS = 12


class PersonError(Exception):
    pass


def _blocks(lines):
    """Every label in a script file: {label, global, start, end}.

    start is the label's line, end is one past its last line (trailing blank
    lines are left out so they stay between blocks)."""
    heads = []
    for i, line in enumerate(lines):
        m = LABEL_RE.match(line)
        if m:
            heads.append((i, m.group(1), line.rstrip().split('@')[0].rstrip().endswith('::')))
    out = []
    for n, (i, label, glob_) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        while end > i + 1 and not lines[end - 1].strip():
            end -= 1
        out.append({'label': label, 'global': glob_, 'start': i, 'end': end})
    return out


def _find_script_file(label):
    pattern = re.compile(r'^%s::?\s*(?:@.*)?$' % re.escape(label), re.M)
    for f in script_files():
        if pattern.search(read_text(f)):
            return f
    return None


def _body(lines, b):
    return '\n'.join(lines[b['start'] + 1:b['end']])


def _code_tokens(text):
    """Names used in a script, skipping comments and quoted text."""
    out = []
    for line in text.split('\n'):
        line = re.sub(r'"(?:[^"\\]|\\.)*"', '', line).split('@')[0]
        out += TOKEN_RE.findall(line)
    return out


def person(map_folder, index, text_db, map_index):
    if not re.match(r'^\w+$', map_folder):
        raise PersonError('Unknown map.')
    data = load_map(map_folder)
    objs = data.get('object_events') or []
    try:
        obj = objs[int(index)]
    except (IndexError, ValueError):
        raise PersonError('That person is not on this map any more. Reload the map.')
    label = obj.get('script') or ''
    base = {'map': map_folder, 'index': int(index), 'label': label, 'graphics_id': obj.get('graphics_id', ''),
            'scripts': [], 'texts': [], 'shared': [], 'usedBy': 0, 'file': ''}
    if not label or label == '0x0' or label == 'NULL':
        base['label'] = ''
        return base
    path = _find_script_file(label)
    if not path:
        base['missing'] = True
        return base
    lines = read_text(path).split('\n')
    blocks = _blocks(lines)
    by_label = {b['label']: b for b in blocks}
    texts_here = {e.label: e for e in text_db.entries(path)}
    all_texts = None

    order, seen = [label], {label}
    i = 0
    text_names, shared = [], []
    while i < len(order):
        b = by_label[order[i]]
        i += 1
        for tok in _code_tokens(_body(lines, b)):
            if tok in seen:
                continue
            if tok in texts_here:
                seen.add(tok)
                text_names.append(tok)
            elif tok in by_label:
                seen.add(tok)
                ob = by_label[tok]
                if ob['global'] and '_Movement_' not in tok and len(order) < MAX_SCRIPTS:
                    order.append(tok)
            elif '_Text_' in tok or '_EventScript_' in tok:
                if all_texts is None:
                    all_texts = {e.label: e for e in text_db.all()}
                seen.add(tok)
                if tok in all_texts:
                    text_names.append(tok)
                elif '_EventScript_' in tok:
                    shared.append(tok)

    base['file'] = os.path.relpath(path, ROOT)
    base['scripts'] = [{'label': n, 'code': _body(lines, by_label[n])} for n in order]
    texts = []
    for n in text_names:
        e = texts_here.get(n) or all_texts.get(n)
        texts.append(e.to_json())
    base['texts'] = texts
    base['shared'] = shared
    base['labels'] = list(by_label)
    map_index.refresh()
    base['usedBy'] = len(map_index.objects.get(label, []))
    return base


def save_scripts(file, scripts):
    """scripts: [{label, before, code}]. Replaces the lines under each label,
    but only when they still match what the editor showed (before)."""
    path = project_path(file)
    if path not in script_files():
        raise PersonError('That is not a script file.')
    lines = read_text(path).split('\n')
    by_label = {b['label']: b for b in _blocks(lines)}
    todo = []
    for s in scripts:
        b = by_label.get(s['label'])
        if not b:
            raise PersonError('Could not find %s any more. Reload the map.' % s['label'])
        if _body(lines, b).replace('\r', '') != s['before'].replace('\r', ''):
            raise PersonError('%s was changed somewhere else. Reload the map to see the new version.' % s['label'])
        code = s['code'].replace('\r\n', '\n').rstrip('\n')
        todo.append((b, code))
    for b, code in sorted(todo, key=lambda t: -t[0]['start']):
        lines[b['start'] + 1:b['end']] = code.split('\n') if code else []
    write_text(path, '\n'.join(lines))


def _script_name(name):
    words = re.sub(r'[^A-Za-z0-9 ]', ' ', name or '').split()
    return ''.join(w[0].upper() + w[1:] for w in words) or 'Person'


def new_script(map_folder, index, name, friendly):
    """Give someone with no script a simple 'talks to you' script."""
    from textdb import friendly_to_raw, split_string_lines
    if not re.match(r'^\w+$', map_folder):
        raise PersonError('Unknown map.')
    map_path = project_path('data/maps/%s/map.json' % map_folder)
    script_path = project_path('data/maps/%s/scripts.inc' % map_folder)
    if not os.path.exists(script_path):
        raise PersonError('This map has no script file.')
    text = read_text(map_path)
    data = json.loads(text)
    objs = data.get('object_events') or []
    idx = int(index)
    if idx >= len(objs):
        raise PersonError('That person is not on this map any more. Reload the map.')
    if objs[idx].get('script') not in (None, '', '0x0', 'NULL'):
        raise PersonError('This person already has a script.')
    script = read_text(script_path)
    taken = set(m.group(1) for m in re.finditer(r'^([A-Za-z_]\w*)::?', script, re.M))
    base = _script_name(name)
    label = '%s_EventScript_%s' % (map_folder, base)
    text_label = '%s_Text_%s' % (map_folder, base)
    n = 2
    while label in taken or text_label in taken:
        label = '%s_EventScript_%s%d' % (map_folder, base, n)
        text_label = '%s_Text_%s%d' % (map_folder, base, n)
        n += 1
    raw = friendly_to_raw(friendly or '...').replace('"', '\\"').replace('\\\\"', '\\"')
    block = '%s::\n\tmsgbox %s, MSGBOX_NPC\n\tend\n\n%s:\n%s\n' % (
        label, text_label, text_label, '\n'.join('\t.string "%s"' % c for c in split_string_lines(raw)))
    write_text(script_path, script.rstrip('\n') + '\n\n' + block)
    # change only that person's "script" value so map.json keeps its layout
    matches = list(re.finditer(r'"script"\s*:\s*"[^"]*"', text))
    objects_start = text.find('"object_events"')
    obj_matches = [m for m in matches if m.start() > objects_start]
    if objects_start >= 0 and len(obj_matches) >= len(objs) and all('script' in o for o in objs):
        m = obj_matches[idx]
        text = text[:m.start()] + '"script": "%s"' % label + text[m.end():]
    else:
        objs[idx]['script'] = label
        text = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    write_text(map_path, text)
    return label
