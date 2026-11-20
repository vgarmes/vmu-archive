"""Redraw Virtua Tennis 2's turning title, the way the game draws it.

    python3 turn.py <1ST_READ.BIN> <out dir>

Writes inbox/*.png and sidecars for `pnpm icons:import`: one animation per
title logo, its frames stacked top to bottom (dark = lit).

The game doesn't store the turn: it draws it from the logo screen every update
with a small 3D renderer. This script re-runs that renderer in single-precision
floats. Addresses are for the European release; see
content/games/virtua-tennis-2.md.
"""
import json
import math
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image

LOAD = 0x8C010000
SCREENS = 0x8C17EF8C  # the eleven screens, 192 bytes each, turned 180°
STEP_MS = 33  # the VMU code runs every second frame of the game loop (0x8C032F74)


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def const(b, addr):
    return struct.unpack_from('<f', b, addr - LOAD)[0]


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def ftrc(x):
    """FTRC: toward zero, saturating."""
    if x != x:
        return 0
    return max(-0x80000000, min(0x7FFFFFFF, int(x)))


def lit(screen, x, y):
    """A dot of a screen stored turned 180°: row 31-y, byte 5-x/8, bit x%8."""
    return screen[(31 - y) * 6 + 5 - (x >> 3)] >> (x & 7) & 1


def fsca(a):
    t = 2 * math.pi * (a & 0xFFFF) / 65536
    return f32(math.sin(t)), f32(math.cos(t))


def mat_mul_cols(cols, i, j, a, s, c):
    """The library's rotations (0x8C10A090, 0x8C10A300): two of the matrix's
    columns become c*i + s*j and -s*i + c*j, each through FTRV."""
    ci, cj = cols[i], cols[j]
    cols[i] = [f32(f32(c * p) + f32(s * q)) for p, q in zip(ci, cj)]
    cols[j] = [f32(f32(-s * p) + f32(c * q)) for p, q in zip(ci, cj)]


def frames(b, screen):
    # Constants of the renderer (0x8C033EFC): a field of view of 20 out of 90,
    # scaled to 3π/8 across and π/4 down: 24 dots each side of tan 15°, 16
    # each side of tan 10°. A dot is divided by the same scale it's projected
    # with, so at a depth of 1 the logo lands dot for dot on the screen.
    fov = f32(20.0)
    sx = f32(24.0 / f32(math.tan(f32(f32(fov * const(b, 0x8C034008)) / f32(90.0)))))
    sy = f32(16.0 / f32(math.tan(f32(f32(fov * const(b, 0x8C034010)) / f32(90.0)))))
    dz1, da1 = const(b, 0x8C033510), const(b, 0x8C033514)  # -1/15, 546.13
    dz2, da2 = const(b, 0x8C033518), const(b, 0x8C03351C)  # 1/60, 955.73
    z = const(b, 0x8C0332B0)  # -0.1 (0x8C0331D0, at the VMUs' setup)
    tilt, spin = -16384, 0  # 0x8C17F7E0, 0x8C17F7E4: -90°, 0
    dots = [(x, y) for y in range(32) for x in range(48) if lit(screen, x, y)]
    out = []
    while True:
        # The update (0x8C033486): swing down while the tilt is negative,
        # then spin while z is below -1, then stop at z = 1.
        if tilt < 0:
            z = f32(z + dz1)
            tilt = s16(ftrc(f32(f32(tilt) + da1)))
        elif z < -1.0:
            z = f32(z + dz2)
            spin = s16(ftrc(f32(f32(spin) + da2)))
        else:
            break
        # The matrix (0x8C033D7E): identity, translate (0, 0, z), rotate Y by
        # 0x8C17F7E2 (always 0), X by the tilt, Z by the spin.
        cols = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        s, c = fsca(tilt)
        mat_mul_cols(cols, 1, 2, tilt, s, c)
        s, c = fsca(spin)
        mat_mul_cols(cols, 0, 1, spin, s, c)
        frame = bytearray(48 * 32)
        for x, y in dots:
            # 0x8C033EA4 makes the dot on the plane at depth 1, then
            # 0x8C034044 overwrites its z with 0: the plane passes through the
            # eye, and the translation alone sets its depth.
            p = (f32((x - 24) / sx), f32((16 - y) / sy), 0.0)
            # 0x8C108E20 with the 3x3 part, then + translation (0x8C10A6E0).
            q = [f32(f32(f32(cols[0][k] * p[0]) + f32(cols[1][k] * p[1])) + f32(cols[2][k] * p[2]))
                 for k in range(3)]
            q[2] = f32(q[2] + z)
            if q[2] == 0:
                continue
            d = abs(q[2])  # 0x8C03406C: a point behind the eye is drawn mirrored in z
            px = ftrc(f32(f32(f32(q[0] * sx) / d) + 24.0))  # 0x8C033EC8
            py = ftrc(f32(16.0 - f32(f32(q[1] * sy) / d)))
            if 0 <= px <= 47 and 0 <= py <= 31:  # 0x8C0340DA
                frame[py * 48 + px] = 1
        out.append(bytes(frame))
    # Then z is 1 and the screen is drawn plain (0x8C033D7C skips the 3D).
    out.append(bytes(lit(screen, x, y) for y in range(32) for x in range(48)))
    return out


LOGOS = [
    dict(index=0, name='turn-power-smash-2', title='Title screen turning (Power Smash 2)', region='ntsc-j'),
    dict(index=1, name='turn', title='Title screen turning', region='pal'),
    dict(index=2, name='turn-tennis-2k2', title='Title screen turning (Tennis 2K2)', region='ntsc-u'),
]


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)
    for logo in LOGOS:
        addr = SCREENS + logo['index'] * 192
        fs = frames(b, b[addr - LOAD:addr - LOAD + 192])
        im = Image.new('1', (48, 32 * len(fs)), 1)
        im.putdata([0 if v else 1 for f in fs for v in f])
        stem = f'vt2-{logo["name"]}'
        im.save(inbox / f'{stem}.png')
        meta = dict(title=logo['title'], game='virtua-tennis-2', region=logo['region'], tags=['logo'],
                    frameDelayMs=STEP_MS, posterFrame=len(fs) - 1)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(f'{logo["title"]}: {len(fs)} frames')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
