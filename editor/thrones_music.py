"""Game of Thrones music: new medieval / epic-fantasy songs for the Thrones theme.

Every song here is an original piece written for this game (none of it copies the
show's music). They are played by the game's own sound engine with its own
instrument samples: strings, French horns, trumpets, tuba, choir, timpani, war
drums, harp, lute, flute and oboe, gathered in one new instrument set
(sound/voicegroups/thrones.inc).

Applying Fun Modes with the Thrones theme (and its Music switch on) copies the
.mid files from editor/fun/music/thrones/ over the game's own songs and points
them at the Thrones instruments in midi.cfg. Resetting Fun Modes puts the
original music back.

To change a song, edit its score below and run:
    python3 editor/thrones_music.py            (writes the .mid files)
    python3 editor/music_preview.py            (renders previews you can listen to)
You can also drop in any .mid of your own with the same file name.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import ROOT  # noqa: E402
from midi_score import Song, pitch  # noqa: E402

MUSIC_DIR = os.path.join(ROOT, 'editor', 'fun', 'music', 'thrones')
MIDI_DIR = 'sound/songs/midi'
MIDI_CFG = MIDI_DIR + '/midi.cfg'
VOICEGROUP = 'thrones'

# ---- the instrument set ---------------------------------------------------------------------
# Program numbers follow General MIDI, so the .mid files also sound right in any MIDI player.
DRUMS = 0
BELL = 14
LUTE = 24
PIZZ = 45
HARP = 46
TIMPANI = 47
STRINGS = 48
CHOIR = 52
TRUMPET = 56
TUBA = 58
HORN = 60
OBOE = 68
FLUTE = 73
TAIKO = 116

# Drum keys in the drum kit (voicegroup_rs_drumset).
KICK, SNARE, CRASH, SWELL = 36, 40, 57, 60
TOM_LO, TOM_MID, TOM_HI = 41, 45, 48

FILLER = '\tvoice_square_1 60, 0, 0, 2, 0, 0, 15, 0'
VOICES = {
    DRUMS: '\tvoice_keysplit_all voicegroup_rs_drumset',
    BELL: '\tvoice_directsound 60, 0, DirectSoundWaveData_sc88pro_tubular_bell, 255, 165, 90, 216',
    LUTE: '\tvoice_directsound 60, 0, DirectSoundWaveData_sc88pro_nylon_str_guitar, 255, 249, 25, 127',
    PIZZ: '\tvoice_directsound 60, 0, DirectSoundWaveData_sc88pro_pizzicato_strings, 255, 216, 0, 165',
    HARP: '\tvoice_directsound 60, 0, DirectSoundWaveData_sc88pro_harp, 255, 242, 51, 242',
    TIMPANI: '\tvoice_directsound 60, 0, DirectSoundWaveData_sc88pro_timpani, 255, 246, 0, 226',
    STRINGS: '\tvoice_keysplit voicegroup_strings_keysplit, keysplit_strings',
    CHOIR: '\tvoice_directsound 60, 0, DirectSoundWaveData_classical_choir_voice_ahhs, 40, 0, 255, 210',
    TRUMPET: '\tvoice_keysplit voicegroup_trumpet_keysplit, keysplit_trumpet',
    TUBA: '\tvoice_keysplit voicegroup_tuba_keysplit, keysplit_tuba',
    HORN: '\tvoice_keysplit voicegroup_french_horn_keysplit, keysplit_french_horn',
    OBOE: '\tvoice_directsound 60, 0, DirectSoundWaveData_sd90_classical_oboe, 255, 0, 255, 190',
    FLUTE: '\tvoice_directsound 60, 0, DirectSoundWaveData_sc88pro_flute, 255, 0, 255, 165',
    TAIKO: '\tvoice_directsound 60, 0, DirectSoundWaveData_sc88pro_taiko, 255, 0, 255, 235',
}


def voicegroup_text():
    lines = ['@ Instruments for the Game of Thrones music (editor/thrones_music.py).',
             'voice_group %s' % VOICEGROUP]
    lines += [VOICES.get(i, FILLER) for i in range(max(VOICES) + 1)]
    return '\n'.join(lines) + '\n'


# ---- harmony helpers ------------------------------------------------------------------------

def chord(name):
    """'Dm' -> (root, [0, 3, 7]). Root is in octave 3 (D3 = 50)."""
    m = re.fullmatch(r'([A-G][#b]?)(m?)', name)
    root = pitch(m.group(1) + '3')
    if root > pitch('F#3'):
        root -= 12  # keep roots between F#2 and F#3
    return root, [0, 3, 7] if m.group(2) else [0, 4, 7]


def bars(spec):
    """'Dm Gm | C Dm' -> ['Dm', 'Gm', 'C', 'Dm']; 'Gm/C' is two chords in one bar."""
    return spec.replace('|', ' ').split()


def each_chord(beat, spec, bar):
    """Yields (beat, length, chord name) for every chord, splitting 'X/Y' bars in half."""
    for b in bars(spec):
        parts = b.split('/')
        ln = bar / len(parts)
        for i, c in enumerate(parts):
            yield beat + i * ln, ln, c
        beat += bar


def bass(t, beat, spec, bar, octave=-1, vel=96, rhythm=None):
    """Roots. rhythm: beat offsets inside each chord to play the root again."""
    for b, ln, c in each_chord(beat, spec, bar):
        root, _ = chord(c)
        hits = rhythm or [0]
        hits = [h for h in hits if h < ln]
        for i, h in enumerate(hits):
            nxt = hits[i + 1] if i + 1 < len(hits) else ln
            t.note(b + h, root + 12 * octave, nxt - h, vel - (8 if h else 0), 0.95)
    return beat + bar * len(bars(spec))


def pad(t, beat, spec, bar, tones=(1, 2), base=pitch('E3'), vel=80, gate=0.98):
    """Held chords: two chord tones (1 = third, 2 = fifth, 0 = root), placed at or above 'base'."""
    for b, ln, c in each_chord(beat, spec, bar):
        root, iv = chord(c)
        for k in tones:
            p = root + iv[k]
            while p < base:
                p += 12
            while p >= base + 12:
                p -= 12
            t.note(b, p, ln, vel, gate)
    return beat + bar * len(bars(spec))


def ostinato(t, beat, spec, bar, minor, major=None, step=0.5, octave=0, vel=92, gate=0.8, accent=10):
    """A repeating figure moved to each chord. The patterns are semitones above the root."""
    major = major or minor
    for b, ln, c in each_chord(beat, spec, bar):
        root, iv = chord(c)
        pat = minor if iv[1] == 3 else major
        n = int(round(ln / step))
        for i in range(n):
            v = vel + (accent if i % (len(pat) if len(pat) <= n else n) == 0 else 0)
            t.note(b + i * step, root + 12 * octave + pat[i % len(pat)], step, v, gate)
    return beat + bar * len(bars(spec))


def roll(t, beat, key, beats, v0, v1, step=0.25):
    n = int(round(beats / step))
    for i in range(n):
        t.note(beat + i * step, key, step, v0 + (v1 - v0) * i / max(1, n - 1), 0.9)


# ---- the songs ------------------------------------------------------------------------------
# One melody, "the Crown", ties the set together. It is in D minor and turns up in the
# title, in Gym battles and in a gentler form at home.

CROWN = {
    'A': 'D4:2 A4:1 | Bb4:1.5 A4:.5 G4:1 | F4:1 E4:1 C4:1 | D4:3',
    'B': 'F4:2 G4:1 | A4:1.5 Bb4:.5 C5:1 | D5:1 C5:1 A4:1 | A4:3',
    'C': 'Bb4:2 A4:1 | G4:1 F4:1 E4:1 | F4:1.5 E4:.5 C4:1 | D4:3',
}
CROWN_CHORDS = {'A': 'Dm Gm C Dm', 'B': 'F Am Dm A', 'C': 'Bb C F Dm'}


def title():
    """Title screen: a slow, heavy oath. Timpani roll, then the Crown on horns, then the
    whole army: trumpets, choir and war drums."""
    s = Song('mus_title', bpm=72, beats_per_bar=3)
    mel = s.track(HORN, 112)
    tpt = s.track(TRUMPET, 127)
    strings = s.track(STRINGS, 78)
    choir = s.track(CHOIR, 70)
    low = s.track(TUBA, 88)
    timp = s.track(TIMPANI, 110)
    taiko = s.track(TAIKO, 110)
    drums = s.track(DRUMS, 104)

    # Intro: 4 bars. A drone on D grows out of a timpani roll.
    strings.note(0, pitch('D3'), 12, 70, 1.0)
    strings.note(0, pitch('A3'), 12, 70, 1.0)
    strings.ramp(0, 11, 30, 78)
    roll(timp, 0, pitch('D3'), 9, 30, 112)
    timp.note(9, pitch('A2'), 1.5, 120)
    timp.note(10.5, pitch('A2'), 0.5, 100)
    timp.note(11, pitch('D3'), 1, 127)
    choir.note(6, pitch('A4'), 6, 90, 1.0)
    drums.note(6, SWELL, 6, 110)

    # Part 1: the Crown on horns, held chords, tuba and timpani.
    p1 = 12
    form = 'ABAC'
    beat = p1
    for k in form:
        mel.play(beat, CROWN[k], vel=108, gate=0.97)
        pad(strings, beat, CROWN_CHORDS[k], 3, vel=82)
        bass(low, beat, CROWN_CHORDS[k], 3, octave=-1, vel=100)
        for i, c in enumerate(bars(CROWN_CHORDS[k])):
            root, _ = chord(c)
            timp.note(beat + 3 * i, root, 1, 100 if i == 0 else 84)
        timp.play(beat + 9 + 1.5, 'A2:.5 A2:.5 A2:.5', vel=96)
        beat += 12
    drums.note(beat - 3, SWELL, 3, 100)

    # Part 2: the army. Trumpets carry the Crown, strings run, the choir holds the chords.
    for n, k in enumerate(form):
        tpt.play(beat, CROWN[k], vel=124, gate=0.97)
        ostinato(strings, beat, CROWN_CHORDS[k], 3, [0, 7, 12, 7, 15, 7], [0, 7, 12, 7, 16, 7], vel=86)
        pad(choir, beat, CROWN_CHORDS[k], 3, tones=(1,), base=pitch('A3'), vel=96)
        for i in range(4):
            b = beat + 3 * i
            if i == 0 and n % 2 == 0:
                drums.hits(b, CRASH, [(0, 108)])
            taiko.hits(b, pitch('C3'), [(0, 120), (1.5, 96)], beats=0.5)
            drums.hits(b, SNARE, [(2, 84), (2.5, 92)])
        roll(drums, beat + 10, SNARE, 1, 70, 112)
        beat += 12

    # Ending: one long D minor chord. Like the original title song it does not loop:
    # when it ends, the game goes back to the intro.
    mel.note(beat, pitch('D4'), 6, 112, 1.0)
    tpt.note(beat, pitch('A4'), 6, 118, 1.0)
    strings.note(beat, pitch('F3'), 6, 90, 1.0)
    choir.note(beat, pitch('D5'), 6, 100, 1.0)
    low.note(beat, pitch('D2'), 6, 104, 1.0)
    taiko.note(beat, pitch('C3'), 1, 124)
    drums.note(beat, CRASH, 2, 116)
    roll(timp, beat + 3, pitch('D3'), 2.5, 70, 120)
    timp.note(beat + 5.5, pitch('D3'), 0.5, 124)
    for t in (mel, tpt, strings, choir, low):
        t.ramp(beat + 3, beat + 6, 110, 40, steps=6)
    beat += 6
    s.end = beat
    return s


def littleroot():
    """Littleroot: a hearth in a quiet village. A lute, a flute, and later an oboe and harp.
    D Dorian, the old folk mode."""
    s = Song('mus_littleroot', bpm=96, beats_per_bar=3)
    flute = s.track(FLUTE, 92)
    oboe = s.track(OBOE, 92)
    harp = s.track(HARP, 124, pan=84)
    lute = s.track(LUTE, 100, pan=50)
    low = s.track(STRINGS, 70)

    prog = 'Dm G Dm C | Dm G Am Dm | Dm G Dm C | Dm G Am Dm'
    tune = ('D5:1.5 E5:.5 F5:1 | E5:1 D5:1 B4:1 | A4:2 F4:1 | G4:1 E4:1 C4:1 | '
            'D4:1 F4:1 A4:1 | B4:1.5 A4:.5 G4:1 | A4:1 C5:1 E5:1 | D5:3 | '
            'F5:1.5 E5:.5 D5:1 | D5:1 B4:1 G4:1 | A4:1.5 G4:.5 F4:1 | E4:1 G4:1 C5:1 | '
            'A4:1 F4:1 D4:1 | G4:1.5 A4:.5 B4:1 | C5:1 B4:.5 A4:.5 E4:1 | D4:3')
    echo = ('r:3 | r:2 D5:.5 E5:.5 | F5:3 | E5:3 | F5:3 | D5:3 | C5:2 E5:1 | F5:3 | '
            'A5:3 | G5:3 | F5:2 A5:1 | G5:3 | F5:3 | D5:2 B4:1 | E5:3 | D5:3')
    lute_pat = [0, 7, 12, 15, 12, 7]
    lute_maj = [0, 7, 12, 16, 12, 7]

    for half in range(2):
        b0 = half * 48
        ostinato(lute, b0, prog, 3, lute_pat, lute_maj, step=0.5, vel=88, gate=1.0, accent=12)
        bass(low, b0, prog, 3, octave=0, vel=78)
        if half == 0:
            flute.play(b0, tune, vel=96, gate=0.95)
        else:
            oboe.play(b0, tune, vel=94, gate=0.95, shift=-12)
            harp.play(b0, echo, vel=82, gate=1.0)
    s.loop(0, 96)
    return s


def route101():
    """The King's Road: riding out. A galloping march in A minor."""
    s = Song('mus_route101', bpm=116, beats_per_bar=4)
    mel = s.track(HORN, 110)
    oboe = s.track(OBOE, 98)
    drums = s.track(DRUMS, 92)
    gallop = s.track(PIZZ, 104)
    strings = s.track(STRINGS, 76)

    prog = 'Am F G Am | Am F G E | F G Am E | F G E Am'
    tune = ('A3:1.5 E4:.5 E4:1 D4:.5 C4:.5 | C4:1 A3:1 F4:2 | G4:1.5 F4:.5 E4:1 D4:1 | E4:3 r:1 | '
            'A4:1.5 G4:.5 E4:1 C4:1 | F4:1 E4:.5 D4:.5 C4:2 | D4:1 E4:1 G4:1 B4:1 | B4:3 G#4:1 | '
            'C5:1.5 B4:.5 A4:1 F4:1 | G4:1.5 F4:.5 D4:2 | E4:1 A4:1 C5:1 E5:1 | B4:1.5 A4:.5 G#4:2 | '
            'A4:1.5 G4:.5 F4:1 A4:1 | G4:1.5 F4:.5 E4:1 D4:1 | E4:1 G#4:1 B4:1 D5:1 | C5:1 B4:.5 G#4:.5 A4:2')
    for half in range(2):
        b0 = half * 64
        if half == 0:
            mel.play(b0, tune, vel=104, gate=0.95)
        else:
            oboe.play(b0, tune, vel=100, gate=0.95, shift=12)
            mel.play(b0, tune, vel=80, gate=0.95, shift=-12)
        # The gallop: long-short-short on every beat, like hooves on the road.
        for b, ln, c in each_chord(b0, prog, 4):
            root, iv = chord(c)
            for k in range(int(ln)):
                up = root + (iv[2] if k % 2 else 0)
                gallop.note(b + k, up, 0.5, 98, 0.9)
                gallop.note(b + k + 0.5, root, 0.25, 80, 0.9)
                gallop.note(b + k + 0.75, root + 12, 0.25, 84, 0.9)
        if half == 0:
            pad(strings, b0, prog, 4, tones=(1,), base=pitch('A3'), vel=80)
        for bar in range(16):
            b = b0 + bar * 4
            drums.hits(b, SNARE, [(0, 96), (1.5, 70), (1.75, 74), (2, 90), (3, 80), (3.5, 70), (3.75, 76)])
            drums.hits(b, KICK, [(2, 92)])
            if bar % 4 == 3:
                roll(drums, b + 3, SNARE, 1, 70, 104)
        drums.hits(b0, CRASH, [(0, 100)])
    s.loop(0, 128)
    return s


def gym():
    """The Great Hall of a noble house: a stately processional in G minor, with a bell."""
    s = Song('mus_gym', bpm=100, beats_per_bar=4)
    mel = s.track(TRUMPET, 127)
    horn = s.track(HORN, 96)
    bell = s.track(BELL, 80)
    strings = s.track(STRINGS, 72)
    low = s.track(TUBA, 78)
    timp = s.track(TIMPANI, 100)

    a = 'Gm Eb F D | Gm Eb Cm/D Gm'
    tune_a = ('G4:1 D4:.5 G4:.5 A4:1 Bb4:1 | Bb4:1.5 A4:.5 G4:2 | F4:1 A4:1 C5:1 A4:1 | D5:3 r:1 | '
              'D5:1 Bb4:.5 G4:.5 D5:1 Eb5:1 | Eb5:1.5 D5:.5 C5:1 Bb4:1 | C5:1 Eb5:1 D5:1 F#4:1 | G4:3 r:1')
    b = 'Bb F Gm D | Eb Bb Cm D'
    tune_b = ('D5:2 C5:1 Bb4:1 | C5:2 A4:2 | Bb4:1.5 A4:.5 G4:1 Bb4:1 | A4:3 F#4:1 | '
              'G4:1 Bb4:1 Eb5:2 | D5:1.5 C5:.5 Bb4:2 | C5:1 Bb4:1 A4:1 G4:1 | F#4:2 A4:2')

    beat = 0
    bell.note(0, pitch('G4'), 4, 100)
    for part, (prog, tune, who) in enumerate([(a, tune_a, mel), (a, tune_a, strings), (b, tune_b, horn)]):
        if who is strings:
            strings.play(beat, tune, vel=96, gate=0.97)
            horn.play(beat, tune, vel=72, gate=0.97, shift=-12)
        else:
            who.play(beat, tune, vel=120, gate=0.95)
            pad(strings, beat, prog, 4, vel=76)
        bass(low, beat, prog, 4, octave=-1, vel=96, rhythm=[0, 2])
        for i, c in enumerate(bars(prog)):
            root, _ = chord(c.split('/')[0])
            timp.hits(beat + 4 * i, root, [(0, 104), (2, 84)], beats=1)
            if i % 4 == 3:
                timp.hits(beat + 4 * i, root, [(3, 80), (3.25, 86), (3.5, 92), (3.75, 100)])
        beat += 32
    bell.note(64, pitch('D4'), 4, 90)
    s.loop(0, beat)
    return s


def vs_gym_leader():
    """Gym Leader battle, in the style of the show's opening: a driving low-string figure in
    3/4, C minor, war drums, and a big sweeping tune passed from horns to trumpets and choir.
    The tune and figure are new; only the mood and instruments follow the show."""
    s = Song('mus_vs_gym_leader', bpm=162, beats_per_bar=3)
    cello = s.track(STRINGS, 120)   # the strings sample played low reads as cellos
    horn = s.track(HORN, 116)
    tpt = s.track(TRUMPET, 127)
    choir = s.track(CHOIR, 80)
    strings = s.track(STRINGS, 92)
    drums = s.track(DRUMS, 108)
    taiko = s.track(TAIKO, 112)
    harp = s.track(HARP, 110, pan=80)   # plucked, close to a hammered dulcimer

    fig_m = [0, 0, 7, 0, 8, 7]   # C C G C Ab G: the strings never stop
    fig_M = [0, 0, 7, 0, 9, 7]
    prog = 'Cm Cm Ab Eb | Fm Cm G G | Cm Cm Ab Eb | Fm Cm G Cm'
    tune = ('C4:2 G4:1 | Eb4:1.5 D4:.5 C4:1 | Ab4:2 G4:.5 F4:.5 | G4:3 | '
            'F4:2 Ab4:1 | G4:1.5 Eb4:.5 C4:1 | D4:1.5 B3:.5 D4:1 | D4:3 | '
            'C5:2 G4:1 | Bb4:1.5 Ab4:.5 G4:1 | C5:2 Eb5:1 | Bb4:3 | '
            'Ab4:2 C5:1 | G4:1.5 F4:.5 Eb4:1 | D4:1 G4:1 B4:1 | C5:3')
    bridge = 'Ab Ab Bb Bb | Cm Cm G G'
    bridge_tune = 'Eb4:3 | C4:3 | F4:3 | D4:3 | G4:3 | Eb4:3 | D4:3 | B3:3'

    def war_drums(b, bar, fill=False):
        taiko.hits(b, pitch('C3'), [(0, 124), (1.5, 100)], beats=0.5)
        drums.hits(b, SNARE, [(2, 96), (2.5, 104)])
        if bar % 4 == 0:
            drums.hits(b, CRASH, [(0, 108)])
        if fill:
            roll(drums, b + 1, SNARE, 2, 80, 124)

    # Intro: a dark opening. Low strings alone, a plucked figure answers, then the drums.
    ostinato(strings, 0, 'Cm Cm Cm Cm Cm Cm Cm Cm', 3, fig_m, vel=96)
    ostinato(harp, 12, 'Cm Cm Cm Cm', 3, [24, 19, 24, 27, 24, 19], vel=90, gate=1.0, accent=0)
    taiko.hits(0, pitch('G2'), [(0, 127)], beats=1)
    taiko.hits(6, pitch('G2'), [(0, 127)], beats=1)
    for i in range(4, 8):
        war_drums(3 * i, 1, fill=i == 7)

    beat = 24
    # A: the tune on cellos, low and broad.
    ostinato(strings, beat, prog, 3, fig_m, fig_M, vel=86)
    cello.play(beat, tune, vel=124, gate=0.99, shift=-12)
    for i in range(16):
        war_drums(beat + 3 * i, i, fill=i == 15)
    beat += 48
    # B: trumpets take it, horns an octave below, the choir holds the chords.
    ostinato(strings, beat, prog, 3, fig_m, fig_M, vel=90)
    tpt.play(beat, tune, vel=124, gate=0.97, shift=0)
    horn.play(beat, tune, vel=92, gate=0.97, shift=-12)
    pad(choir, beat, prog, 3, tones=(2,), base=pitch('G4'), vel=100)
    for i in range(16):
        war_drums(beat + 3 * i, i, fill=i == 15)
    beat += 48
    # Bridge: everything drops back, then builds to the top again.
    ostinato(strings, beat, bridge, 3, fig_m, fig_M, vel=84)
    cello.play(beat, bridge_tune, vel=120, gate=0.99, shift=-12)
    ostinato(harp, beat, bridge, 3, [24, 19, 24, 27, 24, 19], [24, 19, 24, 28, 24, 19], vel=84, gate=1.0, accent=0)
    for i in range(8):
        taiko.hits(beat + 3 * i, pitch('C3'), [(0, 100 + 3 * i)], beats=0.5)
        if i >= 4:
            drums.hits(beat + 3 * i, SNARE, [(2, 90), (2.5, 100)])
    roll(drums, beat + 21, SNARE, 3, 70, 127)
    beat += 24
    s.loop(24, beat)
    return s


def vs_trainer():
    """Trainer battle: a duel in the yard. E minor, quick and bright-edged."""
    s = Song('mus_vs_trainer', bpm=160, beats_per_bar=4)
    mel = s.track(TRUMPET, 127)
    oboe = s.track(OBOE, 96)
    strings = s.track(STRINGS, 80)
    low = s.track(TUBA, 84)
    drums = s.track(DRUMS, 100)

    fig_m = [0, 7, 12, 7, 0, 7, 10, 7]
    fig_M = [0, 7, 12, 7, 0, 7, 12, 7]
    a = 'Em C D Em | Em C Am B'
    tune_a = ('E5:1 B4:1 E5:.5 F#5:.5 G5:1 | E5:1.5 D5:.5 C5:1 B4:1 | A4:1 D5:1 F#5:1.5 E5:.5 | E5:3 r:1 | '
              'G5:1 F#5:.5 E5:.5 B4:1 E5:1 | C5:1 E5:1 G5:1 E5:1 | A4:1 C5:1 E5:1 F#5:1 | D#5:2 F#5:2')
    b = 'C D Bm Em | C D B B'
    tune_b = ('G4:2 E4:1 G4:1 | A4:2 F#4:1 A4:1 | B4:1.5 A4:.5 F#4:2 | G4:1 F#4:1 E4:2 | '
              'E4:1 G4:1 C5:2 | D5:1 C5:1 A4:2 | B4:1.5 A4:.5 F#4:1 D#4:1 | F#4:4')

    # Intro: one bar of strings.
    ostinato(strings, 0, 'Em', 4, fig_m, vel=96)
    drums.hits(0, SNARE, [(2, 90), (2.5, 96), (3, 104), (3.5, 112)])
    beat = 4
    for prog, tune, who in ((a, tune_a, mel), (a, tune_a, oboe), (b, tune_b, mel)):
        ostinato(strings, beat, prog, 4, fig_m, fig_M, vel=88)
        who.play(beat, tune, vel=104, gate=0.9)
        bass(low, beat, prog, 4, octave=-1, vel=92, rhythm=[0, 1.5, 2])
        for i in range(8):
            bb = beat + 4 * i
            drums.hits(bb, KICK, [(0, 104), (2, 96), (2.5, 88)])
            drums.hits(bb, SNARE, [(1, 92), (3, 98)])
            if i == 0:
                drums.hits(bb, CRASH, [(0, 100)])
            if i == 7:
                drums.hits(bb, SNARE, [(3.25, 90), (3.5, 100), (3.75, 110)])
        beat += 32
    s.loop(4, beat)
    return s


def vs_wild():
    """Wild battle: something in the woods. F sharp minor, horns and war drums."""
    s = Song('mus_vs_wild', bpm=152, beats_per_bar=4)
    mel = s.track(HORN, 112)
    flute = s.track(FLUTE, 90)
    strings = s.track(STRINGS, 84)
    low = s.track(TUBA, 92)
    drums = s.track(DRUMS, 104)

    fig_m = [0, 12, 7, 12, 0, 12, 8, 7]
    fig_M = [0, 12, 7, 12, 0, 12, 9, 7]
    a = 'F#m Bm E F#m | F#m D Bm C#'
    tune_a = ('F#4:1.5 C#5:1.5 A4:1 | B4:1 A4:1 F#4:2 | E4:1.5 G#4:1.5 B4:1 | C#5:4 | '
              'F#5:1.5 E5:.5 C#5:1 A4:1 | D5:1 C#5:1 A4:2 | B4:1 D5:1 F#5:1 E5:1 | C#5:2 G#4:2')
    b = 'D E C#m F#m | D E C# C#'
    tune_b = ('A4:2 F#4:2 | B4:2 G#4:2 | C#5:1.5 B4:.5 G#4:2 | A4:1 G#4:1 F#4:2 | '
              'F#4:1 A4:1 D5:2 | E5:1 D5:1 B4:2 | C#5:1.5 B4:.5 G#4:1 F4:1 | G#4:4')

    # Intro: a horn call over a drum roll.
    roll(drums, 0, SNARE, 4, 60, 120)
    mel.play(0, 'C#4:1 F#4:1 C#5:2', vel=110)
    beat = 4
    for prog, tune, who, shift in ((a, tune_a, mel, 0), (b, tune_b, mel, 0), (a, tune_a, flute, 12)):
        ostinato(strings, beat, prog, 4, fig_m, fig_M, vel=88)
        who.play(beat, tune, vel=104, gate=0.92, shift=shift)
        if who is flute:
            mel.play(beat, tune_a, vel=76, gate=0.92, shift=-12)
        bass(low, beat, prog, 4, octave=-1, vel=92, rhythm=[0, 0.5, 2, 2.5])
        for i in range(8):
            bb = beat + 4 * i
            drums.hits(bb, KICK, [(0, 108), (0.5, 92), (2, 104), (2.5, 92)])
            drums.hits(bb, SNARE, [(1, 96), (3, 100), (3.5, 84)])
            if i == 0:
                drums.hits(bb, CRASH, [(0, 104)])
        beat += 32
    s.loop(4, beat)
    return s


# Song file -> (score, what it is, where it plays). The first few places to get new music.
SONGS = {
    'mus_title': (title, 'Title screen', 'The title screen.'),
    'mus_littleroot': (littleroot, 'Littleroot Town', 'Littleroot Town and the houses there.'),
    'mus_route101': (route101, "The King's Road", 'Routes 101, 102 and 103.'),
    'mus_gym': (gym, 'Gym (Great Hall)', 'Inside every Gym.'),
    'mus_vs_gym_leader': (vs_gym_leader, 'Gym Leader battle', 'Battles against Gym Leaders.'),
    'mus_vs_trainer': (vs_trainer, 'Trainer battle', 'Battles against trainers.'),
    'mus_vs_wild': (vs_wild, 'Wild battle', 'Battles against wild POKéMON.'),
}


def write_files():
    """Write every .mid from its score, and the instrument set."""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    for name, (score, _, _) in SONGS.items():
        with open(os.path.join(MUSIC_DIR, name + '.mid'), 'wb') as f:
            f.write(score().midi())
    path = os.path.join(ROOT, 'sound', 'voicegroups', VOICEGROUP + '.inc')
    with open(path, 'w', newline='\n') as f:
        f.write(voicegroup_text())


def apply(ov):
    """Put the Thrones songs in place of the game's own. Returns report lines."""
    cfg = ov.read(MIDI_CFG)
    done = []
    for name, (_, label, where) in SONGS.items():
        src = os.path.join(MUSIC_DIR, name + '.mid')
        if not os.path.exists(src):
            continue
        with open(src, 'rb') as f:
            ov.write_bytes('%s/%s.mid' % (MIDI_DIR, name), f.read())
        line = re.compile(r'^(%s\.mid:\s*)(.*)$' % re.escape(name), re.M)
        m = line.search(cfg)
        if m:
            opts = re.sub(r'-G\S+', '-G_' + VOICEGROUP, m.group(2))
            if '-G' not in opts:
                opts += ' -G_' + VOICEGROUP
            cfg = cfg[:m.start(2)] + opts + cfg[m.end(2):]
        done.append('%s: new music (%s)' % (label, where))
    ov.write(MIDI_CFG, cfg)
    return done


if __name__ == '__main__':
    write_files()
    print('Wrote %d songs to %s' % (len(SONGS), MUSIC_DIR))
