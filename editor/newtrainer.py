"""Adds brand new trainers: an ID in include/constants/opponents.h, a team in
src/data/trainers.party, and (if a map is chosen) a person on that map with
a battle script and their lines in the map's scripts.inc.

The game keeps one "beaten" flag per trainer and only has room for a few
more before those flags would run into other flags, so new trainers use the
spare slots the game leaves free (9 in Emerald)."""

import os
import re

import mapview
from common import ROOT, read_text, write_text

OPPONENTS_H = os.path.join(ROOT, 'include/constants/opponents.h')
PARTY = os.path.join(ROOT, 'src/data/trainers.party')
FACING = {'down': 'MOVEMENT_TYPE_FACE_DOWN', 'up': 'MOVEMENT_TYPE_FACE_UP', 'left': 'MOVEMENT_TYPE_FACE_LEFT',
          'right': 'MOVEMENT_TYPE_FACE_RIGHT', 'around': 'MOVEMENT_TYPE_LOOK_AROUND'}


class NewTrainerError(Exception):
    pass


def _counts(text):
    c = re.search(r'#define TRAINERS_COUNT_EMERALD\s+(\d+)', text)
    m = re.search(r'#define MAX_TRAINERS_COUNT_EMERALD\s+(\d+)', text)
    if not c or not m:
        raise NewTrainerError('Could not find the trainer count in opponents.h.')
    return int(c.group(1)), int(m.group(1))


def room():
    count, maximum = _counts(read_text(OPPONENTS_H))
    return max(0, maximum - count)


def _const_name(name, text):
    base = 'TRAINER_' + (re.sub(r'[^A-Z0-9]+', '_', name.upper()).strip('_') or 'NEW')
    cand, n = base, 2
    while re.search(r'#define %s\b' % cand, text):
        cand = '%s_%d' % (base, n)
        n += 1
    return cand


def _script_name(name):
    return ''.join(w.capitalize() for w in re.findall(r'[A-Za-z0-9]+', name)) or 'Trainer'


def _string_lines(text):
    """Plain text -> .string lines (a blank line starts a new box)."""
    from textdb import friendly_to_raw, split_string_lines
    raw = friendly_to_raw(text).replace('"', '\\"')
    return split_string_lines(raw)


def create(info):
    """info: name, class, pic, gender, music, species, level, and optionally
    map, x, y, graphics_id, facing, sight, intro, defeat, after."""
    name = (info.get('name') or '').strip()[:12]
    if not name:
        raise NewTrainerError('Give the trainer a name.')
    opp = read_text(OPPONENTS_H)
    count, maximum = _counts(opp)
    if count >= maximum:
        raise NewTrainerError('The game has no room for more new trainers. You can still change any existing trainer.')
    const = _const_name(name, opp)

    # 1. the ID, right after the last trainer
    last = list(re.finditer(r'^#define TRAINER_\w+\s+\d+[ \t]*\n', opp, re.M))
    last = [m for m in last if int(re.search(r'(\d+)\s*$', m.group(0).strip()).group(1)) == count - 1]
    if not last:
        raise NewTrainerError('Could not find where to add the trainer in opponents.h.')
    at = last[-1].end()
    opp = opp[:at] + '#define %-35s %d\n' % (const, count) + opp[at:]
    opp = re.sub(r'(#define TRAINERS_COUNT_EMERALD\s+)\d+', lambda m: m.group(1) + str(count + 1), opp)

    # 2. the team
    species = (info.get('species') or 'Zigzagoon').strip()
    level = max(1, min(100, int(info.get('level') or 5)))
    block = ['=== %s ===' % const, 'Name: %s' % name.upper(), 'Class: %s' % (info.get('class') or 'Youngster'),
             'Pic: %s' % (info.get('pic') or 'Youngster'), 'Gender: %s' % (info.get('gender') or 'Male'),
             'Music: %s' % (info.get('music') or 'Male'), 'Double Battle: No', 'AI: Basic Trainer', '',
             species, 'Level: %d' % level, '']
    party = read_text(PARTY)
    party = party.rstrip('\n') + '\n\n' + '\n'.join(block)

    # 3. the person on the map, with their battle script
    folder = info.get('map') or ''
    map_data = script_path = script = None
    if folder:
        map_data = mapview.load_map(folder)
        objs = map_data.get('object_events') or []
        if len(objs) >= mapview.MAX_OBJECTS:
            raise NewTrainerError('That map is full.')
        layout = mapview.layouts()[map_data['layout']]
        x, y = int(info.get('x', 0)), int(info.get('y', 0))
        if not (0 <= x < layout['width'] and 0 <= y < layout['height']):
            raise NewTrainerError('Pick a spot on the map.')
        blocks = mapview.blockdata(layout)
        prefix = folder + '_'
        base = prefix + 'EventScript_' + _script_name(name)
        script_path = os.path.join(ROOT, 'data/maps', folder, 'scripts.inc')
        existing = read_text(script_path) if os.path.exists(script_path) else ''
        label, n = base, 2
        while re.search(r'^%s::?' % label, existing, re.M):
            label, n = '%s%d' % (base, n), n + 1
        tbase = prefix + 'Text_' + label[len(base) - len(_script_name(name)):]
        texts = [(tbase + 'Intro', info.get('intro') or "Hey! Let's battle!"),
                 (tbase + 'Defeat', info.get('defeat') or 'You win this time!'),
                 (tbase + 'PostBattle', info.get('after') or 'You are really strong!')]
        script = ['', '%s::' % label,
                  '\ttrainerbattle_single %s, %s, %s' % (const, texts[0][0], texts[1][0]),
                  '\tmsgbox %s, MSGBOX_AUTOCLOSE' % texts[2][0], '\tend', '']
        for tl, tx in texts:
            script.append('%s:' % tl)
            script.extend('\t.string "%s"' % l for l in _string_lines(tx))
            script.append('')
        script = existing.rstrip('\n') + '\n' + '\n'.join(script)
        objs.append({
            'graphics_id': info.get('graphics_id') or 'OBJ_EVENT_GFX_YOUNGSTER', 'x': x, 'y': y,
            'elevation': mapview._elevation(blocks, layout['width'], x, y),
            'movement_type': FACING.get(info.get('facing') or 'down', FACING['down']),
            'movement_range_x': 0, 'movement_range_y': 0, 'trainer_type': 'TRAINER_TYPE_NORMAL',
            'trainer_sight_or_berry_tree_id': str(max(1, min(8, int(info.get('sight') or 3)))),
            'script': label, 'flag': '0'})
        map_data['object_events'] = objs

    write_text(OPPONENTS_H, opp)
    write_text(PARTY, party)
    if map_data is not None:
        write_text(script_path, script)
        mapview.save_map(folder, map_data)
    return const
