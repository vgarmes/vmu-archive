"""Decode Power Stone's and Power Stone 2's VMU screens from /1ST_READ.BIN.

    python3 vmu.py <ps1|ps2> <1ST_READ.BIN> <out dir>

Both games run through the 0x0C000000 alias of main RAM, so 1ST_READ.BIN loads
at 0x0C010000. Each has two screens of 192 bytes, packed 1 bit per pixel, high bit
first, stored upright. Each screen has its own routine that expands it into a
byte buffer (8 = lit, 0 = unlit) before it goes to the VMU, and that routine
decides the polarity:

    mov.b @r9+,r0 ; … ; shld r2,r3 ; tst r12,r3 ; bt zero ; bra next ; mov.b r11,@r5 ; zero: mov.b r13,@r5

stores the first register for a 1 bit and the second for a 0 bit. Power Stone's
title routine stores 8 for a 0 bit, so its title is stored inverted; every other
screen stores 8 for a 1 bit.

Writes lcd/<release>-NN.png (dark = lit, as `pnpm icons:import` reads it),
<release>.json (each screen with its frame in the archive's hex encoding) and a
contact sheet.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x0C010000
SIZE = 192
RELEASES = {
    # routine that expands the screen, where it loads the screen's address, what it shows
    'ps1': dict(game='Power Stone', screens=[
        dict(routine=0x0C020174, literal=0x0C020254, what='title', inverted=True),
        dict(routine=0x0C0201BC, literal=0x0C02025C, what='access', inverted=False),
    ]),
    'ps2': dict(game='Power Stone 2', screens=[
        dict(routine=0x0C03A670, literal=0x0C03A74C, what='title', inverted=False),
        dict(routine=0x0C03A6B6, literal=0x0C03A754, what='access', inverted=False),
    ]),
}


def main(release, src, out):
    cfg = RELEASES[release]
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for n, s in enumerate(cfg['screens']):
        ptr = struct.unpack_from('<I', b, s['literal'] - LOAD)[0]
        blk = b[ptr - LOAD:ptr - LOAD + SIZE]
        if s['inverted']:
            blk = bytes(x ^ 0xFF for x in blk)
        bits = ''.join(f'{x:08b}' for x in blk)
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if c == '1' else 1 for c in bits])
        name = f'{release}-{n:02d}'
        im.save(out / 'lcd' / f'{name}.png')
        manifest.append(dict(name=name, game=cfg['game'], what=s['what'], pointer=f'{ptr:#x}',
                             routine=f'{s["routine"]:#x}', inverted=s['inverted'], frame_hex=blk.hex()))
        images.append((name, im))
        print(name, cfg['game'], s['what'], f'{ptr:#x}', 'stored inverted' if s['inverted'] else '')
    (out / f'{release}.json').write_text(json.dumps(manifest, indent=1))

    scale = 3
    cw = 48 * scale + 16
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + 32 * scale + 30), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'{cfg["game"]}: 1ST_READ.BIN', fill='black')
    for k, (name, im) in enumerate(images):
        x = 16 + k * cw
        draw.text((x, 44), name, fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / f'{release}-contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 4 or sys.argv[1] not in RELEASES:
        sys.exit(__doc__)
    main(*sys.argv[1:])
