"""Saved versions of the game folder, kept in git without touching your history.

- A version is a commit object of the whole folder (your edits included),
  stored under refs/emerald/versions/. Saving one never changes HEAD or
  what Update sees.
- Switching to a version, undoing Fun Modes and resetting to the base game
  all put the game files back from such a commit. The editor's own code
  (editor/, windows/, .github/) is never rolled back.
- Before any of those, the current folder is saved as an automatic version,
  so nothing is ever lost.
"""

import json
import os
import re
import subprocess
import tempfile
import time

from common import ROOT

TOOL_PATHS = ('editor', 'windows', '.github')
REF_PREFIX = 'refs/emerald/versions/'


def git(*args, env=None):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True, errors='replace',
                       env=dict(os.environ, **(env or {})))
    return r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip()


def _git_ok(*args, env=None):
    code, out, err = git(*args, env=env)
    if code != 0:
        raise RuntimeError(err or out or 'git %s failed' % args[0])
    return out


def _git_dir():
    return os.path.join(ROOT, _git_ok('rev-parse', '--git-dir'))


def _state_path():
    return os.path.join(_git_dir(), 'emerald-fun.json')


def load_state():
    try:
        with open(_state_path(), encoding='utf-8') as f:
            st = json.load(f)
    except (OSError, ValueError):
        st = {}
    st.setdefault('versions', [])
    st.setdefault('fun', {'before': None, 'applied': []})
    return st


def save_state(st):
    path = _state_path()
    with open(path + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(st, f, indent=1)
    os.replace(path + '.tmp', path)


def _ensure_identity():
    if git('config', 'user.email')[1] == '':
        git('config', 'user.email', 'editor@emerald.local')
        git('config', 'user.name', 'Emerald Editor')


def snapshot_commit(message):
    """Commit the current folder (tracked + new files) without touching HEAD or the index."""
    _ensure_identity()
    fd, index = tempfile.mkstemp(prefix='emerald-index-')
    os.close(fd)
    os.unlink(index)
    env = {'GIT_INDEX_FILE': index}
    try:
        code, head, _ = git('rev-parse', '--verify', '-q', 'HEAD')
        if code == 0:
            _git_ok('read-tree', 'HEAD', env=env)
        _git_ok('add', '-A', '.', env=env)
        tree = _git_ok('write-tree', env=env)
    finally:
        if os.path.exists(index):
            os.unlink(index)
    args = ['commit-tree', tree, '-m', message]
    if code == 0:
        args[2:2] = ['-p', head]
    return _git_ok(*args)


def _slug(name):
    s = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:40] or 'version'
    return '%s-%d' % (s, int(time.time() * 1000) % 10 ** 10)


def save_version(name, auto=False):
    name = (name or '').strip() or 'Untitled'
    commit = snapshot_commit('Emerald Editor version: ' + name)
    vid = _slug(name)
    _git_ok('update-ref', REF_PREFIX + vid, commit)
    st = load_state()
    st['versions'].insert(0, {'id': vid, 'name': name, 'time': int(time.time()), 'auto': auto,
                              'commit': commit})
    # keep at most 15 automatic versions
    autos = [v for v in st['versions'] if v.get('auto')]
    for old in autos[15:]:
        git('update-ref', '-d', REF_PREFIX + old['id'])
        st['versions'].remove(old)
    save_state(st)
    return vid


def list_versions():
    st = load_state()
    return [{k: v[k] for k in ('id', 'name', 'time', 'auto')} for v in st['versions']]


def delete_version(vid):
    st = load_state()
    st['versions'] = [v for v in st['versions'] if v['id'] != vid]
    git('update-ref', '-d', REF_PREFIX + vid)
    if st['fun'].get('before') == vid:
        st['fun'] = {'before': None, 'applied': []}
    save_state(st)


def _restore(commit):
    excludes = [':(exclude)%s' % p for p in TOOL_PATHS]
    _git_ok('restore', '--source=' + commit, '--staged', '--worktree', '--', '.', *excludes)
    git('reset', '-q')  # leave the index as it was (matching HEAD); only the files change


def switch_to(vid):
    st = load_state()
    v = next((v for v in st['versions'] if v['id'] == vid), None)
    if not v:
        raise KeyError('That version no longer exists.')
    save_version('Before switching to "%s"' % v['name'], auto=True)
    _restore(REF_PREFIX + vid)
    st = load_state()
    st['fun'] = {'before': None, 'applied': []}
    save_state(st)
    return v['name']


def base_commit():
    """The newest GitHub version that is part of this folder, without your own edits."""
    code, upstream, _ = git('rev-parse', '--abbrev-ref', 'origin/HEAD')
    upstream = upstream if code == 0 and upstream else 'origin/master'
    code, base, _ = git('merge-base', 'HEAD', upstream)
    if code == 0 and base:
        return base
    return _git_ok('rev-parse', 'HEAD')


def reset_to_base():
    save_version('Before reset to base game', auto=True)
    _restore(base_commit())
    st = load_state()
    st['fun'] = {'before': None, 'applied': []}
    save_state(st)


def base_file(rel):
    """Text of a file in the base game, or None."""
    code, out, _ = git('show', '%s:%s' % (base_commit(), rel))
    return out + '\n' if code == 0 else None


# ---- fun mode bookkeeping ----------------------------------------------------

def before_fun():
    """Save the folder before the first fun mode, once."""
    st = load_state()
    if not st['fun'].get('before'):
        vid = save_version('Before Fun Modes', auto=True)
        st = load_state()
        st['fun'] = {'before': vid, 'applied': []}
        save_state(st)


def record_fun(summary):
    st = load_state()
    st['fun']['applied'].append({'time': int(time.time()), 'summary': summary})
    save_state(st)


def fun_status():
    st = load_state()
    return {'active': bool(st['fun'].get('before')), 'applied': st['fun'].get('applied', [])}


def undo_fun():
    st = load_state()
    vid = st['fun'].get('before')
    if not vid:
        raise KeyError('No Fun Modes are applied right now.')
    save_version('Fun Modes (before undo)', auto=True)
    _restore(REF_PREFIX + vid)
    st = load_state()
    st['fun'] = {'before': None, 'applied': []}
    save_state(st)
