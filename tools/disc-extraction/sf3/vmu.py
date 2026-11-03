"""Decode Street Fighter III 3rd Strike's VMU screens from /1ST_READ.BIN.

    python3 vmu.py <1ST_READ.BIN> <out dir>

JP v1.003. 1ST_READ.BIN loads at 0x8C010000. Four screens of 192 bytes each sit
back to back at 0x8CCB2310, stored upright: packed 1 bit per pixel, high bit
first, 1 = lit, the archive's own encoding.

0x8CB1730A is the only code that sends anything to a VMU screen (through
0x8CD50FE0). For each of the 8 VMU slots whose state byte changed, it picks the
screen by state, expands it into a byte buffer (8 for a 1 bit) and sends it:

    1  title logo   0x8CCB2310  (literal at 0x8CB17394)
    2  ACCESS...    0x8CCB23D0  (literal at 0x8CB17398)
    3  OK!          0x8CCB2490  (literal at 0x8CB1739C)
    4  ERROR!       0x8CCB2550  (literal at 0x8CB17460)

Nothing animates.

Writes lcd/NN.png (dark = lit, as `pnpm icons:import` reads it), manifest.json and
contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SIZE = 192
# (state, literal holding the screen's address, what it shows)
SCREENS = [
    (1, 0x8CB17394, 'Title logo'),
    (2, 0x8CB17398, 'ACCESS...'),
    (3, 0x8CB1739C, 'OK!'),
    (4, 0x8CB17460, 'ERROR!'),
]


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for n, (state, literal, what) in enumerate(SCREENS):
        ptr = struct.unpack_from('<I', b, literal - LOAD)[0]
        off = ptr - LOAD
        blk = b[off:off + SIZE]
        bits = ''.join(f'{x:08b}' for x in blk)
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if c == '1' else 1 for c in bits])
        im.save(out / 'lcd' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', kind='screen', what=what, state=state, width=48,
                             height=32, pointer=f'{ptr:#x}', offset=off, frame_hex=blk.hex()))
        images.append(im)
        print(n, f'state {state}', f'{ptr:#x}', what)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    scale = 3
    cw, ch = 48 * scale + 16, 32 * scale + 30
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'1ST_READ.BIN, drawn by 0x8CB1730A: {len(images)} screens', fill='black')
    for n, im in enumerate(images):
        x = 16 + n * cw
        draw.text((x, 44), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')
    print(len(images), 'screens ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
