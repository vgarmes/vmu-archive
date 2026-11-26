"""Pull Mars Matrix's six VMU screens out of its program.

    python3 vmu.py <folder with 00MMXDC.BIN> <out dir>

Writes <out>/inbox/ (each screen as a PNG, dark = lit, with its sidecar, for
`pnpm icons:import`) and <out>/contact-sheet.png.

Redump `Mars Matrix (Japan)` (T-1238M V1.000); its boot file, 00MMXDC.BIN,
loads at 0x8C010000. Before writing anything it checks, in the program, the
facts the entries rest on. See content/games/mars-matrix.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H = 48, 32
SIZE = W * H
BASE = dict(game='mars-matrix', publisher='Capcom', year=2000)

# pdLcd 1.04 (the build Grandia II and Guilty Gear X link): its write, which
# takes a byte a dot and turns it for the VMU's orientation (0x8C20311C), and
# its check that a VMU with a screen is there (0x8C2031CC). Its write for
# packed screens (0x8C203182) is linked but never called.
LCD_WRITE, LCD_CHECK, LCD_PACKED = 0x8C20311C, 0x8C2031CC, 0x8C203182
# The screens, a pointer each, in TABLE. The VMU code reads entry 0 (the
# logo) at 0x8C014F28, entry 1 (LOADING) at 0x8C014EE0, and entries 4 and 5
# (OK!, NG!) through r8 (loaded at 0x8C01501E) as @(16,r8) and @(20,r8).
TABLE = 0x8C131AAC
TABLE_LOADS = [0x8C014F28, 0x8C01501E]
ENTRY_1 = 0x8C014EE0
OK_LOADS, NG_LOADS = [0x8C015406], [0x8C01526E, 0x8C015300, 0x8C01539E]
# The save's icon follows the last screen: its palette, then its picture.
SAVE_PALETTE = 0x8C1317EC

SCREENS = [
    ('mars-matrix-logo', 'Mars Matrix logo', ['logo'], False),
    ('mars-matrix-loading', 'Loading', ['memory-card'], False),
    ('mars-matrix-saving', 'Saving', ['memory-card'], True),
    ('mars-matrix-searching', 'Searching', ['memory-card'], True),
    ('mars-matrix-ok', 'OK', ['memory-card'], False),
    ('mars-matrix-ng', 'NG', ['memory-card'], False),
]


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def word(b, addr):
    return struct.unpack('<I', at(b, addr, 4))[0]


def literal_loads(b, value):
    """Addresses of `mov.l @(disp,pc),Rn` instructions loading value."""
    out = []
    for off in range(0, len(b) - 1, 2):
        w = b[off] | b[off + 1] << 8
        if w >> 12 == 0xD:
            lit = (off & ~3) + 4 + (w & 0xFF) * 4
            if lit + 4 <= len(b) and struct.unpack_from('<I', b, lit)[0] == value:
                out.append(LOAD + off)
    return out


def half(b, addr):
    return struct.unpack('<H', at(b, addr, 2))[0]


def main(src, out):
    src, out = Path(src), Path(out)
    b = (src / '00MMXDC.BIN').read_bytes()

    assert b'pdLcd Ver 1.04 Build:Apr 26 1999 16:55:25' in b
    assert literal_loads(b, LCD_WRITE) == [0x8C014EE4, 0x8C014F2C, 0x8C015272, 0x8C015304, 0x8C0153A2, 0x8C01540A]
    assert literal_loads(b, LCD_CHECK) == [0x8C014ECE, 0x8C014F16, 0x8C015018]
    assert literal_loads(b, LCD_PACKED) == []
    assert literal_loads(b, TABLE) == TABLE_LOADS
    assert literal_loads(b, TABLE + 4) == [ENTRY_1]
    # Nothing names entries 2 and 3 (SAVING, SEARCHING), or the art itself.
    pointers = [word(b, TABLE + 4 * k) for k in range(len(SCREENS))]
    for k in (2, 3):
        assert literal_loads(b, TABLE + 4 * k) == []
        assert b.count(struct.pack('<I', pointers[k])) == 1  # its table entry
    assert [half(b, a) for a in OK_LOADS] == [0x5584]  # mov.l @(16,r8),r5
    assert [half(b, a) for a in NG_LOADS] == [0x5585] * 3  # mov.l @(20,r8),r5
    assert word(b, TABLE + 4 * len(SCREENS)) == 0  # the table ends
    assert pointers == [pointers[0] + SIZE * k for k in range(len(SCREENS))]
    assert pointers[-1] + SIZE == SAVE_PALETTE

    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)
    screens = []
    for (slug, title, tags, unused), ptr in zip(SCREENS, pointers):
        raw = at(b, ptr, SIZE)
        assert set(raw) == {0, 8}, slug  # 8 lit, 0 not
        im = Image.new('1', (W, H), 1)
        im.putdata([0 if v else 1 for v in raw])  # stored as shown
        im.save(inbox / f'{slug}.png')
        meta = dict(title=title, **BASE, tags=tags)
        if unused:
            meta['unused'] = True
        (inbox / f'{slug}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n')
        screens.append((title + (' (unused)' if unused else ''), im))
        print(f'{ptr:#x} -> {slug}')

    scale = 4
    sheet = Image.new('RGB', (16 + len(screens) * (W * scale + 16), 40 + H * scale + 32), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), f'Mars Matrix: 00MMXDC.BIN {pointers[0]:#x}', fill='black')
    for k, (label, im) in enumerate(screens):
        x = 16 + k * (W * scale + 16)
        sheet.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, 40))
        draw.text((x, 44 + H * scale), label, fill='black')
    sheet.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
