"""Turn the Goodies viewer on the Passport disc into input for `pnpm icons:import`.

    python3 passport.py <SYEN.BIN> <inbox dir>

/PASSPORT/ATU/SYEN.BIN on disc 4 (Passport v1.010) is the VMU program Passport
installs to show the Goodies. Its art is stored as plain 1-bit screens, 192 bytes
each (6 bytes a row, high bit first, 1 = lit), back to back:

    0x5445  a brush-stroke drawing
    0x5505  the Dreamcast logo
    0x55c5  あつめて シェンムー, the viewer's title, white on black
    0x5685  the four built-in characters: portraits, then three poses each
            (already in the archive from the Goodies import)

Before them, from 0x4380 to 0x4c80, is the viewer's font: one byte per row,
8 pixels wide, glyphs of more than one height. It's kept as stored, as one
8-pixel-wide strip, since where each glyph starts wasn't decoded.

Writes the three screens and the font strip (as a sprite).
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

BASE = dict(game='Shenmue', publisher='Sega', year=1999, region='JP')
SOURCE = '/PASSPORT/ATU/SYEN.BIN'
# (offset, stem, title, tags)
SCREENS = [
    (0x5445, 'brush-stroke', 'Goodies brush stroke', []),
    (0x5505, 'dreamcast-logo', 'Goodies Dreamcast logo', ['logo']),
    (0x55c5, 'title', 'Goodies title', ['logo']),
]
FONT = (0x4380, 0x4C80)
CHARACTERS = 0x5685  # first of the four built-in characters' pictures


def bitmap(data, offset, width, height):
    stride = width // 8
    im = Image.new('1', (width, height), 1)
    for y in range(height):
        for x in range(width):
            if data[offset + y * stride + x // 8] >> (7 - x % 8) & 1:
                im.putpixel((x, y), 0)
    return im


def main(src, inbox):
    data, inbox = Path(src).read_bytes(), Path(inbox)
    assert len(data) == 25263, 'expected SYEN.BIN from Passport v1.010'
    assert SCREENS[-1][0] + 192 == CHARACTERS
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    for offset, stem, title, tags in SCREENS:
        bitmap(data, offset, 48, 32).save(inbox / f'passport-{stem}.png')
        (inbox / f'passport-{stem}.json').write_text(
            json.dumps(dict(title=title, **BASE, tags=tags), ensure_ascii=False, indent=1))
    start, end = FONT
    bitmap(data, start, 8, end - start).save(inbox / 'passport-sprite-font.png')
    (inbox / 'passport-sprite-font.json').write_text(json.dumps(
        dict(title='Goodies viewer font', **BASE, tags=['font', 'sheet'], sprite=True,
             source={'file': SOURCE, 'offset': start}), ensure_ascii=False, indent=1))
    print(len(SCREENS), 'screens and the font ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
