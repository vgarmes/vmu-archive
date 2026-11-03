"""Decode Bakuretsu Muteki Bangaioh's VMU screens and animations from /1ST_READ.BIN.

    python3 vmu.py <1ST_READ.BIN> <out dir>

JP v1.003. The game keeps its VMU art inside the executable, not in a file of its
own: 24 screens of 192 bytes from 0x8C05D460, packed 1 bit per pixel (high bit
first, 1 = lit), rotated 180 degrees as the VMU's LCD expects. Reversing the whole
bit stream turns one upright.

Right after them, 0x8C05E6FC holds seven pointers to animation scripts for the
game's generic sprite animator (0x8C01141A). Each step is 4 bytes: s16 screen,
u8 hold in ticks, u8 op. Op 0 shows the screen for the hold, 1 shows it and stops,
3 jumps to the step in the screen field (the loop). The VMU routine at 0x8C05125C
ticks the player once per video frame (60 Hz) and sends the screen whenever it
changes.

Only one routine starts a script (0x8C0512D2, called from 0x8C014C16): it plays 3
or 5 in game states 17, 18, 23, 24, 29 and 30, depending on the pilot flag at
0x8C4C8E54, and 1 otherwise. Scripts 0, 2, 4 and 6 are never started.

Writes lcd/NN.png (dark = lit, as `pnpm icons:import` reads it), manifest.json
(every screen with its frame in the archive's hex encoding), animations.json and
contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
BANK, SCREENS, SIZE = 0x8C05D460, 24, 192
SCRIPTS, COUNT = 0x8C05E6FC, 7
PLAYED = {1, 3, 5}  # what 0x8C014C16 passes to 0x8C0512D2
HZ = 60


def frame_hex(blk):
    bits = ''.join(f'{x:08b}' for x in blk)[::-1]  # 180 degree turn
    return ''.join(f'{int(bits[i:i + 8], 2):02x}' for i in range(0, len(bits), 8))


def script(b, ptr):
    steps, off = [], ptr - LOAD
    while True:
        screen, hold, op = struct.unpack_from('<hBB', b, off)
        if op == 0:
            steps.append((screen, hold))
        elif op == 1:
            return dict(screens=[screen], loop=False)
        elif op == 3:
            assert screen == 0, 'loops jump back to the first step'
            return dict(screens=[s for s, _ in steps], holds_ticks=[h for _, h in steps],
                        delays_ms=[round(h * 1000 / HZ) for _, h in steps], loop=True)
        else:
            raise ValueError(f'op {op} at {LOAD + off:#x}')
        off += 4


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for n in range(SCREENS):
        off = BANK - LOAD + n * SIZE
        hx = frame_hex(b[off:off + SIZE])
        bits = bin(int(hx, 16))[2:].zfill(48 * 32)
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if c == '1' else 1 for c in bits])
        im.save(out / 'lcd' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', kind='screen', width=48, height=32, offset=off, frame_hex=hx))
        images.append(im)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    ptrs = struct.unpack_from(f'<{COUNT}I', b, SCRIPTS - LOAD)
    anims = []
    for k, p in enumerate(ptrs):
        a = script(b, p)
        anims.append(dict(script=k, played=k in PLAYED, **a))
        print(k, 'played' if k in PLAYED else 'never started', a['screens'], a.get('delays_ms', 'still'))
    shown = {s for a in anims for s in a['screens']}
    assert shown == set(range(SCREENS)), 'every screen belongs to a script'
    (out / 'animations.json').write_text(json.dumps(dict(animations=anims), indent=1))

    scale, cols = 3, 6
    cw, ch = 48 * scale + 16, 32 * scale + 30
    rows = (SCREENS + cols - 1) // cols
    sheet = Image.new('RGB', (16 + cols * cw, 44 + rows * ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'1ST_READ.BIN @ {BANK:#x}: {SCREENS} screens', fill='black')
    for n, im in enumerate(images):
        x, y = 16 + n % cols * cw, 44 + n // cols * ch
        draw.text((x, y), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')
    print(SCREENS, 'screens ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
