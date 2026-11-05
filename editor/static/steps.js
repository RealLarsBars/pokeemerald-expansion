'use strict';
// ---------------------------------------------------------------------------
// Scripts, simple view: every script in the file as a list of steps in plain
// words, with boxes to change them. The code view (the text box) stays the
// real file; this view reads it and writes back only the lines you change.
// Uses the helpers in app.js (S, el, api, INSERTS, openInsertForm...).
// ---------------------------------------------------------------------------
S.view = (() => { try { return localStorage.getItem('emerald.scriptView') || 'steps'; } catch (e) { return 'steps'; } })();

const LABEL_LINE = /^([A-Za-z_]\w*)::?\s*(?:@.*)?$/;
const PLAIN_STEPS = {
  lock: 'Stop the player from moving', lockall: 'Stop everyone from moving',
  release: 'Let the player move again', releaseall: 'Let everyone move again',
  faceplayer: 'Turn to face the player', end: 'End', return: 'Go back to where this was called from',
  waitmessage: 'Wait for the message to finish', closemessage: 'Close the message box',
  waitmovement: 'Wait until everyone has finished moving', waitstate: 'Wait', waitfanfare: 'Wait for the jingle to finish',
  waitse: 'Wait for the sound to finish', waitbuttonpress: 'Wait for a button press', checkplayergender: 'Check if the player is a boy or girl',
  showmoneybox: 'Show the money box', hidemoneybox: 'Hide the money box', fadedefaultbgm: 'Go back to the map’s music',
  savebgm: 'Remember the music', pokemart: 'Open the shop',
};
const MSG_KIND = { MSGBOX_NPC: 'says', MSGBOX_DEFAULT: 'shows', MSGBOX_SIGN: 'sign reads', MSGBOX_AUTOCLOSE: 'shows (closes by itself)', MSGBOX_YESNO: 'asks (Yes/No)' };

function scriptLines() { return S.textarea.value.split('\n'); }
function setScriptLines(lines) {
  S.textarea.value = lines.join('\n');
  S.textarea.dispatchEvent(new Event('input'));
}

function splitArgs(rest) {
  const out = [];
  let depth = 0, cur = '';
  for (const ch of rest) {
    if (ch === '(') depth++;
    if (ch === ')') depth--;
    if (ch === ',' && !depth) { out.push(cur.trim()); cur = ''; } else cur += ch;
  }
  if (cur.trim()) out.push(cur.trim());
  return out;
}

function parseScriptFile(lines) {
  const blocks = [];
  let cur = null;
  lines.forEach((line, i) => {
    const m = line.match(LABEL_LINE);
    if (m) { cur = { label: m[1], line: i, steps: [], kind: null }; blocks.push(cur); return; }
    if (!cur) return;
    const body = line.replace(/\s*@.*$/, '').trim();
    if (!body || body.startsWith('.align')) return;
    const sm = body.match(/^(\.?\w+)\s*(.*)$/);
    if (!sm) return;
    const step = { line: i, cmd: sm[1], args: splitArgs(sm[2]), comment: (line.match(/\s*(@.*)$/) || [])[1] || '' };
    if (!cur.kind) cur.kind = step.cmd === '.string' ? 'text' : step.cmd === '.2byte' ? 'list' : (step.cmd.startsWith('.') || step.cmd === 'map_script' || step.cmd === 'map_script_2') ? 'mapscripts' : /^(walk|face|step|delay_|jump|run|slide|emote|lock_facing|unlock_facing|set_|enable_|disable_|ride_|player_run|walk_in_place|go_|nurse|fly_|levitate|figure_8|store_|restore_|init_)/.test(step.cmd) ? 'movement' : 'script';
    cur.steps.push(step);
  });
  return blocks;
}

function textOf(blocks, label) {
  const b = blocks.find(x => x.label === label && x.kind === 'text');
  if (!b) return null;
  const raw = b.steps.map(s => (s.args.join(', ').match(/^"(.*)"$/) || [])[1] || '').join('');
  return raw.replace(/\$$/, '').replace(/\\p/g, '\n\n').replace(/\\[nl]/g, '\n').replace(/\\"/g, '"');
}

function writeText(label, friendly) {
  const lines = scriptLines();
  const blocks = parseScriptFile(lines);
  const b = blocks.find(x => x.label === label && x.kind === 'text');
  if (!b) return;
  const first = b.steps[0].line, last = b.steps[b.steps.length - 1].line;
  const fresh = textBlock(label, friendly).split('\n').slice(1);
  lines.splice(first, last - first + 1, ...fresh);
  setScriptLines(lines);
}

function rewriteStep(step, args) {
  const lines = scriptLines();
  const indent = (lines[step.line].match(/^\s*/) || ['\t'])[0] || '\t';
  lines[step.line] = `${indent}${step.cmd}${args.length ? ' ' + args.join(', ') : ''}${step.comment ? ' ' + step.comment : ''}`;
  step.args = args;
  setScriptLines(lines);
}

function moveStep(step, block, d) {
  const lines = scriptLines();
  const i = block.steps.indexOf(step);
  const other = block.steps[i + d];
  if (!other) return;
  [lines[step.line], lines[other.line]] = [lines[other.line], lines[step.line]];
  setScriptLines(lines);
  renderSteps();
}

function deleteStep(step) {
  const lines = scriptLines();
  lines.splice(step.line, 1);
  setScriptLines(lines);
  renderSteps();
}

function addStepAfter(step) {
  const ta = S.textarea;
  const lines = scriptLines();
  ta.selectionStart = ta.selectionEnd = lines.slice(0, step.line + 1).join('\n').length + 1;
  const pick = el('div', { class: 'stepkinds' }, Object.entries(INSERTS).filter(([k]) => k !== 'newscript').map(([k, v]) =>
    el('button', { class: 'btn', onclick: () => { closeModal(); openInsertForm(k); } }, v.title)));
  openModal('Add a step', pick);
}

// --- one line per step, in plain words, with boxes to change it -------------------------------
function stepView(step, blocks, block) {
  const a = step.args;
  const box = el('div', { class: 'stepbody' });
  const say = (...parts) => box.append(el('div', { class: 'stepsay' }, ...parts));
  const pickInput = (value, list, toArg, i, cls = 'grow') => {
    const input = el('input', { class: cls, value, list, oninput: () => { const v = a.slice(); v[i] = toArg(input.value); rewriteStep(step, v); } });
    return input;
  };
  const numInput = (i, min = 0, max = 9999) => {
    const input = el('input', { type: 'number', class: 'lv', min, max, value: parseInt(a[i], 10) || 0,
      oninput: () => { const v = a.slice(); v[i] = String(parseInt(input.value, 10) || 0); rewriteStep(step, v); } });
    return input;
  };
  const textEditor = label => {
    const t = textOf(blocks, label);
    if (t === null) return el('div', { class: 'note' }, `Text ${label} is in another file (find it in the Dialogue tab).`);
    const ta = el('textarea', { class: 'steptext', value: t, oninput: () => { writeText(label, ta.value); renderBoxes(ta.value, preview); } });
    const preview = el('div', { class: 'boxes' });
    renderBoxes(t, preview);
    return el('div', { class: 'steptextwrap' }, ta, preview);
  };
  const jump = label => el('a', { href: '#', class: 'steplink', onclick: e => { e.preventDefault(); document.getElementById('step-' + label)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); } }, label);
  const c = step.cmd;
  if (c === 'msgbox' || c === 'message') {
    const kind = el('select', { onchange: () => { const v = a.slice(); v[1] = kind.value; rewriteStep(step, v); } },
      Object.keys(MSG_KIND).map(k => el('option', { value: k, selected: a[1] === k }, MSG_KIND[k])));
    say('💬 ', c === 'msgbox' ? kind : 'shows', ':');
    box.append(textEditor(a[0]));
  } else if (/^trainerbattle/.test(c)) {
    const t = T.list?.find(x => x.id === a[0]);
    say('⚔️ Battle with ', el('b', {}, t ? `${t.class} ${t.name}` : a[0]), ' ',
      t ? el('button', { class: 'btn small', onclick: () => { showView('trainers'); openTrainer(a[0]); } }, 'Edit team') : null);
    const texts = c === 'trainerbattle_no_intro' ? [['When they lose', a[1]]] : [['Before the battle', a[1]], ['When they lose', a[2]]];
    for (const [title, label] of texts) if (label && /^\w+$/.test(label)) box.append(el('div', { class: 'boxlabel' }, title), textEditor(label));
  } else if (['giveitem', 'finditem', 'additem', 'removeitem', 'checkitem', 'checkitemspace'].includes(c)) {
    const verb = { giveitem: 'Give', finditem: 'Find', additem: 'Quietly give', removeitem: 'Take away', checkitem: 'Check the bag for', checkitemspace: 'Check there is room for' }[c];
    say('🎒 ', verb, ' ', a[1] !== undefined ? numInput(1, 1, 999) : null, a[1] !== undefined ? ' × ' : '', pickInput(prettyFromConst('ITEM', a[0]), 'dl-items', v => toConst('ITEM', v), 0));
  } else if (c === 'givemon' && /^SPECIES_/.test(a[0])) {
    say('🥚 Give the Pokémon ', pickInput(index.species.get(a[0])?.name || a[0], 'dl-species', speciesConst, 0), ' at level ', numInput(1, 1, 100));
  } else if (c === 'setwildbattle' && /^SPECIES_/.test(a[0])) {
    say('🐾 Get ready to battle a wild ', pickInput(index.species.get(a[0])?.name || a[0], 'dl-species', speciesConst, 0), ' at level ', numInput(1, 1, 100));
  } else if (c === 'setflag' || c === 'clearflag') {
    say(c === 'setflag' ? '✅ Remember that ' : '❌ Forget ', pickInput(a[0], 'dl-flags', v => v.trim(), 0));
  } else if (/^(goto|call)_if_(set|unset)$/.test(c)) {
    say('❓ If ', el('code', {}, a[0]), c.endsWith('_unset') ? ' has NOT happened' : ' has happened', c.startsWith('goto') ? ', go to ' : ', run ', jump(a[1]));
  } else if (/^(goto|call)_if_(eq|ne|lt|ge|le|gt)$/.test(c)) {
    const op = { eq: 'is', ne: 'is not', lt: 'is less than', ge: 'is at least', le: 'is at most', gt: 'is more than' }[c.split('_').pop()];
    say('❓ If ', el('code', {}, a[0]), ` ${op} `, el('code', {}, a[1]), c.startsWith('goto') ? ', go to ' : ', run ', jump(a[2]));
  } else if (c === 'goto' || c === 'call') {
    say(c === 'goto' ? '➡️ Go to ' : '↪️ Run ', jump(a[0]));
  } else if (c === 'warp' || c === 'warpsilent' || c === 'warpdoor' || c === 'warpteleport') {
    const sel = el('select', { onchange: () => { const v = a.slice(); v[0] = sel.value; rewriteStep(step, v); } },
      GD.maps.map(m => el('option', { value: m.const, selected: m.const === a[0] }, m.name)));
    say('🚪 Take the player to ', sel, a.length >= 3 ? ' at x ' : '', a.length >= 3 ? numInput(a.length - 2) : null, a.length >= 3 ? ' y ' : '', a.length >= 3 ? numInput(a.length - 1) : null);
  } else if (c === 'special' && a[0] === 'HealPlayerParty') {
    say('❤️ Heal the player’s Pokémon');
  } else if (c === 'delay') {
    say('⏳ Wait ', numInput(0, 1, 999), ' frames (60 = one second)');
  } else if (c === 'setvar') {
    say('🔢 Set ', el('code', {}, a[0]), ' to ', el('code', {}, a[1]));
  } else if (c === 'applymovement') {
    say('🚶 Move ', el('code', {}, a[0] === 'LOCALID_PLAYER' || a[0] === 'OBJ_EVENT_ID_PLAYER' ? 'the player' : a[0]), ' using ', jump(a[1]));
  } else if (c === 'removeobject' || c === 'addobject') {
    say(c === 'removeobject' ? '👻 Hide ' : '👤 Show ', el('code', {}, a[0]));
  } else if (c === 'playse' || c === 'playfanfare' || c === 'playbgm' || c === 'playmoncry') {
    say('🎵 Play ', el('code', {}, a.join(', ')));
  } else if (PLAIN_STEPS[c]) {
    say(PLAIN_STEPS[c]);
  } else {
    const raw = el('input', { class: 'grow rawline', value: [c, a.join(', ')].filter(Boolean).join(' '),
      onchange: () => { const lines = scriptLines(); lines[step.line] = '\t' + raw.value.trim() + (step.comment ? ' ' + step.comment : ''); setScriptLines(lines); renderSteps(); } });
    box.append(el('div', { class: 'stepsay' }, raw));
  }
  return el('div', { class: 'step' }, box,
    el('div', { class: 'steptools' },
      el('button', { class: 'iconbtn', title: 'Move up', onclick: () => moveStep(step, block, -1) }, '↑'),
      el('button', { class: 'iconbtn', title: 'Move down', onclick: () => moveStep(step, block, 1) }, '↓'),
      el('button', { class: 'iconbtn', title: 'Add a step after this one', onclick: () => addStepAfter(step) }, '+'),
      el('button', { class: 'iconbtn', title: 'Delete this step', onclick: () => { if (confirm('Delete this step?')) deleteStep(step); } }, '✕')));
}

function renderSteps() {
  const holder = document.getElementById('scriptSteps');
  if (!holder || !S.textarea) return;
  const keep = $('#scriptEditor').scrollTop;
  const blocks = parseScriptFile(scriptLines());
  const scripts = blocks.filter(b => b.kind === 'script' || (b.kind === null));
  const moves = blocks.filter(b => b.kind === 'movement');
  const lists = blocks.filter(b => b.kind === 'list');
  const hooks = blocks.filter(b => b.kind === 'mapscripts').flatMap(b => b.steps.filter(st => st.cmd === 'map_script'));
  const WHEN = { MAP_SCRIPT_ON_TRANSITION: 'When the player arrives', MAP_SCRIPT_ON_LOAD: 'When the map is drawn', MAP_SCRIPT_ON_FRAME_TABLE: 'Every moment, if something is true',
    MAP_SCRIPT_ON_WARP_INTO_MAP_TABLE: 'Right after arriving, if something is true', MAP_SCRIPT_ON_RESUME: 'When coming back from a menu or battle', MAP_SCRIPT_ON_RETURN_TO_FIELD: 'When returning to the map' };
  const cards = scripts.map(b => el('div', { class: 'card stepcard', id: 'step-' + b.label },
    el('h3', {}, b.label.replace(/^.*?_EventScript_/, '').replace(/^.*?_OnTransition$/, 'When you enter the map').replace(/([a-z])([A-Z])/g, '$1 $2'), el('span', { class: 'idtag' }, b.label)),
    b.steps.length ? b.steps.map(s => stepView(s, blocks, b)) : el('div', { class: 'note' }, 'Empty.')));
  const extra = [];
  if (hooks.length) extra.unshift(el('div', { class: 'card' }, el('h3', {}, 'Runs by itself'),
    hooks.map(h => el('div', { class: 'stepsay' }, (WHEN[h.args[0]] || h.args[0]) + ': ', document.getElementById('step-' + h.args[1]) || blocks.some(b => b.label === h.args[1] && b.kind === 'script') ? el('a', { href: '#', class: 'steplink', onclick: e => { e.preventDefault(); document.getElementById('step-' + h.args[1])?.scrollIntoView({ behavior: 'smooth' }); } }, h.args[1]) : el('code', {}, h.args[1])))));
  if (moves.length) extra.push(el('div', { class: 'card' }, el('h3', {}, 'Movements'),
    moves.map(b => el('div', { class: 'stepsay', id: 'step-' + b.label }, el('code', {}, b.label), ': ', b.steps.map(s => s.cmd.replace(/_/g, ' ')).join(', ')))));
  if (lists.length) extra.push(el('div', { class: 'note' }, 'Shop lists are easiest to change in the Maps tab (pick the shop’s map, then Shop).'));
  holder.replaceChildren(
    el('p', { class: 'note' }, 'Each box is one script, step by step. Change the words, items or Pokémon right here, use + to add a step, or switch to Code view for anything else.'),
    ...extra.filter((x, i) => i === 0 && hooks.length), ...(cards.length ? cards : [el('div', { class: 'note' }, 'This file has no scripts, only text.')]), ...extra.filter((x, i) => !(i === 0 && hooks.length)));
  $('#scriptEditor').scrollTop = keep;
}

const _renderScriptEditorBase = renderScriptEditor;
renderScriptEditor = function () {
  _renderScriptEditorBase();
  const tools = document.querySelector('#scriptEditor .scripttools');
  const ta = S.textarea;
  const toggle = el('div', { class: 'segmented' },
    ['steps', 'code'].map(v => el('button', { class: S.view === v ? 'on' : '', onclick: () => {
      S.view = v;
      try { localStorage.setItem('emerald.scriptView', v); } catch (e) { /* ignore */ }
      renderScriptEditor();
    } }, v === 'steps' ? 'Simple view' : 'Code view')));
  tools.prepend(toggle);
  if (S.view === 'steps') {
    ta.classList.add('hidden');
    tools.querySelectorAll('select').forEach(s => s.classList.add('hidden'));
    tools.querySelector('.note')?.classList.add('hidden');
    tools.append(el('button', { class: 'btn small', onclick: () => {
      ta.selectionStart = ta.selectionEnd = ta.value.length;
      openInsertForm('newscript');
    } }, '+ New script'));
    ta.after(el('div', { id: 'scriptSteps' }));
    ta.addEventListener('change', renderSteps);
    renderSteps();
  }
};
