"""Shared helpers for the Emerald editor."""

import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def read_text(path):
    with open(path, encoding='utf-8', errors='surrogateescape') as f:
        return f.read()


def write_text(path, text):
    # Leave a file alone when nothing in it changed. Rewriting it anyway gives it a
    # new timestamp, and the build then recompiles everything that uses it.
    try:
        with open(path, encoding='utf-8', errors='surrogateescape', newline='') as f:
            if f.read() == text:
                return
    except OSError:
        pass
    tmp = path + '.editor-tmp'
    with open(tmp, 'w', encoding='utf-8', errors='surrogateescape', newline='') as f:
        f.write(text)
    os.replace(tmp, path)


def project_path(rel):
    """Resolve a project-relative path, refusing anything outside the project."""
    full = os.path.abspath(os.path.join(ROOT, rel))
    if full != ROOT and not full.startswith(ROOT + os.sep):
        raise ValueError('path outside project')
    return full


def pretty_name(suffix):
    """THUNDER_PUNCH -> Thunder Punch. trainerproc turns it back into the same constant."""
    return ' '.join(w.capitalize() if not w.isdigit() else w for w in suffix.split('_') if w)


def to_const(prefix, value):
    """Mirror of trainerproc's fprint_constant: 'Aqua Grunt M' -> TRAINER_PIC_AQUA_GRUNT_M."""
    value = value.strip()
    if not value:
        return prefix + '_NONE'
    if value.startswith(prefix + '_'):
        return value
    out = []
    for c in value:
        if c.isascii() and c.isalnum():
            out.append(c.upper())
        elif c == "'":
            continue
        else:
            out.append('_')
    return prefix + '_' + ''.join(out)


def species_const(value):
    """Mirror of trainerproc's fprint_species (collapses separators, handles gender signs)."""
    value = value.strip()
    if not value:
        return 'SPECIES_NONE'
    if value.startswith('SPECIES_'):
        return value
    out = []
    underscore = False
    for c in value:
        if c.isascii() and c.isalnum():
            if underscore:
                out.append('_')
            underscore = False
            out.append(c.upper())
        elif c in "'%’":
            continue
        elif c == '♂':
            underscore = False
            out.append('_M')
        elif c == '♀':
            underscore = False
            out.append('_F')
        elif c == 'é':
            if underscore:
                out.append('_')
            underscore = False
            out.append('E')
        else:
            underscore = True
    return 'SPECIES_' + ''.join(out)


def const_to_name(prefix, const):
    if const.startswith(prefix + '_'):
        return pretty_name(const[len(prefix) + 1:])
    return const


def map_display_name(folder):
    """Route102 -> Route 102, PetalburgCity_Gym -> Petalburg City Gym."""
    s = folder.replace('_', ' ')
    s = re.sub(r'(?<=[a-z])(?=[A-Z0-9])', ' ', s)
    s = re.sub(r'(?<=[0-9])(?=[A-Z][a-z])', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()
