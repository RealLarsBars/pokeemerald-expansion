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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gamedata  # noqa: E402
import maps  # noqa: E402
import tasks  # noqa: E402
import textdb  # noqa: E402
import trainers  # noqa: E402
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
        self.restart_requested = False

    def gamedata(self):
        if self._gamedata is None:
            data = gamedata.load()
            data['charWidths'] = textdb.char_widths()
            data['textBoxWidth'] = textdb.TEXT_BOX_WIDTH
            self._gamedata = data
        return self._gamedata


STATE = None


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
        except Exception as e:  # keep the app alive, show the error
            self._send(500, {'error': '%s: %s' % (type(e).__name__, e)})

    def do_POST(self):
        # The custom header blocks other websites from posting here.
        if not self._host_ok() or self.headers.get('X-Emerald') != '1':
            return self._send(403, {'error': 'forbidden'})
        url = urlparse(self.path)
        try:
            self._post(url.path, self._body())
        except ApiError as e:
            self._send(e.status, {'error': str(e)})
        except Exception as e:
            self._send(500, {'error': '%s: %s' % (type(e).__name__, e)})

    # ---- GET ----
    def _get(self, path, q):
        S = STATE
        if path == '/' or path == '/index.html':
            return self._static('index.html')
        if path.startswith('/static/'):
            return self._static(path[len('/static/'):])
        if path == '/img':
            rel = q.get('path', '')
            if not rel.startswith('graphics/') or not rel.endswith('.png'):
                raise ApiError('bad image', 404)
            full = project_path(rel)
            if not os.path.exists(full):
                raise ApiError('missing image', 404)
            with open(full, 'rb') as f:
                return self._send(200, with_transparent_background(f.read()), 'image/png', cache=True)
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
        if path == '/api/text/search':
            return self._send(200, S.text.search(q.get('q', ''), q.get('case') == '1'))
        if path == '/api/text/get':
            e = S.text.find_label(q.get('label', ''), q.get('file') or None)
            if not e:
                raise ApiError('No text called ' + q.get('label', ''), 404)
            return self._send(200, e.to_json())
        if path == '/api/scripts':
            return self._send(200, maps.script_file_list())
        if path == '/api/script':
            full = script_path(q.get('path', ''))
            return self._send(200, {'path': q['path'], 'text': read_text(full)})
        if path == '/api/job':
            return self._send(200, S.job.snapshot(int(q.get('since', 0))))
        if path == '/api/updates':
            return self._send(200, tasks.check_updates())
        raise ApiError('Not found', 404)

    def _static(self, name):
        full = os.path.abspath(os.path.join(STATIC, name))
        if not full.startswith(STATIC + os.sep) or not os.path.isfile(full):
            raise ApiError('Not found', 404)
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        with open(full, 'rb') as f:
            self._send(200, f.read(), ctype)

    # ---- POST ----
    def _post(self, path, body):
        S = STATE
        if path == '/api/trainer':
            return self._send(200, save_trainer(body['id'], body))
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
        if path == '/api/script':
            full = script_path(body['path'])
            text = body['text'].replace('\r\n', '\n')
            with S.lock:
                write_text(full, text)
            return self._send(200, {'ok': True})
        if path == '/api/play':
            started = S.job.start('Play', lambda job: tasks.play(job, S.mgba))
            return self._send(200, {'started': started})
        if path == '/api/build':
            started = S.job.start('Build', tasks.build)
            return self._send(200, {'started': started})
        if path == '/api/update':
            def do_update(job):
                ok, msg = tasks.apply_update(job)
                if ok and msg.startswith('Updated'):
                    S.restart_requested = True
                return ok, msg
            started = S.job.start('Update', do_update)
            return self._send(200, {'started': started})
        raise ApiError('Not found', 404)


def main():
    global STATE
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--mgba', default=os.environ.get('EMERALD_MGBA', ''), help='Windows path to mGBA.exe')
    args = ap.parse_args()
    STATE = State(args.mgba)
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
                print('Restarting after update...', flush=True)
                os.execv(sys.executable, [sys.executable] + sys.argv)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
