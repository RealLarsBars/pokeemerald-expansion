"""Listen to the game's music without building the game.

Plays a song's .mid through the same instrument samples, envelopes and channel limit
(5 sampled voices at once) the game's sound engine uses, and saves a .wav. It is a
close approximation, not a perfect copy: the real game mixes at a lower sample rate,
so it sounds a little grittier there.

    python3 editor/music_preview.py                     (every Thrones song)
    python3 editor/music_preview.py path/to/song.mid -g thrones -o out.wav
Needs numpy.
"""

import argparse
import os
import re
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT  # noqa: E402

RATE = 32768
FRAME = 1 / 59.7275  # the engine updates envelopes once per screen frame
MAX_DS = 5           # sampled voices the game plays at once (src/m4a.c)
ENGINE_RATE = 13379  # fixed-rate drum samples play at the mixer rate
SOUND = os.path.join(ROOT, 'sound')


# ---- instruments ----------------------------------------------------------------------------

_samples = {}


def sample(name):
    """DirectSoundWaveData_xxx -> (float array, rate at middle C, loop start or None)"""
    if name in _samples:
        return _samples[name]
    path = os.path.join(SOUND, 'direct_sound_samples', name.replace('DirectSoundWaveData_', '') + '.wav')
    d = open(path, 'rb').read()
    i, rate, pitch, loop, loop_end, data = 12, None, None, None, None, b''
    while i < len(d) - 8:
        cid, sz = d[i:i + 4], struct.unpack('<I', d[i + 4:i + 8])[0]
        body = d[i + 8:i + 8 + sz]
        if cid == b'fmt ':
            rate = struct.unpack('<I', body[4:8])[0]
            bits = struct.unpack('<H', body[14:16])[0]
        elif cid == b'smpl' and struct.unpack('<I', body[28:32])[0]:
            loop = struct.unpack('<I', body[44:48])[0]
            loop_end = struct.unpack('<I', body[48:52])[0] + 1
        elif cid == b'agbp':
            pitch = struct.unpack('<I', body[:4])[0] / 1024
        elif cid == b'agbl':
            loop_end = struct.unpack('<I', body[:4])[0]
        elif cid == b'data':
            data = body
        i += 8 + sz + (sz & 1)
    if bits == 8:
        a = (np.frombuffer(data, dtype=np.uint8).astype(np.float32) - 128) / 128
    else:
        a = np.frombuffer(data, dtype='<i2').astype(np.float32) / 32768
    if loop_end:
        a = a[:loop_end]
    _samples[name] = (a, pitch or rate, loop)
    return _samples[name]


def _groups():
    """Every voice_group in the sound folder: name -> (first key, [voice lines])."""
    groups, cur = {}, None
    for dirpath, _, files in os.walk(os.path.join(SOUND, 'voicegroups')):
        for fn in files:
            if not fn.endswith('.inc'):
                continue
            for line in open(os.path.join(dirpath, fn)):
                line = line.split('@')[0].strip()
                m = re.match(r'voice_group\s+(\w+)(?:\s*,\s*(\d+))?', line)
                if m:
                    cur = groups[m.group(1)] = (int(m.group(2) or 0), [])
                elif line.startswith('voice_') and cur:
                    cur[1].append(line)
    return groups


def _keysplits():
    tables, cur = {}, None
    for line in open(os.path.join(SOUND, 'keysplit_tables.inc')):
        line = line.split('@')[0].strip()
        m = re.match(r'keysplit\s+(\w+),\s*(\d+)', line)
        if m:
            cur = tables['keysplit_' + m.group(1)] = (int(m.group(2)), [])
        m = re.match(r'split\s+(\d+),\s*(\d+)', line)
        if m and cur:
            cur[1].append((int(m.group(1)), int(m.group(2))))
    return tables


class Bank:
    def __init__(self, group):
        self.groups = _groups()
        self.splits = _keysplits()
        self.group = group

    def voice(self, program, key):
        """-> (sample name, key to play, fixed rate?, pan or None, adsr) or None for PSG/unknown."""
        start, lines = self.groups[self.group]
        line = lines[program] if program < len(lines) else ''
        m = re.match(r'voice_keysplit_all\s+voicegroup_(\w+)', line)
        if m:
            first, sub = self.groups[m.group(1)]
            idx = key - first
            if not 0 <= idx < len(sub):
                return None
            return self._direct(sub[idx], key, drum=True)
        m = re.match(r'voice_keysplit\s+voicegroup_(\w+),\s*(\w+)', line)
        if m:
            first, splits = self.splits[m.group(2)]
            if key < first:
                raise ValueError('note %d is below the %s key split (lowest %d)' % (key, m.group(2), first))
            idx = next((i for i, end in splits if key <= end), splits[-1][0])
            return self._direct(self.groups[m.group(1)][1][idx], key)
        return self._direct(line, key)

    def _direct(self, line, key, drum=False):
        m = re.match(r'voice_directsound(_no_resample)?\s+(\d+),\s*(\d+),\s*(\w+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)', line)
        if not m:
            return None
        fixed = bool(m.group(1))
        base, pan = int(m.group(2)), int(m.group(3))
        play = base if drum else key
        return (m.group(4), play, fixed, pan if pan else None, tuple(int(m.group(i)) for i in range(5, 9)))


# ---- reading the .mid -----------------------------------------------------------------------

def read_midi(path):
    d = open(path, 'rb').read()
    ntr, ppq = struct.unpack('>HH', d[10:14])
    pos, events, tempo, loop = 14, [], 500000, [None, None]
    for _ in range(struct.unpack('>H', d[8:10])[0] and ntr):
        ln = struct.unpack('>I', d[pos + 4:pos + 8])[0]
        p, end, tick, status = pos + 8, pos + 8 + ln, 0, 0
        while p < end:
            dt = 0
            while True:
                b = d[p]
                p += 1
                dt = (dt << 7) | (b & 0x7F)
                if b < 0x80:
                    break
            tick += dt
            if d[p] & 0x80:
                status = d[p]
                p += 1
            if status == 0xFF:
                typ, ln2 = d[p], d[p + 1]
                body = d[p + 2:p + 2 + ln2]
                p += 2 + ln2
                if typ == 0x51:
                    tempo = int.from_bytes(body, 'big')
                elif typ in (1, 6) and body in (b'[', b']'):
                    loop[0 if body == b'[' else 1] = tick
                continue
            n = 1 if status & 0xF0 in (0xC0, 0xD0) else 2
            events.append((tick, status, d[p:p + n]))
            p += n
        pos = end
    events.sort(key=lambda e: (e[0], 0 if e[1] & 0xF0 == 0x80 else 1))
    return events, tempo / 1e6 / ppq, loop


# ---- playing it -----------------------------------------------------------------------------

def render(mid, group, master=90, reverb=50, loops=2, fade=5.0, only=None, normalize=True):
    bank = Bank(group)
    events, sec_per_tick, (lstart, lend) = read_midi(mid)
    if lstart is not None and lend:
        body = [e for e in events if lstart <= e[0] < lend]
        last = [e for e in events if e[0] == lend and e[1] & 0xF0 == 0x80]
        out = [e for e in events if e[0] < lend] + last
        for k in range(1, loops):
            out += [(t + k * (lend - lstart), s, b) for t, s, b in body + last]
        events = sorted(out, key=lambda e: (e[0], 0 if e[1] & 0xF0 == 0x80 else 1))
    total = events[-1][0] * sec_per_tick + 3
    buf = np.zeros((int(total * RATE) + RATE, 2), dtype=np.float32)
    prog, vol, pan = [0] * 16, [100] * 16, [64] * 16
    notes = []  # dicts: start, stop, ch, key, vel, voice, env info
    for tick, st, b in events:
        t = tick * sec_per_tick
        ch, kind = st & 0x0F, st & 0xF0
        if only is not None and ch != only and kind in (0x80, 0x90):
            continue
        if kind == 0xC0:
            prog[ch] = b[0]
        elif kind == 0xB0 and b[0] == 7:
            vol[ch] = b[1]
            for n in notes:
                if n['ch'] == ch and n['stop'] is None:
                    n['vols'].append((t, b[1]))
        elif kind == 0xB0 and b[0] == 10:
            pan[ch] = b[1]
        elif kind == 0x90 and b[1]:
            v = bank.voice(prog[ch], b[0])
            if v is None:
                continue
            notes.append({'start': t, 'stop': None, 'ch': ch, 'key': b[0], 'vel': b[1], 'voice': v,
                          'vols': [(t, vol[ch])], 'pan': pan[ch] if v[3] is None else v[3]})
        elif kind == 0x80 or (kind == 0x90 and not b[1]):
            for n in notes:
                if n['ch'] == ch and n['key'] == b[0] and n['stop'] is None:
                    n['stop'] = t
                    break
    for n in notes:
        if n['stop'] is None:
            n['stop'] = total

    # The channel limit, as the engine does it: a new note takes a free voice, else a voice
    # that is already fading out, else a voice of the same or a later track. Notes of later
    # tracks never cut earlier tracks; when nothing can be taken, the new note is not heard.
    active, played = [], []
    for n in notes:
        active = [a for a in active if a['end'] > n['start']]
        n['end'] = _note_end(n)
        if len(active) >= MAX_DS:
            released = [a for a in active if a['stop'] <= n['start']]
            later = [a for a in active if a['ch'] >= n['ch']]
            if released:
                victim = min(released, key=lambda a: a['start'])
            elif later:
                victim = max(later, key=lambda a: (a['ch'], -a['start']))
            else:
                n['dropped'] = True
                continue
            victim['end'] = n['start']
            victim['stolen'] = True
            active.remove(victim)
        active.append(n)
        played.append(n)
    render.dropped = [(round(n['start'], 2), n['ch'], n['key']) for n in notes if n.get('dropped')]
    notes = played
    for n in notes:
        _mix(buf, n, master)
    render.stolen = [(round(n['start'], 2), n['ch'], n['key']) for n in notes
                     if n.get('stolen') and n['stop'] > n['end'] + 0.02]

    if reverb:
        d = int(RATE * 0.05)
        wet = buf.copy()
        for _ in range(4):
            wet[d:] += wet[:-d] * (reverb / 128 * 0.45)
        buf = buf + (wet - buf) * 0.35
    end = int(total * RATE)
    buf = buf[:end]
    if lstart is not None and fade:
        f = int(fade * RATE)
        buf[-f:] *= np.linspace(1, 0, f)[:, None]
    if not normalize:
        return buf
    peak = np.abs(buf).max() or 1
    return buf / peak * 0.89


def _env_curve(adsr, gate, length):
    """The engine's envelope, one value per frame: attack adds, decay and release multiply."""
    a, d, s, r = adsr
    env, phase, out = 0.0, 'a', []
    nframes = int(length / FRAME) + 2
    gate_f = gate / FRAME
    for f in range(nframes):
        if f >= gate_f and phase != 'r':
            phase = 'r'
        if phase == 'a':
            env = min(255, env + a)
            if env >= 255:
                phase = 'd'
        elif phase == 'd':
            env = env * d / 256
            if env <= s:
                env, phase = s, 's'
            if env < 1:
                break  # faded to nothing: the engine frees the voice
        elif phase == 'r':
            env = env * r / 256
            if env < 1:
                env = 0
        out.append(env / 255)
        if phase == 'r' and env == 0:
            break
    return np.array(out, dtype=np.float32)


def _note_end(n):
    env = _env_curve(n['voice'][4], n['stop'] - n['start'], n['stop'] - n['start'] + 4)
    return n['start'] + len(env) * FRAME


def _mix(buf, n, master):
    name, key, fixed, _, adsr = n['voice']
    data, mid_rate, loop = sample(name)
    rate = ENGINE_RATE if fixed else mid_rate * 2 ** ((key - 60) / 12)
    length = n['end'] - n['start']
    if length <= 0:
        return
    count = int(length * RATE)
    pos = np.arange(count, dtype=np.float64) * (rate / RATE)
    if loop is not None and loop < len(data) - 1:
        span = len(data) - loop
        over = pos >= len(data)
        pos[over] = loop + np.mod(pos[over] - loop, span)
    else:
        count = min(count, int(len(data) * RATE / rate))
        pos = pos[:count]
    if count <= 0:
        return
    idx = np.minimum(pos.astype(np.int64), len(data) - 1)
    sig = data[idx]
    env = _env_curve(adsr, n['stop'] - n['start'], length)
    fr = np.minimum((np.arange(count) / RATE / FRAME).astype(np.int64), len(env) - 1)
    sig = sig * env[fr]
    # track volume (with any swells), velocity, the song's master volume
    times = np.arange(count) / RATE + n['start']
    vt = np.array([v for _, v in n['vols']], dtype=np.float32)
    vi = np.searchsorted([t for t, _ in n['vols']], times, side='right') - 1
    sig = sig * (vt[np.maximum(vi, 0)] / 127) * (n['vel'] / 127) * (master / 127)
    p = n['pan'] / 127
    s0 = int(n['start'] * RATE)
    seg = buf[s0:s0 + count]
    seg[:, 0] += sig[:len(seg)] * (1 - p) * 2 * 0.5
    seg[:, 1] += sig[:len(seg)] * p * 2 * 0.5


def save_wav(path, buf):
    pcm = (np.clip(buf, -1, 1) * 32767).astype('<i2')
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + pcm.nbytes) + b'WAVEfmt ')
        f.write(struct.pack('<IHHIIHH', 16, 1, 2, RATE, RATE * 4, 4, 16))
        f.write(b'data' + struct.pack('<I', pcm.nbytes) + pcm.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mid', nargs='?')
    ap.add_argument('-g', '--group', default='thrones')
    ap.add_argument('-o', '--out')
    ap.add_argument('-v', '--master', type=int, default=90)
    args = ap.parse_args()
    if args.mid:
        save_wav(args.out or os.path.splitext(args.mid)[0] + '.wav', render(args.mid, args.group, args.master))
        return
    import thrones_music
    out = os.path.join(ROOT, 'editor', 'fun', 'music', 'preview')
    os.makedirs(out, exist_ok=True)
    for name in thrones_music.SONGS:
        path = os.path.join(out, name + '.wav')
        save_wav(path, render(os.path.join(thrones_music.MUSIC_DIR, name + '.mid'), thrones_music.VOICEGROUP))
        print(path)


if __name__ == '__main__':
    main()
