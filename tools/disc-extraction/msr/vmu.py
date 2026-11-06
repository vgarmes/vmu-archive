"""Pull Metropolis Street Racer's VMU screens and font from its program, for `pnpm icons:import`.

    python3 vmu.py <MSR.BIN> <inbox dir>

The game itself is MSR.BIN (1ST_READ.BIN only loads it), which runs from
0x8C010000. Its three screens are 192 bytes each, back to back; its font is a
character map and 38 glyphs just before them. Writes one PNG (dark = lit) and
sidecar per screen, and the font as one sprite. See
content/games/metropolis-street-racer.md for how the code uses them. Needs no
third-party modules.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bios'))
import png  # noqa: E402

GAME = 'Metropolis Street Racer'
LOAD = 0x8C010000  # where MSR.BIN runs from
SIZE = 192  # 48x32 at 1 bit a dot

# 0x8C02F224 (port mask, screen, flag) spreads screen bit i, read as
# byte i >> 3, bit i & 7 (low bit first), to a byte of 0xFF or 0, row-major,
# and sends that through the library's LCD write (0x8C11D4C4). 1 is lit;
# nothing is turned or inverted.
SCREENS = [
    # 0x8C010418 sends it to all four ports at boot; 0x8C02EF08 puts it back
    # when a slot's countdown (0x8C10C7A4, set to 150 with OK!) runs out.
    dict(address=0x8C10C9F0, stem='title', title='Title screen', tags=['logo']),
    # 0x8C02F3AE, from the save-finished callback 0x8C06EC5C.
    dict(address=0x8C10CAB0, stem='ok', title='OK!', tags=['memory-card']),
    # 0x8C06EFD4, as a save starts.
    dict(address=0x8C10CB70, stem='saving', title='Saving', tags=['memory-card']),
]

# The VMU printf (0x8C02EB00, nothing calls it) maps a character through
# CHARMAP to a glyph of 8 bytes, one a row. A row's top 5 bits are its dots;
# row 0's low 3 bits are the glyph's advance, and the renderer draws one
# column fewer (the last is the gap). Glyph 37, character 0x0A, is the
# newline: it's never drawn, and is 8 empty bytes.
CHARMAP = 0x8C10C7AC
FONT = 0x8C10C8AC
GLYPHS = 38
NEWLINE = 37
FONT_W = 5


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def screen(blk):
    return [[blk[(y * 48 + x) >> 3] >> ((y * 48 + x) & 7) & 1 for x in range(48)] for y in range(32)]


def font(b):
    raw = at(b, FONT, 8 * GLYPHS)
    charmap = at(b, CHARMAP, 256)
    expect = {0x0A: NEWLINE, **{c: c - 0x40 for c in range(0x41, 0x5B)},
              **{c: c - 0x60 for c in range(0x61, 0x7B)}, **{c: c - 0x30 + 27 for c in range(0x30, 0x3A)}}
    if any(charmap[c] != expect.get(c, 0) for c in range(256)):
        sys.exit(f'{CHARMAP:#x}: not the character map this script knows; is this MSR.BIN?')
    if any(raw[8 * NEWLINE:8 * NEWLINE + 8]):
        sys.exit('the newline glyph is not empty')
    kept = range(NEWLINE)
    widths = [raw[8 * n] & 7 for n in kept]
    rows = [[raw[8 * n + y] >> (7 - x) & 1 for x in range(FONT_W)] for n in kept for y in range(8)]
    # Rebuild the disc's bytes from what's kept: the dots, row 0's advance,
    # and the newline's empty glyph.
    rebuilt = bytearray()
    for n in kept:
        for y in range(8):
            dots = sum(bit << (7 - x) for x, bit in enumerate(rows[8 * n + y]))
            rebuilt.append(dots | (widths[n] if y == 0 else 0))
    rebuilt += bytes(8)
    if bytes(rebuilt) != raw:
        sys.exit('the font does not rebuild to the disc bytes')
    return rows, widths


def main(program, inbox):
    b = Path(program).read_bytes()
    inbox = Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    # Same logo across the top of each, so a wrong file shows up here.
    logos = {at(b, s['address'] + 24, 48) for s in SCREENS}
    if len(logos) != 1 or at(b, SCREENS[-1]['address'] + SIZE, 4) != b'SNIG':
        sys.exit('the screens are not where this script expects; is this MSR.BIN?')
    for i, s in enumerate(SCREENS):
        png.save(inbox / f'msr-{s["stem"]}.png', screen(at(b, s['address'], SIZE)))
        meta = dict(title=s['title'], game=GAME, tags=s['tags'])
        if i == 0:
            meta.update(publisher='Sega', year=2000)
        (inbox / f'msr-{s["stem"]}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(f'{s["stem"]}: {s["address"]:#010x}')
    rows, widths = font(b)
    png.save(inbox / 'msr-font.png', rows)
    meta = dict(title='Font', game=GAME, sprite=True, glyphs=dict(height=8, width=widths),
                source=dict(file='/MSR.BIN', offset=FONT - LOAD), tags=['font', 'unused'])
    (inbox / 'msr-font.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f'font: {len(widths)} glyphs at {FONT:#010x}, rebuilt byte for byte')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
