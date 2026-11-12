"""Extract the screens of Kikaioh Mini, the VMU game Choukou Senki Kikaioh carries.

    python3 mini.py <KIKAIOH.BIN> <out dir>

The game writes /GAME/KIKAIOH.BIN to the memory card as KIKAIOH___VM: a whole
VMU program (VMS description ｷｶｲｵｰ ﾐﾆ at +0x200, キカイオー ミニ after it),
63341 bytes, run from 0 in the VMU's flash. Addresses below are offsets into
it; read the code with ../common/lc86k.py. It is Capcom's Power Stone Mini
engine: same timer setup, same way of drawing.

All art is plain 1 bit per dot, high bit first, upright, rows of whole bytes.
Screens are drawn in two ways, both taking the art's address in TRH:TRL:

- 0x0DC3 copies 192 bytes straight to the LCD (the title, CAPCOM and
  copyright screens, the money screens).
- 0xAE57 copies them to a 192-byte buffer in work RAM (high scores, money
  held), which is then sent to the LCD. 0xA8F7 is the general version
  (x byte 0x84, row 0x85 / 6, bytes per row 0x86, rows 0x87): AND (0xA95F)
  and OR (0xA92A) variants draw masked sprites over a screen.

Not here yet: the sub-menus (built like the main menu, around strips of
items that slide), the start/how-to-play menu, the three games'
own sprites (drawn by routines of their own, straight to the LCD) and the
digits and fonts drawn over the score screens.

Writes:
  KIKAIOH.VMS      the program, as a VMU file image
  inbox/           a .png and sidecar per piece for `pnpm icons:import`
  contact-sheet.png
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HEADER = 'ｷｶｲｵｰ ﾐﾆ'.encode('shift_jis')  # VMS description, at +0x200
SIZE = 63341
BASE = dict(game='Tech Romancer', publisher='Capcom', year=1999)
FILE = '/GAME/KIKAIOH.BIN'
# Estimated, not measured, as for Power Stone Mini: timer 0's high byte
# (t0prr 0xF5, t0hr 0xF8, set at 0x1134) interrupts at about 62 Hz if its
# input is the 32.768 kHz crystal's cycle clock, and its handler (0x0052)
# is what the main loop (0x11AE) wakes on.
TICK_MS = 16

LOVE = ('love-and-punch', 'Love & Punch')
GATTAI = ('mugen-gattai', 'Mugen Gattai!!')
JANKEN = ('janken-fight', 'Janken Fight!')

# (stem, title, address, tags, Japanese text?): 48x32 stills, each drawn
# whole by 0x0DC3 or 0xAE57 (callers listed).
SCREENS = [
    ('caution', 'Caution: replace the battery', 0xA81D, ['system'], True),  # 0x11A8, at start-up
    ('capcom', 'Capcom logo', 0x8CC8, ['logo'], False),  # 0x1222, 0x130A
    ('copyright', 'Copyright', 0x8D88, ['letters'], False),  # 0x1250, 0x131F
    ('great-5000', 'Great!! 5000G get!', 0x4421, ['minigame'], False),  # 0x20EB
    ('total', 'Total G get!!', 0x44E1, ['minigame'], False),  # 0x23BC
    ('g-get', 'G get!!', 0x5AF0, ['minigame'], False),  # 0x86D9
    ('great-10000', 'Great!! 10000G get!', 0x5BB0, ['minigame'], False),  # 0x8666, by 0xA8F7
    ('money', 'Money held', 0x9CF0, ['menu'], True),  # 0xAFCF
    ('hiscore-' + LOVE[0], f'High score: {LOVE[1]}', 0x9880, ['menu', LOVE[0]], True),  # 0xB128
    ('hiscore-' + GATTAI[0], f'High score: {GATTAI[1]}', 0x9940, ['menu', GATTAI[0]], True),  # 0xB10C
    ('hiscore-' + JANKEN[0], f'High score: {JANKEN[1]}', 0x9A00, ['menu', JANKEN[0]], True),  # 0xB0F2
]
# Rules pages: 0x1D49 picks one of three lists of big-endian pointers, ended
# by a 0 byte, and shows a page per button press.
RULES = [(LOVE, 0x9E40), (GATTAI, 0xA149), (JANKEN, 0xA390)]
# Title: 0x12B9 shows the 192 bytes at 0x8BE4, then 0x12CF moves the start
# down one row (6 bytes) a tick until it reaches 0x8C08, 6 rows on, and waits
# for A+B there. The logo rises as PRESS: A+B comes into view.
TITLE, TITLE_ROWS = 0x8BE4, 6
TITLE_HOLD_MS = 2000  # the last frame stays until A+B; this is only for playback
# Main menu (0x134E): 0x13FE clears the work RAM buffer, 0x1424 copies the
# header's 48 bytes to rows 0-7, 0x1451 copies rows 2-20 of the selected
# item (40x24, 5 bytes a row) to rows 10-28, 0x1487 ORs the frame (40x24)
# over rows 8-31, and 0x14C6/0x14EA puts an arrow (8x24) in the last byte of
# rows 8-31. 0x13AE sends the buffer to the LCD.
MENU_HEADER, MENU_FRAME = 0x8E48, 0x8E78
MENU_ITEMS = [  # 0x1377: by 0x1B
    ('play', 'Play a minigame', 0x8F38),
    ('hiscores', 'See the high scores', 0x8FB0),
    ('money', 'See the money held', 0x9028),
    ('sound', 'Sound settings', 0x90A0),
]
# Resting on an item (0x151D), the menu adds 1 to 0x3E a tick and, when
# 0x3E & 7 is 0, calls 0x14C6, which adds 1 more and draws the arrow frame
# picked by 0x3E & 0x18: 0x8EF0, 0x8F08, 0x8F20, then 0x8EF0 again. So the
# arrow moves every 7 ticks. Between items the strip of items slides 2 rows
# a tick (0x156F); that isn't kept.
ARROW = [0x8EF0, 0x8F08, 0x8F20, 0x8EF0]
ARROW_TICKS = 7


def bits(prog, addr, w, h):
    """w x h at addr as an Image ('1', 0 = lit)."""
    bpr = (w + 7) // 8
    im = Image.new('1', (w, h), 1)
    px = im.load()
    for y in range(h):
        for x in range(w):
            if prog[addr + y * bpr + x // 8] >> (7 - x % 8) & 1:
                px[x, y] = 0
    return im


def from_bytes(buf):
    return bits(buf, 0, 48, 32)


def stack(images):
    out = Image.new('1', (48, 32 * len(images)), 1)
    for k, im in enumerate(images):
        out.paste(im, (0, 32 * k))
    return out


def pointers(prog, t):
    """A list of big-endian pointers ended by a 0 byte (what 0x1D61 reads)."""
    out = []
    while prog[t]:
        out.append(prog[t] << 8 | prog[t + 1])
        t += 2
    return out, t + 1


def menu(prog, item, arrow):
    """The main menu's work RAM buffer as 0x134E builds it."""
    buf = bytearray(192)
    buf[0:48] = prog[MENU_HEADER:MENU_HEADER + 48]
    for r in range(19):
        src = item + 10 + 5 * r
        buf[60 + 6 * r:60 + 6 * r + 5] = prog[src:src + 5]
    for r in range(24):
        for c in range(5):
            buf[48 + 6 * r + c] |= prog[MENU_FRAME + 5 * r + c]
    for r in range(24):
        buf[53 + 6 * r] = prog[arrow + r]
    return bytes(buf)


def main(src, out):
    b = Path(src).read_bytes()
    assert b[0x200:0x200 + len(HEADER)] == HEADER and b[0] == 0x21, 'not Kikaioh Mini'
    prog = b[:SIZE]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'KIKAIOH.VMS').write_bytes(prog)
    inbox = out / 'inbox'
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir()

    pieces = []  # (stem, image, meta)

    def piece(stem, title, im, tags, jp, **extra):
        meta = dict(title=title, **BASE, **({'region': 'ntsc-j'} if jp else {}), tags=['minigame'] + tags, **extra)
        pieces.append((stem, im, meta))

    frames = [from_bytes(prog[TITLE + 6 * r:TITLE + 6 * r + 192]) for r in range(TITLE_ROWS + 1)]
    piece('title', 'Kikaioh Mini title screen', stack(frames), ['logo'], True,
          frameDelaysMs=[TICK_MS] * TITLE_ROWS + [TITLE_HOLD_MS])
    for stem, title, addr, tags, jp in SCREENS:
        piece(stem, title, bits(prog, addr, 48, 32), [t for t in tags if t != 'minigame'], jp)
    for (key, name), t in RULES:
        pages, end = pointers(prog, t)
        assert pages == [end + 192 * k for k in range(len(pages))], f'{name}: pages not back to back'
        for k, a in enumerate(pages):
            piece(f'rules-{key}-{k + 1}', f'{name} rules ({k + 1}/{len(pages)})', bits(prog, a, 48, 32),
                  ['letters', key], True)
    for stem, title, item in MENU_ITEMS:
        frames = [from_bytes(menu(prog, item, a)) for a in ARROW]
        piece(f'menu-{stem}', f'Menu: {title}', stack(frames), ['menu'], True, frameDelayMs=ARROW_TICKS * TICK_MS)

    stems = [p[0] for p in pieces]
    assert len(stems) == len(set(stems)), 'two pieces share a file name'
    for stem, im, meta in pieces:
        im.save(inbox / f'kikaioh-mini-{stem}.png')
        (inbox / f'kikaioh-mini-{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(len(pieces), 'pieces ->', inbox)

    S, pad, cols = 3, 12, 6
    cw, chh = 48 * S + pad, 32 * S + pad + 14
    rows = (len(pieces) + cols - 1) // cols
    cs = Image.new('RGB', (cols * cw + pad, rows * chh + pad), '#f5f2e9')
    d = ImageDraw.Draw(cs)
    for n, (stem, im, _) in enumerate(pieces):
        x, y = pad + n % cols * cw, pad + n // cols * chh
        d.text((x, y), stem[:24], fill='black')
        first = im.crop((0, 0, 48, 32)).convert('RGB')
        cs.paste(first.resize((48 * S, 32 * S), Image.NEAREST), (x, y + 14))
    cs.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
