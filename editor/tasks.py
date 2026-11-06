"""Long-running jobs: building the game, opening it in mGBA, and updating the editor."""

import os
import signal
import subprocess
import threading
import time

import common
from common import ROOT

ROM = os.path.join(ROOT, 'pokeemerald.gba')


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = 'idle'   # idle | running | done | failed
        self.title = ''
        self.log = []
        self.message = ''
        self.proc = None      # the program the job is running right now, if any
        self.run_id = 0       # bumps on every start, so a stopped job cannot report back

    def snapshot(self, since=0):
        with self.lock:
            return {'state': self.state, 'title': self.title, 'message': self.message,
                    'log': self.log[since:], 'next': len(self.log)}

    def start(self, title, fn):
        with self.lock:
            if self.state == 'running':
                return False
            self.state, self.title, self.log, self.message = 'running', title, [], ''
            self.run_id += 1
            run_id = self.run_id
        threading.Thread(target=self._run, args=(fn, run_id), daemon=True).start()
        return True

    def _run(self, fn, run_id):
        try:
            ok, message = fn(self)
        except Exception as exc:  # report anything unexpected in the window
            ok, message = False, 'Something went wrong: %s' % exc
        with self.lock:
            if self.run_id == run_id and self.state == 'running':
                self.state = 'done' if ok else 'failed'
                self.message = message

    def stop(self):
        """Stops whatever is running (a stuck build, a save that never finished...)
        so the editor is free again. Always works, even if the job hangs."""
        with self.lock:
            proc, was = self.proc, self.state
            self.run_id += 1
            self.proc = None
            if was == 'running':
                self.state = 'failed'
                self.message = 'Stopped. You can start again whenever you like.'
                self.log.append('Stopped by you.')
        if proc and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                proc.wait(timeout=5)
            except Exception:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    pass
        return was == 'running'

    def write(self, line):
        with self.lock:
            self.log.append(line.rstrip('\n'))
            if len(self.log) > 4000:
                del self.log[:1000]


class QuietJob:
    """Stands in for Job when a step runs without the job panel (auto-sync)."""
    def __init__(self):
        self.proc = None
        self.editor_changed = False
        self.log = []

    def write(self, line):
        self.log.append(line)


def run(job, args, cwd=ROOT):
    proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors='replace', start_new_session=True)
    job.proc = proc
    try:
        for line in proc.stdout:
            job.write(line)
        return proc.wait()
    finally:
        if job.proc is proc:
            job.proc = None


def capture(args, timeout=None):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')   # never sit waiting for a password
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, errors='replace',
                           timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return 124, 'Timed out (no internet?)'
    return r.returncode, (r.stdout + r.stderr).strip()


# ---- build and play ---------------------------------------------------------

def build(job):
    job.write('Building your changes...')
    start = time.monotonic()
    common.watch_saves(True)
    try:
        code = run(job, ['make', '-j%d' % (os.cpu_count() or 2)])
    finally:
        # Anything saved mid-build may have been read before the change, so mark
        # it as changed again; the next build then picks it up.
        for path in common.watch_saves(False):
            try:
                os.utime(path)
            except OSError:
                pass
    took = _duration(time.monotonic() - start)
    if code != 0:
        return False, 'The build failed. The lines just above the end of the log say what is wrong.'
    job.write('Build took %s.' % took)
    return True, 'Build finished in %s.' % took


def _duration(seconds):
    seconds = int(round(seconds))
    if seconds < 60:
        return '1 second' if seconds == 1 else '%d seconds' % seconds
    return '%d min %d s' % (seconds // 60, seconds % 60)


def windows_path(linux_path):
    code, out = capture(['wslpath', '-w', linux_path])
    return out if code == 0 else linux_path


def linux_path(win_path):
    code, out = capture(['wslpath', '-u', win_path])
    return out if code == 0 else win_path


def play(job, mgba):
    ok, message = build(job)
    if not ok:
        return ok, message
    if not mgba:
        return True, 'Built! mGBA is not set up, so open pokeemerald.gba from your project folder in mGBA.'
    exe = linux_path(mgba)
    if not os.path.exists(exe):
        return True, 'Built! I could not find mGBA at %s. Run Setup.bat again to pick it.' % mgba
    subprocess.Popen([exe, windows_path(ROM)], cwd='/', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     stdin=subprocess.DEVNULL, start_new_session=True)
    job.write('Opening mGBA.')
    return True, 'Started the game. If an older mGBA window is still open, close it.'


# ---- updates ------------------------------------------------------------------

def _upstream():
    code, out = capture(['git', 'rev-parse', '--abbrev-ref', 'origin/HEAD'])
    return out if code == 0 and out else 'origin/master'


def check_updates():
    upstream = _upstream()
    branch = upstream.split('/', 1)[1]
    code, out = capture(['git', 'fetch', '--quiet', 'origin', branch], timeout=60)
    if code != 0:
        return {'ok': False, 'message': 'Could not reach GitHub: ' + out[-300:]}
    code, out = capture(['git', 'rev-list', '--count', 'HEAD..' + upstream])
    count = int(out) if code == 0 and out.isdigit() else 0
    code, log = capture(['git', 'log', '--format=%s', '-n', '10', 'HEAD..' + upstream])
    return {'ok': True, 'count': count, 'changes': log.splitlines() if count else []}


def save_my_changes(job=None, message='My changes (saved by Emerald Editor)'):
    """Commit the user's edits so an update can never overwrite them."""
    if capture(['git', 'config', 'user.email'])[1] == '':
        capture(['git', 'config', 'user.email', 'editor@emerald.local'])
        capture(['git', 'config', 'user.name', 'Emerald Editor'])
    capture(['git', 'add', '-A'])
    code, _ = capture(['git', 'diff', '--cached', '--quiet'])
    if code != 0:
        code, out = capture(['git', 'commit', '-q', '-m', message])
        if job:
            job.write('Saved your changes so far.' if code == 0 else out)
        return code == 0
    return True


def apply_update(job, auto=False):
    """Brings in new editor features. With auto (when the editor opens), it never
    asks anything: if an update touches the same lines you changed, it puts
    everything back the way it was and leaves it for the Update button."""
    info = check_updates()
    if not info['ok']:
        return False, info['message']
    if info['count'] == 0:
        return True, 'You already have the latest version.'
    import team
    if auto and team.merging():
        return True, 'Skipped: finish picking versions first.'
    job.write('Bringing in %d update(s)...' % info['count'])
    ok, msg = team.merge_in(job, _upstream(), 'update', save_my_changes, quiet=True)
    if not ok:
        return ok, msg
    if msg == 'conflict':
        if auto:
            team.git('merge', '--abort')
            team.git('config', '--unset', 'emerald.mergeWhy')
            team.git('config', '--unset', 'emerald.mergeBefore')
            job.write('An update touches lines you changed, so I left everything as it was.')
            return True, 'Skipped: an update changes lines you edited. Click Update to pick which to keep.'
        return False, ('An update changes the same lines you edited. Pick which version to keep '
                       'in the window that just opened.')
    return True, 'Updated! The editor will restart in a moment.'
