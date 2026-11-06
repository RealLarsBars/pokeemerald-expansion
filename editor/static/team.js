'use strict';
// ---------------------------------------------------------------------------
// Team: work on one game with friends (a private GitHub copy under the hood).
// ---------------------------------------------------------------------------

const TEAM = { status: null, syncing: false, syncSince: 0 };

function teamAgo(t) {
  const s = Math.max(0, Date.now() / 1000 - t);
  if (s < 90) return 'just now';
  if (s < 3600) return Math.round(s / 60) + ' min ago';
  if (s < 86400) return Math.round(s / 3600) + ' h ago';
  return Math.round(s / 86400) + ' days ago';
}

// Syncing only while something is really talking to GitHub (and never for more than 3 minutes).
function teamBusy() {
  return TEAM.syncing && ($('#teamBtn').disabled || teamSyncing) && Date.now() - TEAM.syncSince < 3 * 60 * 1000;
}

function teamSetSyncing(on) {
  TEAM.syncing = on;
  if (on) TEAM.syncSince = Date.now();
  teamBadge(TEAM.status);
}

// One plain answer to "is my team game up to date on GitHub?"
function teamSyncState(st) {
  if (!st || !st.repo) return null;
  if (st.merging) return { cls: 'warn', icon: '!', short: 'Pick versions',
    long: 'You and a friend changed the same thing. Click Team to pick which version to keep.' };
  if (teamBusy()) return { cls: 'busy', icon: '⟳', short: 'Syncing…',
    long: 'Talking to GitHub right now...' };
  const err = st.fetchError || st.syncError;
  if (err || !st.signedIn) return { cls: 'bad', icon: '⚠', short: 'Not synced',
    long: st.signedIn ? 'Could not sync with GitHub: ' + err : 'Nothing is being shared right now. Click Team and paste your team code (or sign in, if you started this team game).' };
  if (st.empty) return { cls: 'bad', icon: '⚠', short: 'Not uploaded yet',
    long: 'Your game is not on GitHub yet, so friends cannot get it. Click Team and then Share my changes to upload it. ' +
      'The first upload is big and can take a long time. If it stops, click Share my changes again and it carries on where it left off.' };
  if (st.outgoing || st.unsaved || anyDirty()) return { cls: 'warn', icon: '●', short: 'Not shared yet',
    long: anyDirty() ? 'You have edits that are not saved yet. Save them and they are shared on the next sync.'
      : st.auto ? 'You have changes that are not on GitHub yet. They go up on the next sync (about a minute), or click Team and then Share my changes.'
        : 'You have changes that are not on GitHub yet. Click Team and then Share my changes.' };
  if (st.incoming) return { cls: 'warn', icon: '⬇', short: st.incoming + ' new from friends',
    long: `${st.incoming} change(s) from friends are on GitHub but not in your game yet. ` +
      (st.auto ? 'They come in on the next sync, or click Team and then Get friends\' changes.' : 'Click Team and then Get friends\' changes.') };
  return { cls: 'ok', icon: '✓', short: 'Up to date',
    long: 'Up to date. GitHub has everything you saved, and you have everything your friends shared.' };
}

function teamBadge(st) {
  const tag = $('#teamState');
  const s = teamSyncState(st);
  if (!s) { tag.className = 'teamstate hidden'; $('#teamBtn').title = 'Work on this game with friends: share your changes and get theirs'; return; }
  tag.className = 'teamstate ' + s.cls;
  tag.textContent = s.icon + ' ' + s.short;
  $('#teamBtn').title = s.long + (st.lastSync ? ' (Last checked with GitHub ' + teamAgo(st.lastSync) + '.)' : '');
  // Keep the Team window's status card live too, instead of frozen at the moment it opened.
  const card = $('#teamSyncCard');
  if (card && card.dataset.key !== teamCardKey(st, s)) card.replaceWith(teamStatusCard(st));
}

function teamCardKey(st, s) {
  return [s.short, s.long, st.lastSync ? teamAgo(st.lastSync) : '', st.github ? st.github.time : ''].join('|');
}

// The window's top card: the same answer, with times and a link to see it on GitHub.
function teamStatusCard(st) {
  const s = teamSyncState(st);
  const card = el('div', { class: 'card syncstatus ' + s.cls, id: 'teamSyncCard', 'data-key': teamCardKey(st, s) },
    el('div', { class: 'syncline' }, el('span', { class: 'teamstate ' + s.cls }, s.icon + ' ' + s.short),
      el('button', { class: 'btn small', onclick: async (e) => {
        if (teamSyncing) return;
        teamSyncing = true; teamSetSyncing(true);
        try { await teamRefresh(true); } catch (err) { toast(err.message, true); }
        finally { teamSyncing = false; teamSetSyncing(false); }
      } }, 'Check now')),
    el('p', {}, s.long),
    el('p', { class: 'note' }, 'Last checked with GitHub: ', el('b', {}, st.lastSync ? teamAgo(st.lastSync) : 'not yet'),
      st.auto ? ' (it checks about once a minute while the editor is open).' : '.'),
    st.github ? el('p', { class: 'note' }, 'Newest change on GitHub: ', el('b', {}, st.github.what), ' by ', st.github.who, ', ', teamAgo(st.github.time), '.') : null,
    st.url && !st.viaCode ? el('p', { class: 'note' }, el('a', { href: st.url + '/commits/main', target: '_blank' }, 'See the team game on GitHub'),
      ' (the top entry there is the newest shared change).') : null);
  return card;
}

async function teamRefresh(fetch = false) {
  TEAM.status = await api('/api/team' + (fetch ? '?fetch=1' : ''));
  teamBadge(TEAM.status);
  return TEAM.status;
}

// A team step runs in the job panel; afterwards the Team window reopens with the result.
function teamJob(path, body, title) {
  closeModal();
  const run = async () => {
    const res = await api(path, body);
    if (!res.started) { toast('The editor is busy. Try again in a moment.', true); return; }
    setJobButtons(true);
    showJob(title);
    teamSetSyncing(true);
    jobDone = async (j) => {
      teamSetSyncing(false);
      if (/restart in a moment/.test(j.message)) { waitForRestart(); return; }
      const st = await teamRefresh().catch(() => null);
      if (st && st.merging) openConflicts();
      else if (j.state === 'done' && /^(Your team game is ready|Joined)/.test(j.message)) openTeam();
    };
    pollJob();
  };
  if (anyDirty() && !confirm('Some changes are not saved yet and will not be included. Continue?')) return;
  run().catch(e => toast(e.message, true));
}

async function openTeam() {
  let st;
  try { st = await teamRefresh(true); } catch (e) { toast(e.message, true); return; }
  if (st.merging) { openConflicts(); return; }
  if (!st.signedIn) { openModal('Work on this game with friends', teamSignInBody(st)); return; }
  if (!st.repo) { openModal('Work on this game with friends', await teamStartBody(st)); return; }
  openModal('Team game', teamMainBody(st));
}

function teamSignInBody(st) {
  const box = el('input', { class: 'search', type: 'password', placeholder: 'Paste the code from GitHub here (starts with ghp_)' });
  const signIn = async () => {
    try {
      const me = await api('/api/team/signin', { token: box.value });
      toast('Signed in as ' + me.login);
      openTeam();
    } catch (e) { toast(e.message, true); }
  };
  box.addEventListener('keydown', e => { if (e.key === 'Enter') signIn(); });
  const myName = el('input', { class: 'search', type: 'text', placeholder: 'Your name (friends see it next to your changes)' });
  const code = el('input', { class: 'search', type: 'text', placeholder: 'Team code (starts with EMERALD-)' });
  const joinCode = () => teamJob('/api/team/joincode', { code: code.value, name: myName.value }, 'Join a team game');
  code.addEventListener('keydown', e => { if (e.key === 'Enter') joinCode(); });
  return el('div', { class: 'team' },
    el('p', {}, 'Everyone on the team keeps their own copy of the game and plays it on their own PC. ' +
      'Your copies stay in sync through a private space on GitHub that only your team can see.'),
    el('div', { class: 'card' },
      el('h3', {}, 'Join a friend\'s game with their team code'),
      el('p', { class: 'note' }, 'No GitHub account needed. Your edits in this project are kept and combined with the team\'s game. To keep your own game separate, first make a new project with 📁 at the top left and join from there.'),
      el('div', { class: 'searchrow' }, myName),
      el('div', { class: 'searchrow' }, code, el('button', { class: 'btn primary', onclick: joinCode }, 'Join'))),
    el('h3', { class: 'teamsub' }, 'Start your own team game'),
    el('p', {}, 'The person who starts the game signs in to GitHub once (the editor remembers you):'),
    el('ol', { class: 'teamsteps' },
      el('li', {}, 'No GitHub account yet? ', el('a', { href: 'https://github.com/signup', target: '_blank' }, 'Make one here'), ' (it is free).'),
      el('li', {}, el('a', { class: 'btn primary small', href: st.tokenUrl, target: '_blank' }, 'Open the GitHub sign-in page'),
        el('div', { class: 'note' }, 'On that page: set Expiration to "No expiration", scroll to the bottom and click the green "Generate token" button, then copy the code it shows.')),
      el('li', {}, 'Paste the code here:', el('div', { class: 'searchrow' }, box, el('button', { class: 'btn primary', onclick: signIn }, 'Sign in')))),
    el('p', { class: 'note' }, 'The code stays on this PC. Treat it like a password and do not share it with anyone.'));
}

async function teamStartBody(st) {
  const name = el('input', { class: 'search', type: 'text', value: 'my-emerald-game' });
  const invites = el('div', { class: 'rows' }, el('div', { class: 'note' }, 'Looking for invites...'));
  const loadInvites = async () => {
    try {
      const { list } = await api('/api/team/invitations');
      invites.replaceChildren(...(list.length ? list.map(i => el('div', { class: 'rowline teamrow' },
        el('div', { class: 'grow' }, el('b', {}, i.repo), i.from ? el('span', { class: 'note' }, ' from ' + i.from) : null,
          i.team ? null : el('div', { class: 'note' }, 'This one was not made by the editor. Only join it if your friend says so.')),
        el('button', { class: 'btn primary small', onclick: () => teamJob('/api/team/join', { repo: i.repo, inviteId: i.inviteId }, 'Join a team game') }, 'Join')))
        : [el('div', { class: 'note' }, 'No invites yet. Tell your friend your GitHub username: ', el('b', {}, st.login),
          '. Once they invite you, click Look again.')]));
    } catch (e) { invites.replaceChildren(el('div', { class: 'warnbox' }, e.message)); }
  };
  loadInvites();
  return el('div', { class: 'team' },
    el('p', {}, 'Signed in as ', el('b', {}, st.login), '.'),
    el('div', { class: 'row' },
      el('div', { class: 'card grow' },
        el('h3', {}, 'Start a team game'),
        el('p', { class: 'note' }, 'Makes a private copy of this game on your GitHub and uploads it. Then you invite friends. The first upload can take several minutes.'),
        el('p', { class: 'note' }, 'Tip: to keep your solo game separate, first make a new project with 📁 at the top left, open it, and start the team game there.'),
        el('div', { class: 'searchrow' }, name,
          el('button', { class: 'btn primary', onclick: () => teamJob('/api/team/create', { name: name.value }, 'Start a team game') }, 'Start'))),
      el('div', { class: 'card grow' },
        el('h3', {}, 'Join a friend\'s game'),
        el('p', { class: 'note' }, 'Your own unshared edits are kept and combined with the team\'s game.'),
        invites,
        el('button', { class: 'btn small', onclick: loadInvites }, 'Look again'))),
    el('p', { class: 'note' }, el('a', { href: '#', onclick: async (e) => { e.preventDefault(); await api('/api/team/signout', {}); openTeam(); } }, 'Sign out')));
}

function teamMainBody(st) {
  const note = el('input', { class: 'search', type: 'text', placeholder: 'What did you change? (optional, e.g. "Made Roxanne harder")' });
  const people = el('div', { class: 'rows' }, el('div', { class: 'note' }, 'Loading the team...'));
  const invite = el('input', { class: 'search', type: 'text', placeholder: 'Friend\'s GitHub username' });
  const loadPeople = async () => {
    try {
      const d = await api('/api/team/details');
      if (d.error) { people.replaceChildren(el('div', { class: 'warnbox' }, d.error)); return; }
      const rows = d.members.map(m => el('div', { class: 'rowline teamrow' },
        m.avatar ? el('img', { class: 'avatar', src: m.avatar + '&s=48', alt: '' }) : null,
        el('div', { class: 'grow' }, m.login, m.login === d.owner ? el('span', { class: 'note' }, ' (owner)') : null),
        d.admin && m.login !== d.owner ? el('button', { class: 'btn small ghost', title: 'Remove from the team', onclick: () => teamRemove(m.login) }, '✕') : null));
      for (const i of d.invited) rows.push(el('div', { class: 'rowline teamrow' },
        el('div', { class: 'grow' }, i.login, el('span', { class: 'note' }, ' (invited, has not joined yet)')),
        el('button', { class: 'btn small ghost', title: 'Take back the invite', onclick: () => teamRemove(i.login, i.id) }, '✕')));
      people.replaceChildren(...rows);
      if (!d.admin) $('#teamInviteRow')?.remove();
    } catch (e) { people.replaceChildren(el('div', { class: 'warnbox' }, e.message)); }
  };
  const doInvite = async () => {
    try { toast((await api('/api/team/invite', { login: invite.value })).message); invite.value = ''; loadPeople(); }
    catch (e) { toast(e.message, true); }
  };
  invite.addEventListener('keydown', e => { if (e.key === 'Enter') doInvite(); });
  if (!st.viaCode) loadPeople();
  const mine = st.outgoing || st.unsaved || st.empty;
  return el('div', { class: 'team' },
    teamStatusCard(st),
    el('p', {}, 'Team game ', el('b', {}, st.repo), st.viaCode ? '. You are ' : '. Signed in as ', el('b', {}, st.login), '.'),
    el('label', { class: 'autosync' },
      el('input', { type: 'checkbox', checked: st.auto, onchange: async (e) => {
        try { await api('/api/team/auto', { on: e.target.checked }); await teamRefresh(); toast(e.target.checked ? 'Auto-sync is on.' : 'Auto-sync is off. Use the buttons below.'); }
        catch (err) { toast(err.message, true); }
      } }),
      el('span', {}, el('b', {}, 'Keep everyone up to date automatically'),
        el('div', { class: 'note' }, 'About once a minute, everything you saved is shared and friends\' changes come in. It waits while you have unsaved edits open, and asks you when two people changed the same thing.'))),
    el('div', { class: 'row' },
      el('div', { class: 'card grow' },
        el('h3', {}, 'Your changes'),
        el('p', { class: 'note' }, st.empty ? 'Your game is not uploaded yet. Click Share my changes to upload it.'
          : mine ? 'You have changes your friends do not have yet.' : 'Friends already have everything you made.'),
        el('div', { class: 'searchrow' }, note,
          el('button', { class: 'btn primary', onclick: () => teamJob('/api/team/share', { note: note.value }, 'Share my changes') }, 'Share my changes'))),
      el('div', { class: 'card grow' },
        el('h3', {}, 'Friends\' changes'),
        el('p', { class: 'note' }, st.incoming ? `${st.incoming} new change(s) from your friends are ready.` : 'You have everything your friends shared.'),
        el('button', { class: 'btn' + (st.incoming ? ' primary' : ''), onclick: () => teamJob('/api/team/get', {}, "Get friends' changes") }, 'Get friends\' changes'))),
    el('p', { class: 'note' }, 'If you and a friend changed the same thing, the editor shows both and you pick which one to keep. Nothing is overwritten without asking.'),
    el('div', { class: 'row' },
      el('div', { class: 'card grow' },
        el('h3', {}, 'Recent changes'),
        st.recent.length ? el('div', { class: 'rows' }, st.recent.map(r => el('div', { class: 'rowline teamrow' },
          el('b', {}, r.who), el('span', { class: 'grow' }, r.what), el('span', { class: 'note' }, teamAgo(r.time)))))
          : el('div', { class: 'note' }, 'Nothing shared yet.')),
      el('div', { class: 'card grow' },
        el('h3', {}, 'Team'),
        st.people.length ? el('div', { class: 'note' }, 'Shared changes so far: ' + st.people.join(', ')) : null,
        st.viaCode ? teamNewCodeBox(st) : teamCodeBox(st),
        st.viaCode ? null : el('details', { class: 'teammore' },
          el('summary', {}, 'Or invite by GitHub username'),
          people,
          el('div', { class: 'searchrow', id: 'teamInviteRow' }, invite, el('button', { class: 'btn', onclick: doInvite }, 'Invite')),
          el('p', { class: 'note' }, 'Invited friends sign in with their own GitHub account and click Join.')))),
    el('p', { class: 'note' },
      st.viaCode ? null : el('a', { href: '#', onclick: async (e) => { e.preventDefault(); await api('/api/team/signout', {}); openTeam(); } }, 'Sign out'), st.viaCode ? null : ' · ',
      el('a', { href: '#', onclick: async (e) => {
        e.preventDefault();
        if (!confirm('Stop syncing this folder with the team? Your game stays as it is, and you can join again later.')) return;
        await api('/api/team/leave', {});
        if (st.viaCode) await api('/api/team/signout', {});
        openTeam();
      } }, 'Leave this team game')));
}

// Friends who joined with a team code: swap in a new one if the owner changed it.
function teamNewCodeBox(st) {
  const code = el('input', { class: 'search', type: 'text', placeholder: 'New team code (starts with EMERALD-)' });
  const go = () => teamJob('/api/team/joincode', { code: code.value, name: st.login }, 'Join a team game');
  code.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
  return el('details', { class: 'teammore' },
    el('summary', {}, 'Got a new team code?'),
    el('p', { class: 'note' }, 'If the owner made a new code, paste it here. Your game and edits stay as they are.'),
    el('div', { class: 'searchrow' }, code, el('button', { class: 'btn', onclick: go }, 'Use code')));
}

function teamCodeBox(st) {
  const box = el('div', {});
  const showCode = (c) => {
    const out = el('input', { class: 'search mono', type: 'text', readonly: true, value: c, onclick: (e) => e.target.select() });
    box.replaceChildren(
      el('p', {}, el('b', {}, 'Team code'), ': send this to friends. They paste it in Team with their name, and that is all.'),
      el('div', { class: 'searchrow' }, out, el('button', { class: 'btn primary', onclick: async () => {
        try { await navigator.clipboard.writeText(c); toast('Copied the team code.'); } catch (e) { out.select(); document.execCommand('copy'); toast('Copied the team code.'); }
      } }, 'Copy')),
      el('p', { class: 'note' }, 'Anyone with this code can change the game, so only give it to friends. To lock someone out, ',
        el('a', { href: 'https://github.com/settings/personal-access-tokens', target: '_blank' }, 'delete the old code on GitHub'),
        ' and ', el('a', { href: '#', onclick: (e) => { e.preventDefault(); makeForm(); } }, 'make a new one'), '.'));
  };
  const makeForm = () => {
    const paste = el('input', { class: 'search', type: 'password', placeholder: 'Paste the code GitHub shows (starts with github_pat_)' });
    const go = async () => {
      try { const r = await api('/api/team/code', { token: paste.value }); toast('Team code ready.'); showCode(r.code); }
      catch (e) { toast(e.message, true); }
    };
    paste.addEventListener('keydown', e => { if (e.key === 'Enter') go(); });
    const repoName = st.repo.split('/')[1];
    box.replaceChildren(
      el('p', {}, el('b', {}, 'Make a team code'), ' so friends can join without a GitHub account:'),
      el('ol', { class: 'teamsteps' },
        el('li', {}, el('a', { class: 'btn primary small', href: st.codeTokenUrl, target: '_blank' }, 'Open the GitHub page')),
        el('li', {}, 'Under Repository access pick "Only select repositories" and choose ', el('b', {}, repoName),
          '. Check that Contents and Workflows both say "Read and write". Click "Generate token" at the bottom and copy the code.'),
        el('li', {}, 'Paste it here:', el('div', { class: 'searchrow' }, paste, el('button', { class: 'btn primary', onclick: go }, 'Make code')))),
      el('p', { class: 'note' }, 'This code only opens this one game, nothing else on your GitHub.'));
  };
  if (st.teamCode) showCode(st.teamCode); else makeForm();
  return box;
}

async function teamRemove(login, inviteId = null) {
  if (!confirm(inviteId ? `Take back the invite for ${login}?` : `Remove ${login} from the team? They keep their own copy but can no longer share or get changes.`)) return;
  try { await api('/api/team/remove', { login, inviteId }); openTeam(); } catch (e) { toast(e.message, true); }
}

// ---- picking versions ---------------------------------------------------------

async function openConflicts() {
  let data;
  try { data = await api('/api/team/conflicts'); } catch (e) { toast(e.message, true); return; }
  const picks = {};
  const fromLabel = data.why === 'update' ? 'the editor update' : null;
  const finish = el('button', { class: 'btn primary', disabled: true }, 'Done, combine them');
  const left = el('span', { class: 'note' });
  const total = data.files.reduce((n, f) => n + (f.blocks ? f.blocks.length : 1), 0);
  const refresh = () => {
    let done = 0;
    for (const f of data.files) {
      const p = picks[f.path];
      done += f.blocks ? (p || []).filter(Boolean).length : (p ? 1 : 0);
    }
    finish.disabled = done < total;
    left.textContent = done < total ? `${total - done} left to pick` : 'All picked.';
  };
  const choiceRow = (onPick, opts) => {
    const btns = opts.map(([key, label]) => el('button', { class: 'btn small', onclick: () => {
      for (const b of btns) b.classList.toggle('primary', b === btns[opts.findIndex(o => o[0] === key)]);
      onPick(key); refresh();
    } }, label));
    return el('div', { class: 'rowline' }, btns);
  };
  const files = data.files.map(f => {
    const them = fromLabel || f.who;
    const head = el('div', { class: 'conflicthead' }, el('b', {}, f.area), el('span', { class: 'note' }, ' · ' + f.path));
    if (!f.blocks) {
      const mineTxt = f.mineGone ? 'You deleted this file' : 'Your version of the whole file';
      const theirTxt = f.theirsGone ? `${them} deleted this file` : `${them}'s version of the whole file`;
      return el('div', { class: 'card' }, head,
        el('p', { class: 'note' }, 'This file cannot be shown line by line, so pick one whole version.'),
        choiceRow(k => { picks[f.path] = k; }, [['mine', 'Keep mine: ' + mineTxt], ['theirs', 'Keep theirs: ' + theirTxt]]));
    }
    picks[f.path] = new Array(f.blocks.length).fill(null);
    return el('div', { class: 'card' }, head,
      f.blocks.map((b, i) => el('div', { class: 'conflict' },
        b.before ? el('pre', { class: 'ctx' }, b.before) : null,
        el('div', { class: 'sides' },
          el('div', { class: 'side mine' }, el('div', { class: 'label' }, 'Yours'), el('pre', {}, b.mine || '(nothing: you removed this)')),
          el('div', { class: 'side theirs' }, el('div', { class: 'label' }, them), el('pre', {}, b.theirs || '(nothing: they removed this)'))),
        b.after ? el('pre', { class: 'ctx' }, b.after) : null,
        choiceRow(k => { picks[f.path][i] = k; }, [['mine', 'Keep mine'], ['theirs', 'Keep theirs'], ['both', 'Keep both']]))));
  });
  finish.addEventListener('click', async () => {
    try {
      const res = await api('/api/team/resolve', { choices: picks });
      closeModal();
      teamRefresh().catch(() => {});
      if (res.editorChanged) { toast('Combined. The editor is restarting with the newer version...'); waitForRestart(); return; }
      if (res.why === 'share') teamJob('/api/team/share', {}, 'Share my changes');
      else toast('Combined! Your game now has both sets of changes.');
      if (typeof loadTrainerList === 'function') loadTrainerList().catch(() => {});
    } catch (e) { toast(e.message, true); }
  });
  const cancel = el('button', { class: 'btn ghost', onclick: async () => {
    if (!confirm('Put everything back to how it was before, without their changes? You can get them again later.')) return;
    try { await api('/api/team/cancel', {}); closeModal(); teamRefresh().catch(() => {}); toast('Back to how it was.'); }
    catch (e) { toast(e.message, true); }
  } }, 'Cancel, keep my game as it was');
  refresh();
  openModal('Pick which version to keep', el('div', { class: 'team' },
    el('p', {}, `You and ${fromLabel || 'a friend'} changed the same thing. For each one, keep yours, theirs, or both.`),
    files,
    el('div', { class: 'rowline', style: 'justify-content:flex-end' }, left, cancel, finish)));
}

$('#teamBtn').addEventListener('click', openTeam);

// Auto-sync about once a minute; otherwise just look for friends' changes for the badge.
let teamSyncing = false;

function teamIdle() {
  const jobBusy = $('#teamBtn').disabled;   // a build, update or team step is running
  return !jobBusy && !anyDirty() && $('#modal').classList.contains('hidden');
}

async function teamAfterChanges(names) {
  toast('Got changes from ' + (names.join(', ') || 'your team') + '.');
  try { await loadTrainerList(); } catch (e) { /* ignore */ }
  if (typeof T !== 'undefined' && T.current && !T.dirty && typeof openTrainer === 'function') {
    try { openTrainer(T.current.id); } catch (e) { /* ignore */ }
  }
  const active = document.querySelector('.view.active');
  if (active) views[active.id.replace('view-', '')]?.onShow?.();
}

async function teamTick(first) {
  if (teamSyncing) return;
  teamSyncing = true;
  try {
    let st = await teamRefresh(false);
    if (st.merging) { if (first && $('#modal').classList.contains('hidden')) openConflicts(); return; }
    if (st.repo && st.signedIn && st.auto && teamIdle()) {
      teamSetSyncing(true);
      let res;
      try { res = await api('/api/team/sync', {}); } finally { teamSetSyncing(false); }
      if (res.restarting) { toast('Got a newer editor from your team. Restarting...'); waitForRestart(); return; }
      if (res.conflict) { await teamRefresh(); openConflicts(); return; }
      if (res.got) await teamAfterChanges(res.from || []);
      await teamRefresh(false);
    } else if (st.repo && st.signedIn) {
      await teamRefresh(true);
    }
  } catch (e) {
    // Offline is fine; try again next time, but say so on the button.
    if (TEAM.status && TEAM.status.repo) { TEAM.status.fetchError = TEAM.status.fetchError || 'The editor could not reach GitHub: ' + e.message; teamBadge(TEAM.status); }
  }
  finally { teamSyncing = false; }
}

setTimeout(() => teamTick(true), 3000);
setInterval(() => teamTick(false), 60 * 1000);
// Unsaved edits change the sign right away, without waiting for the next sync.
setInterval(() => { if (TEAM.status) teamBadge(TEAM.status); }, 3000);
