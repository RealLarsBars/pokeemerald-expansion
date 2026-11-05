"""Long-running jobs: building the game, opening it in mGBA, and updating the editor."""

import base64
import json
import ntpath
import os
import shutil
import subprocess
import threading
import time

from common import ROOT

ROM = os.path.join(ROOT, 'pokeemerald.gba')


class Job:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = 'idle'   # idle | running | done | failed
        self.title = ''
        self.log = []
        self.message = ''

    def snapshot(self, since=0):
        with self.lock:
            return {'state': self.state, 'title': self.title, 'message': self.message,
                    'log': self.log[since:], 'next': len(self.log)}

    def start(self, title, fn):
        with self.lock:
            if self.state == 'running':
                return False
            self.state, self.title, self.log, self.message = 'running', title, [], ''
        threading.Thread(target=self._run, args=(fn,), daemon=True).start()
        return True

    def _run(self, fn):
        try:
            ok, message = fn(self)
        except Exception as exc:  # report anything unexpected in the window
            ok, message = False, 'Something went wrong: %s' % exc
        with self.lock:
            self.state = 'done' if ok else 'failed'
            self.message = message

    def write(self, line):
        with self.lock:
            self.log.append(line.rstrip('\n'))
            if len(self.log) > 4000:
                del self.log[:1000]


def run(job, args, cwd=ROOT):
    proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, errors='replace')
    for line in proc.stdout:
        job.write(line)
    return proc.wait()


def capture(args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, errors='replace')
    return r.returncode, (r.stdout + r.stderr).strip()


# ---- build and play ---------------------------------------------------------

def build(job):
    job.write('Building your changes...')
    code = run(job, ['make', '-j%d' % (os.cpu_count() or 2)])
    if code != 0:
        return False, 'The build failed. The lines just above the end of the log say what is wrong.'
    return True, 'Build finished.'


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


# ---- save a copy of the game as a new .gba ---------------------------------

EXPORT_SETTINGS = os.path.join(os.path.expanduser('~'), '.emerald-editor.json')
EXPORT_DIR = os.path.join(ROOT, 'my-builds')   # used when no Windows dialog is available


def _settings():
    try:
        with open(EXPORT_SETTINGS, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_settings(data):
    try:
        with open(EXPORT_SETTINGS, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except OSError:
        pass


def _ask_where_to_save(default_name, start_dir):
    """Shows a Windows "Save as" box and returns the chosen Windows path,
    '' if the user cancelled, or None if no Windows dialog is available."""
    ps = shutil.which('powershell.exe')
    if not ps:
        return None
    script = (
        "[Console]::OutputEncoding = [Text.Encoding]::UTF8\n"
        "Add-Type -AssemblyName System.Windows.Forms\n"
        "$owner = New-Object System.Windows.Forms.Form -Property @{ TopMost = $true }\n"
        "$d = New-Object System.Windows.Forms.SaveFileDialog\n"
        "$d.Title = 'Save your game as'\n"
        "$d.Filter = 'Game Boy Advance game (*.gba)|*.gba'\n"
        "$d.DefaultExt = 'gba'\n"
        "$d.OverwritePrompt = $true\n"
        "$d.FileName = %s\n"
        "%s"
        "if ($d.ShowDialog($owner) -eq 'OK') { $d.FileName }\n"
    ) % (_ps_quote(default_name),
         ("$d.InitialDirectory = %s\n" % _ps_quote(start_dir)) if start_dir else '')
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    cwd = '/mnt/c' if os.path.isdir('/mnt/c') else '/'
    r = subprocess.run([ps, '-NoProfile', '-STA', '-EncodedCommand', encoded], cwd=cwd,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    return lines[-1] if lines else ''


def _ps_quote(text):
    return "'" + text.replace("'", "''") + "'"


def export(job):
    """Builds the game and saves it as a new .gba file where the user picks."""
    ok, message = build(job)
    if not ok:
        return ok, message
    name = time.strftime('Emerald %Y-%m-%d %H%M.gba')
    settings = _settings()
    job.write('Asking where to save it (look for the "Save your game as" window)...')
    chosen = _ask_where_to_save(name, settings.get('exportDir', ''))
    if chosen == '':
        return True, 'Built, but not saved anywhere because the save window was cancelled.'
    if chosen is None:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        target = os.path.join(EXPORT_DIR, name)
        shown = target
    else:
        target = linux_path(chosen)
        shown = chosen
        settings['exportDir'] = ntpath.dirname(chosen)
        _save_settings(settings)
    shutil.copyfile(ROM, target)
    job.write('Saved %s' % shown)
    return True, 'Saved your game as %s' % shown


# ---- updates ------------------------------------------------------------------

def _upstream():
    code, out = capture(['git', 'rev-parse', '--abbrev-ref', 'origin/HEAD'])
    return out if code == 0 and out else 'origin/master'


def check_updates():
    upstream = _upstream()
    branch = upstream.split('/', 1)[1]
    code, out = capture(['git', 'fetch', '--quiet', 'origin', branch])
    if code != 0:
        return {'ok': False, 'message': 'Could not reach GitHub: ' + out[-300:]}
    code, out = capture(['git', 'rev-list', '--count', 'HEAD..' + upstream])
    count = int(out) if code == 0 and out.isdigit() else 0
    code, log = capture(['git', 'log', '--format=%s', '-n', '10', 'HEAD..' + upstream])
    return {'ok': True, 'count': count, 'changes': log.splitlines() if count else []}


def save_my_changes(job=None):
    """Commit the user's edits so an update can never overwrite them."""
    if capture(['git', 'config', 'user.email'])[1] == '':
        capture(['git', 'config', 'user.email', 'editor@emerald.local'])
        capture(['git', 'config', 'user.name', 'Emerald Editor'])
    capture(['git', 'add', '-A'])
    code, _ = capture(['git', 'diff', '--cached', '--quiet'])
    if code != 0:
        code, out = capture(['git', 'commit', '-q', '-m', 'My changes (saved by Emerald Editor)'])
        if job:
            job.write('Saved your changes so far.' if code == 0 else out)
        return code == 0
    return True


def apply_update(job):
    info = check_updates()
    if not info['ok']:
        return False, info['message']
    if info['count'] == 0:
        return True, 'You already have the latest version.'
    if not save_my_changes(job):
        return False, 'Could not save your changes before updating, so nothing was changed.'
    upstream = _upstream()
    job.write('Bringing in %d update(s)...' % info['count'])
    code = run(job, ['git', 'merge', '--no-edit', upstream])
    if code != 0:
        _, files = capture(['git', 'diff', '--name-only', '--diff-filter=U'])
        capture(['git', 'merge', '--abort'])
        return False, ('The update changes the same lines you edited in: %s. Nothing was changed. '
                       'Ask Claude in your project to help combine them.' % ', '.join(files.splitlines()))
    return True, 'Updated! The editor will restart in a moment.'
