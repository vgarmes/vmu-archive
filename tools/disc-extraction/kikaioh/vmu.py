"""Decode Choukou Senki Kikaioh's VMU screens from /1ST_READ.BIN.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Redump `Choukou Senki Kikaioh (Japan)` (T-1206M, V1.003, 1999-11-18).
1ST_READ.BIN loads at 0x8C010000.

The save file's descriptor sits at 0x8C160CE8: its VMS description
(ｷｶｲｵｰ ｾｰﾌﾞﾃﾞｰﾀ), its Dreamcast description (キカイオー　セーブデータ),
then two screens of 192 bytes each, stored upright: packed 1 bit per pixel,
high bit first, 1 = lit, the archive's own encoding.

    0x8C160D28  the キカイオー logo
    0x8C160DE8  ··· ACCESS ··· over the logo

0x8C014066 sends one of them to every VMU (ports A-D, both slots): the logo
when its first argument is 0, ACCESS otherwise. 0x8C0141B8 does the same for
one VMU. Nothing animates.

Writes inbox/ (a .png and sidecar per screen, for `pnpm icons:import`) and
contact-sheet.png.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

LOAD = 0x8C010000
HEADER = 'ｷｶｲｵｰ ｾｰﾌﾞﾃﾞｰﾀ'.encode('shift_jis')
DESCRIPTOR = 0x8C160CE8
BASE = dict(game='Tech Romancer', publisher='Capcom', year=1999)
# (stem, title, address, tags). The logo is the Japanese one, so both are
# Japan's alone.
SCREENS = [
    ('logo', 'Title screen', 0x8C160D28, ['logo']),
    ('access', 'Access', 0x8C160DE8, ['logo', 'memory-card']),
]


def screen(b, off):
    im = Image.new('1', (48, 32), 1)
    im.putdata([0 if b[off + i // 8] >> (7 - i % 8) & 1 else 1 for i in range(48 * 32)])
    return im


def main(src, out):
    b = Path(src).read_bytes()
    if not b[DESCRIPTOR - LOAD:].startswith(HEADER):
        sys.exit(f'no save descriptor at {DESCRIPTOR:#x}: not the dump this was written for')
    out = Path(out)
    inbox = out / 'inbox'
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    images = []
    for stem, title, addr, tags in SCREENS:
        im = screen(b, addr - LOAD)
        im.save(inbox / f'kikaioh-{stem}.png')
        meta = dict(title=title, **BASE, region='ntsc-j', tags=tags)
        (inbox / f'kikaioh-{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        images.append(im)
        print(f'{addr:#x}', title)
    sheet = Image.new('1', (len(images) * 52, 32), 1)
    for n, im in enumerate(images):
        sheet.paste(im, (n * 52, 0))
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(out / 'contact-sheet.png')
    print(len(images), 'screens ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
