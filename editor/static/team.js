'use strict';
// ---------------------------------------------------------------------------
// Team: work on one game with friends (a private GitHub copy under the hood).
// ---------------------------------------------------------------------------

const TEAM = { status: null };

function teamAgo(t) {
  const s = Math.max(0, Date.now() / 1000 - t);
  if (s < 90) return 'just now';
  if (s < 3600) return Math.round(s / 60) + ' min ago';
  if (s < 86400) return Math.round(s / 3600) + ' h ago';
  return Math.round(s / 86400) + ' days ago';
}

function teamBadge(st) {
  const b = $('#teamBadge');
  if (st && st.merging) { b.textContent = '!'; b.classList.remove('hidden'); return; }
  if (st && st.incoming) { b.textContent = st.incoming; b.classList.remove('hidden'); return; }
  b.classList.add('hidden');
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
    jobDone = async (j) => {
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
  return el('div', { class: 'team' },
    el('p', {}, 'Everyone on the team keeps their own copy of the game and plays it on their own PC. ' +
      'Your copies stay in sync through a private space on GitHub that only your team can see.'),
    el('p', {}, 'Sign in once and the editor remembers you:'),
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
  loadPeople();
  const mine = st.outgoing || st.unsaved;
  return el('div', { class: 'team' },
    st.fetchError ? el('div', { class: 'warnbox' }, st.fetchError) : null,
    el('p', {}, 'Team game ', el('b', {}, st.repo), '. Signed in as ', el('b', {}, st.login), '.'),
    el('div', { class: 'row' },
      el('div', { class: 'card grow' },
        el('h3', {}, 'Your changes'),
        el('p', { class: 'note' }, mine ? 'You have changes your friends do not have yet.' : 'Friends already have everything you made.'),
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
        people,
        el('div', { class: 'searchrow', id: 'teamInviteRow' }, invite, el('button', { class: 'btn', onclick: doInvite }, 'Invite')),
        el('p', { class: 'note' }, 'Friends need a free GitHub account and the same Emerald setup. After you invite them, they open the editor, click Team, sign in and click Join.'))),
    el('p', { class: 'note' },
      el('a', { href: '#', onclick: async (e) => { e.preventDefault(); await api('/api/team/signout', {}); openTeam(); } }, 'Sign out'), ' · ',
      el('a', { href: '#', onclick: async (e) => {
        e.preventDefault();
        if (!confirm('Stop syncing this folder with the team? Your game stays as it is, and you can join again later.')) return;
        await api('/api/team/leave', {}); openTeam();
      } }, 'Leave this team game')));
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

// Quietly look for friends' changes now and every few minutes, so the Team badge shows them.
(function teamWatch() {
  let first = true;
  const tick = async () => {
    try {
      const st = await teamRefresh(true);
      // Left half-way through picking versions last time: pick up where it stopped.
      if (st.merging && first && $('#modal').classList.contains('hidden')) openConflicts();
    } catch (e) { /* offline is fine */ }
    first = false;
  };
  setTimeout(tick, 3000);
  setInterval(tick, 5 * 60 * 1000);
})();
