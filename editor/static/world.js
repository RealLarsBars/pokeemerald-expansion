'use strict';
// ---------------------------------------------------------------------------
// Maps: a picture of every map, with its items, people, wild Pokemon, shops,
// gifts and trainers. Uses the helpers in app.js (el, api, toast, GD, index...).
// ---------------------------------------------------------------------------
const W = {
  list: null, map: null, items: [], moves: {}, dirty: new Set(), mode: 'select', zoom: 2,
  sel: null, tab: 'items', wild: null, shops: null, prices: {}, gifts: null, filter: 'all',
  personIdx: null, person: null, pEdits: null, showCode: true, pView: 'steps',
};
const TILE = 16;

function itemName(c) { return GD.items.find(i => i.const === c)?.name || prettyFromConst('ITEM', c); }
function speciesName(c) { return index.species.get(c)?.name || prettyFromConst('SPECIES', c); }
function itemConst(name) { return toConst('ITEM', name); }

function markMapDirty(part) {
  W.dirty.add(part);
  const d = $('#mapDirty');
  if (d) d.textContent = 'Unsaved changes';
}

async function loadMapList() {
  W.list = await api('/api/maps');
  renderMapList();
}

function renderMapList() {
  if (!W.list) return;
  const q = $('#mapSearch').value.trim().toLowerCase();
  const f = $('#mapFilter').value;
  const box = $('#mapList');
  const frag = document.createDocumentFragment();
  for (const m of W.list) {
    if (q && !`${m.name} ${m.map}`.toLowerCase().includes(q)) continue;
    if (f === 'outside' && !/ROUTE|TOWN|CITY|UNDERWATER|OCEAN/.test(m.type)) continue;
    if (f === 'items' && !m.items) continue;
    if (f === 'wild' && !m.wild) continue;
    if (f === 'shops' && !m.shops) continue;
    if (f === 'gifts' && !m.gifts) continue;
    const bits = [];
    if (m.items) bits.push(`${m.items} item${m.items > 1 ? 's' : ''}`);
    if (m.wild) bits.push('wild Pokémon');
    if (m.shops) bits.push('shop');
    if (m.gifts) bits.push(`${m.gifts} gift/encounter`);
    frag.append(el('div', { class: 'item' + (W.map?.map === m.map ? ' active' : ''), onclick: () => openMap(m.map) },
      el('div', { class: 'meta' }, el('div', { class: 'title' }, m.name), el('div', { class: 'sub' }, bits.join(' · ') || ' '))));
  }
  box.replaceChildren(frag);
}

async function openMap(folder, keepTab = true) {
  if (W.dirty.size && W.map?.map !== folder && !confirm('You have unsaved changes on this map. Throw them away?')) return;
  try {
    const d = await api('/api/map?map=' + encodeURIComponent(folder));
    const keepPerson = W.map?.map === folder ? W.personIdx : null;
    setMapData(d);
    if (keepPerson !== null && d.objects.some(o => o.index === keepPerson)) await loadPerson(keepPerson, false);
    if (!keepTab) W.tab = 'items';
    renderMapEditor();
    renderMapList();
    try { localStorage.setItem('emerald.map', folder); } catch (e) { /* ignore */ }
  } catch (e) { toast(e.message, true); }
}

function setMapData(d) {
  W.map = d;
  W.items = d.objects.filter(o => o.kind === 'item').map(o => ({ kind: 'ball', index: o.index, x: o.x, y: o.y, item: o.item, quantity: o.quantity }))
    .concat(d.hidden.map(h => ({ kind: 'hidden', index: h.index, x: h.x, y: h.y, item: h.item, quantity: h.quantity })));
  W.moves = {};
  W.dirty = new Set();
  W.sel = null;
  W.wild = JSON.parse(JSON.stringify(d.wild.entries));
  W.shops = JSON.parse(JSON.stringify(d.shops));
  W.prices = Object.assign({}, d.prices);
  W.priceChanges = {};
  W.gifts = JSON.parse(JSON.stringify(d.gifts));
  W.giftChanged = new Set();
  W.personIdx = null;
  W.person = null;
  W.pEdits = null;
  W.door = null;
  W.doorEdit = null;
  W.sign = null;
  W.signData = null;
  W.signEdits = {};
}

function walkable(x, y) { return W.map.walls[y * W.map.width + x] === '0'; }

function occupied(x, y, except) {
  for (const it of W.items) if (it !== except && it.x === x && it.y === y && it.kind === 'ball') return 'an item';
  for (const o of W.map.objects) {
    if (o.kind === 'item') continue;
    const p = W.moves[o.index] || [o.x, o.y];
    if (o !== except && p[0] === x && p[1] === y) return o.kind === 'trainer' ? 'a trainer' : 'someone';
  }
  return null;
}

// ---- the map picture ------------------------------------------------------------------------
function renderMapCanvas() {
  const d = W.map;
  const z = W.zoom;
  const wrap = el('div', { class: 'mapwrap', style: `width:${d.width * TILE * z}px;height:${d.height * TILE * z}px` });
  const img = el('img', { class: 'mapimg', src: `/api/mapimg?map=${encodeURIComponent(d.map)}&t=${Date.now()}`, alt: '', draggable: 'false',
    style: `width:${d.width * TILE * z}px;height:${d.height * TILE * z}px` });
  wrap.append(img);
  const cell = TILE * z;
  const place = (node, x, y, w = 1, h = 1) => {
    node.style.left = x * cell + 'px';
    node.style.top = (y + 1 - h) * cell + 'px';
  };
  for (const w of d.warps) {
    const n = el('div', { class: 'mk warp' + (W.tab === 'doors' && W.door === w.index ? ' sel' : ''),
      title: (w.toName ? `Door to ${w.toName}` : 'Door') + ' – click to see where it leads and go there, double-click to go straight there' });
    n.style.width = n.style.height = cell + 'px';
    // Any mode: a click shows the door on the right (with "Go to"), a double-click goes straight there.
    n.addEventListener('mousedown', e => e.stopPropagation());
    n.addEventListener('click', e => { e.stopPropagation(); openDoor(w.index); });
    n.addEventListener('dblclick', e => { e.stopPropagation(); if (w.toFolder) goThroughDoor(w); });
    place(n, w.x, w.y);
    wrap.append(n);
  }
  for (const sg of d.signs || []) {
    const n = el('div', { class: 'mk signmk' + (W.tab === 'doors' && W.sign === sg.index ? ' sel' : ''), title: 'Sign – click to change what it says' }, '✎');
    n.style.width = n.style.height = cell + 'px';
    n.addEventListener('mousedown', e => e.stopPropagation());
    n.addEventListener('click', e => { e.stopPropagation(); openSign(sg.index); });
    place(n, sg.x, sg.y);
    wrap.append(n);
  }
  for (const o of d.objects) {
    if (o.kind === 'item') continue;
    const [x, y] = W.moves[o.index] || [o.x, o.y];
    const sprite = index.ow.get(o.graphics_id);
    const n = el('div', { class: 'mk person ' + o.kind + (W.personIdx === o.index ? ' sel' : ''), title: personName(o) + ' – click to see their script and what they say, drag to move' });
    const sh = sprite ? sprite.h / 16 : 2;
    n.append(owSprite(sprite, z));
    n.style.width = (sprite ? sprite.w : 16) * z + 'px';
    n.style.marginLeft = -((sprite ? sprite.w : 16) - 16) * z / 2 + 'px';
    place(n, x, y, 1, sh);
    makeDraggable(n, o, 'person');
    wrap.append(n);
  }
  for (const it of W.items) {
    const n = el('div', { class: 'mk itemmk ' + (it.kind === 'hidden' ? 'hid' : 'ball') + (W.sel === it ? ' sel' : ''), title: `${itemName(it.item)}${it.quantity > 1 ? ' ×' + it.quantity : ''}${it.kind === 'hidden' ? ' (hidden)' : ''} – drag to move` });
    n.style.width = n.style.height = cell + 'px';
    if (it.kind === 'ball') n.append(owSprite(index.ow.get('OBJ_EVENT_GFX_ITEM_BALL'), z));
    else n.textContent = '?';
    place(n, it.x, it.y);
    makeDraggable(n, it, 'item');
    wrap.append(n);
  }
  const hover = el('div', { class: 'hovertile' });
  hover.style.width = hover.style.height = cell + 'px';
  wrap.append(hover);
  const tileAt = e => {
    const r = wrap.getBoundingClientRect();
    return [Math.floor((e.clientX - r.left) / cell), Math.floor((e.clientY - r.top) / cell)];
  };
  wrap.addEventListener('mousemove', e => {
    const [x, y] = tileAt(e);
    if (x < 0 || y < 0 || x >= d.width || y >= d.height) return;
    place(hover, x, y);
    hover.classList.toggle('blocked', !walkable(x, y));
    $('#mapCoords').textContent = `x ${x}, y ${y}` + (walkable(x, y) ? '' : ' · the player can’t walk here');
  });
  wrap.addEventListener('click', e => {
    if (W.mode === 'select' || e.target.closest('.mk.itemmk, .mk.person')) return;
    const [x, y] = tileAt(e);
    if (x < 0 || y < 0 || x >= d.width || y >= d.height) return;
    const busy = occupied(x, y);
    if (busy && W.mode !== 'hidden') { toast(`There is already ${busy} there.`, true); return; }
    if (W.mode === 'trainer') { openNewTrainer(x, y); return; }
    if (W.mode === 'ball' && !walkable(x, y)) toast('Heads up: the player can’t walk onto that spot, so they may not reach the item.', true);
    const it = { kind: W.mode === 'hidden' ? 'hidden' : 'ball', index: null, x, y, item: 'ITEM_POTION', quantity: 1 };
    W.items.push(it);
    W.sel = it;
    W.tab = 'items';
    markMapDirty('items');
    renderMapEditor();
    setTimeout(() => document.querySelector('.mapitem.sel input')?.focus(), 30);
  });
  return wrap;
}

function makeDraggable(node, thing, kind) {
  node.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const wrap = node.parentElement;
    const cell = TILE * W.zoom;
    const startX = e.clientX, startY = e.clientY;
    const left0 = parseFloat(node.style.left), top0 = parseFloat(node.style.top);
    let moved = false;
    const move = ev => {
      const dx = ev.clientX - startX, dy = ev.clientY - startY;
      if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
      node.style.left = left0 + dx + 'px';
      node.style.top = top0 + dy + 'px';
    };
    const up = ev => {
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
      if (kind === 'item') { W.sel = thing; W.tab = 'items'; }
      if (!moved && kind === 'person') { loadPerson(thing.index); return; }
      if (!moved) { renderMapEditor(); return; }
      const r = wrap.getBoundingClientRect();
      const x = Math.floor((ev.clientX - r.left) / cell), y = Math.floor((ev.clientY - r.top) / cell);
      if (x >= 0 && y >= 0 && x < W.map.width && y < W.map.height) {
        const busy = occupied(x, y, thing);
        if (busy && !(kind === 'item' && thing.kind === 'hidden')) toast(`There is already ${busy} there.`, true);
        else if (kind === 'item') { thing.x = x; thing.y = y; markMapDirty('items'); }
        else { W.moves[thing.index] = [x, y]; markMapDirty('items'); }
      }
      renderMapEditor();
    };
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  });
}

// ---- the page -----------------------------------------------------------------------------
function renderMapEditor() {
  const d = W.map;
  const root = $('#mapEditor');
  const scroller = root.querySelector('.mapscroll');
  const keep = scroller ? [scroller.scrollLeft, scroller.scrollTop] : null;
  const panelScroll = root.querySelector('.mappanel')?.scrollTop || 0;
  const tools = el('div', { class: 'maptools' },
    ...[['select', '✋ Move things', 'Drag items and people to move them'], ['ball', '+ Item ball', 'Click the map to place an item ball'],
      ['hidden', '+ Hidden item', 'Click the map to hide an item (found with the Itemfinder or by pressing A)'],
      ['trainer', '+ New trainer', 'Click the map where the new trainer should stand']]
      .map(([m, label, tip]) => el('button', { class: 'btn small' + (W.mode === m ? ' primary' : ''), title: tip, onclick: () => { W.mode = m; renderMapEditor(); } }, label)),
    el('span', { style: 'flex:1' }),
    el('button', { class: 'btn small ghost', title: 'Zoom out', onclick: () => { W.zoom = Math.max(1, W.zoom - 1); renderMapEditor(); } }, '−'),
    el('span', { class: 'note', style: 'margin:0' }, `${W.zoom}×`),
    el('button', { class: 'btn small ghost', title: 'Zoom in', onclick: () => { W.zoom = Math.min(4, W.zoom + 1); renderMapEditor(); } }, '+'));
  const hint = { select: 'Drag items and people to move them. Click someone to see their script and what they say. Click a door, ladder or stairs (blue square) to go to that map or change where it leads, or a sign (✎) to change what it says.', ball: 'Click a spot on the map to place an item ball there.',
    hidden: 'Click a spot to hide an item there.', trainer: 'Click where the new trainer should stand.' }[W.mode];
  const left = el('div', { class: 'mapleft' }, tools,
    el('div', { class: 'note maphint' }, hint, ' ', el('span', { id: 'mapCoords' })),
    el('div', { class: 'mapscroll' + (W.mode !== 'select' ? ' placing' : '') }, renderMapCanvas()));
  const tabs = [['items', `Items (${W.items.length})`], ['wild', 'Wild Pokémon'], ['people', 'Trainers & people'],
    ['doors', `Doors & signs (${d.warps.length + (d.signs || []).length})`],
    ['shops', `Shop${W.shops.length ? ` (${W.shops.length})` : ''}`], ['gifts', `Gifts & encounters${W.gifts.length ? ` (${W.gifts.length})` : ''}`]];
  const panel = el('div', { class: 'mappanel' },
    el('div', { class: 'subtabs' }, tabs.map(([k, label]) => el('button', { class: 'subtab' + (W.tab === k ? ' active' : ''), onclick: () => { W.tab = k; renderMapEditor(); } }, label))),
    { items: renderItemsPanel, wild: renderWildPanel, people: renderPeoplePanel, doors: renderDoorsPanel, shops: renderShopsPanel, gifts: renderGiftsPanel }[W.tab]());
  root.replaceChildren(
    el('div', { class: 'savebar' },
      el('h2', {}, d.name, el('span', { class: 'idtag' }, d.id)),
      el('span', { id: 'mapDirty', class: 'dirty' }, W.dirty.size ? 'Unsaved changes' : ''),
      el('button', { class: 'btn ghost', onclick: () => { W.dirty.clear(); openMap(d.map); }, title: 'Undo all unsaved changes' }, 'Revert'),
      el('button', { class: 'btn primary', onclick: saveMap }, 'Save')),
    el('div', { class: 'maplayout' }, left, panel));
  if (keep) { const s = root.querySelector('.mapscroll'); s.scrollLeft = keep[0]; s.scrollTop = keep[1]; }
  root.querySelector('.mappanel').scrollTop = panelScroll;
}

function renderItemsPanel() {
  const box = el('div', { class: 'rows' });
  if (!W.items.length) box.append(el('div', { class: 'note' }, 'No items on this map yet. Use “+ Item ball” or “+ Hidden item” above, then click the map.'));
  W.items.forEach((it, i) => {
    const input = el('input', { value: itemName(it.item), list: 'dl-items', class: 'grow', placeholder: 'Item',
      oninput: () => { it.item = itemConst(input.value); markMapDirty('items'); } });
    const qty = el('input', { type: 'number', min: 1, max: 99, value: it.quantity, class: 'lv', title: 'How many',
      oninput: () => { it.quantity = parseInt(qty.value, 10) || 1; markMapDirty('items'); } });
    box.append(el('div', { class: 'mapitem rowline' + (W.sel === it ? ' sel' : ''), onclick: () => { if (W.sel !== it) { W.sel = it; renderMapEditor(); } } },
      el('span', { class: 'kindtag ' + (it.kind === 'hidden' ? 'hid' : 'ball') }, it.kind === 'ball' ? 'Ball' : 'Hidden'),
      input, el('span', { class: 'note', style: 'margin:0' }, '×'), qty,
      el('span', { class: 'note', style: 'margin:0;min-width:64px' }, `x ${it.x}, y ${it.y}`),
      el('button', { class: 'iconbtn', title: 'Remove this item', onclick: e => { e.stopPropagation(); W.items.splice(i, 1); if (W.sel === it) W.sel = null; markMapDirty('items'); renderMapEditor(); } }, '✕')));
  });
  return el('div', {}, el('p', { class: 'note' }, 'Item balls show on the map. Hidden items are found with the Itemfinder or by pressing A on the spot. Each new item can be picked up once.'), box);
}

// ---- wild Pokemon -------------------------------------------------------------------------
const WILD_SECTIONS = [['land_mons', 'Grass and caves'], ['water_mons', 'Surfing'], ['rock_smash_mons', 'Rock Smash'], ['fishing_mons', 'Fishing']];

function renderWildPanel() {
  const slots = W.map.wild.slots;
  const out = el('div', {});
  if (!W.wild.length) {
    out.append(el('p', { class: 'note' }, 'No wild Pokémon live here yet.'),
      el('button', { class: 'btn', onclick: () => { W.wild.push({ map: W.map.id, base_label: 'g' + W.map.map }); markMapDirty('wild'); renderMapEditor(); } }, 'Add wild Pokémon to this map'));
    return out;
  }
  if (W.wild.length > 1) out.append(el('p', { class: 'note' }, `This map has ${W.wild.length} sets of wild Pokémon (the game picks one, e.g. by time or event).`));
  W.wild.forEach((entry, ei) => {
    if (W.wild.length > 1) out.append(el('h3', { class: 'sectionhead' }, `Set ${ei + 1}`));
    for (const [key, name] of WILD_SECTIONS) {
      const sec = entry[key];
      const info = slots[key];
      if (!info) continue;
      if (!sec) {
        out.append(el('button', { class: 'btn small ghost', style: 'margin:4px 6px 4px 0', onclick: () => {
          const base = (entry.land_mons || entry.water_mons || entry.fishing_mons || entry.rock_smash_mons)?.mons?.[0];
          entry[key] = { encounter_rate: { land_mons: 20, water_mons: 4, rock_smash_mons: 20, fishing_mons: 30 }[key],
            mons: info.chances.map(() => ({ min_level: base?.min_level || 5, max_level: base?.max_level || 5, species: base?.species || 'SPECIES_ZIGZAGOON' })) };
          markMapDirty('wild'); renderMapEditor();
        } }, '+ ' + name));
        continue;
      }
      const rate = el('input', { type: 'number', min: 1, max: 100, value: sec.encounter_rate, class: 'lv', title: 'How often a wild Pokémon appears (higher = more often)',
        oninput: () => { sec.encounter_rate = parseInt(rate.value, 10) || 1; markMapDirty('wild'); } });
      const lo = el('input', { type: 'number', min: 1, max: 100, class: 'lv', placeholder: 'min' });
      const hi = el('input', { type: 'number', min: 1, max: 100, class: 'lv', placeholder: 'max' });
      const rows = el('div', { class: 'rows' });
      let rod = null;
      sec.mons.forEach((m, i) => {
        if (info.rods[i] && info.rods[i] !== rod) { rod = info.rods[i]; rows.append(el('div', { class: 'boxlabel' }, rod)); }
        const sprite = el('img', { src: imgUrl(index.species.get(m.species)?.img), alt: '' });
        const sp = el('input', { value: speciesName(m.species), list: 'dl-species', class: 'grow',
          oninput: () => { m.species = speciesConst(sp.value); sprite.src = imgUrl(index.species.get(m.species)?.img); markMapDirty('wild'); } });
        const a = el('input', { type: 'number', min: 1, max: 100, value: m.min_level, class: 'lv', title: 'Lowest level', oninput: () => { m.min_level = parseInt(a.value, 10) || 1; markMapDirty('wild'); } });
        const b = el('input', { type: 'number', min: 1, max: 100, value: m.max_level, class: 'lv', title: 'Highest level', oninput: () => { m.max_level = parseInt(b.value, 10) || 1; markMapDirty('wild'); } });
        rows.append(el('div', { class: 'rowline tight' }, el('span', { class: 'chance' }, info.chances[i] + '%'), sprite, sp, el('span', { class: 'note', style: 'margin:0' }, 'Lv'), a, '–', b));
      });
      out.append(el('div', { class: 'card', style: 'padding:12px' },
        el('div', { class: 'rowline', style: 'margin-bottom:8px' }, el('h3', { style: 'margin:0;flex:1' }, name),
          el('span', { class: 'note', style: 'margin:0' }, 'How often'), rate,
          el('button', { class: 'iconbtn', title: `Remove all ${name.toLowerCase()} Pokémon`, onclick: () => { if (confirm(`Remove all ${name.toLowerCase()} Pokémon from this map?`)) { delete entry[key]; markMapDirty('wild'); renderMapEditor(); } } }, '✕')),
        rows,
        el('div', { class: 'rowline', style: 'margin-top:8px' }, el('span', { class: 'note', style: 'margin:0' }, 'Set every level to'), lo, '–', hi,
          el('button', { class: 'btn small', onclick: () => {
            const l = parseInt(lo.value, 10), h = parseInt(hi.value || lo.value, 10);
            if (!l) return;
            sec.mons.forEach(m => { m.min_level = l; m.max_level = Math.max(l, h || l); });
            markMapDirty('wild'); renderMapEditor();
          } }, 'Apply'))));
    }
  });
  out.prepend(el('p', { class: 'note' }, 'The % is the chance of each slot. Put the same Pokémon in several slots to make it more common.'));
  return out;
}

// ---- people and new trainers --------------------------------------------------------------
function camelWords(s) { return s.replace(/_/g, ' ').replace(/([a-z])([A-Z0-9])/g, '$1 $2').replace(/(\d)([A-Z][a-z])/g, '$1 $2').trim(); }

function personName(o) {
  if (o.trainerName) return o.trainerName;
  const m = (o.script || '').match(/_EventScript_(\w+)$/);
  if (m) return camelWords(m[1]);
  return prettyFromConst('OBJ_EVENT_GFX', o.graphics_id);
}

function textTitle(label) {
  const m = label.match(/_Text_(\w+)$/);
  return camelWords(m ? m[1] : label);
}

async function loadPerson(idx, render = true) {
  if (W.dirty.has('person') && W.personIdx !== idx && !confirm('You have unsaved changes to this person. Throw them away?')) return;
  W.dirty.delete('person');
  W.personIdx = idx;
  W.tab = 'people';
  W.person = null;
  if (render) renderMapEditor();
  try {
    W.person = await api(`/api/map/person?map=${encodeURIComponent(W.map.map)}&index=${idx}`);
    W.pEdits = { texts: {} };
  } catch (e) { toast(e.message, true); W.personIdx = null; }
  if (render) renderMapEditor();
}

function closePerson() {
  if (W.dirty.has('person') && !confirm('You have unsaved changes to this person. Throw them away?')) return;
  W.dirty.delete('person');
  W.personIdx = null; W.person = null; W.pEdits = null;
  renderMapEditor();
}

function renderPersonCard() {
  const o = W.map.objects.find(x => x.index === W.personIdx);
  if (!o) return null;
  const p = W.person;
  const head = el('div', { class: 'rowline', style: 'margin-bottom:8px' }, owSprite(index.ow.get(o.graphics_id), 2),
    el('div', { class: 'grow' }, el('h3', { style: 'margin:0' }, personName(o)), el('div', { class: 'note', style: 'margin:0' }, `x ${o.x}, y ${o.y}`)),
    o.trainer ? el('button', { class: 'btn small', onclick: () => { showView('trainers'); openTrainer(o.trainer); } }, 'Edit team') : null,
    el('button', { class: 'iconbtn', title: 'Close', onclick: closePerson }, '✕'));
  const card = el('div', { class: 'card personcard', style: 'padding:12px' }, head);
  if (!p) { card.append(el('div', { class: 'note' }, 'Loading…')); return card; }
  if (p.missing) { card.append(el('div', { class: 'warnbox' }, `Their script (${p.label}) could not be found in the script files.`)); return card; }
  if (!p.label) { card.append(renderNoScript(o)); return card; }

  const shared = p.usedBy > 1 || !p.file.startsWith(`data/maps/${W.map.map}/`);
  if (shared) {
    card.append(el('div', { class: 'warnbox' }, p.usedBy > 1
      ? `This script is shared by ${p.usedBy} people or things in the game. Changing it here changes all of them.`
      : 'This script is shared with other places in the game. Changing it here changes those too.'));
  }

  // what they say
  const talk = el('div', {});
  if (!p.texts.length) talk.append(el('div', { class: 'note' }, 'They don’t say anything in their own words.'));
  for (const t of p.texts) {
    const preview = el('div', { class: 'boxes' });
    const ta = el('textarea', { class: 'short', 'data-text-label': t.label, value: W.pEdits.texts[t.label] ?? t.text,
      oninput: () => { W.pEdits.texts[t.label] = ta.value; markMapDirty('person'); renderBoxes(ta.value, preview); syncPersonText(card, t.label, ta.value); } });
    renderBoxes(ta.value, preview);
    talk.append(el('div', { class: 'persontext' },
      el('div', { class: 'boxlabel' }, textTitle(t.label), el('span', { class: 'idtag' }, t.label)),
      el('div', { class: 'textedit' }, ta, preview)));
  }
  card.append(el('h3', { class: 'sectionhead' }, 'What they say'),
    el('p', { class: 'note' }, 'Each new line is a new line in the game. Leave an empty line to start a new text box. {PLAYER} is the player’s name. Red lines are too wide.'),
    talk);

  // the script: all of their scripts in one box, as steps (Simple view) or as code
  const ta = el('textarea', { class: 'code', spellcheck: 'false', value: W.pEdits.code ?? personCode(p),
    oninput: () => { W.pEdits.code = ta.value; markMapDirty('person'); } });
  ta.style.minHeight = Math.min(420, 40 + 19 * (ta.value.split('\n').length + 1)) + 'px';
  ta.addEventListener('keydown', e => {
    if (e.key === 'Tab') { e.preventDefault(); ta.setRangeText('\t', ta.selectionStart, ta.selectionEnd, 'end'); ta.dispatchEvent(new Event('input')); }
  });
  const insertTarget = { ta, prefix: W.map.map, labels: () => p.labels };
  const insert = el('select', {
    onchange: () => { const v = insert.value; insert.value = ''; if (v) openInsertForm(v, insertTarget); },
  }, el('option', { value: '' }, '+ Insert...'), Object.entries(INSERTS).filter(([k]) => k !== 'newscript').map(([k, v]) => el('option', { value: k }, v.title)));
  const simple = W.pView === 'steps';
  const toggle = el('div', { class: 'segmented' },
    ['steps', 'code'].map(v => el('button', { class: W.pView === v ? 'on' : '', onclick: () => { W.pView = v; renderMapEditor(); } }, v === 'steps' ? 'Simple view' : 'Code view')));
  const holder = el('div', { class: 'personsteps' });
  const det = el('details', { open: W.showCode, ontoggle: () => { W.showCode = det.open; } },
    el('summary', { class: 'sectionhead' }, 'Their script (what happens, step by step)'),
    el('div', { class: 'rowline tight', style: 'margin:6px 0' }, toggle, simple ? null : insert),
    el('p', { class: 'note' }, simple
      ? 'Change the words, items or Pokémon right here, or use + on a step to add one after it.'
      : 'Put the cursor where you want something to happen, then use Insert. Don’t change the lines ending in “::”, they are the script names.'),
    simple ? holder : ta,
    p.shared.length ? el('p', { class: 'note' }, 'Also uses shared scripts: ' + p.shared.join(', ') + '. Those are in the Scripts tab.') : null);
  if (simple) {
    const ctx = { ta, holder, scroller: null, insert: insertTarget, texts: {
      get: label => W.pEdits.texts[label] ?? p.texts.find(t => t.label === label)?.text ?? null,
      set: (label, v) => { W.pEdits.texts[label] = v; markMapDirty('person'); syncPersonText(card, label, v); },
    } };
    ta.addEventListener('change', () => { ST = ctx; renderSteps(); });
    ST = ctx;
    renderSteps();
    ST = null;
  }
  card.append(det,
    el('div', { class: 'row', style: 'justify-content:flex-end;margin-top:8px' },
      el('span', { class: 'note' }, p.file),
      el('button', { class: 'btn ghost small', onclick: () => { W.dirty.delete('person'); loadPerson(W.personIdx); } }, 'Revert'),
      el('button', { class: 'btn primary small', onclick: saveMap }, 'Save')));
  return card;
}

// The same text can be open twice (under "What they say" and in the steps): keep both boxes alike.
function syncPersonText(card, label, value) {
  for (const t of card.querySelectorAll('textarea[data-text-label]')) {
    if (t.dataset.textLabel !== label || t === document.activeElement || t.value === value) continue;
    t.value = value;
    const preview = t.nextElementSibling;
    if (preview?.classList.contains('boxes')) renderBoxes(value, preview);
  }
}

// All of a person's scripts as one piece of code, each under its name.
function personCode(p) { return p.scripts.map(sc => `${sc.label}::\n${sc.code}`).join('\n\n'); }

// Split that code back into the scripts it came from. Returns null if a script name was changed.
function splitPersonCode(p, code) {
  const names = p.scripts.map(sc => sc.label);
  const lines = code.replace(/\r/g, '').split('\n');
  const at = [];
  lines.forEach((line, i) => { const m = line.match(/^(\w+)::\s*$/); if (m && names.includes(m[1])) at.push([m[1], i]); });
  if (at.length !== names.length || at.some(([n], i) => n !== names[i])) return null;
  return at.map(([label, i], k) => {
    const body = lines.slice(i + 1, k + 1 < at.length ? at[k + 1][1] : lines.length);
    while (body.length && !body[body.length - 1].trim()) body.pop();
    return { label, code: body.join('\n') };
  });
}

function renderNoScript(o) {
  const name = el('input', { value: '', placeholder: 'e.g. Old Man' });
  const preview = el('div', { class: 'boxes' });
  const ta = el('textarea', { class: 'short', placeholder: 'What should they say?', oninput: () => renderBoxes(ta.value, preview) });
  return el('div', {},
    el('p', { class: 'note' }, 'Nothing happens when you talk to them yet. Give them something to say:'),
    el('label', { class: 'field' }, el('span', {}, 'Name (just for you)'), name),
    el('label', { class: 'field' }, el('span', {}, 'What they say'), ta), preview,
    el('div', { class: 'row', style: 'justify-content:flex-end' },
      el('button', { class: 'btn primary small', onclick: async () => {
        if (!ta.value.trim()) { toast('Type what they should say first.', true); return; }
        if (W.dirty.size) { toast('Save this map first.', true); return; }
        try {
          await api('/api/map/person/new', { map: W.map.map, index: o.index, name: name.value, text: ta.value });
          await openMap(W.map.map);
          renderMapEditor();
          toast('Saved. Press Play to try it.');
        } catch (e) { toast(e.message, true); }
      } }, 'Give them this')));
}

function renderPeoplePanel() {
  const out = el('div', {});
  const card = W.personIdx !== null ? renderPersonCard() : null;
  if (card) out.append(card);
  else out.append(el('p', { class: 'note' }, 'Click someone on the map (or in the list below) to see their script and what they say.'));
  const trainersHere = W.map.objects.filter(o => o.kind === 'trainer');
  out.append(el('div', { class: 'rowline', style: 'margin-bottom:8px' },
    el('button', { class: 'btn primary small', onclick: () => { W.mode = 'trainer'; renderMapEditor(); toast('Click the map where the new trainer should stand.'); } }, '+ New trainer'),
    el('span', { class: 'note', style: 'margin:0' }, `Room for ${W.map.trainerRoom} more new trainer${W.map.trainerRoom === 1 ? '' : 's'} in the game.`),
    el('button', { class: 'btn small ghost', title: 'Make space for 48 more brand-new trainers', onclick: makeTrainerRoom }, 'Make more room')));
  const row = o => el('div', { class: 'rowline mapitem' + (W.personIdx === o.index ? ' sel' : ''), style: 'cursor:pointer', onclick: () => loadPerson(o.index) },
    owSprite(index.ow.get(o.graphics_id), 1),
    el('div', { class: 'grow' }, el('div', {}, personName(o)), el('div', { class: 'note', style: 'margin:0' }, `x ${o.x}, y ${o.y}` + (o.script && o.script !== '0x0' ? '' : ' · says nothing yet'))),
    o.trainer ? el('button', { class: 'btn small', onclick: e => { e.stopPropagation(); showView('trainers'); openTrainer(o.trainer); } }, 'Edit team') : null);
  const rows = el('div', { class: 'rows' }, trainersHere.map(row));
  if (!trainersHere.length) rows.append(el('div', { class: 'note' }, 'No trainers on this map.'));
  out.append(el('h3', { class: 'sectionhead' }, 'Trainers'), rows);
  const people = W.map.objects.filter(o => o.kind === 'person' || o.kind === 'berry' || o.kind === 'other');
  out.append(el('h3', { class: 'sectionhead' }, 'Everyone else'),
    people.length ? el('div', { class: 'rows' }, people.map(row)) : el('p', { class: 'note' }, 'Nobody else is here.'));
  return out;
}

async function makeTrainerRoom() {
  if (!confirm('Make room for 48 more new trainers?\n\nThis moves where the game keeps its saved progress, so an old save file will act strangely. Start a new game after this (Recent changes can undo it).')) return;
  try {
    const res = await api('/api/trainer/room', {});
    W.map.trainerRoom = res.room;
    renderMapEditor();
    toast(`Room for ${res.room} new trainers now. The next Play rebuilds most of the game, so it takes a few minutes.`);
  } catch (e) { toast(e.message, true); }
}

function openNewTrainer(x, y) {
  if (W.dirty.size) { toast('Save this map first, then add the trainer.', true); return; }
  const v = { name: '', class: 'Youngster', pic: 'Youngster', gfx: 'OBJ_EVENT_GFX_YOUNGSTER', gender: 'Male', music: 'Male', facing: 'down', sight: 3,
    species: 'Zigzagoon', level: 5, intro: "Hey! You look strong. Let's battle!", defeat: 'Wow, you really are strong!', after: 'I need to train more...' };
  const pic = index.pics.get(toConst('TRAINER_PIC', v.pic));
  const picImg = el('img', { src: imgUrl(pic?.img), alt: '' });
  const owBox = el('div', {}, owSprite(index.ow.get(v.gfx), 3));
  const field = (label, input) => el('label', { class: 'field' }, el('span', {}, label), input);
  const inp = (key, attrs = {}) => { const i = el('input', Object.assign({ value: v[key], oninput: () => { v[key] = i.value; } }, attrs)); return i; };
  const sel = (key, opts) => { const s = el('select', { onchange: () => { v[key] = s.value; } }, opts.map(([val, l]) => el('option', { value: val, selected: val === v[key] }, l))); return s; };
  const err = el('div');
  const form = el('div', { class: 'form' },
    el('div', { class: 'row' },
      el('div', { class: 'pic-pick', onclick: () => openGallery('Pick a battle picture', GD.trainerPics, toConst('TRAINER_PIC', v.pic), p => { v.pic = p.name; picImg.src = imgUrl(p.img); }) }, picImg, el('div', { class: 'hint' }, 'Battle picture')),
      el('div', { class: 'pic-pick', onclick: () => openGallery('Pick an overworld sprite', GD.overworld, v.gfx, g => { v.gfx = g.const; owBox.replaceChildren(owSprite(g, 3)); }, 'ow') }, owBox, el('div', { class: 'hint' }, 'Sprite on the map')),
      el('div', { class: 'grid' },
        field('Name', inp('name', { maxlength: 12, placeholder: 'e.g. Joey' })),
        field('Class', sel('class', GD.classes.map(c => [c.name, c.name]))),
        field('Gender', sel('gender', [['Male', 'Male'], ['Female', 'Female']])),
        field('Battle music', sel('music', GD.music.map(m => [m.name, m.name]))),
        field('Facing', sel('facing', [['down', 'Down'], ['up', 'Up'], ['left', 'Left'], ['right', 'Right'], ['around', 'Looks around']])),
        field('How far they see', inp('sight', { type: 'number', min: 1, max: 8 })),
        field('First Pokémon', inp('species', { list: 'dl-species' })),
        field('Level', inp('level', { type: 'number', min: 1, max: 100 })))),
    field('Before the battle', (() => { const t = el('textarea', { class: 'short', value: v.intro, oninput: () => { v.intro = t.value; } }); return t; })()),
    field('When they lose', (() => { const t = el('textarea', { class: 'short', value: v.defeat, oninput: () => { v.defeat = t.value; } }); return t; })()),
    field('If you talk to them after', (() => { const t = el('textarea', { class: 'short', value: v.after, oninput: () => { v.after = t.value; } }); return t; })()),
    err,
    el('div', { class: 'row', style: 'justify-content:flex-end;align-items:center' },
      el('span', { class: 'note' }, `Standing at x ${x}, y ${y} on ${W.map.name}. You can add more Pokémon in the Trainers tab after.`),
      el('button', { class: 'btn primary', onclick: async () => {
        if (!v.name.trim()) { err.replaceChildren(el('div', { class: 'warnbox' }, 'Give the trainer a name.')); return; }
        if (!index.species.has(speciesConst(v.species))) { err.replaceChildren(el('div', { class: 'warnbox' }, 'Pick a Pokémon from the list.')); return; }
        try {
          const res = await api('/api/trainer/new', { name: v.name, class: v.class, pic: v.pic, gender: v.gender, music: v.music,
            species: v.species, level: v.level, map: W.map.map, x, y, graphics_id: v.gfx, facing: v.facing, sight: v.sight,
            intro: v.intro, defeat: v.defeat, after: v.after });
          closeModal();
          W.mode = 'select';
          await loadGameData();
          await loadTrainerList();
          await openMap(W.map.map);
          W.tab = 'people';
          renderMapEditor();
          toast(`Added ${v.name}. Press “Edit team” to build their team.`);
          return res;
        } catch (e) { err.replaceChildren(el('div', { class: 'warnbox' }, e.message)); }
      } }, 'Add trainer')));
  openModal('New trainer', form);
}

// ---- shops ----------------------------------------------------------------------------------
function renderShopsPanel() {
  const out = el('div', {});
  if (!W.shops.length) {
    out.append(el('p', { class: 'note' }, 'There is no Poké Mart on this map. Shops are inside the Mart buildings; pick the Mart’s map on the left (try the “Shops” filter).'));
    return out;
  }
  out.append(el('p', { class: 'note' }, 'Prices are the same in every shop, so changing one here changes it everywhere.'));
  W.shops.forEach((sh, si) => {
    const rows = el('div', { class: 'rows' });
    sh.items.forEach((it, i) => {
      const input = el('input', { value: itemName(it), list: 'dl-items', class: 'grow',
        oninput: () => { sh.items[i] = itemConst(input.value); markMapDirty('shops'); } });
      const cur = W.priceChanges[it] ?? W.prices[it];
      const price = el('input', { type: 'number', min: 0, max: 999999, value: cur ?? '', class: 'price', placeholder: 'price', title: 'Price in ₽',
        oninput: () => { W.priceChanges[sh.items[i]] = price.value === '' ? null : parseInt(price.value, 10); markMapDirty('shops'); } });
      rows.append(el('div', { class: 'rowline' }, input, el('span', { class: 'note', style: 'margin:0' }, '₽'), price,
        el('button', { class: 'iconbtn', title: 'Up', onclick: () => { if (i) { [sh.items[i - 1], sh.items[i]] = [sh.items[i], sh.items[i - 1]]; markMapDirty('shops'); renderMapEditor(); } } }, '↑'),
        el('button', { class: 'iconbtn', title: 'Remove', onclick: () => { sh.items.splice(i, 1); markMapDirty('shops'); renderMapEditor(); } }, '✕')));
    });
    out.append(el('div', { class: 'card', style: 'padding:12px' },
      el('h3', {}, W.shops.length > 1 ? `Shop ${si + 1}: ${sh.label.replace(W.map.map + '_', '').replace(/_/g, ' ')}` : 'What the shop sells'),
      rows,
      el('button', { class: 'btn small', style: 'margin-top:8px', onclick: () => { sh.items.push('ITEM_POTION'); markMapDirty('shops'); renderMapEditor(); } }, '+ Add item')));
  });
  return out;
}

// ---- gifts and one-time encounters ---------------------------------------------------------
function renderGiftsPanel() {
  const out = el('div', {});
  if (!W.gifts.length) {
    out.append(el('p', { class: 'note' }, 'No gift Pokémon or one-time battles on this map. Try the “Gifts & legendaries” filter on the left. Starters are in the Pokémon data tab.'));
    return out;
  }
  out.append(el('p', { class: 'note' }, 'Gifts are Pokémon someone gives you. Battles are one-time encounters like legendaries. Changing the Pokémon also changes its cry and name in that scene.'));
  const rows = el('div', { class: 'rows' });
  W.gifts.forEach((g, i) => {
    const sprite = el('img', { src: imgUrl(index.species.get(g.species)?.img), alt: '' });
    const sp = el('input', { value: speciesName(g.species), list: 'dl-species', class: 'grow',
      oninput: () => { g.species = speciesConst(sp.value); sprite.src = imgUrl(index.species.get(g.species)?.img); W.giftChanged.add(i); markMapDirty('gifts'); } });
    const lv = g.level === null ? null : el('input', { type: 'number', min: 1, max: 100, value: g.level, class: 'lv', title: 'Level',
      oninput: () => { g.level = parseInt(lv.value, 10) || 1; W.giftChanged.add(i); markMapDirty('gifts'); } });
    const item = g.command === 'giveegg' ? null : el('input', { value: g.item ? itemName(g.item) : '', list: 'dl-items', placeholder: 'no held item', class: 'grow',
      oninput: () => { g.item = item.value ? itemConst(item.value) : ''; g.itemChanged = true; W.giftChanged.add(i); markMapDirty('gifts'); } });
    rows.append(el('div', { class: 'card', style: 'padding:10px' },
      el('div', { class: 'rowline' }, el('span', { class: 'kindtag ' + g.kind.toLowerCase() }, g.kind), sprite, sp, lv ? 'Lv' : null, lv),
      item ? el('div', { class: 'rowline', style: 'margin-top:6px' }, el('span', { class: 'note', style: 'margin:0' }, 'Holding'), item) : null));
  });
  out.append(rows);
  return out;
}

// ---- saving -------------------------------------------------------------------------------
async function savePerson() {
  const p = W.person;
  let scripts = [];
  if (W.pEdits.code !== undefined && W.pEdits.code !== personCode(p)) {
    const parts = splitPersonCode(p, W.pEdits.code);
    if (!parts) throw new Error('A script name (a line ending in “::”) was changed or removed. Put it back, or press Revert.');
    scripts = parts.map((x, i) => ({ label: x.label, before: p.scripts[i].code, code: x.code })).filter((x, i) => x.code !== p.scripts[i].code);
  }
  const texts = p.texts.filter(t => t.label in W.pEdits.texts && W.pEdits.texts[t.label] !== t.text)
    .map(t => ({ file: t.file, label: t.label, text: W.pEdits.texts[t.label] }));
  if (!scripts.length && !texts.length) return;
  await api('/api/map/person', { map: W.map.map, index: W.personIdx, file: p.file, scripts, texts });
}

async function saveMap() {
  const d = W.map;
  if (!W.dirty.size) { toast('Nothing to save.'); return; }
  if (W.dirty.has('person') && W.person && W.pEdits.code !== undefined && !splitPersonCode(W.person, W.pEdits.code)) {
    W.tab = 'people'; W.pView = 'code'; renderMapEditor();
    toast('A script name (a line ending in “::”) was changed or removed. Put it back, or press Revert.', true);
    return;
  }
  for (const it of W.items) {
    if (!index.items.has(it.item)) { W.tab = 'items'; W.sel = it; renderMapEditor(); toast('Pick an item from the list for every item on the map.', true); return; }
  }
  for (const e of W.wild) for (const [key] of WILD_SECTIONS) for (const m of (e[key]?.mons || [])) {
    if (!index.species.has(m.species)) { W.tab = 'wild'; renderMapEditor(); toast('Pick a Pokémon from the list for every wild slot.', true); return; }
  }
  for (const sh of W.shops) for (const it of sh.items) {
    if (!index.items.has(it)) { W.tab = 'shops'; renderMapEditor(); toast('Pick an item from the list for every shop slot.', true); return; }
  }
  for (const g of W.gifts) {
    if (!index.species.has(g.species)) { W.tab = 'gifts'; renderMapEditor(); toast('Pick a Pokémon from the list for every gift.', true); return; }
    if (g.item && !index.items.has(g.item)) { W.tab = 'gifts'; renderMapEditor(); toast('Pick a held item from the list.', true); return; }
  }
  try {
    if (W.dirty.has('items')) await api('/api/map/items', { map: d.map, items: W.items, moves: W.moves });
    if (W.dirty.has('person') && W.person) await savePerson();
    if (W.dirty.has('wild')) await api('/api/wild', { id: d.id, map: d.map, entries: W.wild });
    if (W.dirty.has('shops')) {
      for (const sh of W.shops) {
        const prices = {};
        for (const it of sh.items) if (it in W.priceChanges) prices[it] = W.priceChanges[it];
        await api('/api/shop', { file: sh.file, label: sh.label, items: sh.items, prices });
      }
    }
    if (W.dirty.has('gifts')) {
      for (const i of W.giftChanged) {
        const g = W.gifts[i];
        await api('/api/gift', { file: g.file, line: g.line, expect: g.text, species: g.species, level: g.level, item: g.itemChanged ? g.item : null });
      }
    }
    if (W.dirty.has('door') && W.doorEdit?.dest && W.doorEdit.warps?.length) {
      await api('/api/map/warp', { map: d.map, index: W.door, dest: W.doorEdit.dest, destWarp: W.doorEdit.destWarp, both: W.doorEdit.both });
    }
    if (W.dirty.has('sign') && signTexts().length) await api('/api/map/sign', { map: d.map, index: W.sign, texts: signTexts() });
    const keepDoor = W.door, keepSign = W.sign, keepTab = W.tab;
    W.dirty.clear();
    await openMap(d.map);
    if (keepTab === 'doors') {
      if (keepDoor !== null && keepDoor !== undefined) await openDoor(keepDoor);
      else if (keepSign !== null && keepSign !== undefined) await openSign(keepSign);
      else { W.tab = 'doors'; renderMapEditor(); }
    }
    W.list = await api('/api/maps');
    renderMapList();
    toast('Saved. Press Play to try it.');
  } catch (e) {
    toast(e.message, true);
    // something may already be saved: show what is on disk now
    W.dirty.clear();
    openMap(d.map);
  }
}

$('#mapSearch').addEventListener('input', debounce(renderMapList, 150));
$('#mapFilter').addEventListener('change', renderMapList);

views.maps = {
  isDirty: () => W.dirty.size > 0,
  save: saveMap,
  onShow: async () => {
    if (W.list) return;
    try {
      await loadMapList();
      let last = null;
      try { last = localStorage.getItem('emerald.map'); } catch (e) { /* ignore */ }
      const first = W.list.find(m => m.map === last) || W.list.find(m => m.map === 'Route102') || W.list[0];
      if (first) openMap(first.map);
    } catch (e) { $('#mapList').replaceChildren(el('div', { class: 'warnbox' }, e.message)); }
  },
};

// ---- doors and signs ---------------------------------------------------------------------------
async function openDoor(idx) {
  W.tab = 'doors';
  W.door = idx;
  W.sign = null;
  const w = W.map.warps.find(x => x.index === idx);
  W.doorEdit = { dest: w.toFolder || '', destWarp: w.toWarp, both: false, warps: null };
  renderMapEditor();
  if (w.toFolder) await loadDoorTargets(w.toFolder);
}

async function loadDoorTargets(folder) {
  try {
    const list = await api('/api/map/warps?map=' + encodeURIComponent(folder));
    if (W.doorEdit && W.doorEdit.dest === folder) { W.doorEdit.warps = list; renderMapEditor(); }
  } catch (e) { toast(e.message, true); }
}

async function openSign(idx) {
  if (W.dirty.has('sign') && W.sign !== idx && !confirm('You have unsaved changes to this sign. Throw them away?')) return;
  W.dirty.delete('sign');
  W.tab = 'doors';
  W.sign = idx;
  W.door = null;
  W.signData = null;
  W.signEdits = {};
  renderMapEditor();
  try { W.signData = await api(`/api/map/sign?map=${encodeURIComponent(W.map.map)}&index=${idx}`); } catch (e) { toast(e.message, true); }
  renderMapEditor();
}

// Opens the map a door, ladder or stairs leads to, with the door you come out of picked.
async function goThroughDoor(w) {
  if (!w.toFolder) return;
  const from = W.map.map;
  await openMap(w.toFolder, false);
  if (W.map?.map !== w.toFolder) return;   // stayed (unsaved changes kept)
  const back = W.map.warps.find(x => x.index === w.toWarp) || W.map.warps.find(x => x.toFolder === from);
  if (back) await openDoor(back.index);
  const mk = document.querySelector('.mk.warp.sel');
  if (mk) mk.scrollIntoView({ block: 'center', inline: 'center' });
}

function renderDoorCard() {
  const w = W.map.warps.find(x => x.index === W.door);
  if (!w) return null;
  const ed = W.doorEdit;
  const mapSel = el('select', { class: 'grow', onchange: () => { ed.dest = mapSel.value; ed.destWarp = 0; ed.warps = null; markMapDirty('door'); renderMapEditor(); loadDoorTargets(ed.dest); } },
    w.toFolder ? null : el('option', { value: '' }, w.toName ? `(${w.toName})` : '(pick a map)'),
    (W.list || []).map(m => el('option', { value: m.map, selected: m.map === ed.dest }, m.name)));
  const warpSel = el('select', { onchange: () => { ed.destWarp = parseInt(warpSel.value, 10); markMapDirty('door'); } },
    (ed.warps || []).map(t => el('option', { value: t.index, selected: t.index === ed.destWarp }, `Door ${t.index + 1} (x ${t.x}, y ${t.y})${t.toName ? ' – leads to ' + t.toName : ''}`)));
  const both = el('input', { type: 'checkbox', checked: ed.both, onchange: () => { ed.both = both.checked; markMapDirty('door'); } });
  return el('div', { class: 'card personcard', style: 'padding:12px' },
    el('div', { class: 'rowline', style: 'margin-bottom:8px' },
      el('div', { class: 'grow' }, el('h3', { style: 'margin:0' }, `Door ${w.index + 1}`), el('div', { class: 'note', style: 'margin:0' }, `x ${w.x}, y ${w.y} · leads to ${w.toName || 'nowhere yet'}`)),
      el('button', { class: 'iconbtn', title: 'Close', onclick: () => { W.door = null; W.dirty.delete('door'); renderMapEditor(); } }, '✕')),
    w.toFolder ? el('button', { class: 'btn primary', style: 'width:100%;margin:4px 0 10px', title: 'Open the map this leads to (or double-click the door on the map)', onclick: () => goThroughDoor(w) }, `Go to ${w.toName} →`) : null,
    w.to === 'MAP_DYNAMIC' ? el('p', { class: 'note' }, 'This door takes the player back to wherever they came in from (like the exit of a Pokémon Center). You can point it at a fixed place instead.') : null,
    el('label', { class: 'field' }, el('span', {}, 'Leads to the map'), mapSel),
    el('label', { class: 'field' }, el('span', {}, 'Comes out at'), ed.dest ? (ed.warps ? warpSel : el('span', { class: 'note' }, 'Loading its doors…')) : el('span', { class: 'note' }, 'Pick a map first.')),
    el('label', { class: 'row', style: 'gap:8px;margin-top:6px' }, both, 'Also make that door lead back here'),
    el('p', { class: 'note' }, 'The player comes out standing on the door you pick.'),
    el('div', { class: 'row', style: 'justify-content:flex-end' },
      el('button', { class: 'btn primary small', disabled: !ed.dest || !ed.warps || !ed.warps.length, onclick: saveDoor }, 'Save door')));
}

async function saveDoor() { await saveMap(); }

function renderSignCard() {
  const sg = (W.map.signs || []).find(x => x.index === W.sign);
  if (!sg) return null;
  const p = W.signData;
  const card = el('div', { class: 'card personcard', style: 'padding:12px' },
    el('div', { class: 'rowline', style: 'margin-bottom:8px' },
      el('div', { class: 'grow' }, el('h3', { style: 'margin:0' }, 'Sign'), el('div', { class: 'note', style: 'margin:0' }, `x ${sg.x}, y ${sg.y}`)),
      el('button', { class: 'iconbtn', title: 'Close', onclick: () => { if (W.dirty.has('sign') && !confirm('Throw away your changes to this sign?')) return; W.sign = null; W.dirty.delete('sign'); renderMapEditor(); } }, '✕')));
  if (!p) { card.append(el('div', { class: 'note' }, 'Loading…')); return card; }
  if (!p.texts.length) { card.append(el('div', { class: 'note' }, 'This sign has no words of its own (it runs a special script). You can change that in the Scripts tab.')); return card; }
  for (const t of p.texts) {
    const preview = el('div', { class: 'boxes' });
    const ta = el('textarea', { class: 'short', value: W.signEdits[t.label] ?? t.text,
      oninput: () => { W.signEdits[t.label] = ta.value; markMapDirty('sign'); renderBoxes(ta.value, preview); } });
    renderBoxes(ta.value, preview);
    card.append(el('div', { class: 'persontext' }, el('div', { class: 'boxlabel' }, textTitle(t.label)), el('div', { class: 'textedit' }, ta, preview)));
  }
  if (p.usedBy > 1) card.append(el('div', { class: 'note' }, 'Other signs use the same words, so they change too.'));
  card.append(el('div', { class: 'row', style: 'justify-content:flex-end' },
    el('button', { class: 'btn primary small', onclick: saveSign }, 'Save sign')));
  return card;
}

async function saveSign() { await saveMap(); }

function signTexts() {
  const p = W.signData;
  if (!p) return [];
  return p.texts.filter(t => W.signEdits[t.label] !== undefined && W.signEdits[t.label] !== t.text)
    .map(t => ({ file: t.file, label: t.label, text: W.signEdits[t.label] }));
}

function renderDoorsPanel() {
  const out = el('div', {});
  const card = W.door !== null && W.door !== undefined ? renderDoorCard() : W.sign !== null && W.sign !== undefined ? renderSignCard() : null;
  if (card) out.append(card);
  else out.append(el('p', { class: 'note' }, 'Click a door, ladder or stairs (blue square) or a sign (✎) on the map, or pick one below. Double-click a door to go straight through it.'));
  const doors = W.map.warps.map(w => el('div', { class: 'rowline mapitem' + (W.door === w.index ? ' sel' : ''), style: 'cursor:pointer', onclick: () => openDoor(w.index) },
    el('span', { class: 'kindtag ball' }, 'Door ' + (w.index + 1)),
    el('div', { class: 'grow' }, 'to ' + (w.toName || '?')),
    el('span', { class: 'note', style: 'margin:0' }, `x ${w.x}, y ${w.y}`),
    w.toFolder ? el('button', { class: 'btn small', title: 'Go to ' + w.toName, onclick: e => { e.stopPropagation(); goThroughDoor(w); } }, 'Go →') : null));
  out.append(el('h3', { class: 'sectionhead' }, 'Doors and exits'), doors.length ? el('div', { class: 'rows' }, doors) : el('p', { class: 'note' }, 'No doors on this map.'));
  const signs = (W.map.signs || []).map(sg => el('div', { class: 'rowline mapitem' + (W.sign === sg.index ? ' sel' : ''), style: 'cursor:pointer', onclick: () => openSign(sg.index) },
    el('span', { class: 'kindtag hid' }, 'Sign'), el('div', { class: 'grow' }, camelWords(sg.script.replace(/^.*_EventScript_/, ''))),
    el('span', { class: 'note', style: 'margin:0' }, `x ${sg.x}, y ${sg.y}`)));
  out.append(el('h3', { class: 'sectionhead' }, 'Signs'), signs.length ? el('div', { class: 'rows' }, signs) : el('p', { class: 'note' }, 'No signs on this map.'));
  return out;
}
