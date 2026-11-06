'use strict';
// ---------------------------------------------------------------------------
// Projects: several game folders (your own hack, team games...) and switching.
// ---------------------------------------------------------------------------

async function loadProjectName() {
  try {
    const d = await api('/api/projects');
    const cur = d.projects.find(p => p.current);
    $('#projectName').textContent = cur ? cur.name : 'Project';
    return d;
  } catch (e) { return null; }
}

function openProjectFolder(p) {
  if (anyDirty() && !confirm('Some changes are not saved yet and will be lost. Switch anyway?')) return;
  api('/api/projects/open', { path: p.path }).then(() => {
    closeModal();
    toast('Opening ' + p.name + '...');
    waitForRestart();
  }).catch(e => toast(e.message, true));
}

async function openProjects() {
  const d = await loadProjectName();
  if (!d) { toast('Could not load your projects.', true); return; }
  const name = el('input', { class: 'search', type: 'text', placeholder: 'Name, e.g. "Team game with Sam"' });
  let kind = 'fresh';
  const kindPick = el('div', { class: 'rows' },
    ['fresh', 'copy'].map(k => el('label', { class: 'rowline' },
      el('input', { type: 'radio', name: 'projkind', value: k, checked: k === kind, onchange: () => { kind = k; } }),
      k === 'fresh' ? el('span', {}, el('b', {}, 'Original game'), ' with the newest editor, none of your edits. Best for a new team game.')
                    : el('span', {}, el('b', {}, 'Copy of this game'), ', with all your edits so far.'))));
  const rows = d.projects.map(p => el('div', { class: 'item project' + (p.current ? ' active' : '') },
    el('div', { class: 'meta', style: 'flex:1;min-width:0' },
      el('div', { class: 'title' }, p.name, p.current ? el('span', { class: 'tag' }, 'open now') : null,
        p.team ? el('span', { class: 'tag team' }, 'team game') : null),
      el('div', { class: 'sub' }, p.missing ? 'The folder is missing.' : p.where)),
    p.current || p.missing ? null : el('button', { class: 'btn primary small', onclick: () => openProjectFolder(p) }, 'Open'),
    el('button', { class: 'btn small ghost', title: 'Rename', onclick: async () => {
      const n = prompt('New name for this project:', p.name);
      if (!n) return;
      try { await api('/api/projects/rename', { path: p.path, name: n }); openProjects(); } catch (e) { toast(e.message, true); }
    } }, '✎'),
    p.current ? null : el('button', { class: 'btn small ghost', title: 'Take off this list (the folder itself stays)', onclick: async () => {
      if (!confirm(`Take "${p.name}" off the list? Its folder and files are not deleted.`)) return;
      try { await api('/api/projects/forget', { path: p.path }); openProjects(); } catch (e) { toast(e.message, true); }
    } }, '✕')));
  openModal('Your projects', el('div', { class: 'team' },
    el('p', { class: 'note' }, 'Each project is its own game folder with its own edits, builds and team. Switching keeps everything as you left it.'),
    el('div', { class: 'list projects' }, rows),
    el('div', { class: 'card' },
      el('h3', {}, 'New project'),
      el('div', { class: 'searchrow' }, name),
      kindPick,
      el('div', { class: 'rowline', style: 'justify-content:flex-end;margin-top:8px' },
        el('button', { class: 'btn primary', onclick: () => {
          if (!name.value.trim()) { toast('Give the new project a name first.', true); return; }
          startJob('/api/projects/create', 'New project', (j) => { if (j.state === 'done') openProjects(); }, true, { name: name.value, kind });
          closeModal();
        } }, 'Make project')),
      el('p', { class: 'note' }, 'To work on a friend\'s team game, make an "Original game" project, open it, then use Team to join.'))));
}

$('#projectBtn').addEventListener('click', openProjects);
loadProjectName();
