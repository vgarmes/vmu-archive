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

Before them are the viewer's two fonts, a byte a row, 8 pixels wide, each
reached through a table of big-endian pointers that 0x0EE6 looks up and
0x26D0 draws 8 rows from:

    0x4380  digits: № then 0-9, 11 glyphs of 8 bytes. № is drawn straight
            from 0x4380, the digits through the table at 0x2874.
    0x43D8  the font: 256 glyphs of 9 bytes, through the table at 0x4CD8.
            The drawer takes 8 rows; the 9th byte is never drawn, and it's
            0 in every glyph.

Writes the three screens and the two fonts (as sprites), each glyph's 8
drawn rows in table order, after checking every pointer and every 9th byte.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

BASE = dict(game='Shenmue', publisher='Sega', year=1999, region='ntsc-j')
SOURCE = '/PASSPORT/ATU/SYEN.BIN'
# (offset, stem, title, tags)
SCREENS = [
    (0x5445, 'brush-stroke', 'Goodies brush stroke', []),
    (0x5505, 'dreamcast-logo', 'Goodies Dreamcast logo', ['logo']),
    (0x55c5, 'title', 'Goodies title', ['logo']),
]
DIGITS, DIGIT_TABLE = 0x4380, 0x2874  # № at DIGITS, then 0-9 through the table
FONT, FONT_TABLE, FONT_COUNT, FONT_STRIDE = 0x43D8, 0x4CD8, 256, 9
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
    for stem, title, offset, rows in (('digits', 'Goodies viewer digits', DIGITS, digit_rows(data)),
                                      ('font', 'Goodies viewer font', FONT, font_rows(data))):
        bitmap(rows, 0, 8, len(rows)).save(inbox / f'passport-sprite-{stem}.png')
        (inbox / f'passport-sprite-{stem}.json').write_text(json.dumps(
            dict(title=title, **BASE, tags=['font'], sprite=True, glyphs={'height': 8},
                 source={'file': SOURCE, 'offset': offset}), ensure_ascii=False, indent=1))
    print(len(SCREENS), 'screens and the two fonts ->', inbox)


def pointer(data, table, n):
    return data[table + 2 * n] << 8 | data[table + 2 * n + 1]


def digit_rows(data):
    """№ and 0-9, 8 rows each, as the digit table lays them out."""
    for n in range(10):
        if pointer(data, DIGIT_TABLE, n) != DIGITS + 8 * (n + 1):
            sys.exit(f'digit table entry {n} does not point at digit {n}')
    if pointer(data, DIGIT_TABLE, 10) != 0xFFFF:
        sys.exit('the digit table has more than 10 entries')
    return data[DIGITS:DIGITS + 8 * 11]


def font_rows(data):
    """The 8 rows 0x26D0 draws of each glyph, in table order. The 9th byte of
    each record must be 0, so leaving it out loses nothing."""
    rows = b''
    for n in range(FONT_COUNT):
        at = pointer(data, FONT_TABLE, n)
        if at != FONT + FONT_STRIDE * n:
            sys.exit(f'font table entry {n} points at {at:#x}, not {FONT + FONT_STRIDE * n:#x}')
        if data[at + 8]:
            sys.exit(f'glyph {n}: its 9th byte is {data[at + 8]:#04x}, not 0')
        rows += data[at:at + 8]
    if FONT + FONT_STRIDE * FONT_COUNT != FONT_TABLE:
        sys.exit('the font does not end where its table starts')
    return rows


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
