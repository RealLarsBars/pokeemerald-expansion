"""Reads the lists the editor offers in its dropdowns and galleries
(species, moves, items, trainer pictures, overworld sprites, ...)
straight from the project's C headers, so they always match the game."""

import os
import re

from common import ROOT, read_text, pretty_name

ENUM_RE_CACHE = {}


def _enum_constants(path, prefix, skip_aliases=True):
    """Constants named PREFIX_* defined in an enum or with #define, in file order."""
    text = read_text(path)
    found = []
    seen = set()
    for m in re.finditer(r'^\s*(?:#define\s+)?(' + prefix + r'_[A-Z0-9_]+)\b\s*(=\s*([^,\n]*))?', text, re.M):
        name, value = m.group(1), (m.group(3) or '').strip()
        if name in seen:
            continue
        if skip_aliases and value.startswith(prefix + '_'):
            continue  # alias of another constant
        if name.endswith(('_COUNT', '_START', '_END', '_FIRST', '_LAST')):
            continue
        seen.add(name)
        found.append(name)
    return found


def _named(consts, prefix, skip=('NONE',)):
    out = []
    for c in consts:
        suffix = c[len(prefix) + 1:]
        if suffix in skip:
            continue
        out.append({'const': c, 'name': pretty_name(suffix)})
    return out


def _guess_species_pic(const):
    parts = const[len('SPECIES_'):].lower().split('_')
    for n in range(len(parts), 0, -1):
        folder = 'graphics/pokemon/' + '/'.join(parts[:n])
        for fn in ('anim_front.png', 'front.png'):
            if os.path.exists(os.path.join(ROOT, folder, fn)):
                return folder + '/' + fn
    return ''


def _species():
    consts = _enum_constants(os.path.join(ROOT, 'include/constants/species.h'), 'SPECIES')
    consts = [c for c in consts if c not in ('SPECIES_NONE', 'SPECIES_EGG', 'SPECIES_SHINY_TAG')]

    # SPECIES_X -> (frontPic symbol, abilities)
    info = {}
    info_dir = os.path.join(ROOT, 'src/data/pokemon/species_info')
    for fn in sorted(os.listdir(info_dir)):
        if not fn.endswith('.h'):
            continue
        text = read_text(os.path.join(info_dir, fn))
        parts = re.split(r'\[(SPECIES_[A-Z0-9_]+)\]\s*=', text)
        for i in range(1, len(parts), 2):
            name, body = parts[i], parts[i + 1]
            pic = re.search(r'\.frontPic\s*=\s*(\w+)', body)
            abil = re.search(r'\.abilities\s*=\s*\{([^}]*)\}', body)
            entry = info.setdefault(name, {})
            if pic and 'pic' not in entry:
                entry['pic'] = pic.group(1)
            if abil and 'abilities' not in entry:
                entry['abilities'] = [a.strip() for a in abil.group(1).split(',')
                                      if a.strip().startswith('ABILITY_') and a.strip() != 'ABILITY_NONE']

    pic_paths = {}
    for m in re.finditer(r'(gMonFrontPic_\w+)\[\]\s*=\s*INCGFX_U32\("([^"]+)"',
                         read_text(os.path.join(ROOT, 'src/data/graphics/pokemon.h'))):
        pic_paths.setdefault(m.group(1), m.group(2))

    out = []
    for c in consts:
        entry = info.get(c, {})
        img = pic_paths.get(entry.get('pic', ''), '') or _guess_species_pic(c)
        out.append({
            'const': c,
            'name': pretty_name(c[len('SPECIES_'):]),
            'img': img,
            'abilities': entry.get('abilities', []),
        })
    return out


def _trainer_pics():
    gfx = read_text(os.path.join(ROOT, 'src/data/graphics/trainers.h'))
    paths = dict(re.findall(r'(gTrainerFrontPic_\w+)\[\]\s*=\s*INCGFX_U32\("([^"]+)"', gfx))
    out = []
    for m in re.finditer(r'\[(TRAINER_PIC_[A-Z0-9_]+)\]\s*=\s*\{\s*\.frontPic\s*=\s*TRAINER_FRONT_PIC\((\w+)', gfx):
        const, sym = m.group(1), m.group(2)
        if const == 'TRAINER_PIC_NONE':
            continue
        out.append({'const': const, 'name': pretty_name(const[len('TRAINER_PIC_'):]), 'img': paths.get(sym, '')})
    return out


def _overworld_gfx():
    base = os.path.join(ROOT, 'src/data/object_events')
    pointers = read_text(os.path.join(base, 'object_event_graphics_info_pointers.h'))
    info_text = read_text(os.path.join(base, 'object_event_graphics_info.h'))
    tables = read_text(os.path.join(base, 'object_event_pic_tables.h'))
    pics = read_text(os.path.join(base, 'object_event_graphics.h'))

    info = {}
    for m in re.finditer(r'(gObjectEventGraphicsInfo_\w+)\s*=\s*\{(.*?)\};', info_text, re.S):
        body = m.group(2)
        w = re.search(r'\.width\s*=\s*(\d+)', body)
        h = re.search(r'\.height\s*=\s*(\d+)', body)
        images = re.search(r'\.images\s*=\s*(\w+)', body)
        info[m.group(1)] = (int(w.group(1)) if w else 16, int(h.group(1)) if h else 32,
                            images.group(1) if images else '')
    table_pic = {}
    for m in re.finditer(r'(sPicTable_\w+)\[\]\s*=\s*\{(.*?)\};', tables, re.S):
        p = re.search(r'(gObjectEventPic_\w+)', m.group(2))
        if p:
            table_pic[m.group(1)] = p.group(1)
    pic_path = {}
    for sym, path in re.findall(r'(gObjectEventPic_\w+)\[\]\s*=\s*INC(?:GFX|BIN)_U32\("([^"]+)"', pics):
        path = re.sub(r'\.4bpp$', '.png', path)
        if os.path.exists(os.path.join(ROOT, path)):
            pic_path.setdefault(sym, path)

    out = []
    for m in re.finditer(r'\[(OBJ_EVENT_GFX_[A-Z0-9_]+)\]\s*=\s*&(\w+)', pointers):
        const, sym = m.group(1), m.group(2)
        w, h, table = info.get(sym, (16, 32, ''))
        img = pic_path.get(table_pic.get(table, ''), '')
        if not img:
            continue
        group = img.split('/')[-2] if '/' in img else ''
        out.append({'const': const, 'name': pretty_name(const[len('OBJ_EVENT_GFX_'):]),
                    'img': img, 'w': w, 'h': h, 'group': group})
    return out


def _ai_flags():
    consts = []
    for m in re.finditer(r'^#define\s+(AI_FLAG_[A-Z0-9_]+)\s', read_text(os.path.join(ROOT, 'include/constants/battle_ai.h')), re.M):
        if m.group(1) not in consts and m.group(1) not in ('AI_FLAG_COUNT',):
            consts.append(m.group(1))
    return _named(consts, 'AI_FLAG', skip=())


def _natures():
    text = read_text(os.path.join(ROOT, 'include/constants/pokemon.h'))
    consts = re.findall(r'^#define\s+(NATURE_[A-Z]+)\s+\d+', text, re.M)
    return [pretty_name(c[len('NATURE_'):]) for c in consts]


def _types():
    text = read_text(os.path.join(ROOT, 'include/constants/pokemon.h'))
    consts = re.findall(r'^\s*(TYPE_[A-Z]+)\s*=\s*\d+', text, re.M)
    return [pretty_name(c[5:]) for c in consts if c not in ('TYPE_NONE', 'TYPE_MYSTERY')]


def _balls():
    consts = _enum_constants(os.path.join(ROOT, 'include/constants/pokeball.h'), 'BALL')
    return [pretty_name(c[5:]) for c in consts if c != 'BALL_STRANGE']


def _maps():
    import glob
    import json
    from common import map_display_name
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'data/maps/*/map.json'))):
        try:
            mid = json.loads(read_text(path)).get('id', '')
        except ValueError:
            continue
        if mid:
            out.append({'const': mid, 'name': map_display_name(os.path.basename(os.path.dirname(path)))})
    return out


def _flags():
    text = read_text(os.path.join(ROOT, 'include/constants/flags.h'))
    return [f for f in re.findall(r'^#define\s+(FLAG_[A-Z0-9_]+)\s', text, re.M)
            if not f.startswith(('FLAG_UNUSED', 'FLAG_HIDDEN_ITEMS_START', 'FLAG_SPECIAL_FLAGS'))]


def _starting_status():
    text = read_text(os.path.join(ROOT, 'include/constants/battle.h'))
    return [pretty_name(c[len('STARTING_STATUS_'):]) for c in re.findall(r'F\((STARTING_STATUS_\w+)', text)]


def _gens():
    text = read_text(os.path.join(ROOT, 'include/config/general.h'))
    return re.findall(r'^#define\s+(GEN_(?:\d|LATEST|CHAMPIONS))\b', text, re.M)


def load():
    trainers_h = os.path.join(ROOT, 'include/constants/trainers.h')
    return {
        'species': _species(),
        'moves': _named(_enum_constants(os.path.join(ROOT, 'include/constants/moves.h'), 'MOVE'), 'MOVE'),
        'items': _named(_enum_constants(os.path.join(ROOT, 'include/constants/items.h'), 'ITEM'), 'ITEM'),
        'abilities': _named(_enum_constants(os.path.join(ROOT, 'include/constants/abilities.h'), 'ABILITY'), 'ABILITY'),
        'classes': _named(_enum_constants(trainers_h, 'TRAINER_CLASS'), 'TRAINER_CLASS', skip=()),
        'music': _named(_enum_constants(trainers_h, 'TRAINER_ENCOUNTER_MUSIC'), 'TRAINER_ENCOUNTER_MUSIC', skip=()),
        'trainerPics': _trainer_pics(),
        'overworld': _overworld_gfx(),
        'aiFlags': _ai_flags(),
        'natures': _natures(),
        'types': _types(),
        'balls': _balls(),
        'maps': _maps(),
        'flags': _flags(),
        'startingStatus': _starting_status(),
        'gens': _gens(),
    }
