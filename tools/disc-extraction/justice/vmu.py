"""Decode Moero! Justice Gakuen's VMU screens from /1ST_READ.BIN.

    python3 vmu.py <1ST_READ.BIN> <out dir>

JP v1.004. The game runs through the 0x0C000000 alias of main RAM, so
1ST_READ.BIN loads at 0x0C010000 and its pointers start with 0x0C, not 0x8C.

A table at 0x0C1F5AB0, right after the save-file descriptors (MJUSTICE_SYS and
the rest), points at four screens of 192 bytes each, stored upright: packed
1 bit per pixel, high bit first, 1 = lit, the archive's own encoding. They are
two pairs, picked by 0x0C033BD6, which is true when the byte at 0x0C3E0028 is 0:

    0  Moero! Justice Gakuen logo    1  ACCESS, under that logo
    2  Project Justice logo          3  ACCESS, under that logo

0x0C021474 redraws screen (pair + state) on every VMU once every 64 calls, and
0x0C021540 draws the pair's ACCESS screen on one VMU at once. Nothing animates.

Writes lcd/NN.png (dark = lit, as `pnpm icons:import` reads it), manifest.json and
contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x0C010000
TABLE, SCREENS, SIZE = 0x0C1F5AB0, 4, 192
NAMES = ['Moero! Justice Gakuen logo', 'ACCESS (Moero! Justice Gakuen)',
         'Project Justice logo', 'ACCESS (Project Justice)']


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for n, ptr in enumerate(struct.unpack_from(f'<{SCREENS}I', b, TABLE - LOAD)):
        off = ptr - LOAD
        blk = b[off:off + SIZE]
        bits = ''.join(f'{x:08b}' for x in blk)
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if c == '1' else 1 for c in bits])
        im.save(out / 'lcd' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', kind='screen', what=NAMES[n], width=48, height=32,
                             pointer=f'{ptr:#x}', offset=off, frame_hex=blk.hex()))
        images.append(im)
        print(n, f'{ptr:#x}', NAMES[n])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    scale = 3
    cw, ch = 48 * scale + 16, 32 * scale + 30
    sheet = Image.new('RGB', (16 + SCREENS * cw, 44 + ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'1ST_READ.BIN table @ {TABLE:#x}: {SCREENS} screens', fill='black')
    for n, im in enumerate(images):
        x = 16 + n * cw
        draw.text((x, 44), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')
    print(SCREENS, 'screens ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
