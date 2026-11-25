"""Pull Spider-Man's VMU screens out of its five /VMU*.BMP files.

    python3 vmu.py <folder with 1ST_READ.BIN and VMU*.BMP> <out dir>

Writes <out>/inbox/ (each screen as a PNG, dark = lit, with its sidecar, for
`pnpm icons:import`) and <out>/contact-sheet.png.

Redump `Spider-Man (USA)`; 1ST_READ.BIN loads at 0x8C010000. Before writing
anything it checks, in the program, the facts the entries rest on. See
content/games/spider-man.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H = 48, 32
BASE = dict(game='spider-man', publisher='Activision', year=2001)

# 0x8C191580 loads a BMP into a picture: a width byte, a height byte, then a
# byte a dot, rows padded to 4. 0x8C191D80 copies one into the 48x32 buffer
# at 0x8C337950 and sends it with pdLcd's write (0x8C044F74), which takes a
# byte a dot, non-zero lit. A BMP that won't load is replaced by FALLBACK, a
# 4x4 checker of 8s, so the loader's 1 (the BMP's black) is lit too.
LOADER, SHOW, BUFFER, LCD_WRITE = 0x8C191580, 0x8C191D80, 0x8C337950, 0x8C044F74
FALLBACK = 0x8C1C6358
FALLBACK_BYTES = bytes([4, 4, 0, 8, 8, 8, 8, 8, 0, 8, 8, 0, 8, 8, 8, 8, 8, 0])

# Each file's name in the program, the code that loads it, and its entry.
SCREENS = [
    # The idle screen: 0x8C191F80 loads it once and sends it to every VMU.
    ('VMULOGO.BMP', 0x8C1C634C, [0x8C191FB6, 0x8C192344], 'spider-man-mask', 'Spider-Man mask', ['logo']),
    # While a save is written (0x8C18F800).
    ('VMUSAVE.BMP', 0x8C1C5458, [0x8C18F82A], 'spider-man-saving', 'Saving', ['memory-card']),
    # While a save is read.
    ('VMULOAD.BMP', 0x8C1C54FC, [0x8C18FC40], 'spider-man-loading', 'Loading', ['memory-card']),
    # After a save or a load that worked, with a falling beep (0x8C190720).
    ('VMUOK.BMP', 0x8C1C54E0, [0x8C18FB28, 0x8C18FD06], 'spider-man-ok', 'OK', ['memory-card']),
    # After one that didn't.
    ('VMUFAILED.BMP', 0x8C1C54EC, [0x8C18FBCA, 0x8C18FD42], 'spider-man-failed', 'Failed', ['memory-card']),
]


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


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


def read_bmp(raw):
    """A 48x32, 8-bit, two-colour BMP (white 0, black 1) as rows of 0/1, top first."""
    assert raw[:2] == b'BM' and len(raw) == 1600
    offset, = struct.unpack_from('<I', raw, 10)
    size, w, h, planes, bpp, comp = struct.unpack_from('<IiiHHI', raw, 14)
    colours, = struct.unpack_from('<I', raw, 46)
    assert (size, w, h, planes, bpp, comp, colours, offset) == (40, W, H, 1, 8, 0, 2, 62)
    assert raw[54:62] == bytes([255, 255, 255, 0, 0, 0, 0, 0])  # white, black
    rows = [list(raw[offset + y * W:offset + (y + 1) * W]) for y in range(H)][::-1]  # stored bottom up
    assert {v for r in rows for v in r} <= {0, 1}
    return rows


def main(src, out):
    src, out = Path(src), Path(out)
    b = (src / '1ST_READ.BIN').read_bytes()

    assert b'pdLcd Ver 1.04' in b
    assert at(b, FALLBACK, len(FALLBACK_BYTES)) == FALLBACK_BYTES
    # The save routine loads SHOW three times (saving, OK, failed); the load
    # routine twice, keeping it in r12 for its OK screen.
    assert literal_loads(b, SHOW) == [0x8C18F828, 0x8C18FB24, 0x8C18FBC6, 0x8C18FC38, 0x8C18FD3E]
    assert literal_loads(b, LOADER) == [0x8C191D92, 0x8C191FB4, 0x8C192342]  # SHOW and the logo's two
    for name, string, loads, *_ in SCREENS:
        assert at(b, string, len(name) + 1) == name.lower().encode() + b'\0', name
        assert literal_loads(b, string) == loads, (name, literal_loads(b, string))

    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)
    screens = []
    for name, _, _, slug, title, tags in SCREENS:
        rows = read_bmp((src / name).read_bytes())
        im = Image.new('1', (W, H), 1)
        im.putdata([0 if v else 1 for r in rows for v in r])  # dark = lit
        im.save(inbox / f'{slug}.png')
        (inbox / f'{slug}.json').write_text(
            json.dumps(dict(title=title, **BASE, tags=tags), ensure_ascii=False, indent=1) + '\n')
        screens.append((name, im))
        print(f'/{name} -> {slug}')

    scale = 4
    sheet = Image.new('RGB', (16 + len(screens) * (W * scale + 16), 40 + H * scale + 32), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), 'Spider-Man: /VMU*.BMP', fill='black')
    for k, (name, im) in enumerate(screens):
        x = 16 + k * (W * scale + 16)
        sheet.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, 40))
        draw.text((x, 44 + H * scale), name, fill='black')
    sheet.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
