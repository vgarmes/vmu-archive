"""Decode the VMU program Jet Set Radio carries (the graffiti viewer) from
/JETRADIO/SYSOPTION.AFS.

    python3 app.py <SYSOPTION.AFS> <out dir>

JP release. The program is the AFS's first member, a VMS file named
JET_VM_APLI ("ジェット VM実行ファイル"); addresses below are offsets into it,
where it runs from 0 in flash. It draws with:

    0x0BD3  a bitmap: width in bytes, height, then the rows (1 = lit)
    0x0C38  a sprite: width in pixels (up to 8), height, then one byte a row
    0x1C94  a string: x, y, then 2-byte characters (font, glyph); FE FE is
            a new line (y + 8), xx FD a 4-pixel space, FF FF the end
    0x1DD5  a full-width line at row y
    0x09B3  clears the screen; 0x09ED clears a rectangle

The screens are rebuilt by drawing what the code draws, in its order, at the
places it gives. Writes screens/<name>.png (dark = lit), sprites/<name>.png,
manifest.json and contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

MEMBER = 0  # SYSOPTION.AFS member holding the program
# Fonts, as 0x1D4C picks them by a character's first byte: 10 bytes a glyph
# (width, height, 8 rows). Font 1 is indexed from 0x20, like ASCII.
FONTS = {
    0xE0: ('title', 0x19F1, 13),  # any other first byte, in practice E0
    1: ('narrow', 0x21BB, 151),  # ASCII 0x20-0x7F, then half-width kana
    2: ('wide', 0x27A1, 123),  # symbols, digits, Latin
    3: ('kana', 0x2C6F, 161),  # katakana and hiragana
}
# Fixed-width fonts with no header: one byte a row, left-aligned. Their sheets
# leave a 1-pixel gap between cells, as the glyphs fill them.
PLAIN_FONTS = {
    'small': (0x0DEE, 256, 5, 7),  # base read at 0x0DA4
    'hex': (0x0C98, 17, 3, 5),
}
BITMAPS = {'sega': 0x3454, 'copyright': 0x33DA, 'channel': 0x1A73}
SLICES = [0x19A3, 0x19BD, 0x19D7]  # the radio, drawn by 0x1DAD at x = 12, 20, 28
SLICE_X = [12, 20, 28]
CURSOR = (1, 0x2A)  # 0x1B75 draws font 1 glyph 0x2A at (0, 8 x choice)


def unpack_afs(path):
    d = Path(path).read_bytes()
    if d[:4] != b'AFS\0':
        sys.exit(f'{path}: not an AFS archive')
    off, size = struct.unpack_from('<II', d, 8 + 8 * MEMBER)
    return d[off:off + size], off


class Screen:
    def __init__(self, prog):
        self.d = prog
        self.px = [[0] * 48 for _ in range(32)]

    def clear(self, x=0, y=0, w=48, h=32):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px[yy][xx] = 0

    def line(self, y):
        self.px[y] = [1] * 48

    def put(self, x, y, w, rows):
        # Like 0x0AF0: the sprite's box is replaced, bit 7 leftmost.
        for r, bits in enumerate(rows):
            for k in range(w):
                if 0 <= x + k < 48 and 0 <= y + r < 32:
                    self.px[y + r][x + k] = bits >> (7 - k) & 1

    def bitmap(self, addr, x, y):
        wb, h = self.d[addr], self.d[addr + 1]
        for r in range(h):
            for c in range(wb):
                self.put(x + 8 * c, y + r, 8, [self.d[addr + 2 + r * wb + c]])

    def sprite(self, addr, x, y):
        w, h = self.d[addr], self.d[addr + 1]
        self.put(x, y, w, self.d[addr + 2:addr + 2 + h])

    def glyph(self, font, code, x, y):
        w, h, rows = glyph(self.d, font, code)
        self.put(x, y, w, rows)

    def string(self, addr):
        x, y = self.d[addr], self.d[addr + 1]
        p = addr + 2
        while True:
            font, code = self.d[p], self.d[p + 1]
            p += 2
            if font == 0 or code in (0xFF, 0x00):
                return
            if code == 0xFE:
                x, y = 0, y + 8
            elif code == 0xFD:
                x += 4
            else:
                self.glyph(font, code, x, y)
                x += 4 if font == 1 else 8  # 0x1CEB

    def hex(self):
        """Encoded like an archive frame: 1 = lit, rows top down, bit 7 leftmost."""
        bits = ''.join(str(v) for row in self.px for v in row)
        return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)).hex()

    def image(self):
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if v else 1 for row in self.px for v in row])
        return im


def glyph(d, font, code):
    _, base, _ = FONTS.get(font, FONTS[0xE0])
    if font == 1:
        code -= 0x20
    a = base + 10 * code
    return d[a], d[a + 1], d[a + 2:a + 2 + d[a + 1]]


def screens(d):
    """Each screen as the code draws it: (name, [frames], ticks a frame)."""
    def new():
        return Screen(d)

    # 0x14EE: clear, SEGA at (0, 4), wait 0x20 ticks; clear, © at (0, 6), 0x20.
    sega = new()
    sega.bitmap(BITMAPS['sega'], 0, 4)
    copy = new()
    copy.bitmap(BITMAPS['copyright'], 0, 6)
    # 0x152E: the radio (0x1DAD) over "JET SET RADIO" (0x3382) for 0x10
    # ticks, then over "Press A+B" (0x3372), until A or B.
    title = []
    for text in (0x3382, 0x3372):
        s = new()
        for a, x in zip(SLICES, SLICE_X):
            s.sprite(a, x, 0)
        s.string(text)
        title.append(s)
    # 0x1574: the channel screen without its bottom row for 0x10 ticks
    # (0x09ED clears 48x8 at y = 24), then whole for 0x10, until A.
    whole = new()
    whole.bitmap(BITMAPS['channel'], 0, 0)
    blink = new()
    blink.bitmap(BITMAPS['channel'], 0, 0)
    blink.clear(0, 24, 48, 8)
    # 0x15E5: the size menu. Title, line at row 7, three choices; the cursor
    # starts on the first (0x013 = 1).
    menu = new()
    menu.string(0x333E)
    menu.line(7)
    for a in (0x334E, 0x335A, 0x3364):
        menu.string(a)
    menu.glyph(*CURSOR, 0, 8)
    # 0x166E then 0x1690: with nothing downloaded (0x04A = 0), the choices
    # are cleared and the message drawn, with a line at row 0x17.
    none = new()
    none.string(0x333E)
    none.line(7)
    none.clear(0, 8, 48, 24)
    none.string(0x33A2)
    none.line(0x17)
    return [
        ('startup', [sega, copy], 0x20),
        ('title', title, 0x10),
        ('channel', [whole, blink], 0x10),
        ('size-menu', [menu], None),
        ('no-graffiti', [none], None),
    ]


def font_sheet(cells, w, h, cols=16):
    rows = -(-len(cells) // cols)
    im = Image.new('1', (cols * w, rows * h), 1)
    for n, (gw, bits) in enumerate(cells):
        for r, b in enumerate(bits):
            for k in range(gw):
                if b >> (7 - k) & 1:
                    im.putpixel(((n % cols) * w + k, (n // cols) * h + r), 0)
    return im


def sprite_image(w, h, rows):
    im = Image.new('1', (w, h), 1)
    for r, b in enumerate(rows):
        for k in range(w):
            if b >> (7 - k) & 1:
                im.putpixel((k, r), 0)
    return im


def bitmap_image(d, addr):
    wb, h = d[addr], d[addr + 1]
    rows = [d[addr + 2 + r * wb:addr + 2 + (r + 1) * wb] for r in range(h)]
    im = Image.new('1', (8 * wb, h), 1)
    for r, row in enumerate(rows):
        for c, b in enumerate(row):
            for k in range(8):
                if b >> (7 - k) & 1:
                    im.putpixel((8 * c + k, r), 0)
    return im


def main(src, out):
    d, member_off = unpack_afs(src)
    if d[0x200:0x20B] != b'JET_VM_APLI':
        sys.exit('member 0 is not the JET_VM_APLI program')
    out = Path(out)
    for sub in ('screens', 'sprites'):
        (out / sub).mkdir(parents=True, exist_ok=True)
    manifest = dict(member=MEMBER, member_offset=member_off, screens=[], sprites=[])
    previews = []

    for name, frames, ticks in screens(d):
        strip = Image.new('1', (48, 32 * len(frames)), 1)
        for k, s in enumerate(frames):
            strip.paste(s.image(), (0, 32 * k))
            previews.append((f'{name} {k + 1}', s.image()))
        strip.save(out / 'screens' / f'{name}.png')
        manifest['screens'].append(dict(name=name, frames=[s.hex() for s in frames],
                                        ticks=ticks))

    def add_sprite(name, im, offset, drawn_at=None):
        im.save(out / 'sprites' / f'{name}.png')
        manifest['sprites'].append(dict(name=name, offset=offset, width=im.width, height=im.height,
                                        drawn_at=drawn_at or []))
        previews.append((name, im))

    add_sprite('sega', bitmap_image(d, BITMAPS['sega']), BITMAPS['sega'] + 2, [('startup', 0, 4)])
    add_sprite('copyright', bitmap_image(d, BITMAPS['copyright']), BITMAPS['copyright'] + 2,
               [('startup', 0, 6)])
    for k, (a, x) in enumerate(zip(SLICES, SLICE_X)):
        add_sprite(f'radio-{k + 1}', sprite_image(d[a], d[a + 1], d[a + 2:a + 2 + d[a + 1]]), a + 2,
                   [('title', x, 0)])
    for font, (name, base, count) in FONTS.items():
        cells = [(d[base + 10 * n], d[base + 10 * n + 2:base + 10 * n + 10]) for n in range(count)]
        add_sprite(f'font-{name}', font_sheet(cells, 8, 8), base)
    for name, (base, count, w, h) in PLAIN_FONTS.items():
        cells = [(w, d[base + h * n:base + h * (n + 1)]) for n in range(count)]
        add_sprite(f'font-{name}', font_sheet(cells, w + 1, h + 1), base)

    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    scale = 3
    sheet = Image.new('RGB', (16 + 6 * (48 * scale + 16), 44 + 4 * (32 * scale + 30)), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), 'SYSOPTION.AFS #0, JET_VM_APLI', fill='black')
    for n, (label, im) in enumerate(p for p in previews if p[1].width <= 48 and p[1].height <= 32):
        x, y = 16 + (n % 6) * (48 * scale + 16), 44 + (n // 6) * (32 * scale + 30)
        draw.text((x, y), label, fill='black')
        sheet.paste(im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')
    print(len(manifest['screens']), 'screens,', len(manifest['sprites']), 'sprites ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
