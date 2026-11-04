"""Makes palette index 0 of a GBA sprite PNG transparent, the way the game draws it."""

import struct
import zlib


def with_transparent_background(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return data
    pos = 8
    chunks = []
    color_type = None
    has_trns = False
    while pos + 8 <= len(data):
        length, ctype = struct.unpack('>I4s', data[pos:pos + 8])
        chunk = data[pos:pos + 12 + length]
        if ctype == b'IHDR':
            color_type = data[pos + 8 + 9]
        if ctype == b'tRNS':
            has_trns = True
        chunks.append((ctype, chunk))
        pos += 12 + length
        if ctype == b'IEND':
            break
    if color_type != 3 or has_trns:
        return data  # not paletted, or already has transparency
    trns_body = b'tRNS' + b'\x00'
    trns = struct.pack('>I', 1) + trns_body + struct.pack('>I', zlib.crc32(trns_body) & 0xffffffff)
    out = [data[:8]]
    for ctype, chunk in chunks:
        if ctype == b'IDAT' and trns is not None:
            out.append(trns)
            trns = None
        out.append(chunk)
    return b''.join(out)
