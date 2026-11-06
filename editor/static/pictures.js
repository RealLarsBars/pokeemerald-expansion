'use strict';
// "Use my own picture": pick any picture file, see how it will look in the
// game (resized, background see-through, 15 colours), then put it in.

function fitDraw(img, w, h) {
  // Draws img into a w x h canvas: kept whole and centred. Small pixel art is
  // scaled up by whole steps with sharp pixels; anything bigger is shrunk smoothly.
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d', { willReadFrequently: true });
  const iw = img.naturalWidth, ih = img.naturalHeight;
  let scale = Math.min(w / iw, h / ih);
  if (scale >= 1) { scale = Math.floor(scale); g.imageSmoothingEnabled = false; }
  else { g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high'; }
  const dw = Math.round(iw * scale), dh = Math.round(ih * scale);
  g.drawImage(img, Math.floor((w - dw) / 2), Math.floor((h - dh) / 2), dw, dh);
  return g.getImageData(0, 0, w, h);
}

function pixelsB64(imageData) {
  const bytes = imageData.data;
  let s = '';
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
  return btoa(s);
}

function loadImageFile(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('That file is not a picture the browser can open. PNG, JPG, GIF and WEBP all work.'));
    img.src = url;
  });
}

async function openPictureImport(kind, target, name, onDone) {
  let info;
  try { info = await api(`/api/picture/info?kind=${kind}&target=${encodeURIComponent(target)}`); } catch (e) { toast(e.message, true); return; }
  if (kind === 'trainer' && info.shared) {
    openModal('Use my own picture', el('div', {}, el('p', {}, "This is the player's picture. Its colours are shared with the back picture used in battle, so it cannot be replaced here."),
      el('p', { class: 'note' }, 'Pick a different battle picture for this trainer first, then use your own picture on that one.')));
    return;
  }
  const state = { front: null, back: null, w: info.w, h: info.h };
  const previews = el('div', { class: 'row', style: 'gap:20px;align-items:flex-end;margin:12px 0' });
  const useBtn = el('button', { class: 'btn primary', disabled: true }, 'Use this picture');
  const msg = el('div', { class: 'note' });

  const showPreview = async () => {
    if (!state.front) return;
    msg.textContent = 'Making the game version...';
    try {
      const res = await api('/api/picture', Object.assign({ kind, target, save: false }, state));
      const fig = (src, label, scale = 3) => el('div', { class: 'picpreview' },
        el('img', { src, style: `width:${state.w * scale}px;height:${state.h * scale}px` }), el('div', { class: 'note' }, label));
      previews.replaceChildren(
        fig(imgUrl(info.current), 'Now'),
        fig(res.preview, kind === 'pokemon' ? 'New front' : 'New'),
        res.previewBack ? fig(res.previewBack, 'New back') : null,
        res.previewShiny ? fig(res.previewShiny, 'Shiny') : null);
      msg.textContent = 'This is how it will look in the game (with the 15 colours the Game Boy Advance allows). The see-through parts show the background colour.';
      useBtn.disabled = false;
    } catch (e) { msg.textContent = e.message; useBtn.disabled = true; }
  };

  const picker = (label, key) => {
    const input = el('input', { type: 'file', accept: 'image/*' });
    input.addEventListener('change', async () => {
      const file = input.files[0];
      if (!file) return;
      try {
        const img = await loadImageFile(file);
        let w = info.w, h = info.h;
        // A whole overworld sheet (every pose) the same size as the current one is kept as it is.
        if (kind === 'overworld' && img.naturalWidth === info.sheetW && img.naturalHeight === info.sheetH) { w = info.sheetW; h = info.sheetH; }
        if (key === 'front') { state.w = w; state.h = h; }
        state[key] = pixelsB64(fitDraw(img, w, h));
        await showPreview();
      } catch (e) { toast(e.message, true); }
    });
    return el('label', { class: 'field' }, el('span', {}, label), input);
  };

  useBtn.addEventListener('click', async () => {
    useBtn.disabled = true;
    try {
      await api('/api/picture', Object.assign({ kind, target, name, save: true }, state));
      IMG_V = Date.now();
      closeModal();
      toast('New picture saved. Press ▶ Play to see it in the game.');
      if (onDone) onDone();
    } catch (e) { toast(e.message, true); useBtn.disabled = false; }
  });

  const body = el('div', {},
    el('p', {}, info.note),
    el('p', { class: 'note' }, 'Any picture works: it is resized to fit and its background is made see-through (a picture with a plain background or a transparent one works best). '
      + (kind === 'trainer' ? 'Every trainer who uses this battle picture gets the new one.' : kind === 'overworld' ? 'Everyone who uses this sprite gets the new one. Its colours are matched to the colours this sprite already uses.' : 'Its shiny colours are made for you.')
      + ' Recent changes can undo it.'),
    el('div', { class: 'row' }, picker(kind === 'pokemon' ? 'Front picture' : 'Picture', 'front'), kind === 'pokemon' ? picker('Back picture (optional)', 'back') : null),
    previews, msg,
    el('div', { class: 'row', style: 'justify-content:flex-end' }, useBtn));
  openModal('Use my own picture: ' + name, body);
}
