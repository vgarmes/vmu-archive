"""Pull Border Down's VMU screens, digits and save icon out of its program.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes:
- screens/<name>.png (dark = lit, as `pnpm icons:import` reads it) and
  sprites/digits.png;
- manifest.json, what each one is and where it came from (read by prep.py);
- saves/BORDERDOWNDC.VMS and saves/save-icons.json: the save's header rebuilt
  the way the game builds it, for `pnpm saveicons:import`;
- contact-sheet.png.

Redump `Border Down (Japan)` (T-46703M V1.000); 1ST_READ.BIN loads at
0x8C010000. See content/games/border-down.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H = 48, 32
LIT = 8  # screens are kept a byte a dot, 8 lit, 0 not: what the LCD library takes

# The SDF logo: a whole screen, sent as it is by 0x8C137C18 (r4 0, r5 this)
# from 0x8C07B5B6, 0x8C12779C, 0x8C127C14 and 0x8C13781E.
LOGO = 0x8C145ED4
# The hit counter. 0x8C127E60 prints the value at 0x8C1D20F4 with "%4d"
# (0x8C16C838) and draws each character but spaces from the digit table
# (0x8C16C7DC, indexed from '0') into BACKGROUND at y 10, x 1 + 12 i, then
# sends it. 0x8C127E3C clears rows 10-21 first; the rest of the buffer, TOTAL
# above and HIT below, is as on the disc.
BACKGROUND = 0x8C1825C8
DIGITS = 0x8C16C7DC
DIGIT_W, DIGIT_H = 10, 12
FORMAT = 0x8C16C838
SHOWN_COUNT = 0  # the screen as the game draws it for a count of 0

# The save (0x8C1379E0): the VMU name and description at BORDERDOWNDC + 84
# and + 93, the palette and one frame from 0x8C145CB4 and 0x8C145CD4, one
# frame at speed 1.
CARD_NAME = 0x8C1810D0
PALETTE, FRAME = 0x8C145CB4, 0x8C145CD4


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def dots(raw, w, h):
    assert set(raw) <= {0, LIT}
    return [[1 if raw[y * w + x] else 0 for x in range(w)] for y in range(h)]


def image(rows):
    im = Image.new('1', (len(rows[0]), len(rows)), 1)
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            if v:
                im.putpixel((x, y), 0)
    return im


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    for sub in ('screens', 'sprites', 'saves'):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir(parents=True)
    manifest, sheet = [], []

    def emit(kind, name, rows, **meta):
        im = image(rows)
        im.save(out / kind / f'{name}.png')
        manifest.append(dict(kind=kind, name=name, width=im.width, height=im.height, **meta))
        sheet.append((name, im))

    emit('screens', 'logo', dots(at(b, LOGO, W * H), W, H), address=f'{LOGO:#x}')

    ptrs = struct.unpack('<10I', at(b, DIGITS, 40))
    assert all(p - ptrs[0] == k * DIGIT_W * DIGIT_H for k, p in enumerate(ptrs))
    glyphs = [dots(at(b, p, DIGIT_W * DIGIT_H), DIGIT_W, DIGIT_H) for p in ptrs]
    font = [row for g in glyphs for row in g]
    rebuilt = bytes(LIT if v else 0 for row in font for v in row)
    assert rebuilt == at(b, ptrs[0], 10 * DIGIT_W * DIGIT_H)
    emit('sprites', 'digits', font, address=f'{ptrs[0]:#x}')

    assert at(b, FORMAT, 4) == b'%4d\0'
    scr = dots(at(b, BACKGROUND, W * H), W, H)
    for y in range(10, 22):
        scr[y] = [0] * W
    for i, ch in enumerate(f'{SHOWN_COUNT:4d}'):
        if ch != ' ':
            for y, row in enumerate(glyphs[int(ch)]):
                for x, v in enumerate(row):
                    scr[10 + y][1 + 12 * i + x] = v
    emit('screens', 'hit-counter', scr, address=f'{BACKGROUND:#x}', count=SHOWN_COUNT)

    hdr = bytearray(0x80)
    hdr[0:16] = at(b, CARD_NAME + 84, 18).split(b'\0')[0].ljust(16, b' ')[:16]
    hdr[0x10:0x30] = at(b, CARD_NAME + 93, 34).split(b'\0')[0].ljust(32, b' ')[:32]
    struct.pack_into('<HH', hdr, 0x40, 1, 1)
    hdr[0x60:0x80] = at(b, PALETTE, 32)
    card = at(b, CARD_NAME, 16).split(b'\0')[0].decode('ascii')
    (out / 'saves' / f'{card}.VMS').write_bytes(bytes(hdr) + at(b, FRAME, 512))
    (out / 'saves' / 'save-icons.json').write_text(json.dumps(dict(
        game='Border Down', publisher='G.rev', year=2003, region='ntsc-j', disc='/1ST_READ.BIN',
        titles={f'{card}.VMS': 'Game data'}), ensure_ascii=False, indent=1))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    scale = 3
    img = Image.new('RGB', (16 + len(sheet) * (48 * scale + 16), 44 + 120 * scale), '#f5f2e9')
    d = ImageDraw.Draw(img)
    d.text((16, 14), 'Border Down: 1ST_READ.BIN', fill='black')
    for k, (name, im) in enumerate(sheet):
        x = 16 + k * (48 * scale + 16)
        d.text((x, 30), name, fill='black')
        img.paste(im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST), (x, 44))
    img.save(out / 'contact-sheet.png')
    print(len(manifest), 'pieces ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
