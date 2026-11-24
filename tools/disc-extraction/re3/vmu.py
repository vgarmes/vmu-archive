"""Pull Resident Evil 3's VMU screens out of /RETENUTO/DC/VMS_1.DCL (Japan) or
/RETENUTO/DC_E/VMS_1.DCL (Europe).

    python3 vmu.py <folder with 1ST_READ.BIN and that VMS_1.DCL> <out dir>

Writes <out>/inbox/*.png with a sidecar each, for `pnpm icons:import`
(animations as their frames stacked, dark = lit), and <out>/contact-sheet.png
with every screen of the file by its number.

Redump `Biohazard 3 - Last Escape (Japan)` (T-1222M V1.002) and `Resident Evil
3 - Nemesis (Europe)` (T-7021D-05 V1.000); it tells the two programs apart by
itself. 1ST_READ.BIN loads at 0x8C010000. Before writing anything it checks,
in the program, the facts the entries rest on: the file's name where the
loader reads it, and the screen numbers and health limits the condition
monitor picks between. The two files differ only in the title, screen 4, so
the importer skips the European file's other screens as duplicates. See
content/games/resident-evil-3-nemesis.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H = 48, 32
SIZE = W * H  # a byte a dot: 0x0F lit, 0 not
COUNT = 45

# Per release: the file the loader opens, where its name sits in the program
# (Japan's loader is 0x8C02D018), where the monitor's picker is (the same
# code in both), and the title's region. The European disc also holds Japan's
# files in RETENUTO/DC and the same files as its own in RETENUTO/DC_U (the
# American set, by its name), but its program only names DC_e; the title it
# shows is the West's, so it gets no region.
RELEASES = {
    'Japan': dict(file='RETENUTO/DC/VMS_1.DCL', name_at=0x8C161230, pick=0x8C02CE30, title_region='ntsc-j'),
    'Europe': dict(file='RETENUTO/DC_E/VMS_1.DCL', name_at=0x8C17CE70, pick=0x8C153304, title_region=None),
}

# The picker (Japan's 0x8C02CE30) picks the monitor's first screen from health (+0x2568 of the game
# state) and its status bits (+0x256E): 0x100 the virus set, 0x200 the poison
# set, else the plain one; within a set, above 100, above 40, above 20, else.
PICKS = [33, 37, 37, 41, 21, 25, 25, 29, 9, 13, 13, 17]
LIMITS = [100, 40, 20] * 3

# The VMU code runs once a pass of the game's frame routine, taken as 60 Hz,
# and steps the monitor every 11 passes (0x8C02DD24), through 4 frames.
STEP_MS = round(11 * 1000 / 60)

BASE = dict(game='resident-evil-3-nemesis', publisher='Capcom', year=2000)
SCREENS = [  # (first screen, frames, slug, title, tags, extra)
    (4, 1, 'title-screen', 'Title screen', ['logo'], 'title'),
    (0, 1, 'access', 'Access', ['memory-card'], {}),
    (2, 1, 'ok', 'Ok', ['memory-card'], {}),
    (3, 1, 'error', 'Error', ['memory-card'], {}),
    (1, 1, 'connect', 'Connect', [], dict(unused=True)),
    (5, 1, 'jill', 'Jill', ['portrait', 'character'], {}),
    (6, 1, 'carlos', 'Carlos', ['portrait', 'character'], {}),
    (7, 1, 'mikhail', 'Mikhail', ['portrait', 'character'], {}),
    (8, 1, 'nikolai', 'Nikolai', ['portrait', 'character'], {}),
]
for first, kind in ((9, ''), (21, 'Poison'), (33, 'Virus')):
    for k, level in enumerate(('Fine', 'Caution', 'Danger')):
        title = f'Condition: {level}' if not kind else f'Condition: {kind} ({level.lower()})'
        slug = 'condition-' + (f'{kind}-{level}' if kind else level).lower()
        SCREENS.append((first + 4 * k, 4, slug, title, ['status'], dict(frameDelayMs=STEP_MS)))


def release(b):
    """Which program this is, by the name at each release's address."""
    for name, r in RELEASES.items():
        at = r['name_at'] - LOAD
        if b[at:at + 40].split(b'\0')[0].decode('latin-1').upper() == r['file']:
            return name, r
    sys.exit('neither the Japanese nor the European program')


def check_program(b, r):
    # every `mov #imm,r0` in the picker, in order, and the limits it compares
    code = b[r['pick'] - LOAD:r['pick'] - LOAD + 0x8C]
    words = struct.unpack(f'<{len(code) // 2}H', code)
    picks = [w & 0xFF for w in words if w & 0xFF00 == 0xE000]
    limits = [w & 0xFF for w in words if w & 0xFF00 == 0xE100]
    assert picks == PICKS, picks
    assert limits == LIMITS, limits


def screen(d, n):
    raw = d[n * SIZE:(n + 1) * SIZE]
    im = Image.new('1', (W, H), 1)
    im.putdata([0 if v else 1 for v in raw])
    return im


def main(src, out):
    src, out = Path(src), Path(out)
    b = (src / '1ST_READ.BIN').read_bytes()
    name, r = release(b)
    check_program(b, r)
    d = (src / r['file']).read_bytes()
    assert len(d) == COUNT * SIZE and set(d) == {0, 0x0F}

    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)
    used = set()
    for first, frames, slug, title, tags, extra in SCREENS:
        strip = Image.new('1', (W, H * frames), 1)
        for k in range(frames):
            strip.paste(screen(d, first + k), (0, H * k))
            used.add(first + k)
        stem = f'resident-evil-3-nemesis-{slug}'
        strip.save(inbox / f'{stem}.png')
        if extra == 'title':
            extra = dict(region=r['title_region']) if r['title_region'] else {}
        meta = dict(title=title, **BASE, tags=tags, **extra)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, indent=1) + '\n')
    assert used == set(range(COUNT))

    scale, cols = 3, 9
    cw, ch = W * scale + 12, H * scale + 26
    sheet = Image.new('RGB', (12 + cols * cw, 40 + (COUNT + cols - 1) // cols * ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 12), f'Resident Evil 3, {name}: /{r["file"]}, {COUNT} screens', fill='black')
    for n in range(COUNT):
        x, y = 12 + n % cols * cw, 40 + n // cols * ch
        draw.text((x, y), f'#{n}', fill='black')
        sheet.paste(screen(d, n).convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')
    print(name, 'program:', len(SCREENS), 'entries from', COUNT, 'screens ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
