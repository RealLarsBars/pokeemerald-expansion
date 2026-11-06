'use strict';
// Moves & items tab: names, power, type, accuracy, PP, category, priority,
// descriptions, and item names, prices and descriptions.

const MI = { kind: 'move', lists: null, current: null, original: null, dirty: false };
const CATEGORY_NAMES = { DAMAGE_CATEGORY_PHYSICAL: 'Physical', DAMAGE_CATEGORY_SPECIAL: 'Special', DAMAGE_CATEGORY_STATUS: 'Status (no damage)' };

function typeConst(name) { return 'TYPE_' + String(name).toUpperCase().replace(/[^A-Z0-9]+/g, '_'); }
function typeName(c) { return prettyFromConst('TYPE', c); }

async function loadMovesItems(force = false) {
  if (!MI.lists || force) MI.lists = await api('/api/movesitems');
  renderMoveItemList();
}

function renderMoveItemList() {
  const q = $('#miSearch').value.trim().toLowerCase();
  document.querySelectorAll('#miKinds button').forEach(b => b.classList.toggle('primary', b.dataset.kind === MI.kind));
  const rows = MI.kind === 'move' ? MI.lists.moves : MI.lists.items;
  const frag = document.createDocumentFragment();
  let n = 0;
  for (const r of rows) {
    if (q && !r.name.toLowerCase().includes(q) && !r.const.toLowerCase().includes(q)) continue;
    if (++n > 500) { frag.append(el('div', { class: 'note', style: 'padding:8px' }, 'Type to search for more...')); break; }
    const sub = MI.kind === 'move'
      ? `${typeName(r.type)} · ${r.power ? 'power ' + r.power : (CATEGORY_NAMES[r.category] || '').split(' ')[0]}`
      : `${r.pocket} · ${r.price ? '₽' + r.price : 'not sold'}`;
    frag.append(el('div', { class: 'item' + (MI.current?.const === r.const ? ' active' : ''), onclick: () => openMoveOrItem(MI.kind, r.const) },
      el('div', { class: 'meta' }, el('div', { class: 'title' }, r.name), el('div', { class: 'sub' }, sub))));
  }
  if (!n) frag.append(el('div', { class: 'empty' }, 'Nothing matches.'));
  $('#miList').replaceChildren(frag);
}

async function openMoveOrItem(kind, id) {
  if (MI.dirty && !confirm('You have unsaved changes. Throw them away?')) return;
  try {
    if (!MI.lists) MI.lists = await api('/api/movesitems');
    if (MI.kind !== kind) { MI.kind = kind; }
    const d = await api(`/api/${kind}?id=` + encodeURIComponent(id));
    MI.current = d;
    MI.original = JSON.parse(JSON.stringify(d));
    MI.dirty = false;
    renderMoveItem();
    renderMoveItemList();
  } catch (e) { toast(e.message, true); }
}

function markMIDirty() { MI.dirty = true; const d = $('#miDirty'); if (d) d.textContent = 'Unsaved changes'; }

function descriptionBox(d) {
  // Each line of a description has to fit its window; the longest line the
  // game already uses is a safe guide.
  const limit = Math.max(110, ...MI.original.description.split('\n').map(lineWidth));
  const maxLines = Math.max(MI.original.description.split('\n').length, d.kind === 'move' ? 4 : 3);
  const ta = el('textarea', { rows: 4, value: d.description, spellcheck: 'true' });
  const warn = el('div', { class: 'note' });
  const check = () => {
    const lines = ta.value.split('\n');
    const problems = [];
    lines.forEach((l, i) => { const w = lineWidth(l); if (w > limit) problems.push(`line ${i + 1} is ${w - limit}px too wide`); });
    if (lines.length > maxLines) problems.push(`at most ${maxLines} lines fit`);
    warn.textContent = problems.length ? '⚠ ' + problems.join(', ') + '. Press Enter to start a new line.' : 'Press Enter to start a new line. Each line must fit in the game\'s window.';
    warn.style.color = problems.length ? 'var(--warn)' : '';
  };
  ta.addEventListener('input', () => { d.description = ta.value; markMIDirty(); check(); });
  check();
  return el('label', { class: 'field', style: 'flex:1 1 100%' }, el('span', {}, 'Description'), ta, warn);
}

function renderMoveItem() {
  const d = MI.current;
  const root = $('#miEditor');
  const save = el('button', { class: 'btn primary', onclick: saveMoveItem }, 'Save');
  const head = el('div', { class: 'savebar' },
    d.icon ? el('img', { src: imgUrl(d.icon), style: 'width:32px;height:32px;image-rendering:pixelated' }) : null,
    el('h2', {}, d.name, el('span', { class: 'idtag' }, d.const)),
    el('span', { id: 'miDirty', class: 'dirty' }, MI.dirty ? 'Unsaved changes' : ''),
    el('button', { class: 'btn ghost', onclick: () => { MI.dirty = false; openMoveOrItem(d.kind, d.const); } }, 'Revert'),
    save);
  const set = (k, v) => { d[k] = v; markMIDirty(); };
  const name = inputField('Name', d.name, v => set('name', v), { maxlength: d.nameMax });
  const card = el('div', { class: 'card' }, el('div', { class: 'row' }, name));
  if (d.kind === 'move') {
    card.firstChild.append(
      selectField('Type', GD.types.map(t => ({ value: typeConst(t), label: t })), d.type, v => set('type', v)),
      selectField('Category', Object.entries(CATEGORY_NAMES).map(([value, label]) => ({ value, label })), d.category, v => set('category', v)),
      inputField('Power', d.power, v => set('power', v), { type: 'number', min: 0, max: 255, style: 'width:90px' }),
      inputField('Accuracy', d.accuracy, v => set('accuracy', v), { type: 'number', min: 0, max: 100, style: 'width:90px' }),
      inputField('PP', d.pp, v => set('pp', v), { type: 'number', min: 1, max: 64, style: 'width:80px' }),
      inputField('Priority', d.priority, v => set('priority', v), { type: 'number', min: -7, max: 5, style: 'width:80px' }));
    card.append(el('p', { class: 'note' }, `What it does: ${d.effect}. Power 0 means it does no direct damage. Accuracy 0 means it never misses. Priority above 0 goes first (like Quick Attack).`));
  } else {
    card.firstChild.append(
      inputField('Price', d.price, v => set('price', v), { type: 'number', min: 0, max: 999999, style: 'width:120px' }),
      el('div', { class: 'field' }, el('span', {}, 'Bag pocket'), el('div', { style: 'padding:7px 0' }, d.pocket)));
    card.append(el('p', { class: 'note' }, 'Shops sell it for this price and buy it back for half. Price 0 means it cannot be sold.' + (d.isTM ? ' A TM takes its name and description from its move when you change the TM list.' : '')));
  }
  card.append(el('div', { class: 'row' }, descriptionBox(d)));
  root.replaceChildren(head, card);
}

async function saveMoveItem() {
  const d = MI.current, o = MI.original;
  if (!d) return;
  const keys = d.kind === 'move' ? ['name', 'description', 'type', 'category', 'power', 'accuracy', 'pp', 'priority'] : ['name', 'description', 'price'];
  const changes = {};
  for (const k of keys) if (String(d[k]) !== String(o[k])) changes[k] = d[k];
  if (!Object.keys(changes).length) { toast('Nothing changed.'); return; }
  try {
    const res = await api('/api/' + d.kind, { id: d.const, changes });
    MI.current = res;
    MI.original = JSON.parse(JSON.stringify(res));
    MI.dirty = false;
    renderMoveItem();
    loadMovesItems(true);
    toast('Saved ' + res.name + '.');
  } catch (e) { toast(e.message, true); }
}

$('#miSearch').addEventListener('input', debounce(() => MI.lists && renderMoveItemList(), 120));
document.querySelectorAll('#miKinds button').forEach(b => b.addEventListener('click', () => { MI.kind = b.dataset.kind; renderMoveItemList(); }));

views.moves = {
  isDirty: () => MI.dirty,
  save: saveMoveItem,
  onShow: () => { if (!MI.lists) loadMovesItems().catch(e => toast(e.message, true)); },
};
