'use strict';
// Recent changes (undo any save), plain-word build errors, Find anything,
// and the quick guide for each tab.

// ---------------------------------------------------------------------------
// Opening a place anywhere in the editor
// ---------------------------------------------------------------------------
async function openPlace(p) {
  if (!p || !p.view) return;
  closeModal();
  _showView(p.view);
  try {
    if (p.view === 'trainers' && p.id) {
      if (!T.list.length) await loadTrainerList();
      await openTrainer(p.id);
    } else if (p.view === 'maps' && p.map) {
      await openMap(p.map);
    } else if (p.view === 'pokemon' && p.id) {
      await openSpecies(p.id);
    } else if (p.view === 'scripts' && p.path) {
      if (!S.files.length) await loadScriptList();
      await openScript(p.path);
      if (p.line) setTimeout(() => goToScriptLine(p.line), 50);
    } else if (p.view === 'dialogue' && p.q) {
      $('#textSearch').value = p.q;
      await runTextSearch();
      if (p.label) {
        const r = (D.results || []).find(x => x.label === p.label);
        if (r) openText(r);
      }
    } else if (p.view === 'settings' && p.q) {
      if (!C.files.length) await loadSettingFiles();
      $('#settingSearch').value = p.q;
      $('#settingSearch').dispatchEvent(new Event('input', { bubbles: true }));
    } else if (p.view === 'moves' && p.id) {
      await openMoveOrItem(p.kind || (p.id.startsWith('ITEM_') ? 'item' : 'move'), p.id);
    }
  } catch (e) { toast(e.message, true); }
}

function goToScriptLine(line) {
  // Show the file as code, then put the cursor on that line.
  const codeBtn = Array.from(document.querySelectorAll('#scriptEditor button')).find(b => /^Code view/.test(b.textContent));
  if (codeBtn && !codeBtn.classList.contains('on')) codeBtn.click();
  const ta = S.textarea;
  if (!ta || !ta.isConnected) return;
  const lines = ta.value.split('\n');
  const start = lines.slice(0, line - 1).reduce((n, l) => n + l.length + 1, 0);
  ta.focus();
  ta.setSelectionRange(start, start + (lines[line - 1] || '').length);
  ta.scrollTop = Math.max(0, (line - 4) * (parseFloat(getComputedStyle(ta).lineHeight) || 19));
}

// ---------------------------------------------------------------------------
// A failed build, in plain words
// ---------------------------------------------------------------------------
function renderJobHelp(help) {
  const box = $('#jobHelp');
  if (!help) { box.classList.add('hidden'); box.replaceChildren(); return; }
  const parts = [
    el('div', { class: 'helpwhat' }, el('b', {}, 'What went wrong: '), help.what),
  ];
  if (help.where) parts.push(el('div', {}, el('b', {}, 'Where: '), help.where, help.line && help.file ? ` (line ${help.line})` : ''));
  if (help.changed && help.changed.length) {
    parts.push(el('div', { class: 'note' }, 'Changed since your game last built: ' + help.changed.join(', ') + '.'));
  }
  const btns = el('div', { class: 'row', style: 'gap:8px;margin-top:8px' });
  if (help.open) btns.append(el('button', { class: 'btn small primary', onclick: () => { $('#jobPanel').classList.add('hidden'); openPlace(help.open); } }, 'Open it so I can fix it'));
  if (help.canGoBack) btns.append(el('button', { class: 'btn small', onclick: goBackToWorking }, '↩ Go back to the last version that worked'));
  btns.append(el('button', { class: 'btn small ghost', onclick: openHistory }, 'Recent changes'));
  parts.push(btns);
  box.replaceChildren(...parts);
  box.classList.remove('hidden');
}

async function goBackToWorking() {
  if (anyDirty() && !confirm('Some changes are not saved yet and will be lost. Continue?')) return;
  if (!confirm('Put your game back to the last version that built? Everything you changed since then is kept in Recent changes, so you can bring it back.')) return;
  try {
    const res = await api('/api/history/lastgood', {});
    toast(res.message);
    reloadAfterRestore();
  } catch (e) { toast(e.message, true); }
}

function reloadAfterRestore() {
  // Every tab may show something that just changed: start fresh.
  setTimeout(() => location.reload(), 900);
}

// ---------------------------------------------------------------------------
// Recent changes
// ---------------------------------------------------------------------------
function timeAgo(t) {
  const s = Math.max(0, Date.now() / 1000 - t);
  if (s < 60) return 'just now';
  if (s < 3600) return Math.floor(s / 60) + ' min ago';
  if (s < 86400) return Math.floor(s / 3600) + ' h ago';
  return fmtTime(t);
}

async function openHistory() {
  let data;
  try { data = await api('/api/history'); } catch (e) { toast(e.message, true); return; }
  const list = el('div', { class: 'historylist' });
  if (!data.entries.length) list.append(el('p', { class: 'note' }, 'Nothing saved yet. Every time you save something, it shows up here and can be undone.'));
  for (const e of data.entries) {
    const files = e.files.join(', ') + (e.fileCount > e.files.length ? ` and ${e.fileCount - e.files.length} more` : '');
    list.append(el('div', { class: 'historyrow' + (e.undone ? ' undone' : '') },
      el('div', { class: 'meta' },
        el('div', { class: 'title' }, e.label, e.worked ? el('span', { class: 'pill ok' }, 'built fine') : null, e.undone ? el('span', { class: 'pill' }, 'undone') : null),
        el('div', { class: 'sub', title: files }, timeAgo(e.time) + ' · ' + files)),
      el('div', { class: 'row', style: 'gap:6px;flex-wrap:nowrap' },
        e.undone ? null : el('button', { class: 'btn small', title: 'Take back only this change. Everything else stays.', onclick: () => historyAction('/api/history/undo', e, `Take back "${e.label}"? Everything else you changed stays.`) }, 'Undo'),
        el('button', { class: 'btn small ghost', title: 'Put the whole game back to how it was just before this change. Later changes are taken back too (and stay in this list).', onclick: () => historyAction('/api/history/goback', e, `Put the whole game back to how it was just before "${e.label}"? Changes made after it are taken back too, but they stay in this list so you can bring them back.`) }, 'Go back to before this'))));
  }
  const top = el('div', {},
    el('p', { class: 'note' }, 'Everything you saved, newest first. Undo takes back one change and keeps the rest. Nothing here is ever lost: undoing is itself added to the list.'),
    data.lastGood ? el('div', { class: 'row', style: 'margin-bottom:10px' },
      el('button', { class: 'btn small', onclick: goBackToWorking }, '↩ Go back to the last version that built'),
      el('span', { class: 'note' }, 'built ' + timeAgo(data.lastGood.time))) : null,
    list);
  openModal('Recent changes', top);
}

async function historyAction(path, e, question) {
  if (anyDirty() && !confirm('Some changes are not saved yet and will be lost. Continue?')) return;
  if (!confirm(question)) return;
  try {
    const res = await api(path, { id: e.id });
    toast(res.message);
    closeModal();
    reloadAfterRestore();
  } catch (err) { toast(err.message, true); }
}

$('#historyBtn').addEventListener('click', openHistory);

// ---------------------------------------------------------------------------
// Find anything
// ---------------------------------------------------------------------------
const FIND_KINDS = {
  trainer: ['Trainers', r => ({ view: 'trainers', id: r.id })],
  map: ['Maps', r => ({ view: 'maps', map: r.id })],
  species: ['Pokémon', r => ({ view: 'pokemon', id: r.id })],
  move: ['Moves', r => ({ view: 'moves', kind: 'move', id: r.id })],
  item: ['Items', r => ({ view: 'moves', kind: 'item', id: r.id })],
  text: ['Dialogue', r => ({ view: 'dialogue', q: r.q, label: r.id })],
  setting: ['Game settings', r => ({ view: 'settings', q: r.id })],
  script: ['Scripts', r => ({ view: 'scripts', path: r.id })],
};

const findBox = el('div', { class: 'findbox hidden' });
document.body.append(findBox);
findBox.addEventListener('mousedown', e => e.preventDefault());
let findActive = -1;
let findRows = [];

const runFind = debounce(async () => {
  const q = $('#globalSearch').value.trim();
  if (q.length < 2) { findBox.classList.add('hidden'); return; }
  let res;
  try { res = await api('/api/find?q=' + encodeURIComponent(q)); } catch (e) { return; }
  if ($('#globalSearch').value.trim() !== q) return;
  findRows = [];
  const frag = document.createDocumentFragment();
  for (const kind of res.order || Object.keys(FIND_KINDS)) {
    if (!FIND_KINDS[kind]) continue;
    const [title, to] = FIND_KINDS[kind];
    const rows = res[kind] || [];
    if (!rows.length) continue;
    frag.append(el('div', { class: 'grouphead' }, title));
    for (const r of rows) {
      const i = findRows.length;
      findRows.push(to(r));
      frag.append(el('div', { class: 'pick', 'data-i': i, onclick: () => chooseFind(i) },
        r.img ? el('img', { src: imgUrl(r.img), alt: '', loading: 'lazy' }) : null,
        el('span', {}, el('b', {}, r.name), r.sub ? el('span', { class: 'findsub' }, ' ' + r.sub) : null)));
    }
  }
  if (!findRows.length) frag.append(el('div', { class: 'pick none' }, `Nothing matches "${q}"`));
  findBox.replaceChildren(frag);
  const r = $('#globalSearch').getBoundingClientRect();
  findBox.style.top = (r.bottom + 4) + 'px';
  findBox.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 440)) + 'px';
  findBox.classList.remove('hidden');
  findActive = findRows.length ? 0 : -1;
  highlightFind();
}, 200);

function highlightFind() {
  findBox.querySelectorAll('.pick[data-i]').forEach(r => r.classList.toggle('active', Number(r.dataset.i) === findActive));
  findBox.querySelector('.pick.active')?.scrollIntoView({ block: 'nearest' });
}

function chooseFind(i) {
  const p = findRows[i];
  findBox.classList.add('hidden');
  $('#globalSearch').blur();
  openPlace(p);
}

$('#globalSearch').addEventListener('input', runFind);
$('#globalSearch').addEventListener('focus', () => { if ($('#globalSearch').value.trim().length > 1) runFind(); });
$('#globalSearch').addEventListener('blur', () => setTimeout(() => findBox.classList.add('hidden'), 100));
$('#globalSearch').addEventListener('keydown', e => {
  if (findBox.classList.contains('hidden')) return;
  if (e.key === 'ArrowDown') { findActive = Math.min(findRows.length - 1, findActive + 1); highlightFind(); e.preventDefault(); }
  else if (e.key === 'ArrowUp') { findActive = Math.max(0, findActive - 1); highlightFind(); e.preventDefault(); }
  else if (e.key === 'Enter' && findActive >= 0) { chooseFind(findActive); e.preventDefault(); }
  else if (e.key === 'Escape') { findBox.classList.add('hidden'); }
});
document.addEventListener('keydown', e => {
  // Ctrl+K or / jumps to Find anything.
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName);
  if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') || (e.key === '/' && !typing)) {
    e.preventDefault();
    $('#globalSearch').focus();
    $('#globalSearch').select();
  }
});

// ---------------------------------------------------------------------------
// Quick guide for each tab
// ---------------------------------------------------------------------------
const HELP = {
  trainers: ['Trainers', [
    'Pick a trainer on the left. Trainers with the same name (like rematches) are grouped, and the strip at the top switches between their battles.',
    'Click the battle picture or the overworld sprite to pick a new look from the gallery.',
    'Each Pokémon card has its species, level, item, ability, nature and moves. Type in any box to search the list.',
    'Paste a team from Pokémon Showdown with "Paste Showdown", or press "Make competitive" for strong sets in one click.',
    'Change what they say before and after the battle at the bottom.',
    'Press Save (or Ctrl+S). Then press ▶ Play to try it.',
  ]],
  maps: ['Maps', [
    'Pick a map on the left to see it drawn.',
    'Click an empty spot to place an item ball or a hidden item. Drag items and people to move them.',
    'Click a person to see what they say and their script, and edit both.',
    'Click a door (the blue squares) to choose where it leads, or press "Go there" to jump to that map. Click a sign to change what it says.',
    'Below the map: wild Pokémon, shop items and prices, gift Pokémon, and "+ New trainer".',
  ]],
  pokemon: ['Pokémon data', [
    'Pick a Pokémon to change its types, abilities, stats, evolutions, moves and Pokédex entry.',
    'Use "New pictures" to put in your own front and back pictures from a PNG file.',
    'The buttons at the top left change the three starters and which move each TM teaches.',
  ]],
  moves: ['Moves & items', [
    'Pick a move to change its name, type, power, accuracy, PP, category, priority and description.',
    'Pick an item to change its name, price and description.',
    'Moves used by many trainers change for all of them.',
  ]],
  dialogue: ['Dialogue', [
    'Type any words the game says to find every line that has them.',
    'Click a result to edit it. The preview shows the text boxes, and red marks lines that are too wide.',
    'To change a word everywhere, type the new word in "Replace with", untick lines you want to keep, then press "Replace in ticked".',
  ]],
  scripts: ['Scripts', [
    'Scripts say what happens on a map: who talks, what you get, battles, doors and events.',
    'Simple view shows each step in plain words with boxes to change it. Code view is the file itself.',
    'Most people are easier to edit by clicking them in the Maps tab.',
  ]],
  settings: ['Game settings', [
    'Every switch that changes how the game works: battle rules by generation, EXP, followers, level caps and more.',
    'Search at the top left (for example "exp" or "crit"). Each setting explains itself.',
    'Changing settings rebuilds most of the game, so the next Play takes a few minutes.',
  ]],
  fun: ['Fun Modes', [
    'Randomizers, Hard mode, level caps and comedy themes.',
    'Pick what you want, press Preview to see what changes, then Apply.',
    'Your game is saved first, so "Undo Fun Modes" on the left always takes you back.',
  ]],
};
const HELP_ALWAYS = [
  'Find anything (top bar, or press Ctrl+K) jumps to any trainer, map, Pokémon, move, item, text or setting.',
  'Recent changes lists everything you saved. Undo takes back one change; nothing is ever lost.',
  'If ▶ Play cannot build the game, it tells you what went wrong and where, and can put your game back to the last version that worked.',
];

function helpSeen(view) { try { return localStorage.getItem('emerald.help.' + view) === '1' || localStorage.getItem('emerald.help.off') === '1'; } catch (e) { return true; } }
function markHelpSeen(view) { try { localStorage.setItem('emerald.help.' + view, '1'); } catch (e) { /* ignore */ } }

function openHelp(view) {
  const h = HELP[view];
  if (!h) return;
  markHelpSeen(view);
  const off = el('input', { type: 'checkbox' });
  try { off.checked = localStorage.getItem('emerald.help.off') === '1'; } catch (e) { /* ignore */ }
  off.addEventListener('change', () => { try { localStorage.setItem('emerald.help.off', off.checked ? '1' : '0'); } catch (e) { /* ignore */ } });
  openModal('How to use: ' + h[0], el('div', { class: 'helptips' },
    el('ol', {}, h[1].map(t => el('li', {}, t))),
    el('h3', {}, 'Anywhere in the editor'),
    el('ul', {}, HELP_ALWAYS.map(t => el('li', {}, t))),
    el('label', { class: 'row', style: 'gap:8px;margin-top:12px' }, off, "Don't open this by itself when I visit a tab"),
    el('p', { class: 'note' }, 'Press ? at the top any time to see this again.')));
}

function activeView() { return document.querySelector('.view.active')?.id.replace('view-', ''); }
$('#helpBtn').addEventListener('click', () => openHelp(activeView()));

// Open the guide by itself the first time each tab is visited.
const _showView = showView;
showView = function (name) {
  _showView(name);
  if (!helpSeen(name) && $('#modal').classList.contains('hidden')) setTimeout(() => openHelp(name), 300);
};
setTimeout(() => { const v = activeView(); if (v && !helpSeen(v)) openHelp(v); }, 1200);
