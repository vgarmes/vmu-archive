"""Pull Napple Tale's VMU screens, font and save icons out of its program.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes:
- screens/NN.png (dark = lit, as `pnpm icons:import` reads it) and
  sprites/font.png;
- manifest.json, what each one is and where it came from (read by prep.py);
- saves/*.VMS and saves/save-icons.json: each save's header rebuilt the way
  the game builds it, for `pnpm saveicons:import`;
- contact-sheet.png.

Redump `Napple Tale - Arsia in Daydream (Japan)`; 1ST_READ.BIN loads at
0x8C010000. See content/games/napple-tale-arsia-in-daydream.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H = 48, 32

# Six screens, a byte a dot (255 lit, 0 not), back to back. The send at
# 0x8C032886 writes screen n (0x8C0328C6: SCREENS + n * 1536) through the LCD
# write at 0x8C114300; n < 0 sends the work buffer at 0x8C2E6B2C instead.
SCREENS, COUNT, LIT = 0x8C0FC6C0, 6, 255
USES = {
    0: 'copied to the score display buffer 0x8C2E4270 (0x8C01841A)',
    1: 'send(1) at 0x8C033EC2', 2: 'send(2) at 0x8C0342BE', 3: 'send(3), as at 0x8C034188',
    4: 'send(4), as at 0x8C033DB2', 5: 'send(5) at 0x8C034E84',
}

# The score display's font (0x8C018360 draws a string): characters from space
# (32) on, 3 bytes each, each byte two rows of 4 dots, high nibble first; 4x6.
FONT, GLYPHS, GW, GH = 0x8C0FEADC, 96, 4, 6

# The two saves (headers built at 0x8C033160 and 0x8C03354A): one frame at
# speed 1 each, the same frame with its own palette. The VMU name, the
# description and the 16 bytes at +52 come from the table at 0x8C105164.
FRAME = 0x8C101130
SAVES = [
    dict(file='NAPPLE_T.000', title='Game file', palette=0x8C1010F0,
         name=0x8C0F6864, slot=1),  # "ﾅｯﾌﾟﾙ ﾌｧｲﾙ%d", the slot from 1
    dict(file='NAPPLE_T.SYS', title='System file', palette=0x8C101110, name=0x8C0F6884),
]
DESCRIPTION = 0x8C0F682C  # ナップル・テール


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def cstr(b, addr):
    raw = b[addr - LOAD:]
    return raw[:raw.index(0)]


def image(rows):
    im = Image.new('1', (len(rows[0]), len(rows)), 1)
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            if v:
                im.putpixel((x, y), 0)
    return im


def font_rows(b):
    raw = at(b, FONT, 3 * GLYPHS)
    rows = []
    for c in range(GLYPHS):
        for r in range(GH):
            byte = raw[3 * c + r // 2]
            nib = byte >> 4 if r % 2 == 0 else byte & 15
            rows.append([nib >> (3 - x) & 1 for x in range(GW)])
    rebuilt = bytes(
        sum(v << (7 - x) for x, v in enumerate(rows[g * GH + 2 * k] + rows[g * GH + 2 * k + 1]))
        for g in range(GLYPHS) for k in range(3))
    assert rebuilt == raw, 'the font rebuilds to the disc bytes'
    return rows


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

    for n in range(COUNT):
        raw = at(b, SCREENS + n * W * H, W * H)
        assert set(raw) == {0, LIT}
        emit('screens', f'{n:02d}', [[1 if raw[y * W + x] else 0 for x in range(W)] for y in range(H)],
             entry=n, address=f'{SCREENS + n * W * H:#x}', use=USES[n])
    emit('sprites', 'font', font_rows(b), address=f'{FONT:#x}')

    titles = {}
    for s in SAVES:
        name = cstr(b, s['name'])
        if 'slot' in s:
            name = name.replace(b'%d', str(s['slot']).encode())
        hdr = bytearray(0x80)
        hdr[0:16] = name.ljust(16, b' ')[:16]
        hdr[0x10:0x30] = cstr(b, DESCRIPTION).ljust(32, b' ')[:32]
        struct.pack_into('<HH', hdr, 0x40, 1, 1)
        hdr[0x60:0x80] = at(b, s['palette'], 32)
        (out / 'saves' / f'{s["file"]}.VMS').write_bytes(bytes(hdr) + at(b, FRAME, 512))
        titles[f'{s["file"]}.VMS'] = s['title']
    (out / 'saves' / 'save-icons.json').write_text(json.dumps(dict(
        game='Napple Tale: Arsia in Daydream', publisher='Sega', year=2000, region='ntsc-j',
        disc='/1ST_READ.BIN', titles=titles), ensure_ascii=False, indent=1))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    scale = 3
    tiles = [(n, im) for n, im in sheet if im.height == H]
    img = Image.new('RGB', (16 + len(tiles) * (W * scale + 16) + GW * scale + 16, 44 + 600 * 2), '#f5f2e9')
    d = ImageDraw.Draw(img)
    d.text((16, 14), 'Napple Tale: 1ST_READ.BIN', fill='black')
    for k, (name, im) in enumerate(tiles):
        x = 16 + k * (W * scale + 16)
        d.text((x, 30), name, fill='black')
        img.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, 44))
    font = sheet[-1][1]
    img.paste(font.convert('RGB').resize((GW * 2, font.height * 2), Image.NEAREST),
              (16 + len(tiles) * (W * scale + 16), 44))
    img.save(out / 'contact-sheet.png')
    print(len(manifest), 'pieces and', len(SAVES), 'saves ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
