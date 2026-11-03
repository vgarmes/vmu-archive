"""Decode Crazy Taxi 2's VMU screens from /1ST_READ.BIN.

    python3 vmu.py <1ST_READ.BIN> <out dir>

US v1.004. The game runs through the 0x0C000000 alias of main RAM, so
1ST_READ.BIN loads at 0x0C010000 and its pointers start with 0x0C.

Each screen is a sprite: a big-endian 16-bit width and height (48, 32), then
192 bytes packed 1 bit per pixel, high bit first, 1 = lit, turned 180° (the
way the VMU's LCD takes it). The screens are read through the pointers the
code itself loads:

    0x0C130644  three-pointer table: the logo animation, drawn by 0x0C058C18
    0x0C058DAC  "Now Loading", drawn by 0x0C058CCA
    0x0C058DA8  "Now Saving", drawn by 0x0C058CCA

Writes lcd/NN.png (dark = lit, upright, as `pnpm icons:import` reads it),
manifest.json, animations.json and contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x0C010000
LOGO_TABLE, LOGO_FRAMES = 0x0C130644, 3
LOADING_PTR, SAVING_PTR = 0x0C058DAC, 0x0C058DA8
SIZE = 192
# 0x0C058C18 serves one VMU slot (4 ports x 2 slots) per main-loop frame and
# bumps its counter once all 8 are done; the frame is (counter >> 1) % 3. So a
# frame lasts 16 loop frames: 267 ms at 60 Hz.
LOGO_DELAY_MS = 267


def u32(b, addr):
    return struct.unpack_from('<I', b, addr - LOAD)[0]


def sprite(b, ptr):
    off = ptr - LOAD
    w, h = struct.unpack_from('>HH', b, off)
    if (w, h) != (48, 32):
        sys.exit(f'{ptr:#x}: expected a 48x32 sprite, header says {w}x{h}')
    raw = b[off + 4:off + 4 + SIZE]
    # Turn 180°: reverse the byte order, then the bits in each byte.
    upright = bytes(int(f'{x:08b}'[::-1], 2) for x in raw[::-1])
    return off, upright


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    screens = [(u32(b, LOGO_TABLE + 4 * k), f'Logo, frame {k + 1}') for k in range(LOGO_FRAMES)]
    screens += [(u32(b, LOADING_PTR), 'Now Loading'), (u32(b, SAVING_PTR), 'Now Saving')]
    manifest, images = [], []
    for n, (ptr, what) in enumerate(screens):
        off, blk = sprite(b, ptr)
        bits = ''.join(f'{x:08b}' for x in blk)
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if c == '1' else 1 for c in bits])
        im.save(out / 'lcd' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', kind='screen', what=what, width=48, height=32,
                             pointer=f'{ptr:#x}', offset=off, frame_hex=blk.hex()))
        images.append(im)
        print(n, f'{ptr:#x}', what)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    animations = [
        dict(name='logo', screens=list(range(LOGO_FRAMES)), delays_ms=[LOGO_DELAY_MS] * LOGO_FRAMES),
        dict(name='loading', screens=[3]),
        dict(name='saving', screens=[4]),
    ]
    (out / 'animations.json').write_text(json.dumps(dict(animations=animations), indent=1))

    scale = 3
    cw, ch = 48 * scale + 16, 32 * scale + 30
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'1ST_READ.BIN: {len(images)} screens', fill='black')
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
