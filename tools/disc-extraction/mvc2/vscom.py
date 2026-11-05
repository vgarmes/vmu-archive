"""Extract the art of VS.COM, the VMU program Marvel vs. Capcom 2 carries.

    python3 vscom.py <VS4.BIN> <out dir>

Marvel vs. Capcom 2 (JP) keeps a VMU program in the disc's root as /VS4.BIN
(28,646 bytes), a VMS image: LC86K code from 0, its VMS header at 0x200
(description ﾏｰｳﾞﾙ VS.ｶﾌﾟｺﾝ 2_VS.COMﾌｧｲﾙ). The game writes it to the memory
card as the "VS.COM file", with the player's data at 0x0A00. Addresses below
are offsets into the file, which is how the VMU's CPU sees its flash; read the
code with ../common/lc86k.py.

The art is plain 1 bit per dot, high bit first, upright, in rows of whole
bytes; a set bit is a lit dot. The program builds each screen in the VMU's
work RAM, 6 bytes a row, with blitters (copy 0x13C1, OR 0x1429) that read
d3 bytes x d4 rows through LDC from TRH:TRL and write at d1+d2, skipping d5
bytes after each row. 0x1315 then copies the 192 bytes to the LCD in order:
no turn, no inversion. 0x12A6 sends a stored 48x32 bitmap straight to the LCD
the same way. Pointer tables are big-endian, read by 0x14EA.

Many tables are indexed by 0x2B, a byte of the player's data (0x0A4D, clamped
to 0-2): 0 picks the Japanese art, 1 and 2 the English, and 1 alone the
copyright with CAPCOM U.S.A.

Writes:
  inbox/            a .png and sidecar per piece for `pnpm icons:import`:
                    whole screens (stills, and two animations rebuilt from
                    the code), everything else as sprites, one per bitmap or
                    per run of bitmaps stored back to back, one under the next
  contact-sheet.png everything, for checking
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HEADER = b'MVS.C2_VS.COM'  # VMS header, at 0x200
SIZE = 28646
FILE = '/VS4.BIN'
BASE = dict(game='Marvel vs. Capcom 2', publisher='Capcom', year=2000)
TAG = 'vs-com'
# Timer 0's high byte (0x10B1: t0prr 0xF5, t0hr 0xF8, t0con 0x84) interrupts
# at 0x0023, whose handler (0x0052) sets the flag the main loop waits on
# (0x10FC), so one step of the program is one timer tick: about 62 Hz if the
# timer counts the 32.768 kHz crystal's cycle clock (ocr 0xA3). Estimated.
TICK_MS = 16

# Pointer tables, each checked against the runs below.
T_COPYRIGHT = 0x272E   # [0x2B] 48x32, drawn by 0x159F
T_MENU_BG = 0x2734     # [0x2B] 48x32, drawn by 0x15E9
T_MENU_ITEMS = 0x273A  # [0x2B] -> 8 items (0x2A == 0), drawn by 0x15E9 at row 12
T_MENU_ITEMS_9 = 0x2740  # [0x2B] -> 9 items, the stage list added (0x2A != 0)
T_SLIDE = 0x292E       # [0xDA] 8 frames of 32x16, drawn by 0x1538
T_NO_POINTS = 0x5173   # [0x2B] 48x32, drawn at 0x26DC


def table(prog, addr, n):
    """n big-endian pointers at addr."""
    return [prog[addr + 2 * i] << 8 | prog[addr + 2 * i + 1] for i in range(n)]


def bits(prog, addr, w, h):
    """w x h at addr, as an Image ('1', 0 = lit)."""
    bpr = (w + 7) // 8
    im = Image.new('1', (w, h), 1)
    px = im.load()
    for y in range(h):
        for x in range(w):
            if prog[addr + y * bpr + x // 8] >> (7 - x % 8) & 1:
                px[x, y] = 0
    return im


def pack(im):
    """The bytes an image was read from (the inverse of bits)."""
    bpr = (im.width + 7) // 8
    out = bytearray(bpr * im.height)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] == 0:
                out[y * bpr + x // 8] |= 0x80 >> (x % 8)
    return bytes(out)


def stack(images):
    out = Image.new('1', (max(i.width for i in images), sum(i.height for i in images)), 1)
    y = 0
    for im in images:
        out.paste(im, (0, y))
        y += im.height
    return out


class Screen:
    """The work RAM screen the blitters draw into (48x32, 6 bytes a row)."""

    def __init__(self):
        self.ram = bytearray(192)

    def blit(self, prog, src, d3, d4, dst, d5=0, op='copy'):
        """0x13C1 (copy) or 0x1429 (OR): d4 rows of d3 bytes from src, rows
        contiguous; the destination skips d5 bytes after each row."""
        a = dst
        for r in range(d4):
            for c in range(d3):
                b = prog[src + r * d3 + c]
                self.ram[a] = b if op == 'copy' else self.ram[a] | b
                a += 1
            a += d5

    def image(self):
        return bits(self.ram, 0, 48, 32)


def full(prog, addr):
    s = Screen()
    s.blit(prog, addr, 6, 32, 0)  # 0x1505, or 0x12A6 straight to the LCD
    return s


def capcom_logo(prog):
    """The opening, as the state machine at 0x1169 plays it, one screen a tick.

    State 0 (0x1178) clears the screen and draws the CAPCOM logo (0x1517:
    0x293E, 48x9 at row 4) and sets a 64-tick count. State 1 (0x118E), each
    tick: while 0xDA < 7 it steps 0xDA and draws slide frame 0xDA (0x1538:
    table 0x292E, 32x16 at x 16, row 16), so a figure slides in from the
    right 4 dots a tick; then every 4th tick (0xD9) it flips 0xDB and draws
    the last frame a row higher or back (0x155B: row 15 or 16). When the count
    runs out (tick 64) it blanks the screen; the copyright and title follow.
    """
    slide = table(prog, T_SLIDE, 8)
    s = Screen()
    s.blit(prog, 0x293E, 6, 9, 0x18)
    shots = [s.image()]
    da, d9, db = 0xFF, 0, 0
    for _ in range(1, 64):
        if da != 7:
            da = (da + 1) & 0xFF
            s.blit(prog, slide[da], 4, 16, 0x62, 2)
        else:
            d9 += 1
            if d9 == 4:
                d9 = 0
                db = 1 - db
                s.blit(prog, slide[7], 4, 16, 0x62 if db == 0 else 0x5C, 2)
        shots.append(s.image())
    return shots


def menu(prog, lang):
    """The menu as 0x15E9 draws it on entry (item 0x28 = 0): the background,
    the item at row 12, and two arrows ORed at x 16, rows 3 and 22. The menu
    loop (0x599D) flips 0xDA every 8 ticks and redraws, swapping the arrows
    between two frames; it starts with 0xDA = 0."""
    shots = []
    for da in (0, 1):
        s = full(prog, table(prog, T_MENU_BG, 3)[lang])
        items = table(prog, table(prog, T_MENU_ITEMS, 3)[lang], 8)
        s.blit(prog, items[0], 6, 9, 0x48)
        top, bottom = (0x2BC4, 0x2BD4) if da == 0 else (0x2BCC, 0x2BDC)
        s.blit(prog, top, 1, 8, 0x14, 5, 'or')
        s.blit(prog, bottom, 1, 8, 0x86, 5, 'or')
        shots.append(s.image())
    return shots


def merge(shots, ms):
    """Back-to-back identical screens as one, with its delay."""
    frames, delays = [], []
    for im in shots:
        if frames and pack(frames[-1]) == pack(im):
            delays[-1] += ms
        else:
            frames.append(im)
            delays.append(ms)
    return frames, delays


# (stem, title, address, tags, region, unused) - stored 48x32 bitmaps shown
# whole. Pairs are picked by 0x2B: Japanese, then English.
STILLS = [
    ('copyright', 'Copyright', 0x2CB4, [], None, False),
    # 0x2B = 1 only; 0 and 2 show the one above.
    ('copyright-usa', 'Copyright (Capcom U.S.A.)', 0x2D74, [], 'ntsc-u', False),
    ('not-enough-points-jp', 'Not enough points', 0x5179, ['letters'], 'ntsc-j', False),
    ('not-enough-points', 'Not enough points', 0x5239, ['letters'], None, False),
    # The trade, through the link cable (0x5F6A, 0x5FEE, 0x603C, 0x61B0).
    ('trade-connect-jp', 'Trade: please connect', 0x47A7, ['letters'], 'ntsc-j', False),
    ('trade-connect', 'Trade: please connect', 0x4867, ['letters'], None, False),
    ('trade-trading-jp', 'Trade: trading', 0x4927, ['letters'], 'ntsc-j', False),
    ('trade-wait', 'Trade: please wait', 0x49E7, ['letters'], None, False),
    ('trade-failed-jp', 'Trade: failed', 0x4AA7, ['letters'], 'ntsc-j', False),
    ('trade-error', 'Trade: error', 0x4B67, ['letters'], None, False),
    ('trade-done-jp', 'Trade: complete, please disconnect', 0x4C27, ['letters'], 'ntsc-j', False),
    ('trade-finished', 'Trade: finished, please disconnect', 0x4CE7, ['letters'], None, False),
    # 0x1104 shows the first when the battery is low, before the player's data
    # (and so 0x2B) is read; nothing loads the English one.
    ('caution-jp', 'Caution: change the battery', 0x57B2, ['system'], 'ntsc-j', False),
    ('caution', 'Caution: change the battery', 0x5872, ['system'], None, True),
]


def sprites(prog):
    """(stem, title, address, image, tags, region, unused, glyphs)."""
    out = []

    def run(stem, title, addr, w, h, n, tags, region=None, unused=False):
        """n bitmaps of w x h stored back to back from addr, one under the next;
        the sprite's bytes are checked to rebuild the program's."""
        size = (w + 7) // 8 * h
        im = stack([bits(prog, addr + k * size, w, h) for k in range(n)])
        assert pack(im) == prog[addr:addr + n * size], stem
        out.append((stem, title, addr, im, tags, region, unused, {'height': h} if n > 1 else None))
        return [addr + k * size for k in range(n)]

    def check(t, n, want, what):
        if table(prog, t, n) != want:
            sys.exit(f'{what}: table {t:#x} does not match')

    # Opening and menu. The menu's backgrounds are kept whole here: the item
    # drawn over rows 12-20 hides part of the disc.
    bg = run('menu-backgrounds', 'Menu backgrounds', 0x2E34, 48, 32, 2, ['menu'], 'ntsc-j')
    check(T_MENU_BG, 3, [bg[0], bg[1], bg[1]], 'menu backgrounds')
    check(T_COPYRIGHT, 3, [0x2CB4, 0x2D74, 0x2CB4], 'copyright')
    check(T_NO_POINTS, 3, [0x5179, 0x5239, 0x5239], 'not enough points')
    check(T_SLIDE, 8, [0x2B54 - 0x40 * k for k in range(8)], 'slide')
    run('menu-arrows', 'Menu arrows', 0x2BC4, 8, 8, 4, ['menu'])
    items = run('menu-items', 'Menu items', 0x2FB4, 48, 9, 15, ['menu', 'letters'], 'ntsc-j')
    lv, pts_jp, pts, shop_jp, shop, chars_jp, chars, trade_jp, trade, time, rank, sound_jp, sound, \
        stages_jp, stages = items
    lists = table(prog, T_MENU_ITEMS, 3) + table(prog, T_MENU_ITEMS_9, 3)
    assert lists[2] == lists[1] and lists[5] == lists[4], 'menu: 0x2B = 2 has its own items'
    check(lists[0], 8, [lv, pts_jp, shop_jp, chars_jp, trade_jp, time, rank, sound_jp], 'menu, Japanese')
    check(lists[1], 8, [lv, pts, shop, chars, trade, time, rank, sound], 'menu, English')
    check(lists[3], 9, [lv, pts_jp, shop_jp, chars_jp, stages_jp, trade_jp, time, rank, sound_jp], 'menu 9, JP')
    check(lists[4], 9, [lv, pts, shop, chars, stages, trade, time, rank, sound], 'menu 9, English')
    # Bits the program never loads: the slide's figure on its own, and the
    # disc of the menu's background.
    run('figure', 'Figure', 0x2974, 16, 16, 1, ['character'], unused=True)
    run('menu-disc', 'Menu disc', 0x2BE4, 16, 32, 1, ['menu'], unused=True)

    # Level and points.
    run('exp', 'EXP!', 0x32DE, 16, 7, 1, ['banner'])
    gauge = run('exp-gauge', 'EXP gauge', 0x32EC, 32, 7, 26, ['status'])
    check(0x28BE, 26, gauge, 'exp gauge')  # index (0xBA >> 2) & 0x3F, at 0x178E
    run('labels', 'Level and points labels', 0x35C4, 48, 7, 4, ['letters'])
    no = run('character-number', 'Character number', 0x366C, 48, 7, 4, ['letters'], 'ntsc-j')
    check(0x27A8, 2, [no[2], no[0]], 'character number, JP')
    check(0x27AC, 2, [no[3], no[1]], 'character number, English')
    r = run('ready-small', 'Standby OK, Ready, New color', 0x3714, 24, 12, 3, ['banner'], 'ntsc-j')
    check(0x27B0, 3, [r[0], r[1], r[1]], 'standby')
    # A 48x20 bitmap (a question mark between arrows) between them and the
    # play-time header: no literal, table or computed address reaches it.
    run('question', 'Question mark', 0x3780, 48, 20, 1, [], unused=True)
    run('play-time-header', 'Dreamcast play time', 0x37F8, 48, 15, 1, ['banner'])
    run('play-time-frame', 'Play time frame', 0x3852, 48, 13, 1, [])
    run('rank-header', 'Rank', 0x38A0, 48, 7, 1, ['banner'])
    run('win-lose', 'Win, lose', 0x38CA, 32, 15, 1, ['letters'])
    ranks = run('net-ranks', 'Net ranks', 0x3906, 16, 15, 8, ['letters'])
    check(0x278A, 8, ranks[::-1], 'net ranks')  # [0xBB]: 0 is G, 7 is S

    # Character list and trade.
    which = run('which-character', 'Which character?', 0x39F6, 48, 8, 2, ['letters'], 'ntsc-j')
    check(0x27B6, 3, [which[0], which[1], which[1]], 'which character')
    yn = run('yes-no', 'Yes, no', 0x3A56, 24, 11, 6, ['letters'])
    check(0x28BA, 2, yn[0:2], 'yes')
    check(0x28B6, 2, yn[3:5], 'no')
    run('ok', 'OK?', 0x3B1C, 16, 7, 1, ['letters'])
    run('get', 'GET!', 0x3B2A, 48, 7, 1, ['banner'])
    sb = run('standby', 'Standby OK, Ready', 0x3B5A, 48, 7, 2, ['banner'], 'ntsc-j')
    check(0x3B54, 3, [sb[0], sb[1], sb[1]], 'standby')
    snd = run('sound-headers', 'Sound settings', 0x3BB4, 48, 12, 2, ['banner'], 'ntsc-j')
    check(0x3BAE, 3, [snd[0], snd[1], snd[1]], 'sound')
    on = run('sound-icons', 'Sound on and off', 0x3C44, 24, 16, 4, [])
    check(0x279A, 2, on[0:2], 'speaker')
    check(0x279E, 2, on[2:4], 'on/off')
    # The 56 characters' names: 63 bitmaps, the Japanese release's names and
    # the overseas ones (Gouki, Akuma...) sharing the rest.
    names = run('character-names', 'Character names', 0x3D04, 48, 7, 63, ['letters'])
    jp, en = table(prog, 0x27C2, 56), table(prog, 0x2832, 56)
    assert set(jp + en) == set(names) and table(prog, 0x27BC, 3) == [0x27C2, 0x2832, 0x2832], 'names'
    # 7 empty bytes, then the digits (table 0x28A2), 8x7 each; the number
    # routines (0x1ACF...) read 8 rows of a digit but draw 7.
    assert prog[0x475A:0x4761] == bytes(7)
    digits = run('digits', 'Digits', 0x4761, 8, 7, 10, ['font', 'digits'])
    check(0x28A2, 10, digits, 'digits')

    # Shop.
    pages = run('page-numbers', 'Page numbers', 0x4DA7, 24, 7, 6, ['digits'])
    check(0x28F2, 3, pages[0::2], 'pages')
    labels = run('shop-prices', 'Shop price labels', 0x4E25, 48, 16, 7, ['letters'])
    check(0x290E, 8, [labels[0]] + labels[0:6] + [labels[5]], 'shop prices')
    asks = run('shop-prompts', 'Shop prompts', 0x50CB, 48, 7, 4, ['letters'], 'ntsc-j')
    check(0x50C5, 3, [asks[0], asks[1], asks[1]], 'get?')
    yn = run('yes-no-small', 'Yes, no (small)', 0x52F9, 24, 7, 3, ['letters'])
    check(0x28F8, 2, [yn[2], yn[0]], 'small yes/no')
    check(0x28FC, 2, [yn[1], yn[0]], 'small yes/no')
    new = run('new', 'New color, new stage, numbers', 0x5338, 48, 7, 9, ['banner'])
    check(0x2900, 7, new[2:], 'stage numbers')
    stage = run('stage-list', 'Stage list', 0x54B2, 48, 16, 8, ['letters'])
    check(0x291E, 8, stage, 'stage list')  # [0x2A]: stages bought
    return out


def main(src, out):
    prog = Path(src).read_bytes()
    assert len(prog) == SIZE and prog[0x200:0x200 + len(HEADER)] == HEADER, 'not VS4.BIN'
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    inbox = out / 'inbox'
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir()

    pieces = []  # (stem, image, meta, preview)

    def meta(title, tags, region=None, unused=False, **more):
        m = dict(title=title, **BASE, **({'region': region} if region else {}), tags=[TAG] + tags)
        if unused:
            m['unused'] = True
        m.update(more)
        return m

    frames, delays = merge(capcom_logo(prog), TICK_MS)
    pieces.append(('capcom-logo', stack(frames), meta('Capcom logo', ['logo'], frameDelaysMs=delays,
                                                      posterFrame=8), frames[8]))
    title = Screen()
    title.blit(prog, 0x2C24, 6, 24, 0)     # 0x15B3: the logo,
    title.blit(prog, 0x2B94, 6, 8, 0x90)   # PRESS A+B under it
    pieces.append(('title', title.image(), meta('Title screen', ['logo']), title.image()))
    for lang, stem, region in ((0, 'menu-jp', 'ntsc-j'), (1, 'menu', None)):
        frames, delays = merge(menu(prog, lang), 8 * TICK_MS)
        pieces.append((stem, stack(frames), meta('Menu', ['menu'], region, frameDelaysMs=delays), frames[0]))
    for stem, name, addr, tags, region, unused in STILLS:
        im = full(prog, addr).image()
        pieces.append((stem, im, meta(name, tags, region, unused), im))
    for stem, name, addr, im, tags, region, unused, glyphs in sprites(prog):
        # A sprite can't be marked unused; the notes say which ones are.
        m = meta(name, tags, region, sprite=True, source={'file': FILE, 'offset': addr})
        if glyphs:
            m['glyphs'] = glyphs
        pieces.append((stem, im, m, im))

    stems = [p[0] for p in pieces]
    assert len(stems) == len(set(stems)), 'two pieces share a file name'
    for stem, im, m, _ in pieces:
        im.save(inbox / f'mvc2-vscom-{stem}.png')
        (inbox / f'mvc2-vscom-{stem}.json').write_text(json.dumps(m, ensure_ascii=False, indent=1))
    print(len(pieces), 'pieces ->', inbox)

    # contact sheet
    S, pad, width = 2, 10, 1400
    x = y = pad
    rowh = 0
    placed = []
    for stem, _, _, im in pieces:
        w, h = im.width * S, min(im.height, 160) * S
        if x + w > width:
            x, y, rowh = pad, y + rowh + 22, 0
        placed.append((stem, im, x, y))
        x += max(w, 110) + pad
        rowh = max(rowh, h)
    cs = Image.new('RGB', (width, y + rowh + 30), '#f5f2e9')
    d = ImageDraw.Draw(cs)
    for stem, im, x, y in placed:
        crop = im.crop((0, 0, im.width, min(im.height, 160)))
        cs.paste(crop.convert('RGB').resize((crop.width * S, crop.height * S), Image.NEAREST), (x, y + 12))
        d.text((x, y), stem, fill='black')
    cs.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
