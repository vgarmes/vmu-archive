"""Pull Virtua Tennis 2's VMU screens out of its program.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes inbox/*.png and their sidecars, for `pnpm icons:import` (dark = lit),
and contact-sheet.png.

Addresses are for the European release (Redump `Virtua Tennis 2 - Sega
Professional Tennis (Europe) (En,Ja,Fr,De,Es)`); 1ST_READ.BIN loads at
0x8C010000. See content/games/virtua-tennis-2.md.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SIZE = 192  # 48x32 at 1 bit a dot

# Eleven screens back to back, 1 bit a dot, high bit first, turned 180° as the
# LCD takes them. The copy at 0x8C033CFE indexes them from this base.
BASE_ADDR = 0x8C17EF8C
# The title shown is picked by the release global at 0x8C2C9EE4 (0x8C03317A):
# 0 shows screen 0, 1 shows screen 2, anything else screen 1. This European
# program sets it to 2 at start (0x8C010D4A), so it shows only its own logo.
SCREENS = [
    dict(name='title-power-smash-2', title='Title screen (Power Smash 2)', tags=['logo'], region='ntsc-j'),
    dict(name='title', title='Title screen', tags=['logo'], region='pal'),
    dict(name='title-tennis-2k2', title='Title screen (Tennis 2K2)', tags=['logo'], region='ntsc-u'),
    dict(name='ok', title='OK', tags=['memory-card']),
    dict(name='ng', title='NG', tags=['memory-card']),
    dict(name='1p', title='1P', tags=['status']),
    dict(name='2p', title='2P', tags=['status']),
    dict(name='3p', title='3P', tags=['status']),
    dict(name='4p', title='4P', tags=['status']),
    dict(name='now-loading', title='Now Loading', tags=['memory-card']),
    dict(name='now-saving', title='Now Saving', tags=['memory-card']),
]
GAME = dict(game='virtua-tennis-2', publisher='Sega', year=2001)


def screen_image(blk):
    bits = ''.join(f'{x:08b}' for x in blk)[::-1]  # turn 180°
    im = Image.new('1', (48, 32), 1)
    im.putdata([0 if c == '1' else 1 for c in bits])
    return im


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)
    images = []
    for n, s in enumerate(SCREENS):
        addr = BASE_ADDR + n * SIZE
        im = screen_image(b[addr - LOAD:addr - LOAD + SIZE])
        stem = f'vt2-{n:02d}-{s["name"]}'
        im.save(inbox / f'{stem}.png')
        meta = dict(title=s['title'], tags=s['tags'], **GAME)
        if 'region' in s:
            meta['region'] = s['region']
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        images.append((s['title'], im))
        print(f'{n:2} {addr:#x} {s["title"]}')

    scale, cols = 2, 6
    cw, ch = 48 * scale + 12, 32 * scale + 24
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new('RGB', (12 + cols * cw, 40 + rows * ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), 'Virtua Tennis 2: 1ST_READ.BIN', fill='black')
    for k, (what, im) in enumerate(images):
        x, y = 12 + (k % cols) * cw, 36 + (k // cols) * ch
        draw.text((x, y), what[:18], fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
