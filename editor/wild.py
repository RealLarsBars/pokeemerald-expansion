"""Wild Pokemon: which Pokemon appear on each map in grass, on water, from
Rock Smash and on each fishing rod, at what levels, and how often.

Reads and writes src/data/wild_encounters.json (the same file the
randomizer changes), keeping its two-space layout."""

import json
import os
import re

from common import ROOT, read_text, write_text

WILD = os.path.join(ROOT, 'src/data/wild_encounters.json')
SECTIONS = [('land_mons', 'Grass and caves'), ('water_mons', 'Surfing'),
            ('rock_smash_mons', 'Rock Smash'), ('fishing_mons', 'Fishing')]
DEFAULT_RATE = {'land_mons': 20, 'water_mons': 4, 'rock_smash_mons': 20, 'fishing_mons': 30}
ROD_NAMES = {'old_rod': 'Old Rod', 'good_rod': 'Good Rod', 'super_rod': 'Super Rod'}


class WildError(Exception):
    pass


def _load():
    return json.loads(read_text(WILD))


def _main_group(data):
    for g in data['wild_encounter_groups']:
        if g.get('for_maps'):
            return g
    raise WildError('The wild Pokemon file has no map list.')


def slot_info(group):
    """For each section: the chance of every slot, and for fishing which rod it belongs to."""
    out = {}
    for f in group.get('fields', []):
        rates = f.get('encounter_rates', [])
        rods = [''] * len(rates)
        for rod, idxs in (f.get('groups') or {}).items():
            for i in idxs:
                if i < len(rods):
                    rods[i] = ROD_NAMES.get(rod, rod)
        # chance within the rod's own slots for fishing, within all slots otherwise
        chances = []
        for i, r in enumerate(rates):
            same = [rates[j] for j in range(len(rates)) if rods[j] == rods[i]]
            chances.append(round(100 * r / max(1, sum(same))))
        out[f['type']] = {'chances': chances, 'rods': rods}
    return out


def for_map(map_id):
    data = _load()
    g = _main_group(data)
    entries = [e for e in g['encounters'] if e.get('map') == map_id]
    return {'map': map_id, 'slots': slot_info(g), 'sections': [{'type': t, 'name': n} for t, n in SECTIONS],
            'entries': entries}


def _species_ok(s, valid):
    return valid is None or s in valid


def save(map_id, entries, valid_species=None, folder=None):
    """entries: the map's encounter tables, as for_map returned them (edited).
    Tables can be added for a map that had none, or removed."""
    if not re.match(r'^MAP_\w+$', map_id or ''):
        raise WildError('bad map')
    data = _load()
    g = _main_group(data)
    slots = slot_info(g)
    clean = []
    for e in entries:
        label = e.get('base_label') or ('g' + (folder or map_id.title().replace('_', '')))
        if not re.match(r'^\w+$', label):
            raise WildError('bad label')
        out = {'map': map_id, 'base_label': label}
        for key, name in SECTIONS:
            sec = e.get(key)
            if not sec:
                continue
            count = len(slots.get(key, {}).get('chances', []))
            mons = sec.get('mons') or []
            if len(mons) != count:
                raise WildError('%s needs exactly %d Pokemon.' % (name, count))
            fixed = []
            for i, m in enumerate(mons):
                sp = (m.get('species') or '').strip()
                if not sp.startswith('SPECIES_') or not _species_ok(sp, valid_species):
                    raise WildError('%s, slot %d: pick a Pokemon.' % (name, i + 1))
                lo, hi = int(m.get('min_level') or 1), int(m.get('max_level') or 1)
                lo, hi = max(1, min(100, lo)), max(1, min(100, hi))
                if lo > hi:
                    lo, hi = hi, lo
                fixed.append({'min_level': lo, 'max_level': hi, 'species': sp})
            rate = max(0, min(255, int(sec.get('encounter_rate') or DEFAULT_RATE[key])))
            out[key] = {'encounter_rate': rate, 'mons': fixed}
        if len(out) > 2:
            clean.append(out)
    # put the map's tables back where they were (or at the end for a new map)
    old = g['encounters']
    first = next((i for i, e in enumerate(old) if e.get('map') == map_id), len(old))
    rest = [e for e in old if e.get('map') != map_id]
    first = min(first, len(rest))
    g['encounters'] = rest[:first] + clean + rest[first:]
    write_text(WILD, json.dumps(data, indent=2) + '\n')
    return for_map(map_id)
