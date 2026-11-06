"""Recent changes: a list of every save made in the editor, each one undoable,
plus the last version of the game that built without errors.

Each entry is a commit of the whole game folder stored under
refs/emerald/history (a chain of its own, so HEAD, Update and Team never see
it). Saving one uses a separate git index kept in .git, so after the first time
git only looks at files that changed, which keeps it quick.

- record(label): after a save, note what changed (runs in the background).
- undo(entry): take back just that save, keeping everything done since.
- go_back(entry): put the whole game back to how it was just before that save.
- mark_good(): called before a build; when the build works, that snapshot
  becomes the "last version that worked".
The editor's own code (editor/, windows/, .github/) is never rolled back.
"""

import json
import os
import shutil
import subprocess
import threading
import time

from common import ROOT

TOOL_PATHS = ('editor', 'windows', '.github')
HISTORY_REF = 'refs/emerald/history'
GOOD_REF = 'refs/emerald/last-good'
MAX_ENTRIES = 300

_lock = threading.Lock()          # one snapshot at a time
_pending = []                     # labels waiting for the background snapshot
_pending_lock = threading.Lock()
_worker = None


class HistoryError(Exception):
    pass


def git(*args, env=None, input=None):
    r = subprocess.run(['git'] + list(args), cwd=ROOT, capture_output=True, text=True, errors='replace',
                       env=dict(os.environ, GIT_TERMINAL_PROMPT='0', **(env or {})), input=input)
    return r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip()


def _ok(*args, env=None, input=None):
    code, out, err = git(*args, env=env, input=input)
    if code != 0:
        raise HistoryError(err or out or 'git %s failed' % args[0])
    return out


def _git_dir():
    return os.path.join(ROOT, _ok('rev-parse', '--git-dir'))


def _state_path():
    return os.path.join(_git_dir(), 'emerald-history.json')


def _load():
    try:
        with open(_state_path(), encoding='utf-8') as f:
            st = json.load(f)
    except (OSError, ValueError):
        st = {}
    st.setdefault('entries', [])   # newest first
    return st


def _save(st):
    path = _state_path()
    with open(path + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(st, f, indent=1)
    os.replace(path + '.tmp', path)


def _ensure_identity():
    if git('config', 'user.email')[1] == '':
        git('config', 'user.email', 'editor@emerald.local')
        git('config', 'user.name', 'Emerald Editor')


def _tree_now():
    """Tree of the whole folder as it is now (new files included)."""
    index = os.path.join(_git_dir(), 'emerald-history-index')
    env = {'GIT_INDEX_FILE': index}
    if not os.path.exists(index):
        # Start from git's own index: it already knows which files are unchanged,
        # so only edited files get read.
        real = os.path.join(_git_dir(), 'index')
        if os.path.exists(real):
            shutil.copyfile(real, index)
    _ok('add', '-A', '.', env=env)
    return _ok('write-tree', env=env)


def _head_of_history():
    code, out, _ = git('rev-parse', '--verify', '-q', HISTORY_REF)
    return out if code == 0 else None


def _tree_of(commit):
    return _ok('rev-parse', commit + '^{tree}')


def _game_files_changed(a, b):
    excludes = [':(exclude)%s' % p for p in TOOL_PATHS]
    out = _ok('diff', '--name-only', a, b, '--', '.', *excludes)
    return [l for l in out.splitlines() if l]


def snapshot(label):
    """Commit the folder onto the history chain. Returns (commit, new_entry_or_None)."""
    with _lock:
        _ensure_identity()
        tree = _tree_now()
        prev = _head_of_history()
        if prev and _tree_of(prev) == tree:
            return prev, None
        args = ['commit-tree', tree, '-m', 'Emerald Editor: ' + (label or 'snapshot')]
        if prev:
            args[2:2] = ['-p', prev]
        commit = _ok(*args)
        _ok('update-ref', HISTORY_REF, commit)
        if not prev:
            return commit, None     # the very first snapshot is only the starting point
        files = _game_files_changed(prev, commit)
        if not files:
            return commit, None
        entry = {'id': commit, 'parent': prev, 'label': label or 'Other changes', 'time': int(time.time()),
                 'files': files[:50], 'fileCount': len(files)}
        st = _load()
        st['entries'].insert(0, entry)
        del st['entries'][MAX_ENTRIES:]
        _save(st)
        return commit, entry


def start():
    """Note how the game looks when the editor opens (in the background)."""
    threading.Thread(target=lambda: _quiet(snapshot, 'Changes made outside the editor'), daemon=True).start()


def _quiet(fn, *args):
    try:
        return fn(*args)
    except Exception:
        return None


def record(label):
    """Remember a save. Several quick saves in a row become one entry."""
    global _worker
    with _pending_lock:
        if label not in _pending:
            _pending.append(label)
        if _worker and _worker.is_alive():
            return
        _worker = threading.Thread(target=_drain, daemon=True)
        _worker.start()


def _drain():
    while True:
        time.sleep(0.3)
        with _pending_lock:
            labels = list(_pending)
            _pending.clear()
        if not labels:
            return
        label = labels[0] if len(labels) == 1 else '; '.join(labels[:3]) + (' and more' if len(labels) > 3 else '')
        _quiet(snapshot, label)


def flush():
    """Wait for background snapshots, then note anything still unrecorded."""
    w = _worker
    if w and w.is_alive():
        w.join(timeout=120)


def listing():
    st = _load()
    good = _good_commit()
    out = []
    import buildhelp
    for e in st['entries'][:120]:
        places = []
        for f in e['files']:
            try:
                w = buildhelp.place(f)['where']
            except Exception:
                w = f
            if w not in places:
                places.append(w)
        out.append({'id': e['id'], 'label': e['label'], 'time': e['time'], 'files': places[:6],
                    'fileCount': max(len(places), 0), 'undone': e.get('undone', False),
                    'worked': e['id'] == good})
    return {'entries': out, 'lastGood': _good_info()}


def _good_commit():
    code, out, _ = git('rev-parse', '--verify', '-q', GOOD_REF)
    return out if code == 0 else None


def _good_info():
    c = _good_commit()
    if not c:
        return None
    code, when, _ = git('log', '-1', '--format=%ct', c)
    return {'time': int(when) if code == 0 and when.isdigit() else 0}


def _find(entry_id):
    st = _load()
    e = next((e for e in st['entries'] if e['id'] == entry_id), None)
    if not e:
        raise HistoryError('That change is no longer in the list.')
    return st, e


def _excludes():
    return [':(exclude)%s' % p for p in TOOL_PATHS]


def undo(entry_id):
    """Take back one save, keeping everything changed since then."""
    flush()
    _st, e = _find(entry_id)
    snapshot('Before undoing "%s"' % e['label'])
    patch = subprocess.run(['git', 'diff', '--binary', e['parent'], e['id'], '--', '.'] + _excludes(),
                           cwd=ROOT, capture_output=True).stdout
    if not patch.strip():
        raise HistoryError('That change has nothing left to undo.')
    r = subprocess.run(['git', 'apply', '-R', '--binary', '--whitespace=nowarn'], cwd=ROOT, input=patch,
                       capture_output=True)
    if r.returncode != 0:
        raise HistoryError('Something you changed later touches the same spot, so I could not take back only '
                           'this change. Use "Go back to before this" instead (that also takes back what came after).')
    st = _load()
    for x in st['entries']:
        if x['id'] == entry_id:
            x['undone'] = True
    _save(st)
    snapshot('Undid: ' + e['label'])
    return e['label']


def _restore(commit):
    _ok('restore', '--source=' + commit, '--worktree', '--', '.', *_excludes())


def go_back(entry_id):
    """Put the whole game back to how it was just before this save."""
    flush()
    _st, e = _find(entry_id)
    snapshot('Before going back')
    _restore(e['parent'])
    snapshot('Went back to before "%s"' % e['label'])
    return e['label']


# ---- last version that built ------------------------------------------------

def before_build():
    """Snapshot what is about to be built. Returns the commit (or None)."""
    flush()
    c = _quiet(snapshot, 'Changes made outside the editor')
    return c[0] if c else None


def mark_good(commit):
    if commit:
        _quiet(_ok, 'update-ref', GOOD_REF, commit)


def has_good():
    return _good_commit() is not None


def restore_good():
    good = _good_commit()
    if not good:
        raise HistoryError('There is no version that built yet, so there is nothing to go back to.')
    flush()
    snapshot('Before going back to the last version that worked')
    _restore(good)
    snapshot('Went back to the last version that worked')


def changed_since_good():
    """Game files changed since the last version that built (newest first)."""
    good = _good_commit()
    if not good:
        return []
    try:
        with _lock:
            tree = _tree_now()
        out = _ok('diff', '--name-only', good, tree, '--', '.', *_excludes())
    except HistoryError:
        return []
    return [l for l in out.splitlines() if l]
