#!/usr/bin/env python3
"""Emerald Editor: a small local web app for editing this project.

Start it with the "Emerald Editor" desktop shortcut, or run
    python3 editor/server.py
and open http://localhost:8765 in a browser.
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import configs  # noqa: E402
import funmodes  # noqa: E402
import gamedata  # noqa: E402
import gifts  # noqa: E402
import history  # noqa: E402
import maps  # noqa: E402
import mapview  # noqa: E402
import pictures  # noqa: E402
import projects  # noqa: E402
import movesets  # noqa: E402
import movedit  # noqa: E402
import newtrainer  # noqa: E402
import npcscript  # noqa: E402
import shops  # noqa: E402
import wild  # noqa: E402
import species  # noqa: E402
import team  # noqa: E402
import tasks  # noqa: E402
import textdb  # noqa: E402
import trainers  # noqa: E402
import versions  # noqa: E402
from common import ROOT, project_path, read_text, write_text  # noqa: E402
from pngutil import with_transparent_background  # noqa: E402

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
ALLOWED_HOSTS = ('localhost', '127.0.0.1')


class State:
    def __init__(self, mgba):
        self.mgba = mgba
        self.lock = threading.Lock()
        self.party = trainers.PartyFile()
        self.text = textdb.TextDB()
        self.maps = maps.MapIndex()
        self.job = tasks.Job()
        self._gamedata = None
        self.map_list = None   # the Maps tab's list; cleared whenever something is saved
        self.restart_requested = False
        self.restart_target = None   # another project's folder to switch to

    def gamedata(self):
        if self._gamedata is None:
            data = gamedata.load()
            data['charWidths'] = textdb.char_widths()
            data['textBoxWidth'] = textdb.TEXT_BOX_WIDTH
            self._gamedata = data
        return self._gamedata


STATE = None
STATIC_TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8'}


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def trainer_detail(tid):
    S = STATE
    S.party.refresh()
    t = S.party.get(tid)
    if t is None:
        raise ApiError('No trainer called ' + tid, 404)
    t.pop('_tail', None)
    appearances = S.maps.trainer_appearances(tid)
    texts = {}
    for a in appearances:
        for key in ('intro', 'defeat'):
            label = a.get(key)
            if label and label not in texts:
                e = S.text.find_label(label)
                if e:
                    texts[label] = {'file': os.path.relpath(e.file, ROOT), 'text': e.friendly}
    t['appearances'] = appearances
    t['texts'] = texts
    return t


def save_trainer(tid, body):
    S = STATE
    with S.lock:
        S.party.refresh()
        S.party.put(tid, {'fields': body['fields'], 'party': body['party']})
        for change in body.get('sprites', []):
            maps.set_object_graphics(change['map'], change['index'], change['graphics_id'])
        for label, t in body.get('texts', {}).items():
            S.text.save(t['file'], label, t['text'])
    return trainer_detail(tid)


def make_competitive(body):
    """Builds strong sets for a team that is being edited (nothing is saved):
    best ability, four good moves, a fitting held item, nature, EVs and perfect IVs."""
    import random
    import fundata
    import sets
    party = [m for m in body.get('party', []) if (m.get('species') or '').strip()]
    for m in party:
        m['item'] = ''  # pick an item that suits the new set
        m.setdefault('moves', [])
        m.setdefault('extra', [])
    p = fundata.pool()
    sets.build_team(party, p, random.Random(), boss=True, doubles=bool(body.get('doubles')), items=True)
    return {'party': party}


def valid(kind):
    """Set of known constants (species, items, moves) for checking input."""
    return {x['const'] for x in STATE.gamedata()[kind]}


def map_page(folder):
    d = mapview.map_detail(folder, STATE.maps)
    d['wild'] = wild.for_map(d['id'])
    d['shops'] = shops.shops_for_map(folder)
    d['prices'] = shops.prices(sorted({i for sh in d['shops'] for i in sh['items']}))
    d['gifts'] = gifts.all_gifts(folder)
    d['trainerRoom'] = newtrainer.room()
    names = {}
    STATE.party.refresh()
    for o in d['objects']:
        if o['trainer'] and o['trainer'] not in names:
            t = STATE.party.get(o['trainer'])
            if t:
                names[o['trainer']] = '%s %s' % (trainers.field(t, 'Class'), trainers.field(t, 'Name'))
        o['trainerName'] = names.get(o['trainer'], '')
    return d


def _map_name(body):
    from common import map_display_name
    return map_display_name(str(body.get('map') or '')) or 'a map'


def _pretty_id(const, prefix):
    from common import const_to_name
    return const_to_name(prefix, str(const or ''))


def _trainer_label(body):
    fields = dict((f[0], f[1]) for f in body.get('fields') or [] if isinstance(f, (list, tuple)) and len(f) == 2)
    name = ('%s %s' % (fields.get('Class', ''), fields.get('Name', ''))).strip()
    return 'Trainer ' + (name or _pretty_id(body.get('id'), 'TRAINER'))


def _text_label(label):
    """LittlerootTown_Text_TownSign -> Littleroot Town: Town Sign"""
    from common import map_display_name
    head, sep, tail = str(label).partition('_Text_')
    if not sep:
        return map_display_name(str(label))
    return '%s: %s' % (map_display_name(head), map_display_name(tail))


def _script_label(path):
    from common import map_display_name
    parts = str(path).split('/')
    if len(parts) >= 4 and parts[1] == 'maps':
        return 'Script for ' + map_display_name(parts[2])
    return 'Script ' + os.path.splitext(parts[-1])[0].replace('_', ' ')


# What each save is called in Recent changes (None: the request saves nothing).
SAVE_LABELS = {
    '/api/trainer': _trainer_label,
    '/api/map/items': lambda b: 'Items on ' + _map_name(b),
    '/api/map/person': lambda b: 'Someone on %s (what they say or do)' % _map_name(b),
    '/api/map/person/new': lambda b: 'New lines for someone on ' + _map_name(b),
    '/api/map/warp': lambda b: 'A door on ' + _map_name(b),
    '/api/map/sign': lambda b: 'A sign on ' + _map_name(b),
    '/api/wild': lambda b: 'Wild Pokémon on ' + _map_name(b),
    '/api/shop': lambda b: 'Shop items and prices',
    '/api/gift': lambda b: 'Gift Pokémon',
    '/api/starters': lambda b: 'Starter Pokémon',
    '/api/trainer/new': lambda b: 'New trainer on ' + _map_name(b),
    '/api/trainer/room': lambda b: 'More room for new trainers',
    '/api/moves/tms': lambda b: 'TM & HM list',
    '/api/moves/species': lambda b: 'Moves %s can learn' % _pretty_id(b.get('id'), 'SPECIES'),
    '/api/text/save': lambda b: 'Text "%s"' % _text_label(b.get('label', '')),
    '/api/text/replace': lambda b: 'Replaced "%s" with "%s"' % (b.get('find', ''), b.get('replace', '')),
    '/api/species': lambda b: 'Pokémon data for %s' % _pretty_id(b.get('id'), 'SPECIES'),
    '/api/config': lambda b: 'Game settings (%s)' % os.path.basename(str(b.get('file', ''))),
    '/api/script': lambda b: _script_label(b.get('path', '')),
    '/api/move': lambda b: 'Move %s' % _pretty_id(b.get('id'), 'MOVE'),
    '/api/item': lambda b: 'Item %s' % _pretty_id(b.get('id'), 'ITEM'),
    '/api/picture': lambda b: ('New picture for %s' % b.get('name', b.get('kind', 'something'))) if b.get('save') else None,
    '/api/fun/run': lambda b: 'Fun Modes applied' if b.get('apply') else None,
    '/api/fun/undo': lambda b: 'Undid Fun Modes',
    '/api/fun/reset': lambda b: 'Reset to the base game',
    '/api/fun/version/switch': lambda b: 'Switched to a saved version',
    '/api/team/resolve': lambda b: "Picked versions after getting friends' changes",
}


def save_label(path, body):
    fn = SAVE_LABELS.get(path)
    if not fn:
        return None
    try:
        return fn(body if isinstance(body, dict) else {})
    except Exception:
        return 'A change'


def find_anything(q):
    """Top bar search: a few of the best matches of every kind."""
    S = STATE
    needle = q.strip().lower()
    if len(needle) < 2:
        return {}
    words = needle.split()

    def score(name, *extra):
        n = name.lower()
        hay = ' '.join([n] + [e.lower() for e in extra if e])
        if not all(w in hay for w in words):
            return None
        return 0 if n == needle else 1 if n.startswith(needle) else 2 if needle in n else 3

    best_score = {}

    def best(rows, limit=6, kind=None):
        rows = [r for r in rows if r[0] is not None]
        rows.sort(key=lambda r: (r[0], r[1]['name']))
        if kind and rows:
            best_score[kind] = rows[0][0]
        return [r[1] for r in rows[:limit]]

    out = {}
    S.party.refresh()
    pics = {p['const']: p.get('img') for p in S.gamedata()['trainerPics']}
    groups = {}
    for tid, text in S.party.blocks:
        t = trainers.summary(trainers.parse_block(text))
        name = ('%s %s' % (t['class'], t['name'])).strip() or tid
        sc = score(t['name'] or tid, t['class'], tid)
        if sc is None:
            continue
        g = groups.get(name)
        if g is None:
            groups[name] = g = [sc, {'id': tid, 'name': name, 'sub': '', 'img': pics.get(t['pic'])}, 0]
        g[2] += 1
        if sc < g[0]:
            g[0], g[1]['id'] = sc, tid
    for g in groups.values():
        g[1]['sub'] = '%d battles' % g[2] if g[2] > 1 else ''
    out['trainer'] = best([(g[0], g[1]) for g in groups.values()], kind='trainer')
    if S.map_list is None:
        S.map_list = mapview.map_list()
    out['map'] = best([(score(m['name'], m['map']), {'id': m['map'], 'name': m['name']}) for m in S.map_list], kind='map')
    gd = S.gamedata()
    out['species'] = best([(score(x['name'], x['const']), {'id': x['const'], 'name': x['name'], 'img': x.get('img')}) for x in gd['species']], kind='species')
    out['move'] = best([(score(x['name'], x['const']), {'id': x['const'], 'name': x['name']}) for x in gd['moves']], 5, 'move')
    out['item'] = best([(score(x['name'], x['const']), {'id': x['const'], 'name': x['name']}) for x in gd['items']], 5, 'item')
    texts = S.text.search(q.strip(), False, limit=6)
    out['text'] = [{'id': r['label'], 'q': q.strip(), 'name': (r['text'][:70] + ('...' if len(r['text']) > 70 else '')).replace('\n', ' '),
                    'sub': r['label']} for r in texts.get('results', [])[:6]]
    st = []
    for f in configs.files():
        for c in configs.read(f['file']):
            st.append((score(c['name'], c['help'], c['section']), {'id': c['name'], 'name': c['name'], 'sub': f['title']}))
    best_score['text'] = 2.5
    out['setting'] = best(st, 4, 'setting')
    out['script'] = best([(score(f['name'], f['path']), {'id': f['path'], 'name': f['name'], 'sub': f['path']})
                          for f in maps.script_file_list() if f['group'] != 'Maps'], 3, 'script')
    # Best matches first: "mudkip" shows the Pokémon before trainers who have one.
    out['order'] = sorted((k for k in out if out[k]), key=lambda k: best_score.get(k, 3))
    return out


ERRORS = (team.TeamError, history.HistoryError, movedit.MoveItemError, pictures.PictureError, mapview.MapError, wild.WildError, shops.ShopError, gifts.GiftError, movesets.MovesetError,
          newtrainer.NewTrainerError, npcscript.PersonError)


def script_path(rel):
    full = project_path(rel)
    if full not in maps.script_files():
        raise ApiError('That is not a script file.')
    return full


class Handler(BaseHTTPRequestHandler):
    server_version = 'EmeraldEditor/1'

    def log_message(self, fmt, *args):
        pass

    def _host_ok(self):
        host = (self.headers.get('Host') or '').split(':')[0]
        return host in ALLOWED_HOSTS

    def _send(self, status, body, ctype='application/json', cache=False):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode('utf-8')
        elif isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'max-age=86400' if cache else 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n) or b'{}')

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {'error': 'forbidden'})
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            self._get(url.path, q)
        except ApiError as e:
            self._send(e.status, {'error': str(e)})
        except ERRORS as e:
            self._send(400, {'error': str(e)})
        except Exception as e:  # keep the app alive, show the error
            traceback.print_exc()
            self._send(500, {'error': '%s: %s' % (type(e).__name__, e)})

    def do_POST(self):
        # The custom header blocks other websites from posting here.
        if not self._host_ok() or self.headers.get('X-Emerald') != '1':
            return self._send(403, {'error': 'forbidden'})
        url = urlparse(self.path)
        STATE.map_list = None
        try:
            body = self._body()
            self._post(url.path, body)
            label = save_label(url.path, body)
            if label:
                history.record(label)
        except ApiError as e:
            self._send(e.status, {'error': str(e)})
        except ERRORS as e:
            self._send(400, {'error': str(e)})
        except Exception as e:
            traceback.print_exc()
            self._send(500, {'error': '%s: %s' % (type(e).__name__, e)})

    def _fun(self, path, body):
        self._send(200, _fun_post(self, path, body))

    # ---- GET ----
    def _get(self, path, q):
        S = STATE
        if path == '/' or path == '/index.html':
            return self._static('index.html')
        if path.startswith('/static/'):
            return self._static(path[len('/static/'):])
        if path == '/api/rom':
            # The built game, for "Save as .gba" (the page writes it where the user chose).
            if not os.path.isfile(tasks.ROM):
                raise ApiError('The game has not been built yet.', 404)
            name = re.sub(r'[^A-Za-z0-9 ._-]', '', q.get('name', '')) or 'Emerald.gba'
            with open(tasks.ROM, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Disposition', 'attachment; filename="%s"' % name)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)
            return
        if path == '/img':
            rel = q.get('path', '')
            if not rel.startswith('graphics/') or not rel.endswith('.png'):
                raise ApiError('bad image', 404)
            full = project_path(rel)
            if not os.path.exists(full):
                raise ApiError('missing image', 404)
            # Pictures can be replaced (your own pictures), so the browser checks
            # whether one changed; unchanged ones are not sent again.
            stamp = str(int(os.path.getmtime(full)))
            if self.headers.get('If-None-Match') == stamp:
                self.send_response(304)
                self.send_header('ETag', stamp)
                self.end_headers()
                return
            with open(full, 'rb') as f:
                body = with_transparent_background(f.read())
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('ETag', stamp)
            self.end_headers()
            self.wfile.write(body)
            return
        if path == '/api/ping':
            return self._send(200, {'ok': True, 'root': ROOT, 'mgba': bool(S.mgba)})
        if path == '/api/gamedata':
            return self._send(200, S.gamedata())
        if path == '/api/trainers':
            S.party.refresh()
            S.maps.refresh()
            out = []
            for tid, text in S.party.blocks:
                t = trainers.summary(trainers.parse_block(text))
                battles = S.maps.battles.get(tid, [])
                places = [o['mapName'] for b in battles for o in S.maps.objects.get(b['label'], [])]
                if not places and battles:
                    places = [maps.map_display_name(b['file'].split('/')[2]) for b in battles if b['file'].startswith('data/maps/')]
                t['where'] = places[0] if places else ''
                t['rematch'] = bool(battles) and all('rematch' in (b['macro'] + b['label']).lower() for b in battles)
                out.append(t)
            return self._send(200, out)
        if path == '/api/trainer':
            return self._send(200, trainer_detail(q.get('id', '')))
        if path == '/api/maps':
            if S.map_list is not None:
                return self._send(200, S.map_list)
            out = mapview.map_list()
            wild_maps = {e['map'] for e in wild._main_group(wild._load())['encounters']}
            shop_maps, gift_maps = {}, {}
            for sh in shops.all_shops():
                shop_maps[sh['map']] = shop_maps.get(sh['map'], 0) + 1
            for g in gifts.all_gifts():
                gift_maps[g['map']] = gift_maps.get(g['map'], 0) + 1
            for m in out:
                m['wild'] = m['id'] in wild_maps
                m['shops'] = shop_maps.get(m['map'], 0)
                m['gifts'] = gift_maps.get(m['map'], 0)
            S.map_list = out
            return self._send(200, out)
        if path == '/api/map':
            return self._send(200, map_page(q.get('map', '')))
        if path == '/api/map/person':
            return self._send(200, npcscript.person(q.get('map', ''), q.get('index', '0'), S.text, S.maps))
        if path == '/api/map/sign':
            return self._send(200, npcscript.sign(q.get('map', ''), q.get('index', '0'), S.text, S.maps))
        if path == '/api/map/warps':
            return self._send(200, mapview.warps_of(q.get('map', '')))
        if path == '/api/mapimg':
            return self._send(200, mapview.map_image(q.get('map', '')), 'image/png')
        if path == '/api/starters':
            return self._send(200, gifts.starters())
        if path == '/api/gifts':
            return self._send(200, gifts.all_gifts())
        if path == '/api/shops':
            return self._send(200, shops.all_shops())
        if path == '/api/moves/tms':
            return self._send(200, dict(movesets.tm_list(), tutors=movesets.tutor_moves()))
        if path == '/api/moves/species':
            sp = species.read(q.get('id', ''))
            return self._send(200, {'teach': movesets.teachables(sp.get('teachSymbol'), sp.get('teachingType')),
                                    'egg': movesets.egg_moves(sp.get('eggSymbol'))})
        if path == '/api/text/search':
            return self._send(200, S.text.search(q.get('q', ''), q.get('case') == '1'))
        if path == '/api/text/get':
            e = S.text.find_label(q.get('label', ''), q.get('file') or None)
            if not e:
                raise ApiError('No text called ' + q.get('label', ''), 404)
            return self._send(200, e.to_json())
        if path == '/api/species':
            try:
                return self._send(200, species.read(q.get('id', '')))
            except species.SpeciesError as e:
                raise ApiError(str(e), 404)
        if path == '/api/specieslists':
            return self._send(200, species.lists())
        if path == '/api/configs':
            return self._send(200, configs.files())
        if path == '/api/config':
            return self._send(200, configs.read(q.get('file', '')))
        if path == '/api/config/search':
            needle = q.get('q', '').lower()
            out = []
            for f in configs.files():
                for st in configs.read(f['file']):
                    if needle in (st['name'] + ' ' + st['help'] + ' ' + st['section']).lower():
                        out.append(dict(st, file=f['file'], fileTitle=f['title']))
            return self._send(200, out[:300])
        if path == '/api/scripts':
            return self._send(200, maps.script_file_list())
        if path == '/api/script':
            full = script_path(q.get('path', ''))
            return self._send(200, {'path': q['path'], 'text': read_text(full)})
        if path == '/api/job':
            return self._send(200, S.job.snapshot(int(q.get('since', 0))))
        if path == '/api/updates':
            return self._send(200, tasks.check_updates())
        if path == '/api/projects':
            return self._send(200, projects.listing())
        if path == '/api/team':
            return self._send(200, team.status(fetch=q.get('fetch') == '1'))
        if path == '/api/team/details':
            return self._send(200, team.details())
        if path == '/api/team/invitations':
            return self._send(200, {'list': team.invitations()})
        if path == '/api/team/conflicts':
            return self._send(200, team.conflicts())
        if path == '/api/movesitems':
            return self._send(200, {'moves': movedit.move_list(), 'items': movedit.item_list()})
        if path == '/api/move':
            return self._send(200, movedit.read_move(q.get('id', '')))
        if path == '/api/item':
            return self._send(200, movedit.read_item(q.get('id', '')))
        if path == '/api/picture/info':
            return self._send(200, pictures.info(q.get('kind', ''), q.get('target', '')))
        if path == '/api/find':
            return self._send(200, find_anything(q.get('q', '')))
        if path == '/api/history':
            return self._send(200, history.listing())
        if path == '/api/fun/status':
            return self._send(200, {'fun': versions.fun_status(), 'versions': versions.list_versions()})
        raise ApiError('Not found', 404)

    def _static(self, name):
        full = os.path.abspath(os.path.join(STATIC, name))
        if not full.startswith(STATIC + os.sep) or not os.path.isfile(full):
            raise ApiError('Not found', 404)
        # Fixed types for the page's own files: some systems map .js oddly.
        ctype = STATIC_TYPES.get(os.path.splitext(full)[1]) or mimetypes.guess_type(full)[0] or 'application/octet-stream'
        with open(full, 'rb') as f:
            self._send(200, f.read(), ctype)

    # ---- POST ----
    def _post(self, path, body):
        S = STATE
        if path == '/api/trainer':
            return self._send(200, save_trainer(body['id'], body))
        if path == '/api/map/items':
            with S.lock:
                mapview.save_items(body['map'], body.get('items', []), valid('items'), body.get('moves') or {})
            return self._send(200, map_page(body['map']))
        if path == '/api/map/person':
            with S.lock:
                if body.get('scripts'):
                    npcscript.save_scripts(body['file'], body['scripts'])
                for t in body.get('texts') or []:
                    S.text.save(t['file'], t['label'], t['text'])
            return self._send(200, npcscript.person(body['map'], body['index'], S.text, S.maps))
        if path == '/api/map/warp':
            with S.lock:
                mapview.save_warp(body['map'], body['index'], body['dest'], body['destWarp'], bool(body.get('both')))
            return self._send(200, map_page(body['map']))
        if path == '/api/map/sign':
            with S.lock:
                if body.get('scripts'):
                    npcscript.save_scripts(body['file'], body['scripts'])
                for t in body.get('texts') or []:
                    S.text.save(t['file'], t['label'], t['text'])
            return self._send(200, npcscript.sign(body['map'], body['index'], S.text, S.maps))
        if path == '/api/map/person/new':
            with S.lock:
                npcscript.new_script(body['map'], body['index'], body.get('name', ''), body.get('text', ''))
            return self._send(200, npcscript.person(body['map'], body['index'], S.text, S.maps))
        if path == '/api/wild':
            with S.lock:
                wild.save(body['id'], body.get('entries', []), valid('species'), body.get('map'))
            return self._send(200, map_page(body['map']) if body.get('map') else {'ok': True})
        if path == '/api/shop':
            with S.lock:
                items = shops.save_shop(body['file'], body['label'], body.get('items', []), valid('items'))
                if body.get('prices'):
                    shops.set_prices({k: v for k, v in body['prices'].items() if v is not None and str(v) != ''})
            return self._send(200, {'items': items, 'prices': shops.prices(items)})
        if path == '/api/gift':
            with S.lock:
                gifts.save_gift(body['file'], int(body['line']), body.get('expect', ''), body['species'],
                                body.get('level'), body.get('item'), valid('species'), valid('items'))
            return self._send(200, {'ok': True})
        if path == '/api/starters':
            with S.lock:
                return self._send(200, gifts.save_starters(body['species'], body.get('level', 5), valid('species')))
        if path == '/api/trainer/room':
            with S.lock:
                return self._send(200, newtrainer.add_room())
        if path == '/api/trainer/new':
            with S.lock:
                const = newtrainer.create(body)
            S._gamedata = None
            return self._send(200, {'id': const})
        if path == '/api/moves/tms':
            with S.lock:
                return self._send(200, movesets.save_tm_list(body['tms'], body['hms'], valid('moves')))
        if path == '/api/moves/species':
            sp = species.read(body['id'])
            with S.lock:
                if 'add' in body or 'remove' in body:
                    movesets.save_teachables(sp.get('teachSymbol'), body.get('add', []), body.get('remove', []), valid('moves'))
                if 'egg' in body:
                    movesets.save_egg_moves(sp.get('eggSymbol'), body['egg'], valid('moves'))
            return self._send(200, {'teach': movesets.teachables(sp.get('teachSymbol'), sp.get('teachingType')),
                                    'egg': movesets.egg_moves(sp.get('eggSymbol'))})
        if path == '/api/move':
            with S.lock:
                return self._send(200, movedit.save_move(body['id'], body.get('changes') or {},
                                                         {'TYPE_' + t.upper().replace(' ', '_') for t in S.gamedata()['types']} | set(S.gamedata()['types'])))
        if path == '/api/item':
            with S.lock:
                return self._send(200, movedit.save_item(body['id'], body.get('changes') or {}))
        if path == '/api/picture':
            with S.lock:
                res = pictures.convert(body, bool(body.get('save')))
            if body.get('save'):
                S._gamedata = None
            return self._send(200, res)
        if path == '/api/trainer/competitive':
            return self._send(200, make_competitive(body))
        if path == '/api/showdown':
            party, warnings = trainers.parse_showdown(body.get('text', ''))
            return self._send(200, {'party': party, 'warnings': warnings})
        if path == '/api/showdown/export':
            text = '\n\n'.join(trainers.serialize_mon(m) for m in body.get('party', []))
            return self._send(200, {'text': text})
        if path == '/api/text/save':
            with S.lock:
                changed = S.text.save(body['file'], body['label'], body['text'])
            return self._send(200, {'changed': changed})
        if path == '/api/text/replace':
            with S.lock:
                n = S.text.replace_all(body['find'], body['replace'], bool(body.get('case')), body['targets'])
            return self._send(200, {'changed': n})
        if path == '/api/species':
            try:
                with S.lock:
                    data = species.save(body['id'], body['changes'])
            except species.SpeciesError as e:
                raise ApiError(str(e))
            S._gamedata = None  # abilities shown in the trainer editor may have changed
            return self._send(200, data)
        if path == '/api/config':
            with S.lock:
                changed = configs.save(body['file'], body['changes'])
            return self._send(200, {'changed': changed})
        if path == '/api/script':
            full = script_path(body['path'])
            text = body['text'].replace('\r\n', '\n')
            with S.lock:
                write_text(full, text)
            return self._send(200, {'ok': True})
        if path.startswith('/api/history/'):
            return self._send(200, _history_post(path, body))
        if path.startswith('/api/fun/'):
            return self._fun(path, body)
        if path.startswith('/api/projects/'):
            return self._send(200, _projects_post(path, body))
        if path.startswith('/api/team/'):
            return self._send(200, _team_post(path, body))
        if path == '/api/play':
            if team.merging():
                raise ApiError('Finish picking which versions to keep first (click Team at the top).')
            started = S.job.start('Play', lambda job: tasks.play(job, S.mgba))
            return self._send(200, {'started': started})
        if path == '/api/build':
            if team.merging():
                raise ApiError('Finish picking which versions to keep first (click Team at the top).')
            started = S.job.start('Build', tasks.build)
            return self._send(200, {'started': started})
        if path == '/api/job/stop':
            return self._send(200, {'stopped': S.job.stop()})
        if path == '/api/update':
            auto = bool(body.get('auto')) if isinstance(body, dict) else False

            def do_update(job):
                ok, msg = tasks.apply_update(job, auto=auto)
                _fun_changed()
                history.record('Editor update')
                if ok and msg.startswith('Updated'):
                    S.restart_requested = True
                return ok, msg
            started = S.job.start('Update', do_update)
            return self._send(200, {'started': started})
        raise ApiError('Not found', 404)


def _history_post(path, body):
    S = STATE
    if S.job.snapshot()['state'] == 'running':
        raise ApiError('Wait for the editor to finish what it is doing first.')
    if team.merging():
        raise ApiError('Finish picking versions first (click Team at the top).')
    with S.lock:
        if path == '/api/history/undo':
            label = history.undo(body['id'])
            msg = 'Took back: ' + label
        elif path == '/api/history/goback':
            label = history.go_back(body['id'])
            msg = 'Your game is back to how it was before: ' + label
        elif path == '/api/history/lastgood':
            history.restore_good()
            msg = 'Your game is back to the last version that worked.'
        else:
            raise ApiError('Not found', 404)
    _fun_changed()
    return {'ok': True, 'message': msg}


def _fun_changed():
    """Files changed underneath the editor: drop cached lists."""
    STATE._gamedata = None


def _team_job(title, fn):
    """Runs a team step in the job panel; restarts the editor if it got new editor code."""
    S = STATE

    def wrapped(job):
        job.editor_changed = False
        try:
            ok, msg = fn(job)
        finally:
            _fun_changed()
            history.record(title)
        if job.editor_changed:
            S.restart_requested = True
            msg = (msg + ' ' if msg else '') + 'They include a newer editor, so it will restart in a moment.'
        return ok, msg
    return {'started': S.job.start(title, wrapped)}


def _projects_post(path, body):
    S = STATE
    if path == '/api/projects/create':
        return {'started': S.job.start('New project', lambda job: projects.create(
            job, body.get('name', ''), body.get('kind', 'fresh'), tasks.save_my_changes))}
    try:
        if path == '/api/projects/rename':
            projects.rename(body['path'], body.get('name', ''))
            return {'ok': True}
        if path == '/api/projects/forget':
            projects.forget(body['path'])
            return {'ok': True}
        if path == '/api/projects/open':
            if S.job.snapshot()['state'] == 'running':
                raise ApiError('Wait for the editor to finish what it is doing first.')
            S.restart_target = projects.target(body['path'])
            S.restart_requested = True
            return {'ok': True}
    except (KeyError, ValueError) as e:
        raise ApiError(str(e).strip("'"))
    raise ApiError('Not found', 404)


def _team_post(path, body):
    S = STATE
    save = tasks.save_my_changes
    if path == '/api/team/signin':
        return team.sign_in(body.get('token', ''))
    if path == '/api/team/signout':
        team.sign_out()
        return {'ok': True}
    if path == '/api/team/code':
        return team.make_code(body.get('token', ''))
    if path == '/api/team/joincode':
        return _team_job('Join a team game', lambda job: team.join_with_code(job, body.get('code', ''), body.get('name', ''), save))
    if path == '/api/team/invite':
        return {'message': team.invite(body.get('login', ''))}
    if path == '/api/team/remove':
        team.remove(body.get('login', ''), body.get('inviteId'))
        return {'ok': True}
    if path == '/api/team/create':
        return _team_job('Start a team game', lambda job: team.create(job, body.get('name', ''), save))
    if path == '/api/team/join':
        return _team_job('Join a team game', lambda job: team.join(job, body['repo'], body.get('inviteId'), save))
    if path == '/api/team/share':
        return _team_job('Share my changes', lambda job: team.share(job, body.get('note', ''), save))
    if path == '/api/team/get':
        return _team_job("Get friends' changes", lambda job: team.get_changes(job, save))
    if path == '/api/team/auto':
        team.set_auto(bool(body.get('on')))
        return {'auto': team.auto_on()}
    if path == '/api/team/sync':
        # Quiet auto-sync from the page; skipped while anything else is going on.
        if S.job.snapshot()['state'] == 'running' or not team.auto_on():
            return {'skipped': True}
        job = tasks.QuietJob()
        with S.lock:
            res = team.sync(job, save)
        if res.get('got') or res.get('conflict'):
            _fun_changed()
            history.record("Friends' changes")
        if job.editor_changed and not res.get('conflict'):
            S.restart_requested = True
            res['restarting'] = True
        return res
    if S.job.snapshot()['state'] == 'running':
        raise ApiError('Wait for the editor to finish what it is doing first.')
    with S.lock:
        if path == '/api/team/resolve':
            res = team.resolve(body.get('choices') or {}, save)
            _fun_changed()
            if res['editorChanged']:
                S.restart_requested = True
            return res
        if path == '/api/team/cancel':
            team.cancel_merge()
            _fun_changed()
            return {'ok': True}
        if path == '/api/team/leave':
            team.leave()
            return {'ok': True}
    raise ApiError('Not found', 404)


def _fun_post(handler, path, body):
    S = STATE
    if S.job.snapshot()['state'] == 'running':
        raise ApiError('Wait for the current build or update to finish first.')
    if team.merging():
        raise ApiError('Finish picking versions first (click Team at the top).')
    with S.lock:
        try:
            if path == '/api/fun/run':
                res = funmodes.run(body.get('settings') or {}, bool(body.get('apply')))
                if res['applied']:
                    _fun_changed()
                return res
            if path == '/api/fun/undo':
                versions.undo_fun()
            elif path == '/api/fun/reset':
                versions.reset_to_base()
            elif path == '/api/fun/version/save':
                versions.save_version(body.get('name', ''))
            elif path == '/api/fun/version/switch':
                versions.switch_to(body['id'])
            elif path == '/api/fun/version/delete':
                versions.delete_version(body['id'])
            else:
                raise ApiError('Not found', 404)
        except (KeyError, ValueError, RuntimeError) as e:
            raise ApiError(str(e).strip("'"))
        _fun_changed()
        return {'ok': True}


def _switch_to(folder):
    """Runs the editor from another project's folder (its own editor code and game)."""
    script = os.path.join(folder, 'editor', 'server.py')
    os.chdir(folder)
    os.execv(sys.executable, [sys.executable, script] + sys.argv[1:])


def main():
    global STATE
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--mgba', default=os.environ.get('EMERALD_MGBA', ''), help='Windows path to mGBA.exe')
    args = ap.parse_args()
    # Open the project used last time (Setup always starts the editor in its own folder).
    other = projects.startup_target()
    if other:
        _switch_to(other)
    STATE = State(args.mgba)
    history.start()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print('Emerald Editor is running at http://localhost:%d  (keep this window open)' % args.port, flush=True)
    try:
        while True:
            time.sleep(0.5)
            if STATE.restart_requested:
                time.sleep(1.5)  # let the page read the final job state
                server.shutdown()
                server.server_close()
                if STATE.restart_target and STATE.restart_target != ROOT:
                    print('Opening project %s...' % STATE.restart_target, flush=True)
                    _switch_to(STATE.restart_target)
                print('Restarting after update...', flush=True)
                os.execv(sys.executable, [sys.executable] + sys.argv)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
