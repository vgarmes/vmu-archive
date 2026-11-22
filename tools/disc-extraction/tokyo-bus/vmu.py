"""Pull Tokyo Bus Guide's VMU art off its disc: the game's own screens and the
traffic sign quiz it writes to the memory card.

    python3 vmu.py <files dir> <out dir>

<files dir> holds /SYSTEM/NOW_LOADING.LCD, VM_BUS.LCD, VM_DANGER.LCD and
PDAQUIZ.BIN as copied by `disc.py` (the six *_COMMON folders hold the same
.LCD files byte for byte). Writes:
- screens/<name>.png, frames stacked top to bottom (dark = lit, as
  `pnpm icons:import` reads it), and sprites/<name>.png at their own size;
- manifest.json, what each one is and where it came from (read by prep.py);
- saves/TOKYOBUS._VM.VMS and saves/save-icons.json: the quiz as the game
  writes it to the card, for `pnpm saveicons:import`;
- contact-sheet.png.

Redump `Tokyo Bus Guide (Japan) (Rev A)` (T-35402M V2.000). See
content/games/tokyo-bus-guide.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

W, H = 48, 32

# The game's .LCD files: a u32 frame count, then 48x32 frames at a byte a dot
# (0x0F lit, 0 not), stored as shown. 1ST_READ.BIN (0x8C01BB78) holds each
# frame for 11 calls of its updater; at one call per 60 Hz frame that's 183 ms.
LCD = [
    dict(name='bus', file='VM_BUS.LCD', delay=183),
    dict(name='danger', file='VM_DANGER.LCD'),
    dict(name='now-loading', file='NOW_LOADING.LCD'),
]

# PDAQUIZ.BIN, a VMU program (VMS header at 0x200). Its image table at 0x2BD6
# holds big-endian pointers to entries: width, height, bytes a row, then up to
# 9 big-endian frame pointers ending in 0. Images are 1 bit a dot, high bit
# first, 1 = lit.
TABLE = 0x2BD6
ENTRIES = 67
SIGNS = range(0, 63)  # 32x32 traffic signs
SCREENS = 63          # 48x32: blank, title, no battery
CREDITS = 64          # 24x7, eight pieces of the credits ticker
ARROWS = 65           # 3x5: blank, right, left
MARKS = 66            # 15x15: circle, cross
# The 8x8 font: glyph = code below 0x80, code - 0x20 above (ASCII, then
# katakana with dakuten, then JIS X 0201 katakana). 192 glyphs, up to the
# first 48x32 screen at 0x33E8.
FONT, GLYPHS = 0x2DE8, 192
# Text scenes: records of (y, x, codes..., 0), ending in 0xFF.
VERSION = 0x189D  # "PDAクイズ / 0.90", drawn by 0x1887, which nothing calls


def lcd_frames(data):
    n = struct.unpack_from('<I', data)[0]
    assert len(data) == 4 + n * W * H
    frames = []
    for k in range(n):
        raw = data[4 + k * W * H:4 + (k + 1) * W * H]
        assert set(raw) <= {0, 0x0F}
        frames.append([[1 if raw[y * W + x] else 0 for x in range(W)] for y in range(H)])
    return frames


def bits(b, addr, w, h, bpr):
    return [[b[addr + y * bpr + x // 8] >> (7 - x % 8) & 1 for x in range(w)] for y in range(h)]


def entry(b, k):
    p = struct.unpack_from('>H', b, TABLE + 2 * k)[0]
    w, h, bpr = b[p], b[p + 1], b[p + 2]
    frames, i = [], p + 3
    while (q := struct.unpack_from('>H', b, i)[0]) != 0:
        frames.append(q)
        i += 2
    return w, h, bpr, frames


def blank():
    return [[0] * W for _ in range(H)]


def paste(scr, art, x0, y0):
    for y, row in enumerate(art):
        for x, v in enumerate(row):
            if v and 0 <= x0 + x < W and 0 <= y0 + y < H:
                scr[y0 + y][x0 + x] = 1


def text_scene(b, a):
    scr = blank()
    while b[a] != 0xFF:
        y, x = b[a], b[a + 1]
        a += 2
        while b[a]:
            c = b[a]
            paste(scr, bits(b, FONT + 8 * (c if c < 0x80 else c - 0x20), 8, 8, 1), x, y)
            x += 8
            a += 1
        a += 1
    return scr


def image(frames, w, h):
    im = Image.new('1', (w, h * len(frames)), 1)
    for k, f in enumerate(frames):
        for y in range(h):
            for x in range(w):
                if f[y][x]:
                    im.putpixel((x, k * h + y), 0)
    return im


def main(src, out):
    src, out = Path(src), Path(out)
    for sub in ('screens', 'sprites', 'saves'):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir(parents=True)
    manifest, sheet = [], []

    def emit(kind, name, frames, w, h, **meta):
        im = image(frames, w, h)
        im.save(out / kind / f'{name}.png')
        manifest.append(dict(kind=kind, name=name, width=w, height=h, frames=len(frames), **meta))
        sheet.append((name, im, w, h))

    for s in LCD:
        frames = lcd_frames((src / 'SYSTEM' / s['file']).read_bytes())
        emit('screens', s['name'], frames, W, H, source=f'/SYSTEM/{s["file"]}',
             **({'delay': s['delay']} if 'delay' in s else {}))

    q = (src / 'SYSTEM' / 'PDAQUIZ.BIN').read_bytes()
    ents = [entry(q, k) for k in range(ENTRIES)]
    file = '/SYSTEM/PDAQUIZ.BIN'

    # The title (0x18E8): the screen, then three pieces of the credits ticker
    # along the top (y 0), 24 dots apart from x = c, starting at piece b. The
    # loop at 0x18AE redraws each base timer tick (0.5 s) until A+B, moving c
    # 8 dots left; at -24 (BNE #0xE9 sets CY below it) b steps on and c is 0
    # again. So the credits scroll 8 dots a tick, 24 steps round.
    w, h, bpr, fr = ents[SCREENS]
    assert (w, h, bpr) == (W, H, 6) and q[fr[0]:fr[0] + 192] == bytes(192)
    title = bits(q, fr[1], W, H, 6)
    cw, ch, cbpr, pieces = ents[CREDITS]
    assert (cw, ch, len(pieces)) == (24, 7, 8)
    credit = [bits(q, p, cw, ch, cbpr) for p in pieces]
    frames = []
    for b in range(8):
        for c in (0, -8, -16):
            scr = [row[:] for row in title]
            for i in range(3):
                paste(scr, credit[(b + i) % 8], c + 24 * i, 0)
            frames.append(scr)
    emit('screens', 'quiz-title', frames, W, H, source=file, offset=fr[1], delay=500)
    emit('screens', 'quiz-no-battery', [bits(q, fr[2], W, H, 6)], W, H, source=file, offset=fr[2])
    emit('screens', 'quiz-version', [text_scene(q, VERSION)], W, H, source=file, offset=VERSION,
         unused=True)

    for k in SIGNS:
        w, h, bpr, fr = ents[k]
        assert (w, h, bpr, len(fr)) == (32, 32, 4, 1)
        emit('sprites', f'quiz-sign-{k:02d}', [bits(q, fr[0], w, h, bpr)], w, h, source=file,
             entry=k, offset=fr[0])
    w, h, bpr, fr = ents[MARKS]
    for name, p in zip(('circle', 'cross'), fr):
        emit('sprites', f'quiz-{name}', [bits(q, p, w, h, bpr)], w, h, source=file,
             entry=MARKS, offset=p)
    w, h, bpr, fr = ents[ARROWS]
    assert q[fr[0]:fr[0] + 5] == bytes(5)  # frame 0 is blank (the zeros at 0x14B0)
    for name, p in zip(('right', 'left'), fr[1:]):
        emit('sprites', f'quiz-arrow-{name}', [bits(q, p, w, h, bpr)], w, h, source=file,
             entry=ARROWS, offset=p)
    font = [row for g in range(GLYPHS) for row in bits(q, FONT + 8 * g, 8, 8, 1)]
    rebuilt = bytes(int(''.join(map(str, row)), 2) for row in font)
    assert rebuilt == q[FONT:FONT + 8 * GLYPHS]
    emit('sprites', 'quiz-font', [font], 8, 8 * GLYPHS, source=file, offset=FONT, font=True)

    # The quiz as the game writes it to the card (TOKYOBUS._VM, 1ST_READ.BIN
    # 0x8C0387D4): the file as it is, a VMU program with its header at 0x200.
    (out / 'saves' / 'TOKYOBUS._VM.VMS').write_bytes(q)
    (out / 'saves' / 'save-icons.json').write_text(json.dumps(dict(
        game='Tokyo Bus Guide', publisher='Fortyfive', year=1999, region='ntsc-j',
        disc=file, titles={'TOKYOBUS._VM.VMS': 'Traffic sign quiz'}), ensure_ascii=False, indent=1))
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1))

    scale, cols = 2, 10
    cell_w, cell_h = 48 * scale + 12, 32 * scale + 24
    small = [s for s in sheet if s[3] <= 32 * 8]
    rows = (len(small) + cols - 1) // cols
    img = Image.new('RGB', (cols * cell_w + 16, rows * cell_h + 50), '#f5f2e9')
    d = ImageDraw.Draw(img)
    d.text((8, 8), 'Tokyo Bus Guide: SYSTEM/*.LCD and PDAQUIZ.BIN', fill='black')
    for i, (name, im, w, h) in enumerate(small):
        x, y = 8 + (i % cols) * cell_w, 30 + (i // cols) * cell_h
        d.text((x, y), name.replace('quiz-', ''), fill='black')
        first = im.crop((0, 0, w, h)).convert('RGB').resize((w * scale, h * scale), Image.NEAREST)
        img.paste(first, (x, y + 12))
    img.save(out / 'contact-sheet.png')
    print(len(manifest), 'pieces ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
