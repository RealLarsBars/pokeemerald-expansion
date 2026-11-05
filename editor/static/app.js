'use strict';

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------
const $ = (sel, root = document) => root.querySelector(sel);

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  // Names of Pokemon, moves and items are not dictionary words: no red squiggles.
  if (tag === 'input') { node.spellcheck = false; node.autocomplete = 'off'; }
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') node.className = v;
    else if (k === 'text') node.textContent = v;
    else if (k === 'html') node.innerHTML = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else if (k === 'value') node.value = v;
    else if (v === true) node.setAttribute(k, '');
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function api(path, body) {
  const opts = body === undefined ? {} : {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Emerald': '1' },
    body: JSON.stringify(body),
  };
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({ error: 'The editor stopped responding. Is its window still open?' }));
  if (!res.ok || data.error) throw new Error(data.error || res.statusText);
  return data;
}

let toastTimer = null;
window.addEventListener('error', (ev) => toast('Something went wrong: ' + ev.message, true));
window.addEventListener('unhandledrejection', (ev) => toast('Something went wrong: ' + ((ev.reason && ev.reason.message) || ev.reason), true));
function toast(msg, bad = false) {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'toast' + (bad ? ' bad' : '');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add('hidden'), bad ? 6000 : 2500);
}

function imgUrl(path) { return path ? '/img?path=' + encodeURIComponent(path) : ''; }

function debounce(fn, ms) {
  let t = null;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// Same rules trainerproc uses to turn names into constants.
function toConst(prefix, value) {
  value = (value || '').trim();
  if (!value) return prefix + '_NONE';
  if (value.startsWith(prefix + '_')) return value;
  let out = '';
  for (const c of value) {
    if (/[A-Za-z0-9]/.test(c)) out += c.toUpperCase();
    else if (c === "'") continue;
    else out += '_';
  }
  return prefix + '_' + out;
}

function speciesConst(value) {
  value = (value || '').trim();
  if (!value) return 'SPECIES_NONE';
  if (value.startsWith('SPECIES_')) return value;
  let out = '', underscore = false;
  for (const c of value) {
    if (/[A-Za-z0-9]/.test(c)) { if (underscore) out += '_'; underscore = false; out += c.toUpperCase(); }
    else if (c === "'" || c === '%' || c === '\u2019') continue;
    else if (c === '\u2642') { underscore = false; out += '_M'; }
    else if (c === '\u2640') { underscore = false; out += '_F'; }
    else if (c === '\u00e9') { if (underscore) out += '_'; underscore = false; out += 'E'; }
    else underscore = true;
  }
  return 'SPECIES_' + out;
}

function prettyFromConst(prefix, c) {
  if (!c || !c.startsWith(prefix + '_')) return c || '';
  return c.slice(prefix.length + 1).split('_').filter(Boolean).map(w => /^\d+$/.test(w) ? w : w[0] + w.slice(1).toLowerCase()).join(' ');
}

// ---------------------------------------------------------------------------
// Game data
// ---------------------------------------------------------------------------
const GD = {};
const index = {};

async function loadGameData() {
  Object.assign(GD, await api('/api/gamedata'));
  index.species = new Map(GD.species.map(s => [s.const, s]));
  index.speciesByName = new Map(GD.species.map(s => [s.name, s]));
  index.moves = new Set(GD.moves.map(m => m.const));
  index.items = new Set(GD.items.map(m => m.const));
  index.abilities = new Set(GD.abilities.map(m => m.const));
  index.pics = new Map(GD.trainerPics.map(p => [p.const, p]));
  index.ow = new Map(GD.overworld.map(o => [o.const, o]));
  index.classes = new Map(GD.classes.map(c => [c.const, c]));
  index.music = new Map(GD.music.map(c => [c.const, c]));
  index.ai = new Map(GD.aiFlags.map(c => [c.const, c]));
  fillDatalist('dl-species', GD.species.map(s => s.name));
  fillDatalist('dl-moves', GD.moves.map(s => s.name));
  fillDatalist('dl-items', GD.items.map(s => s.name));
  fillDatalist('dl-abilities', GD.abilities.map(s => s.name));
  fillDatalist('dl-natures', GD.natures);
  fillDatalist('dl-types', GD.types);
  fillDatalist('dl-balls', GD.balls);
  fillDatalist('dl-status', GD.startingStatus);
}

function fillDatalist(id, values) {
  const dl = document.getElementById(id);
  dl.replaceChildren(...values.map(v => el('option', { value: v })));
}

// ---------------------------------------------------------------------------
// Text width preview (shared by trainer dialogue and the Dialogue tab)
// ---------------------------------------------------------------------------
const PLACEHOLDER_WIDTH = { PLAYER: 42, RIVAL: 42, STR_VAR_1: 48, STR_VAR_2: 48, STR_VAR_3: 48, KUN: 0 };

function lineWidth(line) {
  let w = 0;
  const re = /\{([^}]*)\}|([\s\S])/g;
  let m;
  while ((m = re.exec(line))) {
    if (m[1] !== undefined) w += PLACEHOLDER_WIDTH[m[1]] ?? 0;
    else w += GD.charWidths[m[2]] ?? 6;
  }
  return w;
}

function renderBoxes(text, container) {
  container.replaceChildren();
  const boxes = text.replace(/\r/g, '').replace(/^\n+|\n+$/g, '').split(/\n\s*\n/);
  boxes.forEach((box, i) => {
    const lines = box.split('\n');
    const div = el('div', { class: 'gbabox' });
    const warnings = [];
    lines.forEach((line, j) => {
      const w = lineWidth(line);
      const over = w > GD.textBoxWidth;
      if (over) warnings.push(`line ${j + 1} is ${w - GD.textBoxWidth}px too wide`);
      const span = el('div', { class: over ? 'over' : '' });
      span.innerHTML = escapeHtml(line).replace(/\{[^}]*\}/g, m => `<span class="ph">${m}</span>`) || '&nbsp;';
      div.append(span);
    });
    const label = el('div', { class: 'boxlabel' }, `Text box ${i + 1}` + (lines.length > 2 ? ' (scrolls)' : ''));
    if (warnings.length) label.append(el('span', { class: 'dirty' }, ' \u2013 ' + warnings.join(', ')));
    container.append(el('div', {}, label, div));
  });
}

// ---------------------------------------------------------------------------
// Tabs, keyboard
// ---------------------------------------------------------------------------
const views = {};

function showView(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.view === name));
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === 'view-' + name));
  views[name]?.onShow?.();
  try { localStorage.setItem('emerald.view', name); } catch (e) { /* ignore */ }
}

document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => showView(t.dataset.view)));

document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault();
    const active = document.querySelector('.view.active').id.replace('view-', '');
    views[active]?.save?.();
  }
  if (e.key === 'Escape') closeModal();
});

function anyDirty() { return Object.values(views).some(v => v.isDirty?.()); }
window.addEventListener('beforeunload', e => { if (anyDirty()) { e.preventDefault(); e.returnValue = ''; } });

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------
function openModal(title, body) {
  $('#modalTitle').textContent = title;
  $('#modalBody').replaceChildren(body);
  $('#modal').classList.remove('hidden');
}
function closeModal() { $('#modal').classList.add('hidden'); }
$('#modalClose').addEventListener('click', closeModal);
$('#modal').addEventListener('click', e => { if (e.target.id === 'modal') closeModal(); });

function owSprite(o, scale = 2) {
  const d = el('div', { class: 'ow' });
  if (o) {
    d.style.width = o.w * scale + 'px';
    d.style.height = o.h * scale + 'px';
    d.style.backgroundImage = `url("${imgUrl(o.img)}")`;
    d.style.backgroundSize = `auto ${o.h * scale}px`;
  }
  return d;
}

function openGallery(title, items, currentConst, onPick, kind = 'img') {
  const search = el('input', { class: 'search', type: 'search', placeholder: 'Search...' });
  const grid = el('div', { class: 'gallery' });
  const render = () => {
    const q = search.value.trim().toLowerCase();
    grid.replaceChildren(...items.filter(i => !q || i.name.toLowerCase().includes(q)).map(i => {
      const pic = kind === 'ow' ? owSprite(i, 2) : el('img', { src: imgUrl(i.img), loading: 'lazy', alt: '' });
      return el('div', {
        class: 'g' + (i.const === currentConst ? ' current' : ''),
        title: i.const,
        onclick: () => { onPick(i); closeModal(); },
      }, pic, el('div', { class: 'name' }, i.name));
    }));
  };
  search.addEventListener('input', debounce(render, 120));
  render();
  openModal(title, el('div', {}, search, el('div', { style: 'height:12px' }), grid));
  setTimeout(() => search.focus(), 50);
  grid.querySelector('.current')?.scrollIntoView({ block: 'center' });
}

// ---------------------------------------------------------------------------
// Trainers
// ---------------------------------------------------------------------------
const T = {
  list: null,       // null until loaded
  current: null,     // full trainer data being edited
  dirty: false,
  sprites: {},       // "map:index" -> {map, index, graphics_id}
  texts: {},         // label -> {file, text}
};

const HEADER_KEYS = ['Name', 'Class', 'Pic', 'Gender', 'Music', 'Items', 'AI', 'Double Battle', 'Battle Type', 'Mugshot', 'Starting Status'];
const MUGSHOTS = ['', 'Purple', 'Green', 'Pink', 'Blue', 'Yellow'];

function getField(key, fallback = '') {
  const f = T.current.fields.find(f => f[0] === key);
  return f ? f[1] : fallback;
}
function setField(key, value) {
  const f = T.current.fields.find(f => f[0] === key);
  if (f) f[1] = value;
  else T.current.fields.push([key, value]);
  markTrainerDirty();
}
function markTrainerDirty() {
  T.dirty = true;
  const d = $('#trainerDirty');
  if (d) d.textContent = 'Unsaved changes';
}

async function loadTrainerList() {
  T.list = await api('/api/trainers');
  if (!T.list.length) throw new Error('No trainers were found in src/data/trainers.party.');
  renderTrainerList();
}

// Trainers with the same name and class (e.g. all of Roxanne's battles) are one group.
function groupKey(t) { return `${(t.name || '').toUpperCase()}|${t.class}`; }

function trainerGroups() {
  const groups = new Map();
  for (const t of T.list) {
    if (t.id === 'TRAINER_NONE') continue;
    const k = groupKey(t);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(t);
  }
  return groups;
}

function speciesNamesOf(t) { return t.party.map(s => (index.species.get(s)?.name || s)); }

function renderTrainerList() {
  if (!T.list) return; // still loading
  const q = $('#trainerSearch').value.trim().toLowerCase();
  const box = $('#trainerList');
  const frag = document.createDocumentFragment();
  const currentKey = T.current ? groupKey(T.list.find(x => x.id === T.current.id) || {}) : null;
  for (const [key, battles] of trainerGroups()) {
    const matches = battles.filter(t => !q || `${t.name} ${t.id} ${t.class} ${t.where} ${speciesNamesOf(t).join(' ')}`.toLowerCase().includes(q));
    if (!matches.length) continue;
    const first = battles[0];
    const pic = index.pics.get(first.pic);
    const sub = battles.length > 1
      ? `${first.class} \u00b7 ${battles.length} battles`
      : `${first.class} \u00b7 ${speciesNamesOf(first).join(', ') || 'no Pok\u00e9mon'}`;
    frag.append(el('div', {
      class: 'item' + (key === currentKey ? ' active' : ''),
      'data-group': key,
      onclick: () => openTrainer((key === currentKey && T.current) ? T.current.id : matches[0].id),
    },
    el('img', { class: 'thumb', src: imgUrl(pic?.img), loading: 'lazy', alt: '' }),
    el('div', { class: 'meta' },
      el('div', { class: 'title' }, first.name || '(no name)'),
      el('div', { class: 'sub' }, sub + (first.where ? ` \u00b7 ${first.where}` : '')))));
  }
  box.replaceChildren(frag);
}

function battleLabel(t, i, all) {
  const n = parseInt((t.id.match(/_(\d+)$/) || [])[1], 10);
  if (n > 1 && (t.rematch || !t.where)) return `Rematch ${n - 1}`;
  if (t.rematch) return 'Rematch';
  return t.where || `Battle ${i + 1}`;
}

function levelText(t) {
  const lv = t.levels.map(l => parseInt(l, 10)).filter(n => !isNaN(n));
  if (!lv.length) return '';
  const lo = Math.min(...lv), hi = Math.max(...lv);
  return lo === hi ? `Lv ${lo}` : `Lv ${lo}\u2013${hi}`;
}

function renderBattlePicker() {
  const summary = T.list.find(x => x.id === T.current.id);
  if (!summary) return null;
  const battles = trainerGroups().get(groupKey(summary)) || [summary];
  if (battles.length < 2) return null;
  const strip = el('div', { class: 'battles' }, battles.map((t, i) => el('button', {
    class: 'battle' + (t.id === T.current.id ? ' active' : ''),
    title: t.id,
    onclick: () => openTrainer(t.id),
  },
  el('div', { class: 'btitle' }, battleLabel(t, i, battles)),
  el('div', { class: 'bsub' }, `${t.party.length} Pok\u00e9mon${levelText(t) ? ' \u00b7 ' + levelText(t) : ''}`),
  el('div', { class: 'bmons' }, t.party.map(s => el('img', { src: imgUrl(index.species.get(s)?.img), alt: index.species.get(s)?.name || s, title: index.species.get(s)?.name || s, loading: 'lazy' }))))));
  strip.addEventListener('wheel', e => {
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) { strip.scrollLeft += e.deltaY; e.preventDefault(); }
  }, { passive: false });
  setTimeout(() => strip.querySelector('.active')?.scrollIntoView({ inline: 'center', block: 'nearest' }), 0);
  return el('div', { class: 'card battlescard' },
    el('h3', {}, `All of ${summary.name || 'this trainer'}'s battles (${battles.length}) \u2013 pick one to edit`), strip);
}

async function openTrainer(id) {
  if (T.dirty && T.current && T.current.id !== id && !confirm('You have unsaved changes to this trainer. Throw them away?')) return;
  try {
    const data = await api('/api/trainer?id=' + encodeURIComponent(id));
    T.current = data;
    T.dirty = false;
    T.sprites = {};
    T.texts = {};
    renderTrainer();
    renderTrainerList();
    try { localStorage.setItem('emerald.trainer', id); } catch (e) { /* ignore */ }
  } catch (e) { toast(e.message, true); }
}

function selectField(label, options, value, onChange) {
  const sel = el('select', { onchange: () => onChange(sel.value) });
  let found = false;
  for (const o of options) {
    const opt = el('option', { value: o.value }, o.label);
    if (o.value === value) { opt.selected = true; found = true; }
    sel.append(opt);
  }
  if (!found && value) sel.prepend(el('option', { value, selected: true }, value));
  return el('label', { class: 'field' }, el('span', {}, label), sel);
}

function inputField(label, value, onInput, attrs = {}) {
  const inp = el('input', Object.assign({ value: value ?? '', oninput: () => onInput(inp.value) }, attrs));
  return el('label', { class: 'field' }, el('span', {}, label), inp);
}

function renderTrainer() {
  const t = T.current;
  const root = $('#trainerEditor');
  const picConst = toConst('TRAINER_PIC', getField('Pic'));
  const pic = index.pics.get(picConst);

  // --- header / save bar
  const saveBar = el('div', { class: 'savebar' },
    el('h2', {}, getField('Name') || t.id, el('span', { class: 'idtag' }, t.id)),
    el('span', { id: 'trainerDirty', class: 'dirty' }, T.dirty ? 'Unsaved changes' : ''),
    el('button', { class: 'btn ghost', onclick: () => openTrainer(t.id), title: 'Undo all unsaved changes' }, 'Revert'),
    el('button', { class: 'btn primary', onclick: saveTrainer }, 'Save'));

  // --- identity card
  const picImg = el('img', { src: imgUrl(pic?.img), alt: '' });
  const picPick = el('div', {
    class: 'pic-pick', title: 'Change battle picture',
    onclick: () => openGallery('Pick a battle picture', GD.trainerPics, picConst, p => {
      setField('Pic', p.name);
      picImg.src = imgUrl(p.img);
    }),
  }, picImg, el('div', { class: 'hint' }, 'Change picture'));

  const classes = GD.classes.map(c => ({ value: c.name, label: c.name }));
  const classValue = index.classes.get(toConst('TRAINER_CLASS', getField('Class')))?.name || getField('Class');
  const musicValue = index.music.get(toConst('TRAINER_ENCOUNTER_MUSIC', getField('Music')))?.name || getField('Music');

  const battleKey = t.fields.some(f => f[0] === 'Double Battle') ? 'Double Battle' : 'Battle Type';
  const battleOptions = battleKey === 'Double Battle'
    ? [{ value: 'No', label: 'Single battle' }, { value: 'Yes', label: 'Double battle' }]
    : [{ value: 'Singles', label: 'Single battle' }, { value: 'Doubles', label: 'Double battle' }];

  const identity = el('div', { class: 'card' },
    el('h3', {}, 'Trainer'),
    el('div', { class: 'row' }, picPick,
      el('div', { class: 'grid' },
        inputField('Name', getField('Name'), v => { setField('Name', v); $('.savebar h2').firstChild.textContent = v || t.id; }, { maxlength: 12 }),
        selectField('Class', classes, classValue, v => setField('Class', v)),
        selectField('Gender', [{ value: 'Male', label: 'Male' }, { value: 'Female', label: 'Female' }], getField('Gender'), v => setField('Gender', v)),
        selectField('Battle music', GD.music.map(m => ({ value: m.name, label: m.name })), musicValue, v => setField('Music', v)),
        selectField('Battle type', battleOptions, getField(battleKey, battleOptions[0].value), v => setField(battleKey, v)),
        selectField('Mugshot intro', MUGSHOTS.map(m => ({ value: m, label: m || 'None' })), getField('Mugshot'), v => setField('Mugshot', v)),
        inputField('Field effect at start', getField('Starting Status'), v => setField('Starting Status', v),
          { list: 'dl-status', placeholder: 'none (e.g. Trick Room)', title: 'Terrain, Trick Room, Tailwind... several can be joined with /' }),
      )));

  // --- items + AI
  const items = getField('Items').split('/').map(s => s.trim()).filter(Boolean);
  while (items.length < 4) items.push('');
  const writeItems = () => setField('Items', items.filter(Boolean).join(' / '));
  const itemInputs = items.map((v, i) => inputField('Item ' + (i + 1), v, nv => { items[i] = nv.trim(); writeItems(); }, { list: 'dl-items', placeholder: 'none' }));

  const aiFlags = getField('AI').split('/').map(s => s.trim()).filter(Boolean);
  const chips = el('div', { class: 'chips' });
  const renderChips = () => {
    chips.replaceChildren(...aiFlags.map((f, i) => el('span', { class: 'chip' }, f,
      el('button', { title: 'Remove', onclick: () => { aiFlags.splice(i, 1); setField('AI', aiFlags.join(' / ')); renderChips(); } }, '\u00d7'))));
    const add = el('select', {
      onchange: () => { if (add.value) { aiFlags.push(add.value); setField('AI', aiFlags.join(' / ')); renderChips(); } },
    }, el('option', { value: '' }, '+ Add AI behaviour'), GD.aiFlags.map(a => el('option', { value: a.name }, a.name)));
    chips.append(add);
  };
  renderChips();

  const extras = t.fields.filter(f => !HEADER_KEYS.includes(f[0]));
  const extraBox = extras.length ? el('details', {}, el('summary', {}, `More settings (${extras.length})`),
    el('div', { class: 'grid', style: 'margin-top:8px' }, extras.map(f => inputField(f[0], f[1], v => { f[1] = v; markTrainerDirty(); })))) : null;

  const battleCard = el('div', { class: 'card' },
    el('h3', {}, 'Items the trainer uses in battle'),
    el('div', { class: 'grid' }, itemInputs),
    el('h3', { style: 'margin-top:16px' }, 'How smart the trainer battles (AI)'),
    chips, extraBox);

  // --- party
  const partyCard = el('div', { class: 'card' },
    el('div', { class: 'row', style: 'align-items:center;margin-bottom:12px' },
      el('h3', { style: 'margin:0;flex:1' }, 'Team'),
      el('button', { class: 'btn small', onclick: openShowdownPaste }, 'Paste Showdown team'),
      el('button', { class: 'btn small', onclick: exportShowdown }, 'Copy as Showdown')),
    el('div', { id: 'party', class: 'party' }));

  // --- overworld + dialogue
  const worldCard = renderAppearances();

  root.replaceChildren(...[saveBar, renderBattlePicker(), identity, partyCard, worldCard, battleCard].filter(Boolean));
  renderParty();
}

function renderAppearances() {
  const t = T.current;
  const card = el('div', { class: 'card' }, el('h3', {}, 'In the overworld'));
  const withObjects = t.appearances.flatMap(a => a.objects.map(o => ({ a, o })));
  if (!withObjects.length && !t.appearances.length) {
    card.append(el('div', { class: 'note' }, 'This trainer is not placed on any map, or is started by a special script.'));
    return card;
  }
  const spriteRow = el('div', { class: 'row' });
  const seen = new Set();
  for (const { o } of withObjects) {
    const key = o.map + ':' + o.index;
    if (seen.has(key)) continue;
    seen.add(key);
    const current = T.sprites[key]?.graphics_id || o.graphics_id;
    const holder = el('div', {});
    const draw = gid => holder.replaceChildren(owSprite(index.ow.get(gid), 3));
    draw(current);
    spriteRow.append(el('div', {
      class: 'pic-pick', title: 'Change overworld sprite',
      onclick: () => openGallery('Pick an overworld sprite', GD.overworld, T.sprites[key]?.graphics_id || o.graphics_id, g => {
        T.sprites[key] = { map: o.map, index: o.index, graphics_id: g.const };
        draw(g.const);
        markTrainerDirty();
      }, 'ow'),
    }, holder, el('div', { class: 'note' }, o.mapName), el('div', { class: 'hint' }, 'Change sprite')));
  }
  if (spriteRow.children.length) card.append(spriteRow);

  const dialogs = el('div', { class: 'dialogs', style: 'margin-top:12px' });
  const labels = [];
  for (const a of t.appearances) {
    for (const [key, title] of [['intro', 'Before battle'], ['defeat', 'When defeated']]) {
      const label = a[key];
      if (!label || labels.includes(label) || !t.texts[label]) continue;
      labels.push(label);
      const info = t.texts[label];
      const preview = el('div', { class: 'boxes' });
      const ta = el('textarea', {
        value: T.texts[label]?.text ?? info.text,
        oninput: () => { T.texts[label] = { file: info.file, text: ta.value }; renderBoxes(ta.value, preview); markTrainerDirty(); },
      });
      renderBoxes(ta.value, preview);
      const rematch = /rematch/i.test(a.macro) || /rematch/i.test(label) ? ' (rematch)' : '';
      dialogs.append(el('div', { class: 'dialog' },
        el('label', { class: 'field' }, el('span', {}, title + rematch), ta), preview));
    }
  }
  if (labels.length) card.append(el('h3', { style: 'margin-top:16px' }, 'What they say'), dialogs);
  return card;
}

function newMon() {
  const party = T.current.party;
  const level = party.length ? party[party.length - 1].Level || '' : '5';
  return { species: '', nickname: '', gender: '', item: '', moves: [], extra: [], Level: level };
}

function renderParty() {
  const box = $('#party');
  const party = T.current.party;
  box.replaceChildren(...party.map((m, i) => monCard(m, i)));
  if (party.length < 6) {
    box.append(el('button', {
      class: 'addmon',
      onclick: () => { party.push(newMon()); markTrainerDirty(); renderParty(); box.querySelectorAll('.mon')[party.length - 1]?.querySelector('input')?.focus(); },
    }, '+ Add Pok\u00e9mon'));
  }
}

function monCard(m, i) {
  const party = T.current.party;
  const sprite = el('img', { class: 'sprite', alt: '' });
  const abilityList = el('datalist', { id: 'dl-ab-' + i });
  const update = () => {
    const sp = index.species.get(speciesConst(m.species));
    sprite.src = imgUrl(sp?.img);
    sprite.style.visibility = sp ? 'visible' : 'hidden';
    abilityList.replaceChildren(...(sp?.abilities || []).map(a => el('option', { value: prettyFromConst('ABILITY', a) })));
  };
  update();
  const set = (key, v) => { m[key] = v; markTrainerDirty(); };

  const speciesInput = el('input', {
    value: m.species, list: 'dl-species', placeholder: 'Pok\u00e9mon',
    oninput: () => { m.species = speciesInput.value; update(); markTrainerDirty(); },
  });
  while (m.moves.length < 4) m.moves.push('');
  const moves = m.moves.slice(0, 4).map((mv, j) => el('input', {
    value: mv, list: 'dl-moves', placeholder: 'Move ' + (j + 1),
    oninput: e => { m.moves[j] = e.target.value; markTrainerDirty(); },
  }));
  const move = d => {
    const j = i + d;
    if (j < 0 || j >= party.length) return;
    [party[i], party[j]] = [party[j], party[i]];
    markTrainerDirty();
    renderParty();
  };
  const nature = el('select', { onchange: () => set('Nature', nature.value) },
    el('option', { value: '' }, 'Any'), GD.natures.map(n => el('option', { value: n, selected: (m.Nature || '').toLowerCase() === n.toLowerCase() }, n)));
  const gender = el('select', { onchange: () => set('gender', gender.value) },
    el('option', { value: '' }, 'Random'),
    el('option', { value: 'M', selected: m.gender === 'M' }, 'Male'),
    el('option', { value: 'F', selected: m.gender === 'F' }, 'Female'));
  const shiny = el('select', { onchange: () => set('Shiny', shiny.value) },
    el('option', { value: '' }, 'No'), el('option', { value: 'Yes', selected: /^yes$/i.test(m.Shiny || '') }, 'Yes'));

  const gmax = el('select', { onchange: () => set('Gigantamax', gmax.value) },
    el('option', { value: '' }, 'No'), el('option', { value: 'Yes', selected: /^yes$/i.test(m.Gigantamax || '') }, 'Yes'));

  return el('div', { class: 'mon' },
    el('div', { class: 'top' }, sprite,
      el('label', { class: 'field', style: 'flex:1' }, el('span', {}, 'Pok\u00e9mon'), speciesInput),
      el('div', { class: 'tools' },
        el('button', { title: 'Move earlier', onclick: () => move(-1) }, '\u2190'),
        el('button', { title: 'Move later', onclick: () => move(1) }, '\u2192'),
        el('button', { title: 'Remove', onclick: () => { party.splice(i, 1); markTrainerDirty(); renderParty(); } }, '\u2715'))),
    el('div', { class: 'two' },
      inputField('Level', m.Level, v => set('Level', v), { type: 'number', min: 1, max: 100, placeholder: '100' }),
      inputField('Held item', m.item, v => set('item', v), { list: 'dl-items', placeholder: 'none' }),
      inputField('Ability', m.Ability, v => set('Ability', v), { list: 'dl-ab-' + i, placeholder: 'default' }),
      el('label', { class: 'field' }, el('span', {}, 'Nature'), nature)),
    abilityList,
    el('div', { class: 'field' }, el('span', {}, 'Moves (leave empty to use level-up moves)'), el('div', { class: 'moves' }, moves)),
    el('details', {}, el('summary', {}, 'More: nickname, IVs, EVs, shiny, Tera, Dynamax...'),
      el('div', { class: 'two' },
        inputField('Nickname', m.nickname, v => set('nickname', v), { maxlength: 12 }),
        el('label', { class: 'field' }, el('span', {}, 'Gender'), gender),
        inputField('IVs', m.IVs, v => set('IVs', v), { placeholder: '31 HP / 31 Atk ...' }),
        inputField('EVs', m.EVs, v => set('EVs', v), { placeholder: '252 Atk / 252 Spe' }),
        el('label', { class: 'field' }, el('span', {}, 'Shiny'), shiny),
        inputField('Ball', m.Ball, v => set('Ball', v), { list: 'dl-balls', placeholder: 'Poke' }),
        inputField('Happiness', m.Happiness, v => set('Happiness', v), { type: 'number', min: 0, max: 255 }),
        inputField('Tera type', m['Tera Type'], v => set('Tera Type', v), { list: 'dl-types' }),
        inputField('Dynamax level', m['Dynamax Level'], v => set('Dynamax Level', v), { type: 'number', min: 0, max: 10 }),
        el('label', { class: 'field' }, el('span', {}, 'Gigantamax'), gmax))));
}

function validateTrainer() {
  const problems = [];
  const t = T.current;
  t.party.forEach((m, i) => {
    const where = `Pok\u00e9mon ${i + 1}`;
    if (!m.species.trim()) return;
    if (!index.species.has(speciesConst(m.species))) problems.push(`${where}: I don't know a Pok\u00e9mon called "${m.species}".`);
    m.moves.filter(x => x && x.trim()).forEach(mv => { if (!index.moves.has(toConst('MOVE', mv))) problems.push(`${where}: unknown move "${mv}".`); });
    if (m.item && m.item.trim() && !index.items.has(toConst('ITEM', m.item))) problems.push(`${where}: unknown held item "${m.item}".`);
    if (m.Ability && m.Ability.trim() && !index.abilities.has(toConst('ABILITY', m.Ability))) problems.push(`${where}: unknown ability "${m.Ability}".`);
    const lv = parseInt(m.Level, 10);
    if (m.Level && (isNaN(lv) || lv < 1 || lv > 100)) problems.push(`${where}: level must be 1 to 100.`);
  });
  getField('Items').split('/').map(s => s.trim()).filter(Boolean).forEach(it => {
    if (!index.items.has(toConst('ITEM', it))) problems.push(`Unknown battle item "${it}".`);
  });
  if (!t.party.some(m => m.species.trim()) && t.id !== 'TRAINER_NONE') problems.push('The team needs at least one Pok\u00e9mon.');
  return problems;
}

async function saveTrainer() {
  const t = T.current;
  if (!t) return;
  const problems = validateTrainer();
  if (problems.length) {
    openModal('Fix these first', el('div', {}, el('p', { class: 'note' }, 'The game would not build with these, so nothing was saved:'),
      el('ul', {}, problems.map(p => el('li', {}, p)))));
    return;
  }
  const party = t.party.filter(m => m.species.trim()).map(m => Object.assign({}, m, { moves: m.moves.filter(x => x && x.trim()) }));
  try {
    const data = await api('/api/trainer', {
      id: t.id, fields: t.fields, party,
      sprites: Object.values(T.sprites),
      texts: T.texts,
    });
    T.current = data;
    T.dirty = false;
    T.sprites = {};
    T.texts = {};
    renderTrainer();
    const s = T.list.find(x => x.id === t.id);
    if (s) {
      s.name = getField('Name'); s.class = getField('Class');
      s.pic = toConst('TRAINER_PIC', getField('Pic'));
      s.party = data.party.map(m => speciesConst(m.species));
      s.levels = data.party.map(m => m.Level || '');
    }
    renderTrainerList();
    toast('Saved. Press Play to try it.');
  } catch (e) { toast(e.message, true); }
}

function openShowdownPaste() {
  const ta = el('textarea', { placeholder: 'Paste a team exported from Pok\u00e9mon Showdown here...' });
  const level = el('input', { type: 'number', min: 1, max: 100, value: '50', style: 'width:80px' });
  const warn = el('div');
  const go = async replace => {
    try {
      const res = await api('/api/showdown', { text: ta.value });
      if (!res.party.length) { warn.replaceChildren(el('div', { class: 'warnbox' }, 'I could not find any Pok\u00e9mon in that text.')); return; }
      res.party.forEach(m => { if (!m.Level && level.value) m.Level = level.value; });
      if (replace) T.current.party = res.party;
      else T.current.party = T.current.party.concat(res.party).slice(0, 6);
      markTrainerDirty();
      renderParty();
      closeModal();
      if (res.warnings.length) toast(res.warnings.join(' '), true);
      else toast('Team pasted. Check it, then Save.');
    } catch (e) { warn.replaceChildren(el('div', { class: 'warnbox' }, e.message)); }
  };
  openModal('Paste a Showdown team', el('div', {},
    el('p', { class: 'note' }, 'In Showdown\u2019s teambuilder, choose Import/Export, copy the text, and paste it here.'),
    ta, warn,
    el('div', { class: 'row', style: 'align-items:center;margin-top:10px' },
      el('label', { class: 'check' }, 'Level for Pok\u00e9mon without one:', level),
      el('div', { style: 'flex:1' }),
      el('button', { class: 'btn', onclick: () => go(false) }, 'Add to team'),
      el('button', { class: 'btn primary', onclick: () => go(true) }, 'Replace team'))));
  setTimeout(() => ta.focus(), 50);
}

async function exportShowdown() {
  const party = T.current.party.filter(m => m.species.trim());
  const { text } = await api('/api/showdown/export', { party });
  const ta = el('textarea', { value: text, readonly: true });
  openModal('Team in Showdown format', el('div', {}, ta,
    el('div', { class: 'row', style: 'justify-content:flex-end;margin-top:10px' },
      el('button', { class: 'btn primary', onclick: async () => { try { await navigator.clipboard.writeText(text); toast('Copied'); } catch (e) { ta.select(); document.execCommand('copy'); toast('Copied'); } } }, 'Copy'))));
}

$('#trainerSearch').addEventListener('input', debounce(renderTrainerList, 150));

views.trainers = {
  isDirty: () => T.dirty,
  save: saveTrainer,
};

// ---------------------------------------------------------------------------
// Pokemon data
// ---------------------------------------------------------------------------
const P = { lists: null, current: null, original: null, dirty: false };
const STAT_LABELS = [['baseHP', 'HP'], ['baseAttack', 'Attack'], ['baseDefense', 'Defense'], ['baseSpAttack', 'Sp. Atk'], ['baseSpDefense', 'Sp. Def'], ['baseSpeed', 'Speed']];
const FIELD_NAMES = { baseHP: 'HP', baseAttack: 'Attack', baseDefense: 'Defense', baseSpAttack: 'Sp. Atk', baseSpDefense: 'Sp. Def',
  baseSpeed: 'Speed', expYield: 'EXP given', catchRate: 'catch rate', types: 'types', abilities: 'abilities', friendship: 'friendship',
  evYield_HP: 'HP EVs', evYield_Attack: 'Attack EVs', evYield_Defense: 'Defense EVs', evYield_SpAttack: 'Sp. Atk EVs', evYield_SpDefense: 'Sp. Def EVs', evYield_Speed: 'Speed EVs' };
const EV_KEYS = ['evYield_HP', 'evYield_Attack', 'evYield_Defense', 'evYield_SpAttack', 'evYield_SpDefense', 'evYield_Speed'];

function renderSpeciesList() {
  const q = $('#speciesSearch').value.trim().toLowerCase();
  const frag = document.createDocumentFragment();
  let n = 0;
  for (const sp of GD.species) {
    if (q && !sp.name.toLowerCase().includes(q) && !sp.const.toLowerCase().includes(q)) continue;
    if (++n > 400) { frag.append(el('div', { class: 'note', style: 'padding:8px' }, 'Type to search for more...')); break; }
    frag.append(el('div', { class: 'item' + (P.current?.id === sp.const ? ' active' : ''), onclick: () => openSpecies(sp.const) },
      el('img', { class: 'thumb', src: imgUrl(sp.img), loading: 'lazy', alt: '', style: 'object-fit:cover;object-position:top' }),
      el('div', { class: 'meta' }, el('div', { class: 'title' }, sp.name), el('div', { class: 'sub' }, sp.const))));
  }
  $('#speciesList').replaceChildren(frag);
}

async function openSpecies(id) {
  if (P.dirty && !confirm('You have unsaved changes to this Pokémon. Throw them away?')) return;
  try {
    if (!P.lists) P.lists = await api('/api/specieslists');
    const data = await api('/api/species?id=' + encodeURIComponent(id));
    P.current = data;
    P.original = JSON.parse(JSON.stringify(data));
    P.dirty = false;
    renderSpecies();
    renderSpeciesList();
  } catch (e) { toast(e.message, true); }
}

function markSpeciesDirty() { P.dirty = true; const d = $('#speciesDirty'); if (d) d.textContent = 'Unsaved changes'; }

function constSelect(options, value, prefix, onChange, allowEmpty) {
  const sel = el('select', { onchange: () => onChange(sel.value) },
    allowEmpty ? el('option', { value: '' }, allowEmpty) : null,
    options.map(o => el('option', { value: o, selected: o === value }, prettyFromConst(prefix, o))));
  if (value && !options.includes(value)) sel.prepend(el('option', { value, selected: true }, value));
  return sel;
}

function renderSpecies() {
  const d = P.current;
  const sp = index.species.get(d.id);
  const root = $('#speciesEditor');
  const saveBar = el('div', { class: 'savebar' },
    el('h2', {}, d.speciesName || sp?.name || d.id, el('span', { class: 'idtag' }, d.id)),
    el('span', { id: 'speciesDirty', class: 'dirty' }, P.dirty ? 'Unsaved changes' : ''),
    el('button', { class: 'btn ghost', onclick: () => { P.dirty = false; openSpecies(d.id); } }, 'Revert'),
    el('button', { class: 'btn primary', onclick: saveSpecies, disabled: !d.editable }, 'Save'));
  if (!d.editable) {
    root.replaceChildren(saveBar, el('div', { class: 'warnbox' }, d.note || 'This Pokémon cannot be edited here.'));
    return;
  }
  const set = (k, v) => { d[k] = v; markSpeciesDirty(); };
  const varies = d.varies.length ? el('div', { class: 'note' },
    'Some values here change with the generation settings (' + d.varies.map(v => FIELD_NAMES[v] || v).join(', ') + '). The editor shows the value your game uses now; if you change one, it stays that way whatever the setting.') : null;

  // basics
  const types = [d.types[0] || '', d.types[1] && d.types[1] !== d.types[0] ? d.types[1] : ''];
  const writeTypes = () => set('types', types.filter(Boolean));
  const typeCtl = d.typesEditable
    ? el('div', { class: 'two', style: 'display:grid;grid-template-columns:1fr 1fr;gap:8px' },
      constSelect(P.lists.types, types[0], 'TYPE', v => { types[0] = v; writeTypes(); }),
      constSelect(P.lists.types, types[1], 'TYPE', v => { types[1] = v; writeTypes(); }, '(none)'))
    : el('div', { class: 'note' }, 'Shared by its whole family through a setting; not editable here.');
  const abil = (d.abilities.concat(['', '', ''])).slice(0, 3).map(a => (a && a !== 'ABILITY_NONE') ? prettyFromConst('ABILITY', a) : '');
  const abilInputs = ['Ability 1', 'Ability 2', 'Hidden ability'].map((label, i) => inputField(label, abil[i], v => { abil[i] = v; set('abilitiesPretty', abil.slice()); }, { list: 'dl-abilities', placeholder: 'none' }));
  const basics = el('div', { class: 'card' }, el('h3', {}, 'Basics'),
    el('div', { class: 'row' },
      el('img', { src: imgUrl(sp?.img), style: 'width:128px;height:128px;object-fit:cover;object-position:top;image-rendering:pixelated', alt: '' }),
      el('div', { class: 'grid' },
        inputField('Name in game', d.speciesName, v => set('speciesName', v), { maxlength: 12 }),
        inputField('Category (the "Seed Pokémon" part)', d.categoryName, v => set('categoryName', v), { maxlength: 12 }),
        el('label', { class: 'field' }, el('span', {}, 'Types'), typeCtl),
        ...abilInputs)), varies);

  // stats
  const statsBox = el('div', { class: 'stats' });
  const drawStats = () => {
    statsBox.replaceChildren();
    let total = 0;
    for (const [k, label] of STAT_LABELS) {
      const v = parseInt(d[k], 10) || 0;
      total += v;
      const bar = el('div', { class: 'bar', style: `width:${Math.min(100, v / 2.55)}%` });
      const inp = el('input', { type: 'number', min: 1, max: 255, value: d[k], oninput: () => { set(k, inp.value); bar.style.width = Math.min(100, (parseInt(inp.value, 10) || 0) / 2.55) + '%'; totalEl.textContent = STAT_LABELS.reduce((n, [kk]) => n + (parseInt(d[kk], 10) || 0), 0); } });
      statsBox.append(el('span', {}, label), inp, bar);
    }
    const totalEl = el('span', { class: 'total' }, total);
    statsBox.append(el('span', { class: 'total' }, 'Total'), totalEl, el('span'));
  };
  drawStats();
  const stats = el('div', { class: 'card' }, el('h3', {}, 'Base stats'), statsBox);

  // training & breeding
  const evs = el('div', { class: 'evs' }, EV_KEYS.map((k, i) => el('label', { class: 'field' }, el('span', {}, STAT_LABELS[i][1]),
    el('select', { onchange: e => set(k, e.target.value) }, ['0', '1', '2', '3'].map(n => el('option', { value: n, selected: (d[k] || '0') === n }, n))))));
  const g = d.genderRatio;
  const gMode = g === 'MON_GENDERLESS' ? 'none' : g === 'MON_MALE' ? 'male' : g === 'MON_FEMALE' ? 'female' : 'pct';
  const pct = (g.match(/PERCENT_FEMALE\(([\d.]+)\)/) || [])[1] || '50';
  const pctInput = el('input', { type: 'number', min: 0, max: 100, step: 'any', value: pct, oninput: () => set('genderRatio', `PERCENT_FEMALE(${pctInput.value || 0})`), style: 'width:90px' });
  const gSel = el('select', {
    onchange: () => {
      const v = gSel.value;
      pctInput.style.display = v === 'pct' ? '' : 'none';
      set('genderRatio', v === 'none' ? 'MON_GENDERLESS' : v === 'male' ? 'MON_MALE' : v === 'female' ? 'MON_FEMALE' : `PERCENT_FEMALE(${pctInput.value || 50})`);
    },
  }, [['pct', '% female'], ['male', 'Always male'], ['female', 'Always female'], ['none', 'Genderless']].map(([v, l]) => el('option', { value: v, selected: v === gMode }, l)));
  pctInput.style.display = gMode === 'pct' ? '' : 'none';
  const eggs = [d.eggGroups[0] || '', d.eggGroups[1] && d.eggGroups[1] !== d.eggGroups[0] ? d.eggGroups[1] : ''];
  const writeEggs = () => set('eggGroups', eggs.filter(Boolean));
  const training = el('div', { class: 'card' }, el('h3', {}, 'Catching, training and breeding'),
    el('div', { class: 'grid' },
      inputField('Catch rate (3 = hard, 255 = easy)', d.catchRate, v => set('catchRate', v), { type: 'number', min: 1, max: 255 }),
      inputField('EXP it gives when defeated', d.expYield, v => set('expYield', v), { type: 'number', min: 1, max: 999 }),
      el('label', { class: 'field' }, el('span', {}, 'How fast it levels'), constSelect(P.lists.growth, d.growthRate, 'GROWTH', v => set('growthRate', v))),
      inputField('Starting friendship', d.friendship, v => set('friendship', v), { placeholder: '50' }),
      el('label', { class: 'field' }, el('span', {}, 'Gender'), el('div', { class: 'rowline' }, gSel, pctInput)),
      inputField('Egg cycles', d.eggCycles, v => set('eggCycles', v), { type: 'number', min: 1, max: 255 }),
      el('label', { class: 'field' }, el('span', {}, 'Egg group 1'), constSelect(P.lists.eggGroups, eggs[0], 'EGG_GROUP', v => { eggs[0] = v; writeEggs(); })),
      el('label', { class: 'field' }, el('span', {}, 'Egg group 2'), constSelect(P.lists.eggGroups, eggs[1], 'EGG_GROUP', v => { eggs[1] = v; writeEggs(); }, '(none)')),
      inputField('Wild held item (common, 50%)', prettyFromConst('ITEM', d.itemCommon), v => set('itemCommonPretty', v), { list: 'dl-items', placeholder: 'none' }),
      inputField('Wild held item (rare, 5%)', prettyFromConst('ITEM', d.itemRare), v => set('itemRarePretty', v), { list: 'dl-items', placeholder: 'none' }),
      inputField('Height (tenths of a metre)', d.height, v => set('height', v), { type: 'number', min: 1 }),
      inputField('Weight (tenths of a kg)', d.weight, v => set('weight', v), { type: 'number', min: 1 })),
    el('h3', { style: 'margin-top:14px' }, 'Effort values it gives when defeated'), evs);

  // evolutions
  const evoRows = el('div', { class: 'rows' });
  const drawEvos = () => {
    evoRows.replaceChildren(...d.evolutions.entries.map((e, i) => {
      const target = index.species.get(e.target);
      const img = el('img', { src: imgUrl(target?.img), alt: '' });
      const isItem = e.method === 'EVO_ITEM' || /^ITEM_/.test(e.param);
      return el('div', { class: 'rowline' },
        constSelect(P.lists.evoMethods, e.method, 'EVO', v => { e.method = v; markSpeciesDirty(); drawEvos(); }),
        el('input', {
          class: 'grow', value: isItem ? prettyFromConst('ITEM', e.param) : e.param, list: isItem ? 'dl-items' : null,
          placeholder: isItem ? 'Item' : 'Level (0 = no level needed)', title: 'Level, or item for item evolutions',
          oninput: ev => { e.param = isItem ? toConst('ITEM', ev.target.value) : (ev.target.value.trim() || '0'); markSpeciesDirty(); },
        }),
        el('span', {}, '→'), img,
        el('input', { class: 'grow', value: target?.name || e.target, list: 'dl-species', placeholder: 'Evolves into', oninput: ev => { e.target = speciesConst(ev.target.value); img.src = imgUrl(index.species.get(e.target)?.img); markSpeciesDirty(); } }),
        el('input', { class: 'grow', value: e.conditions, placeholder: 'Extra conditions (optional)', title: 'For example CONDITIONS({IF_TIME, TIME_NIGHT})', oninput: ev => { e.conditions = ev.target.value; markSpeciesDirty(); } }),
        el('button', { class: 'iconbtn', title: 'Remove', onclick: () => { d.evolutions.entries.splice(i, 1); markSpeciesDirty(); drawEvos(); } }, '✕'));
    }));
  };
  drawEvos();
  const evoCard = el('div', { class: 'card' }, el('h3', {}, 'Evolutions'),
    d.evolutions.flattened ? el('div', { class: 'note' }, 'These evolutions normally depend on settings. Shown are the ones your game uses now; saving keeps exactly this list.') : null,
    evoRows,
    el('button', { class: 'btn small', style: 'margin-top:8px', onclick: () => { d.evolutions.entries.push({ method: 'EVO_LEVEL', param: '16', target: '', conditions: '' }); markSpeciesDirty(); drawEvos(); } }, '+ Add evolution'));

  // level-up moves
  const ls = d.learnset;
  const lsRows = el('div', { class: 'rows' });
  const drawLs = () => {
    lsRows.replaceChildren(...ls.moves.map((m, i) => el('div', { class: 'rowline' },
      el('input', { class: 'lv', type: 'number', min: 0, max: 100, value: m[0], title: 'Level (0 = when it evolves)', oninput: e => { m[0] = parseInt(e.target.value, 10) || 0; markSpeciesDirty(); } }),
      el('input', { class: 'grow', value: prettyFromConst('MOVE', m[1]), list: 'dl-moves', oninput: e => { m[1] = toConst('MOVE', e.target.value); markSpeciesDirty(); } }),
      el('button', { class: 'iconbtn', title: 'Remove', onclick: () => { ls.moves.splice(i, 1); markSpeciesDirty(); drawLs(); } }, '✕'))));
  };
  drawLs();
  const lsCard = el('div', { class: 'card' }, el('h3', {}, 'Moves learned by level'),
    el('div', { class: 'note' }, `Editing the Gen ${ls.gen} move lists (${ls.file}), the ones your game uses now. Level 1 moves are known from the start; level 0 means "when it evolves".`),
    ls.editable ? lsRows : el('div', { class: 'warnbox' }, 'This Pokémon’s move list cannot be edited here.'),
    ls.editable ? el('button', { class: 'btn small', style: 'margin-top:8px', onclick: () => { const last = ls.moves[ls.moves.length - 1]; ls.moves.push([last ? last[0] + 1 : 1, '']); markSpeciesDirty(); drawLs(); } }, '+ Add move') : null);

  const dex = d.description !== null ? el('div', { class: 'card' }, el('h3', {}, 'Pokédex entry'),
    el('textarea', { style: 'width:100%;min-height:110px;padding:10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);font-family:Consolas,monospace', value: d.description, oninput: e => set('description', e.target.value) }),
    el('div', { class: 'note' }, 'Up to 4 lines of about 40 characters.')) : null;

  root.replaceChildren(...[saveBar, basics, stats, evoCard, lsCard, training, dex].filter(Boolean));
}

function speciesChanges() {
  const d = P.current, o = P.original, ch = {}, problems = [];
  const keys = ['baseHP', 'baseAttack', 'baseDefense', 'baseSpAttack', 'baseSpDefense', 'baseSpeed', 'catchRate', 'expYield', 'eggCycles', 'friendship', 'growthRate', 'height', 'weight', 'genderRatio', 'speciesName', 'categoryName', 'description', ...EV_KEYS];
  for (const k of keys) if (String(d[k] ?? '') !== String(o[k] ?? '')) ch[k] = d[k];
  for (const k of STAT_LABELS.map(s => s[0])) if (k in ch && !(parseInt(ch[k], 10) >= 1 && parseInt(ch[k], 10) <= 255)) problems.push(`${k} must be 1 to 255.`);
  if (JSON.stringify(d.types) !== JSON.stringify(o.types)) ch.types = d.types;
  if (JSON.stringify(d.eggGroups) !== JSON.stringify(o.eggGroups)) ch.eggGroups = d.eggGroups;
  if (d.abilitiesPretty) {
    const ab = d.abilitiesPretty.map(a => a.trim() ? toConst('ABILITY', a) : 'ABILITY_NONE');
    ab.forEach(a => { if (a !== 'ABILITY_NONE' && !index.abilities.has(a)) problems.push(`Unknown ability "${prettyFromConst('ABILITY', a)}".`); });
    ch.abilities = ab;
  }
  for (const k of ['itemCommon', 'itemRare']) {
    if (d[k + 'Pretty'] !== undefined) {
      const v = d[k + 'Pretty'].trim() ? toConst('ITEM', d[k + 'Pretty']) : '';
      if (v && !index.items.has(v)) problems.push(`Unknown item "${d[k + 'Pretty']}".`);
      if (v !== (o[k] || '')) ch[k] = v;
    }
  }
  if (JSON.stringify(d.evolutions.entries) !== JSON.stringify(o.evolutions.entries)) {
    d.evolutions.entries.forEach((e, i) => {
      if (!index.species.has(e.target)) problems.push(`Evolution ${i + 1}: pick a Pokémon to evolve into.`);
      if (/^ITEM_/.test(e.param) && !index.items.has(e.param)) problems.push(`Evolution ${i + 1}: unknown item.`);
    });
    ch.evolutions = d.evolutions.entries;
  }
  if (JSON.stringify(d.learnset.moves) !== JSON.stringify(o.learnset.moves)) {
    d.learnset.moves.forEach((m, i) => { if (!index.moves.has(m[1])) problems.push(`Level-up move ${i + 1}: unknown move.`); });
    ch.learnset = d.learnset.moves;
  }
  return [ch, problems];
}

async function saveSpecies() {
  if (!P.current) return;
  const [changes, problems] = speciesChanges();
  if (problems.length) {
    openModal('Fix these first', el('div', {}, el('p', { class: 'note' }, 'Nothing was saved:'), el('ul', {}, problems.map(p => el('li', {}, p)))));
    return;
  }
  if (!Object.keys(changes).length) { toast('Nothing to save.'); return; }
  try {
    const data = await api('/api/species', { id: P.current.id, changes });
    P.current = data;
    P.original = JSON.parse(JSON.stringify(data));
    P.dirty = false;
    renderSpecies();
    toast('Saved. Press Play to try it.');
    try { Object.assign(GD, await api('/api/gamedata')); index.species = new Map(GD.species.map(s => [s.const, s])); } catch (e) { /* keep old list */ }
  } catch (e) { toast(e.message, true); }
}

$('#speciesSearch').addEventListener('input', debounce(renderSpeciesList, 150));

views.pokemon = {
  isDirty: () => P.dirty,
  save: saveSpecies,
  onShow: () => { if (!$('#speciesList').children.length) renderSpeciesList(); },
};

// ---------------------------------------------------------------------------
// Dialogue
// ---------------------------------------------------------------------------
const D = { results: [], ticked: new Set(), current: null, dirty: false, total: 0 };

function whereLabel(file) {
  const m = file.match(/^data\/maps\/([^/]+)\//);
  if (m) return m[1].replace(/_/g, ' ').replace(/([a-z])([A-Z0-9])/g, '$1 $2').replace(/(\d)([A-Z][a-z])/g, '$1 $2');
  return file.replace(/^data\//, '');
}

function highlight(text, q, matchCase, replacement) {
  if (!q) return escapeHtml(text);
  const re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), matchCase ? 'g' : 'gi');
  let out = '', last = 0, m;
  while ((m = re.exec(text))) {
    out += escapeHtml(text.slice(last, m.index));
    out += replacement !== null ? `<del>${escapeHtml(m[0])}</del><ins>${escapeHtml(replacement)}</ins>` : `<mark>${escapeHtml(m[0])}</mark>`;
    last = m.index + m[0].length;
    if (m[0].length === 0) re.lastIndex++;
  }
  return out + escapeHtml(text.slice(last));
}

async function runTextSearch() {
  const q = $('#textSearch').value;
  const matchCase = $('#textCase').checked;
  if (!q.trim()) {
    D.results = []; D.total = 0; renderTextResults(); return;
  }
  try {
    const res = await api(`/api/text/search?q=${encodeURIComponent(q)}&case=${matchCase ? 1 : 0}`);
    D.results = res.results;
    D.total = res.total;
    D.ticked = new Set($('#textSelectAll').checked ? res.results.map(r => r.file + '|' + r.label) : []);
    renderTextResults();
  } catch (e) { toast(e.message, true); }
}

function renderTextResults() {
  const q = $('#textSearch').value;
  const matchCase = $('#textCase').checked;
  const repl = $('#textReplace').value;
  const showReplace = repl.length > 0 || document.activeElement === $('#textReplace');
  $('#textCount').textContent = q.trim() ? (D.total > D.results.length ? `showing ${D.results.length} of ${D.total}` : `${D.total} found`) : '';
  $('#replaceBtn').disabled = !q.trim() || !D.ticked.size;
  $('#textResults').replaceChildren(...D.results.map(r => {
    const key = r.file + '|' + r.label;
    const cb = el('input', { type: 'checkbox', checked: D.ticked.has(key), onclick: e => e.stopPropagation(), onchange: () => { cb.checked ? D.ticked.add(key) : D.ticked.delete(key); $('#replaceBtn').disabled = !D.ticked.size; } });
    const snip = el('div', { class: 'snip', html: highlight(r.text, q, matchCase, showReplace ? repl : null) });
    return el('div', { class: 'result' + (D.current && D.current.label === r.label && D.current.file === r.file ? ' active' : ''), onclick: () => openText(r) },
      cb, el('div', { class: 'body' }, el('div', { class: 'where' }, whereLabel(r.file) + ' \u00b7 ' + r.label), snip));
  }));
}

function openText(r) {
  if (D.dirty && !confirm('You have unsaved changes to this text. Throw them away?')) return;
  D.current = r;
  D.dirty = false;
  renderTextEditor();
  renderTextResults();
}

function renderTextEditor() {
  const r = D.current;
  const preview = el('div', { class: 'boxes' });
  const dirty = el('span', { class: 'dirty' });
  const ta = el('textarea', {
    value: r.text, style: 'min-height:320px',
    oninput: () => { D.dirty = ta.value !== r.text; dirty.textContent = D.dirty ? 'Unsaved changes' : ''; renderBoxes(ta.value, preview); },
  });
  D.textarea = ta;
  renderBoxes(r.text, preview);
  $('#textEditor').replaceChildren(
    el('div', { class: 'savebar' },
      el('h2', {}, whereLabel(r.file), el('span', { class: 'idtag' }, r.label)),
      dirty,
      el('button', { class: 'btn ghost', onclick: () => { D.dirty = false; renderTextEditor(); } }, 'Revert'),
      el('button', { class: 'btn primary', onclick: saveText }, 'Save')),
    el('p', { class: 'note' }, 'Each new line is a new line in the game. Leave an empty line to start a new text box. Words in {BRACES} are filled in by the game, like {PLAYER} for the player\u2019s name.'),
    el('div', { class: 'textedit' },
      el('div', {}, ta, el('div', { class: 'note' }, `File: ${r.file}, line ${r.line}`)),
      el('div', {}, el('div', { class: 'boxlabel', style: 'margin-bottom:6px' }, 'Preview (red lines are too wide for the text box)'), preview)));
}

async function saveText() {
  if (!D.current) return;
  try {
    await api('/api/text/save', { file: D.current.file, label: D.current.label, text: D.textarea.value });
    D.current.text = D.textarea.value;
    D.dirty = false;
    renderTextEditor();
    toast('Saved. Press Play to try it.');
    runTextSearch();
  } catch (e) { toast(e.message, true); }
}

async function replaceTicked() {
  const find = $('#textSearch').value;
  const replace = $('#textReplace').value;
  const targets = D.results.filter(r => D.ticked.has(r.file + '|' + r.label)).map(r => ({ file: r.file, label: r.label }));
  if (!targets.length) return;
  if (!confirm(`Replace "${find}" with "${replace}" in ${targets.length} text(s)?`)) return;
  try {
    const res = await api('/api/text/replace', { find, replace, case: $('#textCase').checked, targets });
    toast(`Changed ${res.changed} text(s). Press Play to try it.`);
    D.current = null;
    D.dirty = false;
    $('#textEditor').replaceChildren(el('div', { class: 'empty' }, 'Replaced. Pick a result to check it.'));
    $('#textSearch').value = replace;
    runTextSearch();
  } catch (e) { toast(e.message, true); }
}

$('#textSearch').addEventListener('input', debounce(runTextSearch, 250));
$('#textCase').addEventListener('change', runTextSearch);
$('#textReplace').addEventListener('input', renderTextResults);
$('#textReplace').addEventListener('focus', renderTextResults);
$('#replaceBtn').addEventListener('click', replaceTicked);
$('#textSelectAll').addEventListener('change', () => {
  D.ticked = new Set($('#textSelectAll').checked ? D.results.map(r => r.file + '|' + r.label) : []);
  renderTextResults();
});

views.dialogue = {
  isDirty: () => D.dirty,
  save: saveText,
  onShow: () => $('#textSearch').focus(),
};

// ---------------------------------------------------------------------------
// Scripts
// ---------------------------------------------------------------------------
const S = { files: [], current: null, dirty: false, text: '' };

async function loadScriptList() {
  S.files = await api('/api/scripts');
  renderScriptList();
}

function renderScriptList() {
  const q = $('#scriptSearch').value.trim().toLowerCase();
  const box = $('#scriptList');
  const frag = document.createDocumentFragment();
  let group = null;
  for (const f of S.files) {
    if (q && !f.name.toLowerCase().includes(q) && !f.path.toLowerCase().includes(q)) continue;
    if (f.group !== group) { group = f.group; frag.append(el('div', { class: 'grouphead' }, group)); }
    frag.append(el('div', { class: 'item' + (S.current === f.path ? ' active' : ''), 'data-path': f.path, onclick: () => openScript(f.path) },
      el('div', { class: 'meta' }, el('div', { class: 'title' }, f.name), el('div', { class: 'sub' }, f.path))));
  }
  box.replaceChildren(frag);
}

async function openScript(path) {
  if (S.dirty && !confirm('You have unsaved script changes. Throw them away?')) return;
  try {
    const res = await api('/api/script?path=' + encodeURIComponent(path));
    S.current = path;
    S.text = res.text;
    S.dirty = false;
    renderScriptEditor();
    renderScriptList();
  } catch (e) { toast(e.message, true); }
}

function scriptPrefix() {
  const m = S.current.match(/^data\/maps\/([^/]+)\//);
  return m ? m[1] : 'Common';
}

function labelsIn(text) {
  const out = [];
  text.split('\n').forEach((line, i) => { const m = line.match(/^([A-Za-z_]\w*)::?\s*$/); if (m) out.push({ name: m[1], line: i }); });
  return out;
}

function renderScriptEditor() {
  const f = S.files.find(x => x.path === S.current);
  const dirty = el('span', { class: 'dirty' });
  const ta = el('textarea', { class: 'code', spellcheck: 'false', value: S.text });
  S.textarea = ta;
  const jump = el('select', {
    onchange: () => {
      const line = parseInt(jump.value, 10);
      if (isNaN(line)) return;
      const pos = ta.value.split('\n').slice(0, line).join('\n').length + (line ? 1 : 0);
      ta.focus();
      ta.setSelectionRange(pos, pos);
      const lh = parseFloat(getComputedStyle(ta).lineHeight) || 19;
      ta.scrollTop = Math.max(0, line * lh - 40);
      jump.value = '';
    },
  });
  const fillJump = () => jump.replaceChildren(el('option', { value: '' }, 'Jump to a script or text...'),
    labelsIn(ta.value).map(l => el('option', { value: l.line }, l.name)));
  fillJump();
  ta.addEventListener('input', () => { S.dirty = ta.value !== S.text; dirty.textContent = S.dirty ? 'Unsaved changes' : ''; });
  ta.addEventListener('change', fillJump);
  ta.addEventListener('keydown', e => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const s = ta.selectionStart;
      ta.setRangeText('\t', s, ta.selectionEnd, 'end');
      ta.dispatchEvent(new Event('input'));
    }
  });
  const insert = el('select', {
    onchange: () => { const v = insert.value; insert.value = ''; if (v) openInsertForm(v); },
  }, el('option', { value: '' }, '+ Insert...'),
  Object.entries(INSERTS).map(([k, v]) => el('option', { value: k }, v.title)));

  $('#scriptEditor').replaceChildren(
    el('div', { class: 'savebar' },
      el('h2', {}, f ? f.name : S.current, el('span', { class: 'idtag' }, S.current)),
      dirty,
      el('button', { class: 'btn ghost', onclick: () => { S.dirty = false; openScript(S.current); } }, 'Revert'),
      el('button', { class: 'btn primary', onclick: saveScript }, 'Save')),
    el('div', { class: 'scripttools' }, jump, insert,
      el('span', { class: 'note' }, 'Put the cursor where you want something to happen, then use Insert.')),
    ta);
}

function insertAtCursor(lines, appendix) {
  const ta = S.textarea;
  let pos = ta.selectionStart;
  // insert at the start of the next line so commands stay on their own lines
  const nl = ta.value.indexOf('\n', pos);
  if (ta.value[pos - 1] !== '\n' && pos !== 0) pos = nl === -1 ? ta.value.length : nl + 1;
  let block = lines.map(l => '\t' + l).join('\n') + '\n';
  if (pos === ta.value.length && !ta.value.endsWith('\n')) block = '\n' + block;
  ta.setRangeText(block, pos, pos, 'end');
  if (appendix) {
    const sep = ta.value.endsWith('\n\n') ? '' : (ta.value.endsWith('\n') ? '\n' : '\n\n');
    ta.value = ta.value + sep + appendix + '\n';
  }
  ta.dispatchEvent(new Event('input'));
  ta.dispatchEvent(new Event('change'));
  ta.focus();
}

function textBlock(label, friendly) {
  // Same format as the game files: one .string line per line of text.
  const boxes = friendly.replace(/\r/g, '').trim().split(/\n\s*\n/);
  const raw = boxes.map(b => b.split('\n').map((l, i) => (i === 0 ? '' : (i === 1 ? '\\n' : '\\l')) + l).join('')).join('\\p') + '$';
  const chunks = raw.split(/(?<=\\[nlp])/).filter(Boolean);
  return `${label}:\n` + chunks.map(c => `\t.string "${c.replace(/"/g, '\\"')}"`).join('\n');
}

function uniqueLabel(base) {
  const existing = new Set(labelsIn(S.textarea.value).map(l => l.name));
  let name = base, n = 2;
  while (existing.has(name)) name = base + n++;
  return name;
}

function cleanName(s, fallback) {
  const words = (s || '').replace(/[^A-Za-z0-9 ]/g, ' ').trim().split(/\s+/).filter(Boolean);
  return words.length ? words.map(w => w[0].toUpperCase() + w.slice(1)).join('') : fallback;
}

const MSG_TYPES = [
  ['MSGBOX_NPC', 'Person talks (faces you, waits for A)'],
  ['MSGBOX_DEFAULT', 'Plain message'],
  ['MSGBOX_SIGN', 'Sign'],
  ['MSGBOX_AUTOCLOSE', 'Message that closes by itself'],
  ['MSGBOX_YESNO', 'Yes / No question'],
];

function constList(id, consts) {
  return el('datalist', { id }, consts.map(c => el('option', { value: c })));
}

const INSERTS = {
  message: {
    title: 'Show a message',
    fields: () => [
      ['text', 'What should appear', 'textarea'],
      ['type', 'Kind of message', 'select', MSG_TYPES],
      ['name', 'Short name for this text (optional)', 'input'],
    ],
    build: v => {
      const label = uniqueLabel(`${scriptPrefix()}_Text_${cleanName(v.name, 'Message')}`);
      const lines = [`msgbox ${label}, ${v.type}`];
      if (v.type === 'MSGBOX_YESNO') lines.push('goto_if_eq VAR_RESULT, NO, YourNoScriptHere @ change this to where "No" should go');
      return [lines, textBlock(label, v.text)];
    },
  },
  giveitem: {
    title: 'Give an item',
    fields: () => [['item', 'Item', 'list', 'dl-items'], ['amount', 'How many', 'number', 1]],
    build: v => [[`giveitem ${toConst('ITEM', v.item)}, ${parseInt(v.amount, 10) || 1}`]],
  },
  givemon: {
    title: 'Give a Pok\u00e9mon',
    fields: () => [['species', 'Pok\u00e9mon', 'list', 'dl-species'], ['level', 'Level', 'number', 5], ['item', 'Held item (optional)', 'list', 'dl-items'],
      ['text', 'Message after receiving it (optional)', 'textarea']],
    build: v => {
      const sp = speciesConst(v.species);
      const lines = [`givemon ${sp}, ${parseInt(v.level, 10) || 5}` + (v.item ? `, ${toConst('ITEM', v.item)}` : '')];
      if (v.text.trim()) {
        const label = uniqueLabel(`${scriptPrefix()}_Text_Received${cleanName(v.species, 'Mon')}`);
        lines.push('playfanfare MUS_OBTAIN_ITEM', `message ${label}`, 'waitmessage', 'waitfanfare', 'closemessage');
        return [lines, textBlock(label, v.text)];
      }
      return [lines];
    },
  },
  battle: {
    title: 'Start a trainer battle',
    fields: () => [['trainer', 'Trainer', 'select', T.list.filter(t => t.id !== 'TRAINER_NONE').map(t => [t.id, `${t.name} (${t.class}) - ${t.id}`])],
      ['intro', 'What they say before the battle', 'textarea'], ['defeat', 'What they say when they lose', 'textarea']],
    build: v => {
      const base = cleanName(prettyFromConst('TRAINER', v.trainer), 'Trainer');
      const intro = uniqueLabel(`${scriptPrefix()}_Text_${base}Intro`);
      const defeat = uniqueLabel(`${scriptPrefix()}_Text_${base}Defeat`);
      return [[`trainerbattle_single ${v.trainer}, ${intro}, ${defeat}`],
        textBlock(intro, v.intro || '...') + '\n\n' + textBlock(defeat, v.defeat || '...')];
    },
  },
  setflag: {
    title: 'Set a flag (remember something happened)',
    fields: () => [['flag', 'Flag', 'list', 'dl-flags']],
    build: v => [[`setflag ${v.flag.trim()}`]],
  },
  clearflag: {
    title: 'Clear a flag',
    fields: () => [['flag', 'Flag', 'list', 'dl-flags']],
    build: v => [[`clearflag ${v.flag.trim()}`]],
  },
  ifflag: {
    title: 'Only continue if a flag is set',
    fields: () => [['flag', 'Flag', 'list', 'dl-flags'], ['target', 'Otherwise go to (script name)', 'input']],
    build: v => [[`goto_if_unset ${v.flag.trim()}, ${v.target.trim() || 'YourScriptHere'}`]],
  },
  heal: {
    title: 'Heal the player\u2019s Pok\u00e9mon',
    fields: () => [],
    build: () => [['special HealPlayerParty']],
  },
  warp: {
    title: 'Warp the player to a map',
    fields: () => [['map', 'Map', 'select', GD.maps.map(m => [m.const, m.name])], ['x', 'X', 'number', 0], ['y', 'Y', 'number', 0]],
    build: v => [[`warp ${v.map}, ${parseInt(v.x, 10) || 0}, ${parseInt(v.y, 10) || 0}`, 'waitstate']],
  },
  newscript: {
    title: 'New empty script',
    fields: () => [['name', 'Script name', 'input']],
    build: v => {
      const label = uniqueLabel(`${scriptPrefix()}_EventScript_${cleanName(v.name, 'NewScript')}`);
      return [[], `${label}::\n\tlock\n\tfaceplayer\n\trelease\n\tend`];
    },
  },
};

function openInsertForm(kind) {
  if (!S.textarea) return;
  const def = INSERTS[kind];
  const inputs = {};
  const form = el('div', { class: 'form' });
  if (!document.getElementById('dl-flags')) document.body.append(constList('dl-flags', GD.flags));
  for (const [key, label, type, extra] of def.fields()) {
    let input;
    if (type === 'textarea') input = el('textarea', { style: 'min-height:100px' });
    else if (type === 'select') input = el('select', {}, extra.map(([v, l]) => el('option', { value: v }, l)));
    else if (type === 'list') input = el('input', { list: extra });
    else if (type === 'number') input = el('input', { type: 'number', value: extra });
    else input = el('input', {});
    inputs[key] = input;
    form.append(el('label', { class: 'field' }, el('span', {}, label), input));
  }
  const err = el('div');
  form.append(err, el('div', { class: 'row', style: 'justify-content:flex-end' },
    el('button', {
      class: 'btn primary',
      onclick: () => {
        const v = {};
        for (const [k, i] of Object.entries(inputs)) v[k] = i.value;
        if ('species' in v && !index.species.has(speciesConst(v.species))) { err.replaceChildren(el('div', { class: 'warnbox' }, 'Pick a Pok\u00e9mon from the list.')); return; }
        if ('item' in v && v.item && !index.items.has(toConst('ITEM', v.item))) { err.replaceChildren(el('div', { class: 'warnbox' }, 'Pick an item from the list.')); return; }
        if ('flag' in v && !/^FLAG_\w+$/.test(v.flag.trim())) { err.replaceChildren(el('div', { class: 'warnbox' }, 'Pick a flag from the list (they start with FLAG_).')); return; }
        const [lines, appendix] = def.build(v);
        insertAtCursor(lines, appendix);
        closeModal();
        toast('Inserted. Save when you are done.');
      },
    }, 'Insert')));
  openModal(def.title, form);
}

async function saveScript() {
  if (!S.current) return;
  try {
    await api('/api/script', { path: S.current, text: S.textarea.value });
    S.text = S.textarea.value;
    S.dirty = false;
    renderScriptEditor();
    toast('Saved. Press Play to try it.');
  } catch (e) { toast(e.message, true); }
}

$('#scriptSearch').addEventListener('input', debounce(renderScriptList, 150));

views.scripts = {
  isDirty: () => S.dirty,
  save: saveScript,
  onShow: () => { if (!S.files.length) loadScriptList(); },
};

// ---------------------------------------------------------------------------
// Game settings (include/config/*.h)
// ---------------------------------------------------------------------------
const C = { files: [], file: null, settings: [], changes: {}, searchResults: null };
const RISKY = { 'save.h': 'Changing these can make old save files stop working. Start a new game after changing them.',
  'species_enabled.h': 'Turning generations off removes those Pokémon everywhere, and changing it can break old save files.' };

function genLabel(g) {
  if (g === 'GEN_LATEST') return 'Latest';
  if (g === 'GEN_CHAMPIONS') return 'Champions';
  return 'Gen ' + g.slice(4);
}

async function loadSettingFiles() {
  C.files = await api('/api/configs');
  renderSettingFiles();
}

function renderSettingFiles() {
  $('#settingFiles').replaceChildren(...C.files.map(f => el('div', {
    class: 'item' + (C.file === f.file && !C.searchResults ? ' active' : ''),
    onclick: () => openSettingFile(f.file),
  }, el('div', { class: 'meta' }, el('div', { class: 'title' }, f.title), el('div', { class: 'sub' }, 'include/config/' + f.file)))));
}

function changedCount() { return Object.values(C.changes).reduce((n, c) => n + Object.keys(c).length, 0); }

async function openSettingFile(file) {
  C.searchResults = null;
  $('#settingSearch').value = '';
  C.file = file;
  C.settings = (await api('/api/config?file=' + encodeURIComponent(file))).map(s => Object.assign(s, { file }));
  renderSettingFiles();
  renderSettings(C.settings, C.files.find(f => f.file === file).title, file);
}

const runSettingSearch = debounce(async () => {
  const q = $('#settingSearch').value.trim();
  if (!q) { if (C.file) openSettingFile(C.file); return; }
  C.searchResults = await api('/api/config/search?q=' + encodeURIComponent(q));
  renderSettingFiles();
  renderSettings(C.searchResults, `Settings matching "${q}"`, null);
}, 250);

function settingControl(s) {
  const current = C.changes[s.file]?.[s.name] ?? s.value;
  const set = v => {
    C.changes[s.file] = C.changes[s.file] || {};
    if (v === s.value) delete C.changes[s.file][s.name];
    else C.changes[s.file][s.name] = v;
    row.classList.toggle('changed', v !== s.value);
    $('#settingDirty').textContent = changedCount() ? `${changedCount()} unsaved change(s)` : '';
  };
  let control;
  if (s.kind === 'bool') {
    const cb = el('input', { type: 'checkbox', checked: current === 'TRUE', onchange: () => { set(cb.checked ? 'TRUE' : 'FALSE'); txt.textContent = cb.checked ? 'On' : 'Off'; } });
    const txt = el('span', {}, current === 'TRUE' ? 'On' : 'Off');
    control = el('label', { class: 'switch' }, cb, txt);
  } else if (s.kind === 'gen') {
    control = el('select', { onchange: e => set(e.target.value) }, GD.gens.concat(GD.gens.includes(current) ? [] : [current])
      .map(g => el('option', { value: g, selected: g === current }, genLabel(g))));
  } else if (s.kind === 'number') {
    control = el('input', { type: 'text', inputmode: 'numeric', value: current, oninput: e => set(e.target.value.trim()) });
  } else {
    control = el('input', { type: 'text', value: current, oninput: e => set(e.target.value.trim()) });
  }
  const row = el('div', { class: 'setting' + (current !== s.value ? ' changed' : '') },
    el('div', {}, el('div', { class: 'sname' }, s.name), s.fileTitle ? el('div', { class: 'sfile' }, s.fileTitle) : null),
    el('div', {}, control),
    el('div', { class: 'shelp' }, s.help || ''));
  return row;
}

function renderSettings(list, title, file) {
  const body = el('div');
  let section = null;
  for (const s of list) {
    if (!C.searchResults && s.section !== section) {
      section = s.section;
      if (section) body.append(el('div', { class: 'sectionhead' }, section));
    }
    body.append(settingControl(s));
  }
  if (!list.length) body.append(el('div', { class: 'empty' }, 'No settings found.'));
  $('#settingEditor').replaceChildren(
    el('div', { class: 'savebar' }, el('h2', {}, title),
      el('span', { id: 'settingDirty', class: 'dirty' }, changedCount() ? `${changedCount()} unsaved change(s)` : ''),
      el('button', { class: 'btn ghost', onclick: () => { C.changes = {}; file ? openSettingFile(file) : runSettingSearch(); } }, 'Revert'),
      el('button', { class: 'btn primary', onclick: saveSettings }, 'Save')),
    ...(file && RISKY[file] ? [el('div', { class: 'warnbox' }, RISKY[file])] : []),
    el('p', { class: 'note' }, 'These are pokeemerald-expansion’s own switches. "Gen 3" means the game works like the original Emerald, "Latest" uses the newest games’ rules. Changes apply after you press Play.'),
    body);
}

async function saveSettings() {
  const entries = Object.entries(C.changes).filter(([, c]) => Object.keys(c).length);
  if (!entries.length) { toast('Nothing to save.'); return; }
  try {
    for (const [file, changes] of entries) await api('/api/config', { file, changes });
    C.changes = {};
    toast('Saved. Press Play to try it.');
    if (C.searchResults) runSettingSearch(); else if (C.file) openSettingFile(C.file);
  } catch (e) { toast(e.message, true); }
}

$('#settingSearch').addEventListener('input', runSettingSearch);

views.settings = {
  isDirty: () => changedCount() > 0,
  save: saveSettings,
  onShow: () => { if (!C.files.length) loadSettingFiles(); },
};

// ---------------------------------------------------------------------------
// Fun Modes: randomizers, hard mode, level caps, shops, comedy dialogue
// ---------------------------------------------------------------------------
const FUN_DEFAULTS = {
  seed: '', keepEdited: true,
  wild: { on: false, mode: 'similar', legendaries: false },
  trainers: { on: false, mode: 'similar', keepTheme: true, legendaries: false },
  starters: { on: false, mode: 'triangle', species: ['', '', ''] },
  hard: { on: false, bossTeams: true, levelBoost: 10, biggerBossTeams: true, doublesPercent: 20, doublesMinLevel: 20,
          legendaryLevel: 0, legendaryPercent: 15, regularItems: true },
  caps: { on: false, type: 'hard', mode: 'auto', caps: [15, 19, 24, 29, 31, 33, 42, 46, 58], candyCap: true },
  candy: { on: false },
  comedy: { on: false, theme: 'thrones', hero: true, adult: false, fakeNews: true, battle: true, houseGyms: true, story: true, music: true },
};
const COMEDY_THEMES = [
  ['thrones', 'Game of Thrones', 'A real Game of Thrones story told through Hoenn: hand-written dialogue town by town, noble houses, plots and betrayals, and a dragon on the title screen. Only a little silly. Areas not written yet keep their normal text.'],
  ['madlibs', 'Mad Libs', 'You fill in 16 blanks from a menu at the start (a thing, a place, a food, a name...) and 4 more after every Gym. People all over Hoenn use your words, trainers build their trash talk around them, and signs run news about them.'],
];
const COMEDY_SWITCHES = [
  ['hero', 'Hero talks back', 'Now and then your character answers, in the theme\'s own style.', 'madlibs'],
  ['adult', 'Adult humor', 'A small amount of swearing and crude jokes. Only grown-ups say the crude stuff; your character just swears.', 'madlibs'],
  ['fakeNews', 'Fake news signs', 'Signs get headlines.', 'madlibs'],
  ['battle', 'Battle commentary', 'Battle messages get rewritten: wild Pokémon owe you money, fainting is dramatic.', 'madlibs'],
  ['houseGyms', 'House Gyms', 'Every Gym becomes a noble house with its own wild idea: ghosts in Rustboro\'s library, a cave buffet in Dewford, dragons in Fortree, the Night King in Sootopolis. Gym Guides give the new advice, badges become house sigils. Works with Hard mode too.', 'thrones'],
  ['story', 'Story events', 'New scenes in the real story: a herald with a gift after every badge, a loan from the Iron Bank (the collector comes later), the Red Wedding in Slateport, your rival as your Hand (until they betray you), Wally\'s cape, a spy, and a walk of shame after you white out.', 'thrones'],
  ['music', 'Thrones music', 'New medieval music, written for this game: war drums and brass in battles, a lute by the hearth in Littleroot, a march on the road, a great hall in every Gym, and the theme on the title screen. More places get music over time.', 'thrones'],
];
const CAP_NAMES = ['Badge 1', 'Badge 2', 'Badge 3', 'Badge 4', 'Badge 5', 'Badge 6', 'Badge 7', 'Badge 8', 'Champion'];

const F = { s: null, status: null, busy: false };

function funLoad() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem('emerald.fun') || '{}'); } catch (e) { /* ignore */ }
  const merge = (d, s) => {
    if (Array.isArray(d)) return Array.isArray(s) ? s : d;
    if (d && typeof d === 'object') {
      const out = {};
      for (const k of Object.keys(d)) out[k] = merge(d[k], s ? s[k] : undefined);
      return out;
    }
    return s === undefined ? d : s;
  };
  F.s = merge(FUN_DEFAULTS, saved);
}
function funSave() { try { localStorage.setItem('emerald.fun', JSON.stringify(F.s)); } catch (e) { /* ignore */ } }

function funSwitch(obj, key, label) {
  const cb = el('input', { type: 'checkbox', checked: !!obj[key], onchange: () => { obj[key] = cb.checked; funSave(); renderFun(); } });
  return el('label', { class: 'switch' }, cb, el('span', {}, label));
}
function funCheck(obj, key, label) {
  const cb = el('input', { type: 'checkbox', checked: !!obj[key], onchange: () => { obj[key] = cb.checked; funSave(); } });
  return el('label', { class: 'check' }, cb, label);
}
function funSelect(label, obj, key, options, rerender) {
  return el('label', { class: 'field' }, el('span', {}, label),
    el('select', { onchange: e => { obj[key] = e.target.value; funSave(); if (rerender) renderFun(); } },
      options.map(([v, t]) => el('option', { value: v, selected: obj[key] === v }, t))));
}
function funNumber(label, obj, key, min, max, suffix) {
  return el('label', { class: 'field' }, el('span', {}, label),
    el('input', { type: 'number', min, max, value: obj[key], oninput: e => { obj[key] = Number(e.target.value) || 0; funSave(); } }),
    suffix ? el('small', { class: 'note' }, suffix) : null);
}
function funCard(title, obj, intro, body) {
  return el('div', { class: 'card funcard' + (obj.on ? ' on' : '') },
    el('div', { class: 'funhead' }, funSwitch(obj, 'on', title)),
    el('p', { class: 'note' }, intro),
    obj.on ? el('div', { class: 'funbody' }, body) : null);
}

function renderFun() {
  const s = F.s;
  const seedInput = el('input', { type: 'text', value: s.seed, placeholder: 'Leave empty for a new random seed',
    oninput: e => { s.seed = e.target.value; funSave(); } });
  const header = el('div', { class: 'card' },
    el('h3', {}, 'Fun Modes'),
    el('p', { class: 'note' }, 'Tick the modes you want, press Preview to see what changes, then Apply. Your game is saved as a version first, so Undo Fun Modes on the left always takes you back. Then press Play to try it.'),
    el('div', { class: 'row', style: 'align-items:flex-end' },
      el('label', { class: 'field', style: 'flex:1;min-width:220px' }, el('span', {}, 'Seed (same seed + same settings = same game)'), seedInput),
      el('button', { class: 'btn', onclick: () => { s.seed = String(Math.floor(Math.random() * 1e8)); funSave(); renderFun(); } }, '🎲 New seed')),
    el('div', { style: 'margin-top:10px' }, funCheck(s, 'keepEdited', 'Leave trainers I changed by hand alone')));

  const wild = funCard('Randomize wild Pokémon', s.wild, 'Changes what you find in grass, water, caves and fishing spots.', [
    el('div', { class: 'grid' },
      funSelect('How', s.wild, 'mode', [['similar', 'Similar strength (fair)'], ['random', 'Anything goes'], ['global', 'Swap each species everywhere (1 to 1)']]),
      el('div', { class: 'field' }, el('span', {}, 'Extras'), funCheck(s.wild, 'legendaries', 'Allow legendaries in the wild')))]);

  const tr = funCard('Randomize trainer teams', s.trainers, 'Every trainer gets new Pokémon. Your rival always carries the starter you did not pick.', [
    el('div', { class: 'grid' },
      funSelect('How', s.trainers, 'mode', [['similar', 'Similar strength (fair)'], ['random', 'Anything goes']]),
      el('div', { class: 'field' }, el('span', {}, 'Extras'),
        funCheck(s.trainers, 'keepTheme', 'Gym Leaders keep their type'),
        funCheck(s.trainers, 'legendaries', 'Allow legendaries')))]);

  const st = funCard('Randomize starters', s.starters, 'Changes the three Pokémon in Professor Birch\'s bag, and the rival\'s teams to match.', [
    el('div', { class: 'grid' },
      funSelect('How', s.starters, 'mode', [['triangle', 'Random Grass, Fire and Water'], ['random', 'Any three (that evolve twice)'], ['custom', 'I pick them']], true)),
    s.starters.mode === 'custom' ? el('div', { class: 'grid', style: 'margin-top:8px' },
      [0, 1, 2].map(i => el('label', { class: 'field' }, el('span', {}, ['Left', 'Middle', 'Right'][i] + ' ball'),
        el('input', { type: 'text', value: s.starters.species[i] || '', 'data-list': 'dl-species',
          oninput: e => { s.starters.species[i] = e.target.value; funSave(); } })))) : null]);

  const h = s.hard;
  const hard = funCard('Hard mode', h, 'Smart AI everywhere, real movesets with STAB and coverage, held items, natures and EVs for bosses. Tough but fair.', [
    el('div', { class: 'grid' },
      el('div', { class: 'field' }, el('span', {}, 'Bosses'),
        funCheck(h, 'bossTeams', 'Hand-built teams for Gym Leaders, Elite Four, Wallace, Wally, Maxie and Archie'),
        funCheck(h, 'biggerBossTeams', 'Other bosses get one more Pokémon'),
        funCheck(h, 'regularItems', 'Regular trainers hold items too')),
      funNumber('Trainer levels +%', h, 'levelBoost', 0, 100, 'Hand-built teams keep their own levels.'),
      funNumber('Double battles: % of trainers', h, 'doublesPercent', 0, 100),
      funNumber('...from level', h, 'doublesMinLevel', 1, 100, 'So you have two Pokémon by then.'),
      funNumber('Legendaries from level (0 = never)', h, 'legendaryLevel', 0, 100, 'Bosses at or above this level bring one. The big ones show up 15 levels later.'),
      funNumber('...and % of regular trainers', h, 'legendaryPercent', 0, 100))]);

  const c = s.caps;
  const caps = funCard('Level caps', c, 'Your Pokémon stop gaining EXP at the cap until you win the next badge.', [
    el('div', { class: 'grid' },
      funSelect('Type', c, 'type', [['hard', 'Hard: no EXP at the cap'], ['soft', 'Soft: much less EXP at the cap']]),
      funSelect('Cap levels', c, 'mode', [['auto', 'Match each Gym Leader\'s strongest Pokémon'], ['custom', 'I set them']], true),
      el('div', { class: 'field' }, el('span', {}, 'Rare Candy'), funCheck(c, 'candyCap', 'Rare Candy cannot go past the cap'))),
    c.mode === 'custom' ? el('div', { class: 'capgrid' }, CAP_NAMES.map((n, i) => el('label', { class: 'field' }, el('span', {}, 'Until ' + n),
      el('input', { type: 'number', min: 1, max: 100, value: c.caps[i], oninput: e => { c.caps[i] = Number(e.target.value) || 1; funSave(); } })))) : null]);

  const candy = funCard('Free Rare Candy in every shop', s.candy, 'Every Poké Mart sells Rare Candy for ₽0. Pairs well with level caps.', []);

  const cm = s.comedy;
  const comedy = funCard('Comedy dialogue', cm, 'Pick one theme and the whole game goes all in on it. No joke is used twice, and at most one is added to each conversation.', [
    el('div', { class: 'field' }, el('span', {}, 'Theme')),
    el('div', { class: 'packs' }, COMEDY_THEMES.map(([k, t, d]) => {
      const rb = el('input', { type: 'radio', name: 'comedyTheme', checked: cm.theme === k, onchange: () => { cm.theme = k; funSave(); renderFun(); } });
      return el('label', { class: 'pack' + (cm.theme === k ? ' on' : '') }, rb, el('div', {}, el('b', {}, t), el('div', { class: 'note' }, d)));
    })),
    el('div', { class: 'field', style: 'margin-top:8px' }, el('span', {}, 'Extras')),
    el('div', { class: 'packs' }, COMEDY_SWITCHES.filter(sw => sw[3] === cm.theme).map(([k, t, d]) => {
      const cb = el('input', { type: 'checkbox', checked: !!cm[k], onchange: () => { cm[k] = cb.checked; funSave(); renderFun(); } });
      return el('label', { class: 'pack' + (cm[k] ? ' on' : '') }, cb, el('div', {}, el('b', {}, t), el('div', { class: 'note' }, d)));
    }))]);

  const anyOn = ['wild', 'trainers', 'starters', 'hard', 'caps', 'candy', 'comedy'].some(k => s[k].on);
  const bar = el('div', { class: 'savebar funbar' },
    el('h2', {}, 'Fun Modes'),
    el('button', { class: 'btn', disabled: !anyOn || F.busy, onclick: () => runFun(false) }, 'Preview'),
    el('button', { class: 'btn primary', disabled: !anyOn || F.busy, onclick: () => runFun(true) }, 'Apply'));
  $('#funEditor').replaceChildren(bar, header, wild, tr, st, hard, caps, candy, comedy);
}

async function runFun(apply) {
  if (apply && !confirm('Apply these Fun Modes to your game? Your current game is saved first, and Undo Fun Modes puts it back.')) return;
  F.busy = true; renderFun();
  toast(apply ? 'Applying... this takes a few seconds.' : 'Working out what would change...');
  try {
    const res = await api('/api/fun/run', { settings: F.s, apply });
    if (!F.s.seed) { F.s.seed = res.seed; funSave(); }
    showFunReport(res, apply);
    if (res.applied) { await loadFunStatus(); loadTrainerList().catch(() => {}); }
  } catch (e) { toast(e.message, true); }
  F.busy = false; renderFun();
}

function showFunReport(res, apply) {
  const blocked = res.report.some(r => r.title.startsWith('Problems'));
  const head = res.applied ? 'Done! Press ▶ Play to try it. Seed: ' + res.seed
    : blocked ? 'Nothing was changed because of the problems below. Send them to Claude in your project.'
    : apply ? 'Nothing needed changing.' : 'Preview only, nothing changed yet. Seed: ' + res.seed;
  const body = el('div', {},
    el('p', { class: blocked ? 'warnbox' : 'note' }, head),
    res.report.map(sec => el('details', { class: 'funreport', open: res.report.length <= 2 },
      el('summary', {}, `${sec.title} (${sec.count})`),
      el('ul', {}, sec.lines.map(l => el('li', {}, l)), sec.count > sec.lines.length ? el('li', { class: 'note' }, `...and ${sec.count - sec.lines.length} more`) : null))),
    !res.applied && !blocked && res.files.length ? el('div', { class: 'row', style: 'justify-content:flex-end;margin-top:12px' },
      el('button', { class: 'btn primary', onclick: () => { closeModal(); runFun(true); } }, 'Apply this')) : null);
  openModal(res.applied ? 'Fun Modes applied' : 'Fun Modes preview', body);
}

async function loadFunStatus() {
  try { F.status = await api('/api/fun/status'); } catch (e) { F.status = { error: e.message }; }
  renderFunSide();
}

function fmtTime(t) { return new Date(t * 1000).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }); }

async function funAction(path, body, question, done) {
  if (question && !confirm(question)) return;
  try {
    await api(path, body || {});
    toast(done);
    await loadFunStatus();
    loadTrainerList().catch(() => {});
  } catch (e) { toast(e.message, true); }
}

function renderFunSide() {
  const st = F.status || {};
  const box = $('#funSide');
  if (st.error) { box.replaceChildren(el('div', { class: 'warnbox' }, st.error)); return; }
  const fun = st.fun || { active: false, applied: [] };
  const nameInput = el('input', { class: 'search', type: 'text', placeholder: 'Name this version, e.g. Pirate Nuzlocke' });
  box.replaceChildren(
    el('div', { class: 'funstatus ' + (fun.active ? 'on' : '') },
      el('b', {}, fun.active ? 'Fun Modes are on' : 'Fun Modes are off'),
      fun.active ? el('ul', {}, fun.applied.map(a => el('li', {}, `${a.summary.modes.join(', ')} (seed ${a.summary.seed})`))) : el('div', { class: 'note' }, 'Your game is as you left it.'),
      fun.active ? el('button', { class: 'btn', onclick: () => funAction('/api/fun/undo', {}, 'Put your game back to how it was before Fun Modes? (The fun version is saved, so you can come back to it.)', 'Fun Modes undone.') }, '↩ Undo Fun Modes') : null),
    el('div', { class: 'grouphead' }, 'Saved versions'),
    el('div', { class: 'searchrow' }, nameInput,
      el('button', { class: 'btn small', onclick: () => funAction('/api/fun/version/save', { name: nameInput.value }, null, 'Version saved.') }, 'Save')),
    el('div', { class: 'versions' }, (st.versions || []).length ? st.versions.map(v => el('div', { class: 'item version' },
      el('div', { class: 'meta', style: 'flex:1' }, el('div', { class: 'title' }, v.name), el('div', { class: 'sub' }, (v.auto ? 'Automatic · ' : '') + fmtTime(v.time))),
      el('button', { class: 'btn small', title: 'Switch the game to this version', onclick: () => funAction('/api/fun/version/switch', { id: v.id }, `Switch your game to "${v.name}"? Your current game is saved as a version first.`, 'Switched.') }, 'Use'),
      el('button', { class: 'btn small ghost', title: 'Delete this version', onclick: () => funAction('/api/fun/version/delete', { id: v.id }, `Delete the saved version "${v.name}"?`, 'Deleted.') }, '✕')))
      : el('div', { class: 'note', style: 'padding:8px' }, 'No saved versions yet.')),
    el('div', { class: 'grouphead' }, 'Start over'),
    el('div', { style: 'padding:0 10px 12px' },
      el('button', { class: 'btn danger', onclick: () => funAction('/api/fun/reset', {}, 'Reset every game file to the original pokeemerald-expansion? Your current game is saved as a version first, so you can switch back.', 'Reset to the base game.') }, 'Reset to base game'),
      el('p', { class: 'note' }, 'Puts every game file back to the original. The editor itself is not changed.')));
}

views.fun = {
  onShow: () => { if (!F.s) funLoad(); renderFun(); loadFunStatus(); },
};

// ---------------------------------------------------------------------------
// Play / Update jobs
// ---------------------------------------------------------------------------
let jobNext = 0;
let jobTimer = null;

function showJob(title) {
  $('#jobPanel').classList.remove('hidden');
  $('#jobTitle').textContent = title;
  $('#jobMessage').className = '';
  $('#jobMessage').innerHTML = '<span class="spinner"></span>Working...';
  $('#jobLog').textContent = '';
  jobNext = 0;
}

async function pollJob() {
  clearTimeout(jobTimer);
  try {
    const j = await api('/api/job?since=' + jobNext);
    jobNext = j.next;
    if (j.log.length) {
      const log = $('#jobLog');
      log.textContent += j.log.join('\n') + '\n';
      log.scrollTop = log.scrollHeight;
    }
    if (j.state === 'running') { jobTimer = setTimeout(pollJob, 400); return; }
    const msg = $('#jobMessage');
    msg.textContent = j.message;
    msg.className = j.state === 'done' ? 'ok' : 'bad';
    if (j.state === 'failed') $('#jobLog').classList.remove('hidden');
    $('#playBtn').disabled = false;
    $('#exportBtn').disabled = false;
    $('#updateBtn').disabled = false;
    if (j.title === 'Update' && j.state === 'done' && /^Updated/.test(j.message)) waitForRestart();
    if (jobDone) { const cb = jobDone; jobDone = null; cb(j); }
  } catch (e) {
    jobTimer = setTimeout(pollJob, 1000);
  }
}

let jobDone = null;   // called once when the current job finishes

async function startJob(path, title, onDone = null, confirmed = false) {
  if (!confirmed && anyDirty() && !confirm('Some changes are not saved yet and will not be included. Continue?')) return;
  try {
    const res = await api(path, {});
    if (!res.started) { toast('Already working on something, please wait.', true); return; }
    jobDone = onDone;
    $('#playBtn').disabled = true;
    $('#exportBtn').disabled = true;
    $('#updateBtn').disabled = true;
    showJob(title);
    pollJob();
  } catch (e) { toast(e.message, true); }
}

function waitForRestart() {
  let tries = 0;
  const tick = async () => {
    tries++;
    try { await api('/api/ping'); if (tries > 2) { location.reload(); return; } } catch (e) { /* restarting */ }
    setTimeout(tick, 1000);
  };
  setTimeout(tick, 1500);
}

$('#playBtn').addEventListener('click', () => startJob('/api/play', 'Play'));
$('#exportBtn').addEventListener('click', saveAsGba);

// "Save as .gba": ask where to save first (while the click still counts, so the
// browser allows the window), then build, then write the new game file there.
async function saveAsGba() {
  if (anyDirty() && !confirm('Some changes are not saved yet and will not be included. Continue?')) return;
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  const name = `Emerald ${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}${pad(d.getMinutes())}.gba`;
  let handle = null;
  if (window.showSaveFilePicker) {
    try {
      handle = await window.showSaveFilePicker({
        id: 'emerald-gba',          // the browser remembers the last folder used
        suggestedName: name,
        types: [{ description: 'Game Boy Advance game', accept: { 'application/octet-stream': ['.gba'] } }],
      });
    } catch (e) {
      if (e.name === 'AbortError') return;   // the user closed the window
      handle = null;
    }
  }
  startJob('/api/build', 'Save as .gba', async (j) => {
    if (j.state !== 'done') return;
    const msg = $('#jobMessage');
    try {
      if (handle) {
        const res = await fetch('/api/rom');
        if (!res.ok) throw new Error('Could not read the built game.');
        const w = await handle.createWritable();
        await w.write(await res.blob());
        await w.close();
        msg.textContent = 'Saved your game as ' + handle.name;
      } else {
        // No save window in this browser: download it instead (usually to Downloads).
        const a = el('a', { href: '/api/rom?name=' + encodeURIComponent(name), download: name });
        document.body.append(a); a.click(); a.remove();
        msg.textContent = 'Saved your game as ' + name + ' in your Downloads folder.';
      }
      msg.className = 'ok';
    } catch (e) {
      msg.textContent = 'Built, but saving failed: ' + e.message;
      msg.className = 'bad';
    }
  }, true);
}
$('#updateBtn').addEventListener('click', async () => {
  const info = await api('/api/updates').catch(e => ({ ok: false, message: e.message }));
  if (!info.ok) { toast(info.message, true); return; }
  if (!info.count) { toast('You already have the latest version.'); $('#updateBadge').classList.add('hidden'); return; }
  const body = el('div', {},
    el('p', {}, `${info.count} update(s) are ready:`),
    el('ul', {}, info.changes.map(c => el('li', {}, c))),
    el('p', { class: 'note' }, 'Your own changes are saved first and kept. If an update touches the same lines you changed, nothing is changed and I will tell you.'),
    el('div', { class: 'row', style: 'justify-content:flex-end' },
      el('button', { class: 'btn primary', onclick: () => { closeModal(); startJob('/api/update', 'Update'); } }, 'Update now')));
  openModal('Update the editor', body);
});
$('#jobClose').addEventListener('click', () => $('#jobPanel').classList.add('hidden'));
$('#jobLogToggle').addEventListener('click', () => {
  const log = $('#jobLog');
  log.classList.toggle('hidden');
  $('#jobLogToggle').textContent = log.classList.contains('hidden') ? 'Show details' : 'Hide details';
});

async function checkUpdatesQuietly() {
  try {
    const info = await api('/api/updates');
    if (info.ok && info.count) {
      const b = $('#updateBadge');
      b.textContent = info.count;
      b.classList.remove('hidden');
    }
  } catch (e) { /* offline is fine */ }
}

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
(async function start() {
  try {
    await loadGameData();
    await loadTrainerList();
    let view = 'trainers';
    let trainer = null;
    try { view = localStorage.getItem('emerald.view') || 'trainers'; trainer = localStorage.getItem('emerald.trainer'); } catch (e) { /* ignore */ }
    showView(views[view] ? view : 'trainers');
    if (trainer && T.list.some(t => t.id === trainer)) openTrainer(trainer);
    setTimeout(checkUpdatesQuietly, 2000);
  } catch (e) {
    const msg = 'The editor could not load: ' + e.message + ' (send this to Claude in your project)';
    $('#trainerList').replaceChildren(el('div', { class: 'warnbox' }, msg));
    $('#trainerEditor').replaceChildren(el('div', { class: 'warnbox' }, msg));
  }
})();


// ---------------------------------------------------------------------------
// Pickers: a searchable dropdown for every box that has a list of choices
// (Pokemon, moves, items, abilities...). Clicking a box shows the whole list,
// with the current choice highlighted; typing narrows it down. This replaces
// the browser's own suggestion list, which hides everything that does not
// match the text already in the box and stops after a few hundred entries.
// ---------------------------------------------------------------------------
const Picker = { input: null, box: null, values: [], shown: [], active: -1, typed: false };

function pickerNorm(s) { return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]/g, ''); }

function pickerValues(input) {
  const dl = document.getElementById(input.dataset.list);
  return dl ? Array.from(dl.options, o => o.value) : [];
}

function pickerOpen(input) {
  if (Picker.input !== input) pickerClose();
  Picker.input = input;
  Picker.values = pickerValues(input);
  Picker.typed = false;
  if (!Picker.box) {
    Picker.box = el('div', { class: 'picker' });
    // Keep focus in the text box while clicking the list.
    Picker.box.addEventListener('mousedown', e => e.preventDefault());
    document.body.append(Picker.box);
  }
  pickerRender();
}

function pickerClose() {
  if (Picker.box) Picker.box.classList.add('hidden');
  Picker.input = null;
  Picker.active = -1;
}

function pickerPlace() {
  const r = Picker.input.getBoundingClientRect();
  const box = Picker.box;
  box.style.minWidth = Math.max(r.width, 220) + 'px';
  const below = window.innerHeight - r.bottom;
  const height = Math.min(320, box.scrollHeight || 320);
  box.style.left = Math.min(r.left, window.innerWidth - Math.max(r.width, 220) - 8) + 'px';
  if (below < height + 8 && r.top > below) { box.style.top = ''; box.style.bottom = (window.innerHeight - r.top + 2) + 'px'; }
  else { box.style.bottom = ''; box.style.top = (r.bottom + 2) + 'px'; }
}

function pickerRender() {
  const input = Picker.input;
  const current = input.value.trim();
  const q = Picker.typed ? pickerNorm(current) : '';
  let shown = Picker.values;
  if (q) {
    const starts = [], contains = [];
    for (const v of Picker.values) {
      const n = pickerNorm(v);
      if (n.startsWith(q)) starts.push(v); else if (n.includes(q)) contains.push(v);
    }
    shown = starts.concat(contains);
  }
  Picker.shown = shown;
  const isSpecies = input.dataset.list === 'dl-species';
  const rows = shown.map((v, i) => {
    const row = el('div', { class: 'pick' + (v === current ? ' chosen' : ''), 'data-i': i, onclick: () => pickerChoose(v) });
    if (isSpecies) {
      const sp = GD.species && index.speciesByName ? index.speciesByName.get(v) : null;
      row.append(el('img', { src: sp && sp.img ? imgUrl(sp.img) : '', loading: 'lazy', alt: '' }));
    }
    row.append(el('span', {}, v));
    return row;
  });
  if (!rows.length) rows.push(el('div', { class: 'pick none' }, 'Nothing matches "' + current + '"'));
  Picker.box.replaceChildren(...rows);
  Picker.box.classList.remove('hidden');
  Picker.active = q ? 0 : shown.indexOf(current);
  pickerHighlight(true);
  pickerPlace();
}

function pickerHighlight(scroll) {
  const rows = Picker.box.querySelectorAll('.pick[data-i]');
  rows.forEach(r => r.classList.toggle('active', Number(r.dataset.i) === Picker.active));
  const row = rows[Picker.active];
  if (scroll && row) row.scrollIntoView({ block: Picker.typed ? 'nearest' : 'center' });
}

function pickerChoose(v) {
  const input = Picker.input;
  if (!input) return;
  input.value = v;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  pickerClose();
}

document.addEventListener('focusin', e => {
  const t = e.target;
  if (!(t instanceof HTMLInputElement)) return;
  // Move the browser's own list aside so only our picker shows.
  if (t.hasAttribute('list')) { t.dataset.list = t.getAttribute('list'); t.removeAttribute('list'); }
  if (t.dataset.list) { pickerOpen(t); setTimeout(() => t.select(), 0); }
  else pickerClose();
});
document.addEventListener('focusout', e => { if (e.target === Picker.input) pickerClose(); });
document.addEventListener('mousedown', e => {
  const t = e.target;
  if (t === Picker.input && Picker.box.classList.contains('hidden')) pickerOpen(t);
});
document.addEventListener('input', e => {
  if (e.target !== Picker.input || !e.isTrusted) return;
  Picker.typed = true;
  pickerRender();
}, true);
document.addEventListener('keydown', e => {
  if (e.target !== Picker.input) return;
  const open = !Picker.box.classList.contains('hidden');
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    if (!open) { pickerOpen(e.target); return e.preventDefault(); }
    const n = Picker.shown.length;
    if (!n) return;
    Picker.active = e.key === 'ArrowDown' ? Math.min(n - 1, Picker.active + 1) : Math.max(0, Picker.active - 1);
    pickerHighlight(true);
    e.preventDefault();
  } else if (e.key === 'Enter' && open && Picker.active >= 0 && Picker.shown[Picker.active] !== undefined) {
    pickerChoose(Picker.shown[Picker.active]);
    e.preventDefault();
  } else if (e.key === 'Escape' && open) {
    pickerClose();
    e.preventDefault();
  }
});
window.addEventListener('scroll', e => {
  if (Picker.input && !Picker.box.contains(e.target)) pickerPlace();
}, true);
window.addEventListener('resize', () => { if (Picker.input) pickerPlace(); });
