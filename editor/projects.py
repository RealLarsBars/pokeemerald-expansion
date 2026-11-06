"""Several games side by side: your own hack, team games, experiments.

Each project is a complete game folder (its own files, builds and saved
versions). The list lives in ~/.config/emerald-editor/projects.json. The
editor always starts from the folder Setup made; if you last opened another
project, it switches to that one straight away (see server.main).

New projects are made by copying a folder you already have with git, so the
big download does not happen again:
- "fresh": the original game plus the newest editor, without your edits.
- "copy": this game exactly as it is now, edits included.
"""

import json
import os
import re
import subprocess
import time

from common import ROOT

LIST_FILE = os.path.expanduser('~/.config/emerald-editor/projects.json')


def _read():
    try:
        with open(LIST_FILE, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    data.setdefault('projects', [])
    return data


def _write(data):
    os.makedirs(os.path.dirname(LIST_FILE), exist_ok=True)
    with open(LIST_FILE + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1)
    os.replace(LIST_FILE + '.tmp', LIST_FILE)


def _is_game(path):
    return os.path.isfile(os.path.join(path, 'editor', 'server.py')) and os.path.isdir(os.path.join(path, '.git'))


def _git(path, *args):
    r = subprocess.run(['git'] + list(args), cwd=path, capture_output=True, text=True, errors='replace')
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()


def _team_of(path):
    code, url = _git(path, 'remote', 'get-url', 'team')
    m = re.match(r'^https://github\.com/([^/]+/[^/]+?)(\.git)?/?$', url) if code == 0 else None
    return m.group(1) if m else ''


def _windows_path(path):
    r = subprocess.run(['wslpath', '-w', path], capture_output=True, text=True) if os.path.exists('/usr/bin/wslpath') else None
    return r.stdout.strip() if r and r.returncode == 0 else path


def _ensure(data):
    """Makes sure this folder (and the first, Setup-made one) are on the list."""
    paths = [p['path'] for p in data['projects']]
    if ROOT not in paths:
        data['projects'].insert(0 if not paths else len(paths), {
            'path': ROOT, 'name': 'My game' if not paths else os.path.basename(ROOT), 'added': int(time.time())})
    data.setdefault('home', data['projects'][0]['path'])
    return data


def listing():
    data = _ensure(_read())
    _write(data)
    out = []
    for p in data['projects']:
        ok = _is_game(p['path'])
        out.append({'path': p['path'], 'name': p['name'], 'current': p['path'] == ROOT, 'missing': not ok,
                    'team': _team_of(p['path']) if ok else '', 'where': _windows_path(p['path'])})
    return {'projects': out, 'current': ROOT}


def projects_dir():
    """New projects go next to the first game folder: e.g. ~/Emerald-Projects/<name>."""
    data = _ensure(_read())
    home = data.get('home') or ROOT
    return os.path.join(os.path.dirname(home), 'Emerald-Projects')


def _slug(name):
    # No spaces: the game's build tools do not like them in folder names.
    return re.sub(r'[^A-Za-z0-9._-]+', '-', name).strip('-.') or 'Game'


def create(job, name, kind, save_my_changes):
    name = re.sub(r'\s+', ' ', (name or '').strip())[:60]
    if not name:
        return False, 'Give the new project a name first.'
    data = _ensure(_read())
    if any(p['name'].lower() == name.lower() for p in data['projects']):
        return False, 'You already have a project called "%s". Pick another name.' % name
    base = os.path.join(projects_dir(), _slug(name))
    dest, n = base, 2
    while os.path.exists(dest):
        dest, n = '%s-%d' % (base, n), n + 1
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if kind == 'copy' and not save_my_changes(job, 'Saved before copying to a new project'):
        return False, 'Could not save this game first, so nothing was copied.'
    job.write('Making the new folder %s...' % _windows_path(dest))
    code, out = _git(ROOT, 'clone', '--quiet', ROOT, dest)
    if code != 0:
        return False, 'Could not make the folder: ' + out[-300:]
    _, url = _git(ROOT, 'remote', 'get-url', 'origin')
    if url:
        _git(dest, 'remote', 'set-url', 'origin', url)
    for key in ('user.name', 'user.email'):
        code, val = _git(ROOT, 'config', key)
        if code == 0 and val:
            _git(dest, 'config', key, val)
    if kind == 'fresh':
        # Start from the last editor version this folder got from GitHub (never your edits),
        # then try GitHub itself for anything newer.
        _git(dest, 'fetch', '--quiet', ROOT, '+refs/remotes/origin/*:refs/remotes/origin/*')
        job.write('Getting the newest editor and the original game...')
        if _git(dest, 'fetch', '--quiet', 'origin')[0] != 0:
            job.write('Could not reach GitHub, so using the newest editor version you already have.')
        if _git(dest, 'rev-parse', '--verify', '-q', 'origin/master')[0] != 0:
            return False, 'Could not find the original game to start from.'
        code, out = _git(dest, 'reset', '--quiet', '--hard', 'origin/master')
        if code != 0:
            return False, 'Could not set up the fresh game: ' + out[-300:]
    data['projects'].append({'path': dest, 'name': name, 'added': int(time.time())})
    _write(data)
    return True, 'Made "%s". Open it from Projects. The first Play builds the whole game, which takes a few minutes.' % name


def rename(path, name):
    name = re.sub(r'\s+', ' ', (name or '').strip())[:60]
    if not name:
        raise ValueError('Type a name.')
    data = _ensure(_read())
    for p in data['projects']:
        if p['path'] == path:
            p['name'] = name
    _write(data)


def forget(path):
    if path == ROOT:
        raise ValueError('You cannot remove the project that is open right now. Open another one first.')
    data = _ensure(_read())
    data['projects'] = [p for p in data['projects'] if p['path'] != path]
    _write(data)


def target(path):
    """The folder to switch to, checked against the list."""
    data = _ensure(_read())
    if path not in [p['path'] for p in data['projects']]:
        raise ValueError('That project is not on your list.')
    if not _is_game(path):
        raise ValueError('That project folder is missing or broken.')
    data['last'] = path
    _write(data)
    return path


def startup_target():
    """Where the editor should run: the project opened last time, if it is not this one."""
    data = _read()
    last = data.get('last')
    if last and last != ROOT and _is_game(last) and last in [p['path'] for p in data['projects']]:
        return last
    return None


def remember_current():
    data = _ensure(_read())
    data['last'] = ROOT
    _write(data)
