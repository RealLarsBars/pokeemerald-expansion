'use strict';
// ---------------------------------------------------------------------------
// Pokemon data extras: the three starters, which move each TM and HM teaches,
// and each Pokemon's TM / tutor / egg moves. Uses the helpers in app.js.
// ---------------------------------------------------------------------------
const L = { tms: null };

function moveName(c) { return prettyFromConst('MOVE', c); }

// ---- starters ------------------------------------------------------------------------------
async function openStarters() {
  if (P.dirty && !confirm('You have unsaved changes to this Pokémon. Throw them away?')) return;
  P.dirty = false;
  P.current = null;
  renderSpeciesList();
  const root = $('#speciesEditor');
  let data;
  try { data = await api('/api/starters'); } catch (e) { toast(e.message, true); return; }
  const names = data.species.map(c => index.species.get(c)?.name || c);
  let level = data.level;
  const dirty = el('span', { class: 'dirty' });
  const mark = () => { dirty.textContent = 'Unsaved changes'; };
  const cards = names.map((n, i) => {
    const img = el('img', { class: 'sprite', src: imgUrl(index.species.get(data.species[i])?.img), alt: '' });
    const input = el('input', { value: n, list: 'dl-species', oninput: () => {
      names[i] = input.value;
      img.src = imgUrl(index.species.get(speciesConst(input.value))?.img);
      mark();
    } });
    return el('div', { class: 'mon starter' }, img, el('label', { class: 'field' }, el('span', {}, ['Left ball', 'Middle ball', 'Right ball'][i]), input));
  });
  const lv = el('input', { type: 'number', min: 1, max: 100, value: level, oninput: () => { level = parseInt(lv.value, 10) || 5; mark(); } });
  const save = async () => {
    const consts = names.map(speciesConst);
    if (consts.some(c => !index.species.has(c))) { toast('Pick a Pokémon from the list for every ball.', true); return; }
    try {
      await api('/api/starters', { species: consts, level });
      dirty.textContent = '';
      toast('Saved. Start a new game to pick from the new starters.');
    } catch (e) { toast(e.message, true); }
  };
  root.replaceChildren(
    el('div', { class: 'savebar' }, el('h2', {}, 'Starter Pokémon'), dirty, el('button', { class: 'btn primary', onclick: save }, 'Save')),
    el('div', { class: 'card' },
      el('p', { class: 'note' }, 'The three Pokémon in Prof. Birch’s bag on Route 101. The rival picks the one that is strong against yours, using their teams in the Trainers tab (May and Brendan).'),
      el('div', { class: 'party' }, cards),
      el('label', { class: 'field', style: 'max-width:200px;margin-top:12px' }, el('span', {}, 'Starting level'), lv)));
}

// ---- the TM and HM list --------------------------------------------------------------------
async function openTmList() {
  if (P.dirty && !confirm('You have unsaved changes to this Pokémon. Throw them away?')) return;
  P.dirty = false;
  P.current = null;
  renderSpeciesList();
  let data;
  try { data = await api('/api/moves/tms'); } catch (e) { toast(e.message, true); return; }
  const tms = data.tms.slice(), hms = data.hms.slice();
  const dirty = el('span', { class: 'dirty' });
  const mark = () => { dirty.textContent = 'Unsaved changes'; };
  const list = (arr, prefix) => {
    const box = el('div', { class: 'tmgrid' });
    const draw = () => box.replaceChildren(...arr.map((m, i) => {
      const input = el('input', { value: moveName(m), list: 'dl-moves', oninput: () => { arr[i] = toConst('MOVE', input.value); mark(); } });
      return el('div', { class: 'rowline tight' }, el('span', { class: 'tmno' }, `${prefix}${String(i + 1).padStart(2, '0')}`), input);
    }));
    draw();
    return box;
  };
  const tmBox = list(tms, 'TM');
  const hmBox = list(hms, 'HM');
  const save = async () => {
    const all = tms.concat(hms);
    if (all.some(m => !index.moves.has(m))) { toast('Pick a move from the list for every TM and HM.', true); return; }
    if (new Set(all).size !== all.length) { toast('A move can only be on one TM or HM.', true); return; }
    try {
      await api('/api/moves/tms', { tms, hms });
      dirty.textContent = '';
      toast('Saved. Which Pokémon can learn each TM is worked out when the game is built.');
    } catch (e) { toast(e.message, true); }
  };
  $('#speciesEditor').replaceChildren(
    el('div', { class: 'savebar' }, el('h2', {}, 'TMs and HMs'), dirty, el('button', { class: 'btn primary', onclick: save }, 'Save')),
    el('div', { class: 'card' },
      el('p', { class: 'note' }, 'Which move each TM and HM teaches. A Pokémon can use a TM if that move is ticked on its page (TMs, tutors and egg moves). Shops sell TMs by number, so changing TM05 changes what the TM05 in shops and on the ground teaches.'),
      el('p', { class: 'note' }, 'The TM\u2019s description in the bag changes to match its new move. People who talk about a TM (\u201cTM08 contains Bulk Up\u201d) are in the Dialogue tab.'),
      el('h3', {}, 'TMs'), tmBox,
      el('h3', { style: 'margin-top:16px' }, 'HMs'), hmBox));
}

// ---- one Pokemon's TM, tutor and egg moves --------------------------------------------------
function teachCard(speciesId) {
  const card = el('div', { class: 'card' }, el('h3', {}, 'TMs, tutors and egg moves'), el('div', { class: 'note' }, 'Loading...'));
  (async () => {
    let data;
    try { data = await api('/api/moves/species?id=' + encodeURIComponent(speciesId)); } catch (e) { card.lastChild.textContent = e.message; return; }
    if (P.current?.id !== speciesId) return;
    drawTeach(card, speciesId, data);
  })();
  return card;
}

function drawTeach(card, speciesId, data) {
  const t = data.teach;
  const learns = new Set(t.learns);
  const universal = new Set(t.universal);
  const allTeach = t.teachingType === 'ALL_TEACHABLES';
  const add = new Set(), remove = new Set();
  const egg = data.egg.moves.slice();
  let eggDirty = false;
  const dirty = el('span', { class: 'dirty' });
  const mark = () => { dirty.textContent = 'Unsaved'; };
  const box = (title, moves, prefix) => {
    if (!moves.length) return null;
    const q = el('div', { class: 'tmchecks' }, moves.map((m, i) => {
      const always = allTeach || (universal.has(m) && t.teachingType !== 'TM_ILLITERATE');
      const cb = el('input', { type: 'checkbox', checked: always || learns.has(m), disabled: always || !t.editable,
        onchange: () => {
          if (cb.checked) { add.add(m); remove.delete(m); } else { remove.add(m); add.delete(m); }
          mark();
        } });
      return el('label', { class: 'check tm' + (always ? ' always' : ''), title: always ? 'Every Pokémon can learn this one' : '' }, cb,
        prefix ? el('span', { class: 'tmno' }, `${prefix}${String(i + 1).padStart(2, '0')}`) : null, moveName(m));
    }));
    return el('div', {}, el('div', { class: 'rowline', style: 'margin:10px 0 4px' }, el('b', {}, title),
      t.editable && !allTeach ? el('button', { class: 'btn small ghost', onclick: () => { q.querySelectorAll('input:not(:disabled)').forEach(cb => { if (!cb.checked) { cb.checked = true; cb.dispatchEvent(new Event('change')); } }); } }, 'Tick all') : null,
      t.editable && !allTeach ? el('button', { class: 'btn small ghost', onclick: () => { q.querySelectorAll('input:not(:disabled)').forEach(cb => { if (cb.checked) { cb.checked = false; cb.dispatchEvent(new Event('change')); } }); } }, 'Untick all') : null), q);
  };
  const eggRows = el('div', { class: 'rows' });
  const drawEgg = () => eggRows.replaceChildren(...egg.map((m, i) => el('div', { class: 'rowline tight' },
    el('input', { class: 'grow', value: moveName(m), list: 'dl-moves', oninput: e => { egg[i] = toConst('MOVE', e.target.value); eggDirty = true; mark(); } }),
    el('button', { class: 'iconbtn', title: 'Remove', onclick: () => { egg.splice(i, 1); eggDirty = true; mark(); drawEgg(); } }, '✕'))));
  drawEgg();
  const save = async () => {
    const body = { id: speciesId };
    if (add.size || remove.size) { body.add = [...add]; body.remove = [...remove]; }
    if (eggDirty) {
      if (egg.some(m => !index.moves.has(m))) { toast('Pick a move from the list for every egg move.', true); return; }
      body.egg = egg;
    }
    if (Object.keys(body).length === 1) { toast('Nothing to save.'); return; }
    try {
      const res = await api('/api/moves/species', body);
      drawTeach(card, speciesId, res);
      toast('Saved. Press Play to try it.');
    } catch (e) { toast(e.message, true); }
  };
  card.replaceChildren(
    el('div', { class: 'rowline', style: 'margin-bottom:6px' }, el('h3', { style: 'margin:0;flex:1' }, 'TMs, tutors and egg moves'), dirty,
      el('button', { class: 'btn small primary', onclick: save }, 'Save these')),
    el('div', { class: 'note' }, allTeach ? 'This Pokémon can learn every TM and tutor move.'
      : t.editable ? 'Tick the moves this Pokémon can learn. This is saved on its own with “Save these”.' : 'This form shares its moves with another form, so they can’t be changed here.'),
    box('TMs', t.tms, 'TM'), box('HMs', t.hms, 'HM'), box('Move tutors', t.tutors, ''),
    el('div', { class: 'rowline', style: 'margin:14px 0 4px' }, el('b', {}, 'Egg moves')),
    data.egg.editable ? eggRows : el('div', { class: 'note' }, 'Only the first Pokémon in an evolution line has egg moves.'),
    data.egg.editable ? el('button', { class: 'btn small', style: 'margin-top:8px', onclick: () => { egg.push(''); eggDirty = true; mark(); drawEgg(); } }, '+ Add egg move') : null);
}

// Add the card to the bottom of every Pokemon's page.
const _renderSpeciesBase = renderSpecies;
renderSpecies = function () {
  _renderSpeciesBase();
  const d = P.current;
  if (d && d.editable !== false && d.baseHP) $('#speciesEditor').append(teachCard(d.id));
};

$('#startersBtn').addEventListener('click', openStarters);
$('#tmListBtn').addEventListener('click', openTmList);
