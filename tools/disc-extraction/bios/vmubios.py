"""Decode the VMU's own art from the US VMU BIOS disassembly.

    python3 vmubios.py <american_v1.05.s> <out dir>

The source is american_v1.05.s from gyrovorbis/vmu-bios-disassembly, which
assembles (with waterbear) to the US BIOS v1.05 ROM. No ROM dump is needed:
the art is in the source as .byte data, read here by label. Every label's
address is checked against the one its comment header gives.

    $0473  FontGlyphs8x8   42 glyphs, 8 bytes each: 0-9, ':', two arrows,
                           '/' three times, A-Z (time, date and month names)
    $05C7  Str_VmuBanner   text the main menu draws with the 6x8 font:
                           SEGA logo characters, "Visual", "Memory", "Unit"
    $18CF  AnimSprites     clock animation: dog, fish, bird, two frames each
    $18FF  AnimSpriteBlank the blank sprite that wipes the trail
    $1907  AnimSequences   each animal's path: a count, then XRAM offsets
    $E800  FontAscii6x8    256 characters as 8 planes of 256 bytes (plane n =
                           pixel row n), the top 6 bits of each byte used

Writes main-menu.png (48x32, the screen MainMenu draws), the six clock
sprites, both fonts as sheets in character order, the clock animation as the
BIOS plays it (clock-<animal>.png, lower half only, for the contact sheet),
manifest.json and contact-sheet.png.
"""
import json
import re
import sys
from pathlib import Path

import png

LABELS = {
    'FontGlyphs8x8': 0x0473,
    'Str_VmuBanner': 0x05C7,
    'AnimSprites': 0x18CF,
    'AnimSpriteBlank': 0x18FF,
    'AnimSequences': 0x1907,
    'FontAscii6x8': 0xE800,
}
ANIMALS = ['dog', 'fish', 'bird']


def parse(src):
    """label -> bytes of the .byte lines after it, and the addresses comments give."""
    data, said, cur = {}, {}, None
    for line in Path(src).read_text().splitlines():
        m = re.match(r'^;;\s*([A-Za-z_]\w*)\s+\(\$([0-9A-Fa-f]{4})\)', line)
        if m:
            said[m.group(1)] = int(m.group(2), 16)
        code = line.split(';')[0].rstrip()
        m = re.match(r'^([A-Za-z_]\w*):', code)
        if m:
            cur = m.group(1)
            data[cur] = bytearray()
            continue
        m = re.match(r'^\s*\.byte\s+(.*)', code)
        if m and cur:
            data[cur] += bytes(int(v.strip().lstrip('$'), 16) for v in m.group(1).split(','))
    return data, said


def check(data, said):
    for label, addr in LABELS.items():
        if label in said and said[label] != addr:
            sys.exit(f'{label}: the source says ${said[label]:04X}, expected ${addr:04X}')
    # Labels that follow each other must add up: the data between them is all .byte.
    for a, b in [('FontGlyphs8x8', None), ('AnimSprites', 'AnimSpriteBlank'),
                 ('AnimSpriteBlank', 'AnimSequences')]:
        if b and LABELS[a] + len(data[a]) != LABELS[b]:
            sys.exit(f'{a} is {len(data[a])} bytes, which does not end at {b}')
    if len(data['FontGlyphs8x8']) != 42 * 8:
        sys.exit('FontGlyphs8x8 is not 42 glyphs')
    if len(data['FontAscii6x8']) < 2048:
        sys.exit('FontAscii6x8 is shorter than 8 planes')


def glyph6(font, c):
    return [[font[p * 256 + c] >> (7 - x) & 1 for x in range(6)] for p in range(8)]


def draw_text(font, text):
    """What DrawString puts on the screen: 8 columns x 4 rows of 6x8 cells."""
    px = png.blank(48, 32)
    cx = cy = 0
    for c in text:
        if c == 0x0D:
            cx = 0
        elif c == 0x0A:
            cy += 1
        elif c == 0:
            break
        else:
            png.paste(px, glyph6(font, c), cx * 6, cy * 8)
            cx += 1
    return px


def xram_xy(offset):
    """An XRAM offset ($80-$FF) to x, y on its half of the LCD: two 6-byte lines per 16 bytes."""
    pair, r = divmod(offset & 0x7F, 16)
    return (r % 6) * 8, pair * 2 + r // 6


def clock_frames(sprites, seqs, animal):
    """ClockAnimationStep's frames, once a second: a drawing pass, then a wiping pass."""
    lcd, frames, toggle = png.blank(48, 16), [], 0
    for wiping in (False, True):
        for pos in seqs[animal]:
            x, y = xram_xy(pos)
            rows = sprites[6] if wiping else sprites[animal * 2 + toggle]
            png.paste(lcd, rows, x, y)
            if not wiping:
                toggle ^= 1
            frames.append([r[:] for r in lcd])
    return frames


def main(src, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    data, said = parse(src)
    check(data, said)
    manifest = []

    font6 = data['FontAscii6x8'][:2048]
    banner = bytes(data['Str_VmuBanner']).split(b'\0')[0]
    menu = draw_text(font6, banner)
    png.save(out / 'main-menu.png', menu)
    manifest.append(dict(name='main-menu', kind='screen', what='Main menu banner',
                         label='Str_VmuBanner', address=LABELS['Str_VmuBanner'], text=banner.decode('latin-1')))

    raw = data['AnimSprites'] + data['AnimSpriteBlank']
    sprites = [png.bits(raw[i * 8:i * 8 + 8], 8, 8) for i in range(7)]
    for i in range(6):
        name = f'{ANIMALS[i // 2]}-{i % 2 + 1}'
        png.save(out / f'{name}.png', sprites[i])
        manifest.append(dict(name=name, kind='sprite', what=f'Clock {ANIMALS[i // 2]}, frame {i % 2 + 1}',
                             label='AnimSprites', address=LABELS['AnimSprites'] + 8 * i, width=8, height=8))

    g8 = data['FontGlyphs8x8']
    big = png.blank(42 * 8, 8)
    for i in range(42):
        png.paste(big, png.bits(g8[i * 8:i * 8 + 8], 8, 8), i * 8, 0)
    png.save(out / 'font-8x8.png', big)
    manifest.append(dict(name='font-8x8', kind='sprite', what='Big 8x8 font', label='FontGlyphs8x8',
                         address=LABELS['FontGlyphs8x8'], width=42 * 8, height=8))

    small = png.blank(32 * 6, 8 * 8)
    for c in range(256):
        png.paste(small, glyph6(font6, c), (c % 32) * 6, (c // 32) * 8)
    png.save(out / 'font-6x8.png', small)
    manifest.append(dict(name='font-6x8', kind='sprite', what='6x8 font', label='FontAscii6x8',
                         address=LABELS['FontAscii6x8'], width=32 * 6, height=64))

    seq, seqs, i = data['AnimSequences'], [], 0
    while len(seqs) < 3:
        seqs.append(list(seq[i + 1:i + seq[i]]))
        i += seq[i]
    strips = {}
    for a, name in enumerate(ANIMALS):
        frames = clock_frames(sprites, seqs, a)
        strip = [[None] * (len(frames) * 50 - 2) for _ in range(16)]
        for k, f in enumerate(frames):
            png.paste(strip, f, k * 50, 0)
        png.save(out / f'clock-{name}.png', strip, scale=2, gap=160)
        strips[name] = strip
        print(name, 'walks through', [xram_xy(p) for p in seqs[a]])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    # Contact sheet: the menu, the sprites, both fonts, then each animal's run.
    parts = [menu, png.sheet(sprites[:6], 6), big, small] + list(strips.values())
    w = max(len(p[0]) for p in parts)
    sheet = []
    for p in parts:
        sheet += [row + [None] * (w - len(row)) for row in p] + [[None] * w] * 4
    png.save(out / 'contact-sheet.png', sheet, scale=3, gap=200)
    print('main menu, 6 clock sprites and 2 fonts ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
