"""Decode the art only the Japanese VMU BIOS has, from its ROM.

    python3 vmubios_jp.py <jp1004-19980930-315-6208-01.bin> <out dir>

The Japanese BIOS v1.004 (1998/09/30) has no disassembly, so its art was found
by drawing the ROM and comparing it with the US one (vmubios.py). Its code ends
at $3FF7; $E000-$EFFF, the 6x8 font at $E800 included, is the US ROM's byte for
byte. What differs:

    $0473  big font: 48 characters, 8 bytes each, three sets of 16 (thin, bold,
           slashed zero), each 0-9, ':', two arrows, 年, 月, 日. Only $0473 is
           loaded as a base ($1B7E), so it's one table, like the US's 42.
    $05F7  the main menu's text, drawn at 0,0 by $1C93 (from $02FD)
    $0F1A  clock animals: cat (a paw print), fish, helicopter, two frames
           each, both the same bytes. The fish is the US's; the other two are only here.
    $0F4A  each animal's path: a count, then XRAM offsets (as in the US ROM)
    $0F5F  the clock's text, in half-width katakana: モジ センタク, アニメ
           センタク, then the animals' names, ヘリコプター, ネコ, サカナ

Writes an inbox for `pnpm icons:import` (the main menu as a screen; the big
font, cat and helicopter as sprites; all ntsc-j) and contact-sheet.png, which
also plays each path's drawing pass.
"""
import hashlib
import json
import sys
from pathlib import Path

import png
from vmubios import draw_text, xram_xy

MD5 = '1c75e99bdc6d88a855da1ce212c2b38a'
ROM_FILE = 'jp1004-19980930-315-6208-01.bin'
VMU = dict(game='Visual Memory Unit', region='ntsc-j')

BIG_FONT, BIG_GLYPHS = 0x0473, 48
BANNER = 0x05F7
ANIM, ANIMALS = 0x0F1A, ['cat', 'fish', 'helicopter']
# The cat is its paw print: the clock walks it across the screen as footsteps.
TITLES = {'cat': 'Clock cat paw print', 'helicopter': 'Clock helicopter'}
SEQS = 0x0F4A
FONT6 = 0xE800


def write(inbox, stem, px, meta):
    png.save(inbox / f'{stem}.png', px)
    (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))


def main(rom_path, out):
    rom = Path(rom_path).read_bytes()
    if hashlib.md5(rom).hexdigest() != MD5:
        sys.exit(f'{rom_path} is not the Japanese VMU BIOS v1.004 (md5 {MD5})')
    out = Path(out)
    inbox = out / 'inbox'
    inbox.mkdir(parents=True, exist_ok=True)

    font6 = rom[FONT6:FONT6 + 2048]
    banner = rom[BANNER:rom.index(b'\0', BANNER)]
    if not banner.startswith(b'  \x17\x18\x19\x1a'):
        sys.exit('the main menu text does not start with the SEGA logo')
    menu = draw_text(font6, banner)
    write(inbox, 'vmu-jp-main-menu', menu,
          dict(title='Main menu', **VMU, tags=['bios', 'system', 'menu', 'logo']))

    big = rom[BIG_FONT:BIG_FONT + BIG_GLYPHS * 8]
    write(inbox, 'vmu-jp-sprite-big-font', png.bits(big, 8, BIG_GLYPHS * 8),
          dict(title='Big font', **VMU, tags=['bios', 'font', 'digits'], sprite=True,
               glyphs={'height': 8}, source={'file': ROM_FILE, 'offset': BIG_FONT}))

    raw = [rom[ANIM + i * 8:ANIM + i * 8 + 8] for i in range(6)]
    for a, name in enumerate(ANIMALS):
        if raw[a * 2] != raw[a * 2 + 1]:
            sys.exit(f'the {name}\'s two frames differ')
    sprites = [png.bits(raw[a * 2], 8, 8) for a in range(3)]
    for a in (0, 2):  # the fish is the US's, already in the archive
        write(inbox, f'vmu-jp-sprite-{ANIMALS[a]}', sprites[a],
              dict(title=TITLES[ANIMALS[a]], **VMU, tags=['bios', 'clock', 'animal'], sprite=True,
                   source={'file': ROM_FILE, 'offset': ANIM + a * 16}))

    seqs, i = [], SEQS
    while len(seqs) < 3:
        seqs.append(list(rom[i + 1:i + rom[i]]))
        i += rom[i]

    # Contact sheet: the menu, the font's three sets, then each animal's path.
    sets = png.blank(16 * 8, 3 * 8)
    for g in range(BIG_GLYPHS):
        png.paste(sets, png.bits(big[g * 8:g * 8 + 8], 8, 8), (g % 16) * 8, (g // 16) * 8)
    parts = [menu, sets]
    for a, name in enumerate(ANIMALS):
        lcd = png.blank(48, 16)
        for pos in seqs[a]:
            x, y = xram_xy(pos)
            png.paste(lcd, sprites[a], x, y)
        parts.append(lcd)
        print(name, 'walks through', [xram_xy(p) for p in seqs[a]])
    w = max(len(p[0]) for p in parts)
    sheet = []
    for p in parts:
        sheet += [row + [None] * (w - len(row)) for row in p] + [[None] * w] * 4
    png.save(out / 'contact-sheet.png', sheet, scale=4, gap=200)
    print('main menu, big font, cat and helicopter ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
