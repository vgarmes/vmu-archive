"""Pull Sonic Shuffle's VMU screens and sprites from its program, for `pnpm icons:import`.

    python3 vmu.py <1ST_READ.BIN> <inbox dir> [notes dir]

With a notes dir (public/notes/sonic-shuffle/), also draws an example hand
there, hand.png, built from the sheet as the game builds it.

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

# An example hand for the notes, drawn as 0x8C0A57A4 draws one: seven card
# values (7 is the S card, 8 Eggman's), the slot under the cursor, and the
# count beside the gem. The ring and its plus or minus stay cleared.
EXAMPLE_HAND = dict(cards=[3, 1, 6, 7, 2, 8, 5], cursor=3, count=2)
INK = (23, 23, 23)  # the site's thumbnails' ink, as Power Stone's notes use; unlit is transparent


def write_png(path, px):
    """Native-size palette PNG: lit dots INK, unlit transparent."""
    import zlib
    raw = b''.join(b'\0' + bytes(row) for row in px)
    def chunk(t, c):
        return struct.pack('>I', len(c)) + t + c + struct.pack('>I', zlib.crc32(t + c))
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n'
                           + chunk(b'IHDR', struct.pack('>IIBBBBB', len(px[0]), len(px), 8, 3, 0, 0, 0))
                           + chunk(b'PLTE', bytes([255, 255, 255, *INK]))
                           + chunk(b'tRNS', b'\0')
                           + chunk(b'IDAT', zlib.compress(raw, 9))
                           + chunk(b'IEND', b''))


def hand_screen(sheet, rects, cards, cursor, count):
    """The hand screen as 0x8C0A57A4 builds it, from the sheet's pieces."""
    screen = [[0] * 48 for _ in range(32)]
    def draw(n, x, y):  # 0x8C0A5554
        sx, sy, w, h = rects[n]
        for r in range(h):
            for c in range(w):
                screen[y + r][x + c] = 1 if sheet[(sy + r) * 48 + sx + c] else 0
    card_x = list(range(3, 45, 6))
    draw(14, card_x[cursor], 0)  # the cursor over the chosen card
    for x, v in zip(card_x, cards):  # card v is piece v - 1
        draw(v - 1, x, 6)
    draw(15, card_x[len(cards) - 1] + 6, 6)  # closes the last card
    draw(19, 2, 23)  # the gem
    draw(8 + count, 14, 24)  # its count, through the table at DIGITS
    return screen


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def words(b, addr, n, fmt='<I'):
    size = struct.calcsize(fmt)
    return [struct.unpack(fmt, at(b, addr + i * size, size))[0] for i in range(n)]


def main(program, inbox, notes=None):
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

    if notes:
        Path(notes).mkdir(parents=True, exist_ok=True)
        write_png(Path(notes) / 'hand.png', hand_screen(sheet, rects, **EXAMPLE_HAND))
        print('example hand ->', Path(notes) / 'hand.png')


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
