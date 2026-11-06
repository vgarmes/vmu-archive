"""Pull Sonic Shuffle's VMU screens and sprites from its program, for `pnpm icons:import`.

    python3 vmu.py <1ST_READ.BIN> <inbox dir>

Two whole screens, 192 bytes each (1 bit a dot, high bit first), and one
48x32 sheet of one byte a dot that a rectangle table cuts into the 21 pieces
the hand screen is built from. Writes one PNG (dark = lit) and sidecar per
screen, and the pieces as sprites, one per set the code looks up together.
Checks every table it follows, and rebuilds the sheet's bytes from the
sprites. See content/games/sonic-shuffle.md for how the code uses them. Needs
no third-party modules.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bios'))
import png  # noqa: E402

GAME = 'Sonic Shuffle'
LOAD = 0x8C010000  # where 1ST_READ.BIN runs from
FILE = '/1ST_READ.BIN'

# The save's VMS texts sit just before the sheet; they identify the program.
VMS_NAME = 0x8C0FCDD0
VMS_NAME_BYTES = 'ｿﾆｯｸ    ｼｬｯﾌﾙ   '.encode('shift_jis')

# 0x8C0A5A2E (buffer, n) spreads screen n of this table, 6 bytes a row, high
# bit first, into a port's buffer of one byte a dot (8 lit, 0 unlit): 32 rows
# for screen 1, only 22 for screen 0. Its four callers all pass 1.
SCREEN_TABLE = 0x8C0FD574
SCREENS = [
    dict(stem='no-card', title='No card', unused=True, tags=[]),
    dict(stem='logo', title='Sonic Shuffle logo', tags=['logo'], replaces='sonic-shuffle-logo'),
]

# 0x8C0A5554 (buffer, n, x, y) copies rectangle n of RECTS (x, y, width,
# height: four shorts) out of SHEET, 48 bytes a row, onto the buffer.
SHEET = 0x8C0FCDF4
RECTS = 0x8C0FD5AC
PIECES = 21
LIT = 8

# Each set: its rectangles in the game's order, one under the next.
SETS = [
    # A card's value v draws piece v - 1 (1 to 6, then the S and Eggman
    # cards); 0x8C0A573C swaps in piece 20, face down, under one status.
    dict(stem='cards', title='Cards', pieces=[0, 1, 2, 3, 4, 5, 6, 7, 20], tags=['cards']),
    # Looked up through the table at 0x8C0FD670 by a count from 0 to 5.
    dict(stem='digits', title='Digits', pieces=[8, 9, 10, 11, 12, 13], tags=['font', 'digits']),
    dict(stem='cursor', title='Cursor', pieces=[14], tags=[]),
    dict(stem='hand-end', title='End of the hand', pieces=[15], tags=['cards']),
    dict(stem='ring', title='Ring', pieces=[16], tags=[]),
    dict(stem='plus-and-minus', title='Plus and minus', pieces=[17, 18], tags=[]),
    dict(stem='gem', title='Gem', pieces=[19], tags=[]),
]
DIGITS = 0x8C0FD670
CARD_X = 0x8C0FD654


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def words(b, addr, n, fmt='<I'):
    size = struct.calcsize(fmt)
    return [struct.unpack(fmt, at(b, addr + i * size, size))[0] for i in range(n)]


def main(program, inbox):
    b = Path(program).read_bytes()
    if at(b, VMS_NAME, len(VMS_NAME_BYTES)) != VMS_NAME_BYTES:
        sys.exit(f'{VMS_NAME:#x}: not the save name this script knows; is this the Japanese 1ST_READ.BIN?')
    inbox = Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)

    for addr, s in zip(words(b, SCREEN_TABLE, 2), SCREENS):
        px = png.bits(at(b, addr, 192), 48, 32)
        png.save(inbox / f'sonic-shuffle-{s["stem"]}.png', px)
        meta = dict(title=s['title'], game=GAME, tags=s['tags'])
        for k in ('unused', 'replaces'):
            if k in s:
                meta[k] = s[k]
        (inbox / f'sonic-shuffle-{s["stem"]}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(f'{s["stem"]}: {addr:#010x}')

    sheet = at(b, SHEET, 48 * 32)
    if set(sheet) != {0, LIT}:
        sys.exit('the sheet is not one byte a dot, 0 or 8')
    rects = [words(b, RECTS + 8 * n, 4, '<h') for n in range(PIECES)]
    if words(b, DIGITS, 6) != list(range(8, 14)) or words(b, CARD_X, 7) != list(range(3, 45, 6)):
        sys.exit('the digit or card tables are not what this script knows')
    if sorted(n for s in SETS for n in s['pieces']) != list(range(PIECES)):
        sys.exit('every piece belongs in exactly one set')

    rebuilt = bytearray(len(sheet))
    for s in SETS:
        boxes = [rects[n] for n in s['pieces']]
        width = max(w for _, _, w, _ in boxes)
        rows = []
        for x, y, w, h in boxes:
            for r in range(h):
                line = sheet[(y + r) * 48 + x:(y + r) * 48 + x + w]
                rows.append([1 if v else 0 for v in line] + [0] * (width - w))
                rebuilt[(y + r) * 48 + x:(y + r) * 48 + x + w] = line
        png.save(inbox / f'sonic-shuffle-{s["stem"]}.png', rows)
        heights = [h for *_, h in boxes]
        widths = [w for _, _, w, _ in boxes]
        meta = dict(title=s['title'], game=GAME, sprite=True)
        if len(boxes) > 1:
            meta['glyphs'] = dict(height=heights[0] if len(set(heights)) == 1 else heights)
            if len(set(widths)) > 1:
                meta['glyphs']['width'] = widths
        x, y, *_ = boxes[0]
        meta['source'] = dict(file=FILE, entry=', '.join(map(str, s['pieces'])),
                              offset=SHEET - LOAD + y * 48 + x)
        meta['tags'] = s['tags']
        (inbox / f'sonic-shuffle-{s["stem"]}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(f'{s["stem"]}: pieces {s["pieces"]}, {width}x{len(rows)}')
    # Dots outside every rectangle are all unlit, so the sprites keep the
    # whole sheet.
    if bytes(rebuilt) != sheet:
        sys.exit('the sprites do not rebuild to the sheet')
    print('sheet rebuilt byte for byte from the sprites')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
