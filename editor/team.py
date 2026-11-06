"""Working on one game with friends.

How it works, in plain words:
- The team's game lives in a private GitHub repository ("the team copy"), in
  its main branch. Each person keeps their own full game folder and builds it
  themselves, exactly as before.
- "Share my changes" saves your edits, brings in anything friends shared since,
  and uploads the result. "Get friends' changes" only brings theirs in.
- When two people changed the same lines, nothing is guessed: the merge stays
  open and the editor shows both sides so you can keep yours, theirs or both.
- New editor features still come from the public repository (origin) through
  the Update button. They reach friends through the team copy too.

Your GitHub sign-in is a personal access token, kept in your Linux home folder
(~/.config/emerald-editor/github.json), never inside the game folder.
"""

import base64
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request

from common import ROOT

API = 'https://api.github.com'
REMOTE = 'team'
BRANCH = 'main'
MARKER = 'Emerald Editor team game'
TOKEN_FILE = os.path.expanduser('~/.config/emerald-editor/github.json')
TOKEN_URL = ('https://github.com/settings/tokens/new?scopes=repo'
             '&description=Emerald%20Editor')


class TeamError(Exception):
    pass


# ---- git helpers ---------------------------------------------------------------

def _git_env():
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    tok = token()
    if tok:
        env['EMERALD_GH_TOKEN'] = tok
    return env


# Hands the token to git without ever writing it into a remote URL or the log.
_CRED = ['-c', 'credential.helper=',
         '-c', 'credential.helper=!f() { echo username=x-access-token; echo "password=$EMERALD_GH_TOKEN"; }; f']


def git(*args):
    r = subprocess.run(['git'] + _CRED + list(args), cwd=ROOT, capture_output=True, text=True,
                       errors='replace', env=_git_env())
    return r.returncode, ((r.stdout or '') + (r.stderr or '')).strip()


def git_out(*args):
    code, out = git(*args)
    return out if code == 0 else ''


def run_git(job, *args):
    """Runs git with its output in the job's log (used for slow uploads)."""
    proc = subprocess.Popen(['git'] + _CRED + list(args), cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, errors='replace', env=_git_env(),
                            start_new_session=True)
    job.proc = proc
    out = []
    try:
        for line in proc.stdout:
            for part in line.replace('\r', '\n').split('\n'):
                if part.strip():
                    out.append(part)
                    if not re.match(r'^(remote: )?(Counting|Compressing|Writing|Receiving|Resolving|Enumerating)', part) \
                            or part.rstrip().endswith('done.') or '100%' in part:
                        job.write(part)
        return proc.wait(), '\n'.join(out[-20:])
    finally:
        if job.proc is proc:
            job.proc = None


# ---- sign-in -------------------------------------------------------------------

def _project_file():
    """Sign-in kept with this game folder only (a team code joins one project)."""
    return os.path.join(ROOT, '.git', 'emerald-team.json')


def _read(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _load():
    """Your GitHub sign-in (shared by all your projects), overridden by this project's own."""
    data = _read(TOKEN_FILE)
    local = _read(_project_file())
    if local.get('token'):
        data = {}
    data.update(local)
    return data


def token():
    return _load().get('token', '')


def gh(method, path, body=None, tok=None):
    tok = tok or token()
    if not tok:
        raise TeamError('Sign in to GitHub first.')
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None)
    req.add_header('Authorization', 'token ' + tok)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('User-Agent', 'Emerald-Editor')
    if body is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = res.read()
            return res.status, (json.loads(data) if data else None)
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read() or b'null')
        except ValueError:
            data = None
        if e.code == 401:
            raise TeamError('GitHub did not accept your sign-in. It may have expired: sign in again.')
        return e.code, data
    except (urllib.error.URLError, OSError) as e:
        raise TeamError('Could not reach GitHub. Check your internet connection. (%s)' % e)


def sign_in(tok):
    tok = (tok or '').strip()
    if not re.match(r'^[A-Za-z0-9_]{20,255}$', tok):
        raise TeamError('That does not look like a GitHub token. Copy the whole code GitHub showed you (it starts with ghp_).')
    code, user = gh('GET', '/user', tok=tok)
    if code != 200 or not user:
        raise TeamError('GitHub did not accept that token. Make a new one and paste it right away.')
    _save({'token': tok, 'login': user['login'], 'name': user.get('name') or user['login'], 'id': user['id']})
    _set_identity()
    return {'login': user['login']}


def sign_out():
    path = _project_file() if _read(_project_file()).get('token') else TOKEN_FILE
    try:
        os.remove(path)
    except OSError:
        pass


def _set_identity():
    """Changes you share carry your name, so friends can see who did what."""
    me = _load()
    if me.get('viaCode'):
        git('config', 'user.name', me['name'])
        git('config', 'user.email', '%s@team.emerald' % (re.sub(r'[^a-z0-9]+', '.', me['name'].lower()).strip('.') or 'friend'))
    elif me.get('login'):
        git('config', 'user.name', me.get('name') or me['login'])
        git('config', 'user.email', '%s+%s@users.noreply.github.com' % (me['id'], me['login']))


def _save(data, project=False):
    path = _project_file() if project else TOKEN_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd = os.open(path + '.tmp', os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    os.replace(path + '.tmp', path)


# ---- team codes: friends join with one shared code, no GitHub account ----------
#
# The owner makes a GitHub token that can only read and change the team game (a
# "fine-grained" token limited to that one repository), and the editor wraps it
# with the repository's name into a team code. Anyone with the code can join,
# share and get changes, and nothing else on the owner's GitHub.

CODE_PREFIX = 'EMERALD-'


def code_token_url(repo):
    owner, name = (repo.split('/', 1) + [''])[:2]
    return ('https://github.com/settings/personal-access-tokens/new?name=%s&description=%s'
            '&target_name=%s&expires_in=none&contents=write' % (
                urllib.request.quote('Emerald team code ' + name),
                urllib.request.quote('Lets friends with the team code share changes to ' + repo),
                urllib.request.quote(owner)))


def make_code(tok):
    """Owner: checks the pasted token opens only-the-team-game and turns it into a team code."""
    repo = team_repo()
    tok = (tok or '').strip()
    if not repo:
        raise TeamError('Start a team game first.')
    if not tok.startswith('github_pat_'):
        raise TeamError('That is not the right kind of code. Use the link above: the code GitHub shows starts with github_pat_.')
    code, info = gh('GET', '/repos/' + repo, tok=tok)
    if code != 200:
        raise TeamError('That code cannot open %s. On the GitHub page, under Repository access, pick "Only select '
                        'repositories" and choose %s, and set Contents to "Read and write".' % (repo, repo.split('/')[1]))
    # Make sure it can change the game, not just read it (a dry-run upload asks GitHub for write access).
    url = 'https://github.com/%s.git' % repo
    r = subprocess.run(['git', '-c', 'credential.helper=', '-c',
                        'credential.helper=!f() { echo username=x-access-token; echo "password=$EMERALD_GH_TOKEN"; }; f',
                        'push', '--dry-run', '--quiet', url, 'HEAD:refs/heads/emerald-code-check'],
                       cwd=ROOT, capture_output=True, text=True, errors='replace',
                       env=dict(os.environ, GIT_TERMINAL_PROMPT='0', EMERALD_GH_TOKEN=tok))
    if r.returncode != 0 and ('403' in r.stderr or 'denied' in r.stderr.lower() or 'not found' in r.stderr.lower()):
        raise TeamError('That code can read the game but not change it. On the GitHub page set Contents to "Read and write".')
    team_code = CODE_PREFIX + base64.urlsafe_b64encode(json.dumps({'r': repo, 't': tok}).encode()).decode().rstrip('=')
    local = _read(_project_file())
    local['teamCode'] = team_code
    _save(local, project=True)
    return {'code': team_code}


def team_code():
    """The team code for this project's team game (only shown to its owner)."""
    me = _load()
    c = me.get('teamCode', '')
    if not c or me.get('viaCode') or not team_repo():
        return ''
    try:
        return c if read_code(c)[0] == team_repo() else ''
    except TeamError:
        return ''


def read_code(text):
    text = re.sub(r'\s+', '', text or '')
    if not text.upper().startswith(CODE_PREFIX):
        raise TeamError('A team code starts with EMERALD-. Ask your friend to copy the whole thing.')
    raw = text[len(CODE_PREFIX):]
    try:
        data = json.loads(base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)).decode())
        repo, tok = data['r'], data['t']
    except (ValueError, KeyError, TypeError):
        raise TeamError('That team code is cut off or mistyped. Ask your friend to copy it again.')
    if not re.match(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$', repo):
        raise TeamError('That team code is not valid.')
    return repo, tok


def join_with_code(job, text, name, save_my_changes):
    """Friend: joins with the team code; no GitHub account needed."""
    name = re.sub(r'\s+', ' ', (name or '').strip())[:40]
    if not name:
        return False, 'Type your name first, so friends can see who changed what.'
    repo, tok = read_code(text)
    code, _ = gh('GET', '/repos/' + repo, tok=tok)
    if code != 200:
        return False, 'That team code no longer works. Ask the owner for the new one.'
    _save({'token': tok, 'login': name, 'name': name, 'id': 0, 'viaCode': True}, project=True)
    return join(job, repo, None, save_my_changes)


# ---- the team copy -------------------------------------------------------------

def team_repo():
    """'owner/name' of the team copy this folder is joined to, or ''."""
    url = git_out('remote', 'get-url', REMOTE)
    m = re.match(r'^https://github\.com/([^/]+/[^/]+?)(\.git)?/?$', url)
    return m.group(1) if m else ('' if not url else url)


def _set_remote(full_name):
    url = 'https://github.com/%s.git' % full_name
    if git_out('remote', 'get-url', REMOTE):
        git('remote', 'set-url', REMOTE, url)
    else:
        git('remote', 'add', REMOTE, url)


def leave():
    git('remote', 'remove', REMOTE)
    git('config', '--unset', 'emerald.lastSync')
    git('config', '--unset', 'emerald.syncError')


# ---- sync status (for the "Up to date" sign on the Team button) ---------------

def _synced():
    """Remembers that GitHub answered just now, and clears any old problem."""
    git('config', 'emerald.lastSync', str(int(time.time())))
    git('config', '--unset', 'emerald.syncError')


def _sync_failed(message):
    git('config', 'emerald.syncError', (message or 'Something went wrong.')[:300])


def fetch_team():
    """Looks at the team copy on GitHub and notes whether that worked."""
    code, msg = git('fetch', '--quiet', REMOTE)
    if code == 0:
        _synced()
    else:
        _sync_failed(_friendly_git_error(msg))
    return code, msg


def status(fetch=False):
    me = _load()
    repo = team_repo()
    out = {'signedIn': bool(me.get('token')), 'login': me.get('login', ''), 'repo': repo,
           'viaCode': bool(me.get('viaCode')), 'teamCode': team_code(),
           'codeTokenUrl': code_token_url(repo) if repo else '',
           'tokenUrl': TOKEN_URL, 'merging': merging(), 'auto': auto_on()}
    if not repo:
        return out
    if fetch and me.get('token'):
        code, msg = fetch_team()
        if code != 0:
            out['fetchError'] = _friendly_git_error(msg)
    ref = '%s/%s' % (REMOTE, BRANCH)
    have = git('rev-parse', '--verify', '-q', ref)[0] == 0
    out['incoming'] = int(git_out('rev-list', '--count', 'HEAD..' + ref) or 0) if have else 0
    out['outgoing'] = int(git_out('rev-list', '--count', ref + '..HEAD') or 0) if have else 0
    out['unsaved'] = bool(git_out('status', '--porcelain'))
    out['url'] = 'https://github.com/%s' % repo if re.match(r'^[^/\s]+/[^/\s]+$', repo) else ''
    out['lastSync'] = int(git_out('config', 'emerald.lastSync') or 0)
    out['syncError'] = git_out('config', 'emerald.syncError')
    out['github'] = None
    if have:
        parts = git_out('log', '-1', '--format=%an%x09%ct%x09%s', ref).split('\t', 2)
        if len(parts) == 3:
            out['github'] = {'who': parts[0], 'time': int(parts[1]), 'what': parts[2]}
    out['recent'] = []
    out['people'] = []
    if have:
        for n in git_out('log', '-300', '--no-merges', '--format=%an', ref).splitlines():
            if n and n not in out['people'] and n != 'Emerald Editor':
                out['people'].append(n)
        for line in git_out('log', '-12', '--no-merges', '--format=%an%x09%at%x09%s', ref).splitlines():
            parts = line.split('\t', 2)
            if len(parts) == 3:
                out['recent'].append({'who': parts[0], 'time': int(parts[1]), 'what': parts[2]})
    return out


def details():
    """Members and invites (needs GitHub)."""
    repo = team_repo()
    if not repo or not token():
        return {}
    code, info = gh('GET', '/repos/' + repo)
    if code != 200:
        return {'error': 'Could not open the team copy on GitHub. Has it been deleted, or were you removed from it?'}
    perms = info.get('permissions') or {}
    out = {'owner': info['owner']['login'], 'admin': bool(perms.get('admin')), 'url': info['html_url'],
           'private': info.get('private'), 'members': [], 'invited': []}
    code, people = gh('GET', '/repos/%s/collaborators?per_page=100' % repo)
    if code == 200:
        out['members'] = [{'login': p['login'], 'avatar': p.get('avatar_url', '')} for p in people]
    if out['admin']:
        code, inv = gh('GET', '/repos/%s/invitations?per_page=100' % repo)
        if code == 200:
            out['invited'] = [{'id': i['id'], 'login': (i.get('invitee') or {}).get('login', '?')} for i in inv]
    return out


def invite(login):
    login = (login or '').strip().lstrip('@')
    if not re.match(r'^[A-Za-z0-9-]{1,39}$', login):
        raise TeamError('Type your friend\'s GitHub username (the name on their GitHub profile).')
    code, user = gh('GET', '/users/' + login)
    if code != 200:
        raise TeamError('There is no GitHub user called "%s". Check the spelling with your friend.' % login)
    code, data = gh('PUT', '/repos/%s/collaborators/%s' % (team_repo(), user['login']), {'permission': 'push'})
    if code == 201:
        return 'Invited %s. They open the editor, sign in, and click Join.' % user['login']
    if code == 204:
        return '%s is already on the team.' % user['login']
    raise TeamError(_api_error('Could not invite %s' % login, data))


def remove(login, invite_id=None):
    repo = team_repo()
    if invite_id:
        gh('DELETE', '/repos/%s/invitations/%d' % (repo, int(invite_id)))
    else:
        code, data = gh('DELETE', '/repos/%s/collaborators/%s' % (repo, login))
        if code not in (204, 404):
            raise TeamError(_api_error('Could not remove %s' % login, data))


def invitations():
    """Team games you were invited to or can already open."""
    found = {}
    code, inv = gh('GET', '/user/repository_invitations?per_page=100')
    if code == 200:
        for i in inv:
            r = i['repository']
            found[r['full_name']] = {'repo': r['full_name'], 'from': (i.get('inviter') or {}).get('login', ''),
                                     'inviteId': i['id'], 'team': (r.get('description') or '').startswith(MARKER)}
    code, repos = gh('GET', '/user/repos?per_page=100&affiliation=owner,collaborator&sort=updated')
    if code == 200:
        for r in repos:
            if (r.get('description') or '').startswith(MARKER) and r['full_name'] not in found:
                found[r['full_name']] = {'repo': r['full_name'], 'from': r['owner']['login'], 'inviteId': None,
                                         'team': True}
    return sorted(found.values(), key=lambda x: (not x['team'], x['repo'].lower()))


def _api_error(prefix, data):
    msg = (data or {}).get('message', '') if isinstance(data, dict) else ''
    errs = (data or {}).get('errors') if isinstance(data, dict) else None
    if errs and isinstance(errs, list) and isinstance(errs[0], dict) and errs[0].get('message'):
        msg = errs[0]['message']
    return '%s: %s' % (prefix, msg or 'GitHub said no.')


def _friendly_git_error(msg):
    low = msg.lower()
    if 'authentication failed' in low or 'could not read username' in low or '403' in low:
        return 'GitHub did not let you in. Sign in again, and check you accepted the invite.'
    if 'not found' in low:
        return 'GitHub could not find the team copy. Ask the owner to check it still exists and that you are invited.'
    if 'could not resolve host' in low or 'unable to access' in low:
        return 'Could not reach GitHub. Check your internet connection.'
    return msg[-300:]


# ---- jobs (run in the editor's job panel) ----------------------------------------

def create(job, name, save_my_changes):
    """Makes a new private team copy on your GitHub and uploads this game to it."""
    name = re.sub(r'[^A-Za-z0-9._-]+', '-', (name or '').strip()).strip('-.') or 'my-emerald-game'
    if team_repo():
        return False, 'This game is already a team game (%s).' % team_repo()
    job.write('Making a private copy called %s on your GitHub...' % name)
    code, repo = gh('POST', '/user/repos', {'name': name, 'private': True, 'auto_init': False,
                                             'description': MARKER + ' (made with Emerald Editor)',
                                             'has_issues': False, 'has_wiki': False, 'has_projects': False})
    if code != 201:
        return False, _api_error('GitHub could not make it', repo)
    _set_identity()
    if not save_my_changes(job):
        return False, 'Could not save your changes first, so nothing was uploaded.'
    _set_remote(repo['full_name'])
    job.write('Uploading your game. The first time takes a while (the whole game history goes up once)...')
    code, msg = run_git(job, 'push', '--progress', REMOTE, 'HEAD:refs/heads/' + BRANCH)
    if code != 0:
        return False, 'The upload did not finish: %s Click Share my changes to try again.' % _friendly_git_error(msg)
    fetch_team()
    gh('PATCH', '/repos/' + repo['full_name'], {'default_branch': BRANCH})
    return True, 'Your team game is ready! Invite friends by their GitHub username.'


def join(job, full_name, invite_id, save_my_changes):
    if invite_id:
        job.write('Accepting the invite...')
        code, data = gh('PATCH', '/user/repository_invitations/%d' % int(invite_id))
        if code not in (204, 200):
            return False, _api_error('Could not accept the invite', data)
    _set_identity()
    _set_remote(full_name)
    job.write('Downloading the team\'s game...')
    code, msg = run_git(job, 'fetch', '--progress', REMOTE)
    if code != 0:
        leave()
        return False, _friendly_git_error(msg)
    if git('rev-parse', '--verify', '-q', '%s/%s' % (REMOTE, BRANCH))[0] != 0:
        leave()
        return False, 'The team copy is still empty. Ask its owner to click Share my changes once, then join again.'
    _synced()
    return merge_in(job, '%s/%s' % (REMOTE, BRANCH), 'get', save_my_changes,
                    done='Joined! You now have the team\'s game.')


def get_changes(job, save_my_changes):
    if not team_repo():
        return False, 'This game is not a team game yet.'
    job.write('Checking for friends\' changes...')
    code, msg = fetch_team()
    if code != 0:
        return False, _friendly_git_error(msg)
    return merge_in(job, '%s/%s' % (REMOTE, BRANCH), 'get', save_my_changes)


def share(job, note, save_my_changes):
    if not team_repo():
        return False, 'This game is not a team game yet.'
    _set_identity()
    if not save_my_changes(job, describe_changes(note)):
        return False, 'Could not save your changes, so nothing was shared.'
    for attempt in range(3):
        code, msg = fetch_team()
        if code != 0:
            return False, _friendly_git_error(msg)
        ref = '%s/%s' % (REMOTE, BRANCH)
        if git('rev-parse', '--verify', '-q', ref)[0] == 0:
            ok, res = merge_in(job, ref, 'share', save_my_changes, quiet=True)
            if not ok:
                return ok, res
            if res == 'conflict':
                return False, CONFLICT_MSG
        ok, res = push(job)
        if ok or res != 'retry':
            return ok, res
        job.write('A friend shared at the same moment. Trying again...')
        time.sleep(1)
    return False, 'Friends kept sharing at the same time. Wait a minute and click Share again.'


def auto_on():
    return git_out('config', 'emerald.autoSync') != 'false'


def set_auto(on):
    git('config', 'emerald.autoSync', 'true' if on else 'false')


def sync(job, save_my_changes):
    """Auto-sync: share your saved edits and bring in friends' in one quiet step."""
    if not team_repo() or not token() or merging():
        return {'skipped': True}
    code, msg = fetch_team()
    if code != 0:
        return {'ok': False, 'message': _friendly_git_error(msg)}
    ref = '%s/%s' % (REMOTE, BRANCH)
    who = []
    for n in git_out('log', '--no-merges', '--format=%an', 'HEAD..' + ref).splitlines():
        if n and n not in who:
            who.append(n)
    got = int(git_out('rev-list', '--count', '--no-merges', 'HEAD..' + ref) or 0)
    ok, msg = share(job, '', save_my_changes)
    conflict = merging()
    return {'ok': ok or conflict, 'message': msg, 'got': 0 if (conflict or not ok) else got, 'from': who,
            'shared': ok and msg.startswith('Shared'), 'conflict': conflict}


def push(job):
    if not int(git_out('rev-list', '--count', '%s/%s..HEAD' % (REMOTE, BRANCH)) or 1):
        return True, 'Nothing new to share. Friends already have everything you have.'
    job.write('Uploading your changes...')
    code, msg = run_git(job, 'push', '--progress', REMOTE, 'HEAD:refs/heads/' + BRANCH)
    if code == 0:
        fetch_team()
        return True, 'Shared! Friends get your changes when they click Get friends\' changes.'
    if 'rejected' in msg or 'fetch first' in msg or 'non-fast-forward' in msg:
        return False, 'retry'
    _sync_failed('The upload did not work: ' + _friendly_git_error(msg))
    return False, 'The upload did not work: ' + _friendly_git_error(msg)


CONFLICT_MSG = ('You and someone else changed the same thing. Pick which version to keep '
                'in the window that just opened.')


def merge_in(job, ref, why, save_my_changes, done=None, quiet=False):
    """Brings ref into your game. Returns (ok, message) or (True, 'conflict') with quiet."""
    if merging():
        return False, 'Finish picking versions from the last time first (click Team).'
    count = int(git_out('rev-list', '--count', 'HEAD..' + ref) or 0)
    if count == 0:
        return True, done or ('' if quiet else 'You already have all your friends\' changes.')
    if not save_my_changes(job):
        return False, 'Could not save your changes first, so nothing was changed.'
    before = git_out('rev-parse', 'HEAD')
    job.write('Bringing in %d change(s)...' % count)
    code, msg = git('-c', 'merge.conflictStyle=merge', 'merge', '--no-edit', ref)
    if code != 0:
        if not conflicted_files():
            git('merge', '--abort')
            return False, 'Could not combine the changes: ' + msg[-300:]
        git('config', 'emerald.mergeWhy', why)
        git('config', 'emerald.mergeBefore', before)
        job.write('Some changes touch the same lines as yours.')
        return (True, 'conflict') if quiet else (False, CONFLICT_MSG)
    job.editor_changed = _editor_changed(before)
    return True, done or ('' if quiet else 'Got %d change(s) from your friends.' % count)


def _editor_changed(before):
    return bool(git_out('diff', '--name-only', before, 'HEAD', '--', 'editor'))


# ---- picking versions when two people changed the same thing ------------------

def merging():
    return git('rev-parse', '--verify', '-q', 'MERGE_HEAD')[0] == 0


def conflicted_files():
    return [f for f in git_out('diff', '--name-only', '--diff-filter=U').splitlines() if f]


AREAS = [
    (r'^src/data/trainers\.party$', 'Trainers'),
    (r'^data/maps/.*/scripts\.(inc|pory)$', 'Map dialogue and scripts'),
    (r'^data/maps/.*/map\.json$', 'Map people and items'),
    (r'^src/data/wild_encounters\.json$', 'Wild Pokémon'),
    (r'^data/text/', 'Dialogue'),
    (r'^src/data/text/', 'Game text'),
    (r'^src/data/pokemon/species_info', 'Pokémon data'),
    (r'^src/data/pokemon/', 'Pokémon moves and data'),
    (r'^include/config/', 'Game settings'),
    (r'^graphics/', 'Pictures'),
    (r'^sound/', 'Music'),
    (r'^editor/|^windows/', 'The editor itself'),
]


def area(path):
    for pat, label in AREAS:
        if re.search(pat, path):
            return label
    return 'Other game files'


def describe_changes(note=''):
    """Commit message for a share: your note, or which parts of the game changed."""
    git('add', '-A')
    files = git_out('diff', '--cached', '--name-only').splitlines()
    parts = []
    for f in files:
        a = area(f)
        if a not in parts:
            parts.append(a)
    note = (note or '').strip()
    if note:
        return note[:200]
    return 'Changed ' + (', '.join(parts[:5]) if parts else 'the game')


def _who(path):
    before = git_out('config', 'emerald.mergeBefore') or 'HEAD'
    names = git_out('log', '--format=%an', '%s..MERGE_HEAD' % before, '--', path).splitlines()
    uniq = []
    for n in names:
        if n not in uniq:
            uniq.append(n)
    return ', '.join(uniq[:3]) or 'a friend'


_START, _MID, _END = re.compile(r'^<{7}( |$)'), re.compile(r'^={7}$'), re.compile(r'^>{7}( |$)')


def _parse(text):
    """Splits a file with conflict marks into plain text and [mine, theirs] pairs."""
    pieces, cur, mine, theirs, state = [], [], [], [], 0
    for line in text.splitlines(keepends=True):
        bare = line.rstrip('\r\n')
        if state == 0 and _START.match(bare):
            pieces.append(''.join(cur))
            cur, mine, theirs, state = [], [], [], 1
        elif state == 1 and _MID.match(bare):
            state = 2
        elif state == 2 and _END.match(bare):
            pieces.append([''.join(mine), ''.join(theirs)])
            state = 0
        elif state == 1:
            mine.append(line)
        elif state == 2:
            theirs.append(line)
        else:
            cur.append(line)
    if state != 0:
        return None
    pieces.append(''.join(cur))
    return pieces


def _stages(path):
    have = set()
    for line in git_out('ls-files', '-u', '--', path).splitlines():
        m = re.match(r'^\d+ [0-9a-f]+ (\d)\t', line)
        if m:
            have.add(int(m.group(1)))
    return have


def conflicts():
    why = git_out('config', 'emerald.mergeWhy') or 'get'
    out = []
    for path in conflicted_files():
        stages = _stages(path)
        item = {'path': path, 'area': area(path), 'who': _who(path), 'blocks': None,
                'mineGone': 2 not in stages, 'theirsGone': 3 not in stages}
        full = os.path.join(ROOT, path)
        if 2 in stages and 3 in stages:
            try:
                with open(full, encoding='utf-8', errors='strict', newline='') as f:
                    pieces = _parse(f.read())
            except (OSError, UnicodeDecodeError):
                pieces = None
            if pieces:
                blocks = []
                for i, p in enumerate(pieces):
                    if isinstance(p, list):
                        before = pieces[i - 1] if i > 0 else ''
                        after = pieces[i + 1] if i + 1 < len(pieces) else ''
                        blocks.append({'mine': p[0], 'theirs': p[1],
                                       'before': ''.join(before.splitlines(True)[-3:]),
                                       'after': ''.join(after.splitlines(True)[:3])})
                item['blocks'] = blocks
        out.append(item)
    return {'why': why, 'files': out}


def resolve(choices, save_my_changes):
    """choices: {path: 'mine'|'theirs'} or {path: ['mine'|'theirs'|'both', ...] per block}."""
    if not merging():
        raise TeamError('There is nothing to pick right now.')
    files = conflicted_files()
    for path in files:
        pick = choices.get(path)
        if pick is None:
            raise TeamError('Pick a version for every change first (%s).' % path)
        stages = _stages(path)
        full = os.path.join(ROOT, path)
        if isinstance(pick, list):
            with open(full, encoding='utf-8', newline='') as f:
                pieces = _parse(f.read())
            blocks = [p for p in (pieces or []) if isinstance(p, list)]
            if not pieces or len(blocks) != len(pick):
                raise TeamError('%s changed while you were picking. Close this and open Team again.' % path)
            text, n = [], 0
            for p in pieces:
                if isinstance(p, list):
                    c = pick[n]
                    n += 1
                    text.append(p[0] if c == 'mine' else p[1] if c == 'theirs' else p[0] + p[1])
                else:
                    text.append(p)
            with open(full, 'w', encoding='utf-8', newline='') as f:
                f.write(''.join(text))
            git('add', '--', path)
        else:
            side = 2 if pick == 'mine' else 3
            if side not in stages:
                git('rm', '-q', '--', path)
            else:
                git('checkout', '--ours' if side == 2 else '--theirs', '--', path)
                git('add', '--', path)
    if conflicted_files():
        raise TeamError('Some changes still need a pick.')
    before = git_out('config', 'emerald.mergeBefore')
    code, msg = git('commit', '--no-edit', '-q')
    if code != 0:
        raise TeamError('Could not finish combining: ' + msg[-300:])
    why = git_out('config', 'emerald.mergeWhy') or 'get'
    git('config', '--unset', 'emerald.mergeWhy')
    git('config', '--unset', 'emerald.mergeBefore')
    return {'why': why, 'editorChanged': bool(before) and _editor_changed(before)}


def cancel_merge():
    if merging():
        git('merge', '--abort')
    git('config', '--unset', 'emerald.mergeWhy')
    git('config', '--unset', 'emerald.mergeBefore')
