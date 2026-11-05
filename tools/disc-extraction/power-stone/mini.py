"""Extract Power Stone Mini, the VMU game Power Stone carries, and its art.

    python3 mini.py <1ST_READ.BIN> <out dir>

Power Stone (JP v1.020) keeps a whole VMU program, パワーストーン ミニ, inside
1ST_READ.BIN: the Falcon, Ayame and Gunrock minigames the game lets you
download to a VMU. It starts at file offset 0x15BB98 (found by its VMS header,
whose description at +0x200 is ﾊﾟﾜｰｽﾄｰﾝﾐﾆ) and is 64 KiB. Addresses below are
offsets into that program, which is how the VMU's CPU sees its flash; read the
code with ../common/lc86k.py.

The art is plain 1 bit per dot, high bit first, upright, in rows of whole
bytes. Sprites the game draws over a background are "masked": each row is the
mask's bytes then the image's bytes, and the game does `and mask; or image`,
so a mask bit of 0 marks the sprite's area. Sizes come from the drawing code
(rows and bytes per row) or from the stride of the pointer tables that list a
sprite's frames.

Writes:
  PSMINI.VMS            the program, as a VMU file image
  inbox/                a .png and sidecar per piece for `pnpm icons:import`:
                        48x32 screens and the Falcon course (a "down" scroll,
                        see course_lap) to content/icons/, everything else as
                        sprites (sheets of frames side by side, masks as their
                        own sprite, lit where the sprite is opaque)
  contact-sheet.png     everything, for checking
  notes/                the portraits' sequences as GIFs, for the game's notes
                        (public/notes/power-stone/; see portrait_sequences)
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HEADER = 'ﾊﾟﾜｰｽﾄｰﾝﾐﾆ'.encode('shift_jis')  # VMS description, at +0x200
SIZE = 0x10000
BASE = dict(game='Power Stone', publisher='Capcom', year=1999)
FILE = '/1ST_READ.BIN'
FONT = 0x8E7B  # the small font's 27 characters


def bits(prog, addr, w, h, masked=False, plane='image', invert=False):
    """Image (or mask) of w x h at addr, as an Image ('1', 0 = lit)."""
    bpr = (w + 7) // 8
    step = bpr * 2 if masked else bpr
    im = Image.new('1', (w, h), 1)
    px = im.load()
    for y in range(h):
        row = prog[addr + y * step:addr + (y + 1) * step]
        data = row[:bpr] if (masked and plane == 'mask') else row[bpr:] if masked else row
        for x in range(w):
            b = data[x // 8] >> (7 - x % 8) & 1
            if plane == 'mask':
                b ^= 1  # mask 0 = opaque: show the sprite's area lit
            if invert:
                b ^= 1
            if b:
                px[x, y] = 0
    return im


def table(prog, addr, n):
    """n big-endian pointers at addr."""
    return [prog[addr + 2 * i] << 8 | prog[addr + 2 * i + 1] for i in range(n)]


def sheet(images, cols=None):
    """Frames side by side (or in rows of `cols`)."""
    cols = cols or len(images)
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    out = Image.new('1', (w * cols, h * rows), 1)
    for i, im in enumerate(images):
        out.paste(im, (i % cols * w, i // cols * h))
    return out


def stack(images):
    out = Image.new('1', (max(i.width for i in images), sum(i.height for i in images)), 1)
    y = 0
    for im in images:
        out.paste(im, (0, y))
        y += im.height
    return out


# (stem, title, [screen addresses], tags, Japanese text?) — 48x32 stills.
# Each character has two portraits, kept as separate stills: the game plays
# them in short sequences (see the game's notes), not worth keeping as such.
SCREENS = [
    ('title', 'Power Stone Mini title screen', [0xAD80], ['logo', 'minigame'], False),
    ('capcom', 'Capcom logo', [0xAE40], ['logo'], False),
    ('copyright', 'Copyright', [0xAF00], [], False),
    ('caution', 'Caution: replace the battery', [0xCAA3], ['system'], True),
    ('menu', 'Menu', [0xA9B4], ['menu'], True),
    ('falcon', 'Falcon', [0xAA74], ['character', 'portrait', 'falcon'], False),
    ('falcon-second', 'Falcon (second)', [0xAB34], ['character', 'portrait', 'falcon'], False),
    ('ayame', 'Ayame', [0xCCE3], ['character', 'portrait', 'ayame'], False),
    ('ayame-second', 'Ayame (second)', [0xCDA3], ['character', 'portrait', 'ayame'], False),
    ('gunrock', 'Gunrock', [0x8591], ['character', 'portrait', 'gunrock'], False),
    ('gunrock-second', 'Gunrock (second)', [0x8651], ['character', 'portrait', 'gunrock'], False),
    ('ayame-stage', "Ayame's Shuriken Training stage", [0xCB63], ['minigame', 'ayame'], False),
    ('ayame-stage-2', "Ayame's Shuriken Training stage (second)", [0xCC23], ['minigame', 'ayame'], False),
    ('slots-medal-get', 'Gun-Gun Slots: medal get', [0x81DD], ['minigame', 'gunrock'], True),
    ('slots-quit', 'Gun-Gun Slots: quit?', [0x8351], ['minigame', 'gunrock'], True),
    ('slots-double-up', 'Gun-Gun Slots: double up?', [0x8411], ['minigame', 'gunrock'], True),
    ('slots-match', 'Gun-Gun Slots: match to double', [0x84D1], ['minigame', 'gunrock'], True),
    ('slots-great', 'Gun-Gun Slots: great!', [0x8C11], ['minigame', 'gunrock'], True),
    ('omake-art-museum', 'Art museum opened', [0x8CD1], ['minigame'], True),
    ('omake-music-hall', 'Music hall opened', [0x8D91], ['minigame'], True),
    ('hiscore-falcon', "High score: Falcon's Aerial Adventure", [0xB980], ['menu', 'falcon'], True),
    ('hiscore-ayame', "High score: Ayame's Shuriken Training", [0xBA40], ['menu', 'ayame'], True),
    ('hiscore-gunrock', "High score: Gun-Gun Slots", [0xBB00], ['menu', 'gunrock'], True),
]
# Rules pages: pointer tables of 192-byte pages, shown one per button press.
RULES = [
    ('falcon', "Falcon's Aerial Adventure", 0xBE80, 4),
    ('ayame', "Ayame's Shuriken Training", 0xC189, 4),
    ('gunrock', 'Gun-Gun Slots', 0xC492, 8),
]


def sprites(prog):
    """(stem, title, image, tags, Japanese text?, offset in the program, glyphs).

    One sprite per stored bitmap, or per run of bitmaps stored back to back,
    its frames one under the next in stored order with their sizes in
    `glyphs` (None for a single bitmap). Nothing is laid out side by side.
    """
    out = []

    def add(stem, title, im, tags, jp, addr, glyphs=None):
        out.append((stem, title, im, tags, jp, addr, glyphs))

    def run(stem, title, addr, w, heights, tags, jp=False, widths=None):
        """Bitmaps stored back to back from addr: frame k is widths[k] x heights[k]."""
        widths = widths or [w] * len(heights)
        frames, a = [], addr
        for fw, fh in zip(widths, heights):
            frames.append(bits(prog, a, fw, fh))
            a += (fw + 7) // 8 * fh
        glyphs = {'height': heights[0] if len(set(heights)) == 1 else heights}
        if len(set(widths)) > 1:
            glyphs['width'] = widths
        add(stem, title, stack(frames), tags, jp, addr, glyphs)

    # A sprite that moves sideways has a table of 8 pointers: copies of it
    # pre-shifted right by 0-7 dots (the game picks one with x & 7), so it
    # can be drawn at any x without shifting at run time. Copy k is copy 0
    # shifted by k (checked for every table; the masked ones store copy 7
    # 24 dots wide), so only copy 0 is kept.
    def shift0(t, w, h, masked, plane='image'):
        first = table(prog, t, 8)[0]
        return bits(prog, first, w, h, masked, plane)

    def masked_tables(stem, title, addrs, w, h, tags):
        """One table per frame of an animation: copy 0 of each, stacked."""
        glyphs = {'height': h} if len(addrs) > 1 else None
        add(stem, title, stack([shift0(t, w, h, True) for t in addrs]), tags, False, addrs[0], glyphs)
        add(stem + '-mask', title + ' (mask)', stack([shift0(t, w, h, True, 'mask') for t in addrs]),
            tags, False, addrs[0], glyphs)

    def plain_table(stem, title, t, w, h, tags):
        add(stem, title, shift0(t, w, h, False), tags, False, t)

    def masked(stem, title, a, w, h, tags):
        add(stem, title, bits(prog, a, w, h, True), tags, False, a)
        add(stem + '-mask', title + ' (mask)', bits(prog, a, w, h, True, 'mask'), tags, False, a)

    # Gun-Gun Slots
    gr = ['minigame', 'gunrock']
    # 48 reel symbols of 16x10, 16 per reel, reel by reel.
    run('slots-reels', 'Gun-Gun Slots reels', 0x8811, 16, [10] * 48, gr)
    # The payline the game ORs over the reels: a whole 48x32 bitmap, but an
    # overlay, not a screen.
    add('slots-payline', 'Gun-Gun Slots payline', bits(prog, 0x8711, 48, 32), gr + ['overlay'], False, 0x8711)
    # The payouts table (0x7FDB) points at 7 frames, some more than once;
    # the frames are stored back to back from 0x7FEF.
    payouts = sorted(set(table(prog, 0x7FDB, 10)))
    if payouts != [0x7FEF + 42 * i for i in range(7)]:
        sys.exit('payouts: the table does not point at 7 frames back to back')
    run('slots-payouts', 'Gun-Gun Slots payouts', 0x7FEF, 48, [7] * 7, gr)
    # The coin's 4 frames and the 10 digits, through tables, are stored 16
    # rows tall (the last rows blank), back to back.
    if table(prog, 0x8155, 4) != [0x815D + 32 * i for i in range(4)]:
        sys.exit('coin: the table does not point at 4 frames back to back')
    run('slots-coin', 'Gun-Gun Slots coin', 0x815D, 16, [16] * 4, gr)
    if table(prog, 0x829D, 10) != [0x82B1 + 16 * i for i in range(10)]:
        sys.exit('slots digits: the table does not point at 10 digits back to back')
    run('slots-digits', 'Gun-Gun Slots digits', 0x82B1, 8, [16] * 10, gr + ['font', 'digits'])
    run('slots-1000-2000', 'Gun-Gun Slots 1000 and 2000', 0x8BD1, 32, [8, 8], gr)
    add('bonus-time', 'Bonus time', bits(prog, 0x8E51, 48, 7), ['minigame', 'banner'], True, 0x8E51)
    # The small font: 27 characters of 8x6, 6 bytes each. Glyphs 0-2 are read
    # directly; 3-6 at 0x8E8D + 6n; the digits twice, at 0x8EA5 + 6n in the
    # right half of the byte and at 0x8EE1 + 6n in the left, so two can be
    # ORed into one byte. It starts where BONUS TIME ends and ends where the
    # sight's table starts.
    assert 0x8E51 + 6 * 7 == FONT and FONT + 6 * 27 == 0x8F1D
    run('font', 'Small font', FONT, 8, [6] * 27, ['minigame', 'font', 'digits'], jp=True)
    # BET and $, read on their own by the slots (0x70C3, 0x75E3).
    add('slots-bet', 'Gun-Gun Slots BET', bits(prog, 0x813D, 16, 6), gr, False, 0x813D)
    add('slots-dollar', 'Gun-Gun Slots dollar sign', bits(prog, 0x8149, 8, 6), gr, False, 0x8149)

    # Ayame's Shuriken Training. Titles say what a sprite plainly is; the
    # rest go by size until someone matches them to play.
    st, ay = 'Shuriken Training', ['minigame', 'ayame']
    plain_table('ayame-sight', f'{st}: sight', 0x8F1D, 16, 6, ay)
    plain_table('ayame-16x8', f'{st}: sprite 16x8', 0x8F8D, 16, 8, ay)
    plain_table('ayame-runner-1', f'{st}: running ninja 1', 0x901D, 24, 8, ay)
    plain_table('ayame-runner-2', f'{st}: running ninja 2', 0x90ED, 24, 8, ay)
    masked('ayame-figure', f'{st}: figure 8x14', 0x91BD, 8, 14, ay)
    masked('ayame-16x10', f'{st}: sprite 16x10', 0x91D9, 16, 10, ay)
    add('ayame-ninja', f'{st}: ninja', bits(prog, 0x9201, 8, 16), ay, False, 0x9201)  # XORed on
    plain_table('ayame-16x7', f'{st}: sprite 16x7', 0x9211, 16, 7, ay)
    masked_tables('ayame-ninjas', f'{st}: ninjas', [0x9291, 0x93A1, 0x94B1, 0x95C1], 16, 8, ay)
    add('ayame-icon', f'{st}: icon', bits(prog, 0x96D1, 8, 8), ay, False, 0x96D1)
    masked('ayame-masked-16x8', f'{st}: sprite 16x8 (masked)', 0x96D9, 16, 8, ay)
    masked_tables('ayame-shuriken', f'{st}: shuriken', [0x96F9, 0x9809], 16, 8, ay)
    masked_tables('ayame-scores', f'{st}: score popups', [0x9919, 0x9A73, 0x9BCD, 0x9D27, 0x9E81], 16, 10,
                  ay + ['digits'])

    # Falcon's Aerial Adventure
    aa, fa = 'Aerial Adventure', ['minigame', 'falcon']
    # Four items, each stored on its own. 0x9FEA, a 16x8 item, is the same
    # pixels as Shuriken Training's 0x8F9D, so the importer keeps it once.
    for k, a in enumerate((0x9FDB, 0x9FE3, 0x9FFA, 0xA5F2)):
        add(f'falcon-item-{k + 1}', f'{aa}: item {k + 1}', bits(prog, a, 8, 8), fa, False, a)
    # Eight flight poses, a table each (the item at 0xA5F2 sits between the
    # fifth and the sixth).
    masked_tables('falcon-flying', f'{aa}: Falcon', [0xA002, 0xA132, 0xA262, 0xA392, 0xA4C2, 0xA5FA, 0xA72A,
                                                     0xA85A], 16, 9, fa + ['character'])
    masked('falcon-24x18', f'{aa}: sprite 24x18', 0xABF4, 24, 18, fa)
    add('falcon-check', f'{aa}: check', bits(prog, 0xA98A, 48, 7), fa + ['banner'], False, 0xA98A)
    # The course as stored, the unreached rows included. What the game shows
    # of it is the "course" scroll (see course_lap).
    add('falcon-course', f'{aa}: course', bits(prog, 0xCE63, 48, 896), fa + ['map'], False, 0xCE63)

    # Shared interface
    # Five banners back to back; the first two are stored 9 rows tall, with a
    # line under them, though the code (0x3C5A, 0x53F4) draws 8 rows of each.
    run('banners', 'Banners', 0xAC60, 48, [9, 9, 8, 8, 8], ['minigame', 'banner'])
    for a, what in ((0xAFC0, 'menu'), (0xB290, 'minigames'), (0xB950, 'high scores'), (0xBBC0, 'sound'),
                    (0xBDF0, 'start'), (0xBE20, 'how to play'), (0xBE50, 'start 2')):
        add(f'menu-header-{a:x}', f'Menu header: {what}', bits(prog, a, 48, 8), ['menu'], True, a)
    add('menu-item-frame', 'Menu item frame', bits(prog, 0xAFF0, 40, 24), ['menu'], False, 0xAFF0)
    run('menu-items-main', 'Menu items: main menu', 0xB0B0, 40, [24] * 4, ['menu'], jp=True)
    run('menu-items-minigames', 'Menu items: minigames', 0xB2C0, 40, [24] * 13, ['menu'], jp=True)
    run('menu-items-sound', 'Menu items: sound', 0xBBF0, 40, [24] * 3, ['menu'])
    run('menu-arrows', 'Menu arrows', 0xB068, 8, [24] * 3, ['menu'])
    run('hiscore-parts', 'High score parts', 0xBD58, 40, [19] * 4, ['menu'], widths=[40, 8, 8, 8])
    return out


def portrait_sequences(prog):
    """How the game shows each character's two portraits, one screen a tick.

    Not archive entries (the portraits are kept as stills): reconstructions
    from the code for the notes, which describe each step and its address.
    Falcon's and Ayame's slide in over the game screen, drawn blank here, and
    Gunrock's payout label, blinking over his portraits, is left out.
    """
    def rows(addr, n=32):
        return [prog[addr + 6 * r:addr + 6 * r + 6] for r in range(n)]

    def screen(rws, invert=False):
        # invert: the screen as 0x3CE1 sends it, every dot flipped.
        out = bytearray(192)
        for y, row in enumerate(rws):
            out[6 * y:6 * y + 6] = row
        return bytes(b ^ 0xFF for b in out) if invert else bytes(out)

    def slide_in(addr):
        # Each tick 2 more rows: the portrait's top c rows at the screen's bottom.
        return [screen([bytes(6)] * (32 - c) + rows(addr, c)) for c in range(2, 33, 2)]

    falcon1, falcon2 = rows(0xAA74), rows(0xAB34)
    ayame1, ayame2 = rows(0xCCE3), rows(0xCDA3)
    gunrock1, gunrock2 = rows(0x8591), rows(0x8651)
    return {
        # 0x319E slide; 0x3205 counts 15 ticks, inverted while bit 1 is set;
        # 0x3212 the second portrait, held by 0x3229.
        'falcon': slide_in(0xAA74)
        + [screen(falcon1, bool(k & 2)) for k in range(15, 0, -1)]
        + [screen(falcon2)] * 33,
        # 0x4505 slide; 0x456C swaps for 31 ticks (first while bit 1 is set);
        # 0x4592 the second, held by 0x45A9.
        'ayame': slide_in(0xCCE3)
        + [screen(ayame1 if k & 2 else ayame2) for k in range(31, 0, -1)]
        + [screen(ayame2)] * 65,
        # The flash win: 0x6964 draws the first; state 0x39 (0x6B9B) flashes,
        # inverted while 0x94 is even as 0x93 counts ticks to 4; then the second
        # (0x6BD6), held by state 0x3C (0x6BF3) before the next spin.
        'gunrock': [screen(gunrock1)]
        + [screen(gunrock1, True)] * 3 + [screen(gunrock1)] * 4 + [screen(gunrock1, True)] * 4
        + [screen(gunrock1)] * 4 + [screen(gunrock1, True)] * 4
        + [screen(gunrock2)] * 48,
    }


NOTE_TICK_MS = 16  # estimated, as COURSE_STEP_MS
NOTE_PAUSE_MS = 1000  # blank before each replay; the game plays them once
INK = (23, 23, 23)  # the site's thumbnails' ink (LCD_INK); unlit dots transparent


def write_gif(screens, path):
    """Native-size GIF: frames merged where they repeat, delays in whole
    hundredths (GIF's unit; at least 20 ms, as browsers slow shorter ones)."""
    runs = []
    for s in [bytes(192)] + screens:
        if runs and runs[-1][0] == s:
            runs[-1][1] += NOTE_TICK_MS
        else:
            runs.append([s, NOTE_TICK_MS])
    runs[0][1] = NOTE_PAUSE_MS
    frames = []
    for s, _ in runs:
        im = Image.new('P', (48, 32), 0)
        im.putpalette([255, 255, 255, *INK])
        px = im.load()
        for i in range(48 * 32):
            if s[i // 8] >> (7 - i % 8) & 1:
                px[i % 48, i // 48] = 1
        frames.append(im)
    frames[0].save(path, save_all=True, append_images=frames[1:], loop=0,
                   duration=[max(20, round(ms / 10) * 10) for _, ms in runs],
                   transparency=0, disposal=2, optimize=False)


COURSE_SECTIONS = 0x34CA  # 18 big-endian pointers: each section's bottom screen
SECTION_ROWS = 128
# Estimated, not measured: timer 0 is set up at 0x1677 (t0prr 0xF5, t0hr 0xF8),
# about 62 Hz if its input is the 32.768 kHz crystal's cycle clock; that it
# paces the game loop wasn't traced. 1 row a tick is the cruising speed.
COURSE_STEP_MS = 16


def course_lap(prog):
    """One lap of Falcon's course as the game shows it, as a 48-wide strip.

    The routine at 0x34EE keeps a position (0x8D:0x8E:0x8F, in rows/256),
    adds the speed (0x83:0x84: 1 row a tick cruising, 0.5-3 with the brake and
    accelerator) and draws the 32 rows starting `position % 128` rows above
    section `position / 128 % 18`'s bottom screen. So the window climbs the
    course and the art moves down the screen. The table repeats three
    stretches five times each, so a lap is 18 x 128 rows; every window of it
    is a run of 32 rows of this strip (checked for all 2304 positions), and
    the lap's end meets its start.
    """
    bases = table(prog, COURSE_SECTIONS, 18)

    def window(p):
        top = bases[p // SECTION_ROWS % 18] - 6 * (p % SECTION_ROWS)
        return [prog[top + 6 * r:top + 6 * r + 6] for r in range(32)]

    lap = 18 * SECTION_ROWS
    rows = window(0)
    for p in range(1, lap):
        rows.insert(0, window(p)[0])
    n = len(rows)
    assert all(rows[n - 32 - p:n - p] == window(p) for p in range(lap)), 'course windows'
    assert window(lap) == window(0), 'course loop'
    im = Image.new('1', (48, n), 1)
    px = im.load()
    for y, row in enumerate(rows):
        for x in range(48):
            if row[x // 8] >> (7 - x % 8) & 1:
                px[x, y] = 0
    return im


def main(src, out):
    b = Path(src).read_bytes()
    at = b.find(HEADER) - 0x200
    assert at >= 0 and b[at] == 0x21, 'no Power Stone Mini in this file'
    prog = b[at:at + SIZE]
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'PSMINI.VMS').write_bytes(prog)
    print(f'Power Stone Mini at {FILE} offset {at:#x}')
    inbox = out / 'inbox'
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir()

    pieces = []  # (stem, title, image, meta, preview)
    for stem, title, addrs, tags, jp in SCREENS:
        frames = [bits(prog, a, 48, 32) for a in addrs]
        meta = dict(title=title, **BASE, **({'region': 'ntsc-j'} if jp else {}), tags=tags)
        pieces.append((stem, stack(frames), meta, frames[0]))
    notes = out / 'notes'
    notes.mkdir(exist_ok=True)
    for name, screens in portrait_sequences(prog).items():
        write_gif(screens, notes / f'{name}.gif')
    lap = course_lap(prog)
    meta = dict(title="Falcon's Aerial Adventure course", **BASE, tags=['minigame', 'falcon', 'map'],
                scroll=dict(stepPx=1, delayMs=COURSE_STEP_MS, direction='down'))
    pieces.append(('course', lap, meta, lap.crop((0, lap.height - 32, 48, lap.height))))
    for key, name, t, n in RULES:
        for k, a in enumerate(table(prog, t, n)):
            im = bits(prog, a, 48, 32)
            meta = dict(title=f'{name} rules ({k + 1}/{n})', **BASE, region='ntsc-j',
                        tags=['minigame', 'letters', key])
            pieces.append((f'rules-{key}-{k + 1}', im, meta, im))
    for stem, title, im, tags, jp, addr, glyphs in sprites(prog):
        meta = dict(title=title, **BASE, **({'region': 'ntsc-j'} if jp else {}), tags=tags, sprite=True,
                    source={'file': FILE, 'offset': at + addr})
        if glyphs:
            meta['glyphs'] = glyphs
        pieces.append((stem, im, meta, im))

    stems = [p[0] for p in pieces]
    assert len(stems) == len(set(stems)), 'two pieces share a file name'
    for stem, im, meta, _ in pieces:
        im.save(inbox / f'power-stone-mini-{stem}.png')
        (inbox / f'power-stone-mini-{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
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
        x += max(w, 90) + pad
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
