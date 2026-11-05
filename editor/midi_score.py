"""A tiny way to write music as text and save it as a MIDI file the game can build.

    song = Song('mus_title', bpm=76, beats_per_bar=3)
    horn = song.track(60, vol=100)                      # program 60 = French horn
    horn.play(0, 'D4:2 A4:1 | Bb4:1.5 A4:.5 G4:1')      # note:beats, '|' is only for reading
    song.loop(12, 108)                                  # the game loops between these beats

Notes are C4 (middle C) style names with # or b. 'r' is a rest. 'D3+A3' is a chord.
A length is kept until the next one is given. Beats are quarter notes.
"""

import re
import struct

PPQ = 24  # ticks per quarter note, the same grid the game's music engine uses

_NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def pitch(name):
    m = re.fullmatch(r'([A-G])(#|b)?(-?\d)', name)
    if not m:
        raise ValueError('bad note name: %s' % name)
    n = _NAMES[m.group(1)] + {'#': 1, 'b': -1, None: 0}[m.group(2)]
    return n + 12 * (int(m.group(3)) + 1)


def parse(text, length=1.0):
    """'D4:2 A4 r:.5 D3+A3:1' -> [(beats, [pitches]), ...]"""
    out = []
    for tok in text.replace('|', ' ').split():
        name, _, ln = tok.partition(':')
        if ln:
            length = float(ln)
        notes = [] if name == 'r' else [pitch(p) for p in name.split('+')]
        out.append((length, notes))
    return out


class Track:
    def __init__(self, song, program, vol, pan):
        self.song = song
        self.program = program
        self.events = []  # (tick, order, bytes)
        self.cc(0, 7, vol)
        self.cc(0, 10, pan)

    def _at(self, beat):
        return int(round(beat * PPQ))

    def cc(self, beat, num, value):
        self.events.append((self._at(beat), 0, bytes([0xB0, num, max(0, min(127, int(value)))])))

    def ramp(self, beat0, beat1, v0, v1, steps=8):
        """A volume swell or fade."""
        for i in range(steps + 1):
            self.cc(beat0 + (beat1 - beat0) * i / steps, 7, v0 + (v1 - v0) * i / steps)

    def note(self, beat, p, beats, vel=100, gate=0.92):
        t0 = self._at(beat)
        t1 = max(t0 + 1, self._at(beat + beats * gate))
        self.events.append((t0, 2, bytes([0x90, p, max(1, min(127, int(vel)))])))
        self.events.append((t1, 1, bytes([0x80, p, 0])))

    def play(self, beat, text, vel=100, gate=0.92, shift=0, accent=None):
        """Play a line of notes starting at a beat. Returns the beat after the last note.
        accent: extra velocity on notes that start on a whole beat."""
        for beats, notes in parse(text):
            for p in notes:
                v = vel + (accent if accent and abs(beat - round(beat)) < 1e-6 else 0)
                self.note(beat, p + shift, beats, v, gate)
            beat += beats
        return beat

    def hits(self, beat, key, times, vel=100, beats=0.25, gate=0.9):
        """Drum hits: times are beat offsets from 'beat'. A (time, velocity) pair works too."""
        for t in times:
            v = vel
            if isinstance(t, tuple):
                t, v = t
            self.note(beat + t, key, beats, v, gate)


class Song:
    def __init__(self, name, bpm, beats_per_bar=4):
        self.name = name
        self.bpm = bpm
        self.bar = beats_per_bar
        self.tracks = []
        self.loop_at = None
        self.end = 0

    def track(self, program, vol=100, pan=64):
        if len(self.tracks) >= 10:
            raise ValueError('the game plays at most 10 tracks in a song')
        t = Track(self, program, vol, pan)
        self.tracks.append(t)
        return t

    def loop(self, start, end):
        self.loop_at = start
        self.end = end

    def midi(self):
        def vlq(n):
            out = [n & 0x7F]
            n >>= 7
            while n:
                out.append(0x80 | (n & 0x7F))
                n >>= 7
            return bytes(reversed(out))

        def chunk(events, end_tick):
            data = b''
            last = 0
            for tick, _, ev in sorted(events, key=lambda e: (e[0], e[1])):
                data += vlq(tick - last) + ev
                last = tick
            data += vlq(max(0, end_tick - last)) + b'\xff\x2f\x00'
            return b'MTrk' + struct.pack('>I', len(data)) + data

        end = int(round(self.end * PPQ))
        tempo = int(round(60000000 / self.bpm))
        seq = [(0, 0, b'\xff\x51\x03' + tempo.to_bytes(3, 'big')),
               (0, 0, b'\xff\x58\x04' + bytes([self.bar, 2, 24, 8]))]
        if self.loop_at is not None:
            seq.append((int(round(self.loop_at * PPQ)), 1, b'\xff\x06\x01['))
            seq.append((end, 9, b'\xff\x06\x01]'))
        chunks = [chunk(seq, end)]
        for ch, t in enumerate(self.tracks):
            ch = ch if ch < 9 else ch + 1  # skip MIDI channel 10, other tools treat it as drums
            evs = [(0, -1, bytes([0xC0 | ch, t.program]))]
            for tick, order, ev in t.events:
                if tick > end:
                    raise ValueError('%s: a note goes past the end of the song' % self.name)
                evs.append((tick, order, bytes([ev[0] | ch]) + ev[1:]))
            chunks.append(chunk(evs, end))
        return b'MThd' + struct.pack('>IHHH', 6, 1, len(chunks), PPQ) + b''.join(chunks)
