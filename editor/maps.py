"""Map data the editor needs: where each trainer stands, what they look like
in the overworld, and which texts they say. Also lists script files."""

import glob
import json
import os
import re

from common import ROOT, read_text, write_text, map_display_name, project_path  # noqa: F401
from textdb import LABEL_RE

BATTLE_RE = re.compile(r'^\s*(trainerbattle\w*)\s+(TRAINER_\w+)\s*(?:,\s*(.*))?$')


def script_files():
    files = sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/scripts.inc')))
    files += sorted(glob.glob(os.path.join(ROOT, 'data/scripts/*.inc')))
    return files


def script_file_list():
    out = []
    for f in script_files():
        rel = os.path.relpath(f, ROOT)
        parts = rel.split('/')
        if parts[1] == 'maps':
            out.append({'path': rel, 'name': map_display_name(parts[2]), 'group': 'Maps'})
        else:
            out.append({'path': rel, 'name': os.path.splitext(parts[-1])[0].replace('_', ' '), 'group': 'Shared scripts'})
    return out


class MapIndex:
    def __init__(self):
        self.stamp = None
        self.battles = {}   # TRAINER_X -> [{label, file, intro, defeat, macro}]
        self.objects = {}   # script label -> [{map, index, graphics_id}]

    def _stamp(self):
        newest = 0
        for f in script_files() + glob.glob(os.path.join(ROOT, 'data/maps/*/map.json')):
            newest = max(newest, os.path.getmtime(f))
        return newest

    def refresh(self):
        stamp = self._stamp()
        if stamp == self.stamp:
            return
        self.stamp = stamp
        self.battles = {}
        for f in script_files():
            label = None
            for line in read_text(f).split('\n'):
                m = LABEL_RE.match(line)
                if m:
                    label = m.group(1)
                    continue
                b = BATTLE_RE.match(line)
                if b and label:
                    macro, trainer, rest = b.group(1), b.group(2), b.group(3) or ''
                    args = [a.strip() for a in rest.split(',')]
                    intro = defeat = ''
                    if macro == 'trainerbattle_no_intro':
                        defeat = args[0] if args else ''
                    elif len(args) >= 2:
                        intro, defeat = args[0], args[1]
                    self.battles.setdefault(trainer, []).append({
                        'label': label, 'file': os.path.relpath(f, ROOT), 'macro': macro,
                        'intro': intro,
                        'defeat': defeat,
                    })
        self.objects = {}
        for path in sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/map.json'))):
            folder = os.path.basename(os.path.dirname(path))
            try:
                data = json.loads(read_text(path))
            except ValueError:
                continue
            for i, obj in enumerate(data.get('object_events', [])):
                script = obj.get('script')
                if script:
                    self.objects.setdefault(script, []).append({
                        'map': folder, 'mapName': map_display_name(folder), 'index': i,
                        'graphics_id': obj.get('graphics_id', ''),
                    })

    def trainer_appearances(self, trainer_id):
        self.refresh()
        out = []
        for b in self.battles.get(trainer_id, []):
            objs = self.objects.get(b['label'], [])
            out.append(dict(b, objects=objs))
        return out


def set_object_graphics(map_folder, index, graphics_id):
    if not re.match(r'^OBJ_EVENT_GFX_\w+$', graphics_id) or not re.match(r'^\w+$', map_folder):
        raise ValueError('bad sprite or map')
    path = project_path('data/maps/%s/map.json' % map_folder)
    text = read_text(path)
    data = json.loads(text)
    obj = data['object_events'][int(index)]
    old = obj.get('graphics_id')
    if old == graphics_id:
        return
    # Change only that one value so the rest of the file keeps its formatting.
    pattern = re.compile(r'"graphics_id"\s*:\s*"[^"]*"')
    matches = list(pattern.finditer(text))
    if len(matches) == len(data['object_events']) and all('"graphics_id"' in m.group(0) for m in matches):
        m = matches[int(index)]
        text = text[:m.start()] + '"graphics_id": "%s"' % graphics_id + text[m.end():]
    else:
        obj['graphics_id'] = graphics_id
        text = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    write_text(path, text)
