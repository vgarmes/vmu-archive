"""Redraw Code: Veronica's VMU screens from its program, for `pnpm icons:import`.

    python3 vmu.py <1ST_READ.BIN> <inbox dir>

The game keeps all its VMU art in one 128x128 1-bit sheet and composes each
screen on a 64x64 canvas from rectangles of it, one draw mode at a time; the
VMU shows the canvas's top-left 48x32. This script reads the sheet and the
rectangle table from the program and re-runs each draw mode tick by tick, as
the code at the addresses below does (see
content/games/resident-evil-code-veronica.md), then writes one PNG (frames
stacked, dark = lit) and sidecar per screen. Needs no third-party modules.
"""
import json
import shutil
import struct
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GAME = 'Resident Evil Code: Veronica'
GAME_ID = 'resident-evil-code-veronica'  # its id in content/games.json
LOAD = 0x8C010000  # where 1ST_READ.BIN runs from

# Where each release keeps the art. Code addresses in the docs are the
# Japanese program's; the European one has the same VMU code 0x2D5C bytes on.
#   sheet: 128x128, 16 bytes a row, bit 7 leftmost, 1 lit; followed by the
#     rects, 56 x (y, x, height, width) 16-bit, at +0x800, then the draw-mode
#     table, each status's trace row (6 longs, +0xB3C) and label rect
#     (6 bytes, +0xB54)
#   traces: 6 pointers to a status's six 8-px trace columns (rect numbers)
#   region: the title's (the only screen that differs: BIOHAZARD in Japan,
#     RESIDENT EVIL in Europe; the American disc wasn't checked, so the
#     European title gets no region)
RELEASES = {
    'Japan': dict(sheet=0x8C13CEFC, traces=0x8C16D488, region='ntsc-j'),
    'Europe': dict(sheet=0x8C1404B8, traces=0x8C1705C0, region=None),
}
FIRST_RECT = struct.pack('<4h', 0, 0, 32, 48)  # the title, at (0, 0)


def release(b):
    for name, r in RELEASES.items():
        if b[r['sheet'] - LOAD + 0x800:r['sheet'] - LOAD + 0x808] == FIRST_RECT:
            return name, r
    sys.exit('not a program this script knows: no rect table where expected')

# One tick is every second pass of the game loop (0x8C12CBF6 acts on odd
# passes only); taking that loop as 60 Hz, a tick is 1/30 s.
TICK_MS = 1000 / 30

W, H = 64, 64  # the canvas


class Vmu:
    def __init__(self, b, rel):
        self.b, self.rel = b, rel
        off = rel['sheet'] - LOAD
        self.sheet = [b[off + y * 16:off + y * 16 + 16] for y in range(128)]
        self.rects = [struct.unpack_from('<4h', b, off + 0x800 + n * 8) for n in range(56)]
        self.canvas = [bytearray(8) for _ in range(H)]

    def u32(self, addr):
        return struct.unpack_from('<I', self.b, addr - LOAD)[0]

    def fill(self, y, x, h, w, value):  # 0x8C12D1AC, whole bytes
        for row in range(y, y + h):
            for col in range(x // 8, (x + w) // 8):
                self.canvas[row][col] = value

    def blit(self, y, x, n):  # 0x8C12D054: copy rect n of the sheet to (x, y)
        ry, rx, rh, rw = self.rects[n]
        for row in range(rh):
            src = self.sheet[ry + row][rx // 8:(rx + rw) // 8]
            self.canvas[y + row][x // 8:x // 8 + len(src)] = src

    def screen(self):  # what 0x8C12CF68 sends: the top-left 48x32, as stored
        return bytes(b for row in self.canvas[:32] for b in row[:6])


def static(vmu, draw):
    draw(vmu)
    return [vmu.screen()], False


def text_on_lit(n):  # modes 4-7 (0x8C12D2AA): SAVE, LOAD, OK, NG
    def draw(v):
        v.fill(0, 0, 32, 48, 0xFF)
        v.blit(9, 0, n)
    return draw


def on_clear(y, x, n):  # modes 1, 2, 11-16: one rect on a clear screen
    def draw(v):
        v.fill(0, 0, 32, 48, 0)
        v.blit(y, x, n)
    return draw


def status(vmu, which):
    """Mode 9 (0x8C12D304), the condition monitor, for status `which` (0-5).

    State 1 draws the label at y 24; state 2 sweeps rect 11 across in 8-px
    steps, one every 2 ticks; from its fifth step state 3 draws the trace one
    8-px column a tick behind it; state 4 holds 12 ticks, then back to state 1.
    Returns one cycle once the screen has been drawn once (the first cycle
    starts from a blank screen; every later one from the full trace).
    """
    pieces = vmu.u32(vmu.rel['traces'] + 4 * which)
    piece = [vmu.b[pieces - LOAD + m] for m in range(6)]
    ty = vmu.u32(vmu.rel['sheet'] + 0xB3C + 4 * which)
    label = vmu.b[vmu.rel['sheet'] - LOAD + 0xB54 + which]
    st = {'state': 0, 'n': 0, 'm': 0, 'hold': 0}
    vmu.fill(0, 0, 32, 48, 0)  # state 0
    st['state'] = 1

    def step():
        s = st
        if s['state'] == 1:
            s['n'] = s['m'] = 0
            s['state'] = 2
            vmu.blit(24, 0, label)
            s2()
        elif s['state'] == 2:
            s2()
        elif s['state'] == 3:
            s3()
        elif s['state'] == 4:
            s['hold'] -= 1
            if s['hold'] <= 0:
                s['state'] = 1

    def s2():
        s = st
        col = s['n'] >> 1
        s['n'] += 1
        vmu.blit(0, col * 8, 11)
        if col >= 5:
            s['state'] += 1
        if col > 3:
            s3()

    def s3():
        s = st
        m = s['m']
        s['m'] += 1
        vmu.blit(ty, m * 8, piece[m])
        if m >= 5:
            s['hold'] = 12
            s['state'] += 1

    step()  # the first cycle, from a blank screen
    while st['state'] != 1:
        step()
    out = []  # the second, which every later one repeats
    while True:
        step()
        out.append(vmu.screen())
        if st['state'] == 1:
            return out, False


def you_died(vmu, first):
    """Mode 10 (0x8C12D444): a lit screen held 42 ticks, then the three
    YOU DIED stages at y 10, 16 ticks apart; the last stays up."""
    s = {'state': 0, 'wait': 0, 'k': 0}
    out = []
    while s['state'] != 3:
        if s['state'] == 0:
            vmu.fill(0, 0, 32, 48, 0xFF)
            s['wait'], s['k'] = 42, 0
            s['state'] = 1
        elif s['state'] == 1:
            if s['wait'] > 0:
                s['wait'] -= 1
            else:
                s['state'] = 2
        elif s['state'] == 2:
            if s['wait'] >= 0:
                s['wait'] -= 1
            else:
                vmu.blit(10, 0, first + s['k'])
                s['k'] += 1
                if s['k'] > 2:
                    s['state'] = 3
                s['wait'] = 16
        out.append(vmu.screen())
    return out, True


def merge(frames):
    """Back-to-back identical frames as one, with delays from their ticks."""
    out, runs = [], []
    for f in frames:
        if out and f == out[-1]:
            runs[-1] += 1
        else:
            out.append(f)
            runs.append(1)
    return out, [round(n * TICK_MS) for n in runs]


def png(path, frames):
    """48 wide, frames stacked, 8-bit grey: lit dots black."""
    rows = []
    for f in frames:
        for y in range(32):
            row = bytearray()
            for x in range(48):
                row.append(0 if f[y * 6 + x // 8] >> (7 - x % 8) & 1 else 255)
            rows.append(b'\0' + bytes(row))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'
                     + chunk(b'IHDR', struct.pack('>IIBBBBB', 48, 32 * len(frames), 8, 0, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(b''.join(rows)))
                     + chunk(b'IEND', b''))


# (file stem, title, tags, extra sidecar fields, how to draw it)
# Statuses as mode 9 picks them: 0 HP >= 120, 1 HP >= 60, 2 HP >= 30, 3 below,
# 4 the dead flag, 5 poisoned. Modes 12-16 show the portraits; 15 picks one by
# the character (0 Claire, 1 Chris, 2 bonus, 3), from 0x8C13DA58.
SCREENS = [
    ('title', 'Title screen', ['logo'], {}, lambda v: static(v, lambda v: v.blit(0, 0, 0))),
    ('capcom', 'Capcom', ['logo'], {}, lambda v: static(v, on_clear(12, 0, 5))),
    ('save', 'Save', ['memory-card'], {}, lambda v: static(v, text_on_lit(1))),
    ('load', 'Load', ['memory-card'], {}, lambda v: static(v, text_on_lit(2))),
    ('ok', 'OK', ['memory-card'], {}, lambda v: static(v, text_on_lit(3))),
    ('ng', 'NG', ['memory-card'], {}, lambda v: static(v, text_on_lit(4))),
    ('fine', 'Condition: Fine', ['status'], {}, lambda v: status(v, 0)),
    ('caution', 'Condition: Caution (high)', ['status'], {}, lambda v: status(v, 1)),
    ('caution-2', 'Condition: Caution (low)', ['status'], {}, lambda v: status(v, 2)),
    ('danger', 'Condition: Danger', ['status'], {}, lambda v: status(v, 3)),
    ('died', 'Condition: Died', ['status'], {}, lambda v: status(v, 4)),
    ('poison', 'Condition: Poison', ['status'], {}, lambda v: status(v, 5)),
    ('you-died', 'You Died', [], {}, lambda v: you_died(v, 48)),
    ('mission-clear', 'Mission Clear!', [], {}, lambda v: static(v, on_clear(12, 0, 51))),
    ('claire', 'Claire', ['portrait', 'character'], {}, lambda v: static(v, on_clear(0, 8, 52))),
    ('chris', 'Chris', ['portrait', 'character'], {}, lambda v: static(v, on_clear(0, 8, 53))),
    ('steve', 'Steve', ['portrait', 'character'], {}, lambda v: static(v, on_clear(0, 8, 54))),
    ('wesker', 'Wesker', ['portrait', 'character'], {}, lambda v: static(v, on_clear(0, 8, 55))),
]
HOLD_MS = 3000  # YOU DIED's last stage stays up; the site loops, so hold it


def main(program, inbox):
    b = Path(program).read_bytes()
    inbox = Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    name, rel = release(b)
    print(f'{name} program, sheet at {rel["sheet"]:#010x}')
    for stem, title, tags, extra, draw in SCREENS:
        if stem == 'title':
            extra = {'region': rel['region']} if rel['region'] else {}
        frames, holds = draw(Vmu(b, rel))
        frames, delays = merge(frames)
        if holds:
            delays[-1] = HOLD_MS
        png(inbox / f'cvx-{stem}.png', frames)
        meta = dict(title=title, game=GAME, tags=tags, **extra)
        if len(frames) > 1:
            meta['frameDelaysMs'] = delays
            meta['posterFrame'] = len(frames) - 1  # the whole trace; YOU DIED's last stage
        (inbox / f'cvx-{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(f'{stem}: {len(frames)} frame(s)', delays if len(frames) > 1 else '')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
