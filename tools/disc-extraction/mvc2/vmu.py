"""Pull Marvel vs. Capcom 2's VMU screens and save icons out of its program.

    python3 vmu.py <1ST_READ.BIN> <VS4.BIN> <out dir>

Writes:
- lcd/NN.png, one per screen (dark = lit, as `pnpm icons:import` reads it),
  and manifest.json;
- saves/*.VMS and saves/save-icons.json: each save the game writes, its
  header rebuilt the way the game builds it (for `pnpm saveicons:import`),
  and VS.COM as it is on the disc (VS4.BIN, a whole VMU program);
- contact-sheet.png.

Addresses are for the JP release (Redump `Marvel vs. Capcom 2 - New Age of
Heroes (Japan)`); 1ST_READ.BIN loads at 0x8C010000. See
content/games/marvel-vs-capcom-2.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SIZE = 192  # 48x32 at 1 bit a dot

# The screens are handed to 0x8C1257C0, which spreads each bit to a byte (8 for
# a 1 bit, 0 for a 0 bit) at 0x8C1906E4; the library packs a byte with bit 3
# set as a lit dot (0x8C1AD772). Nothing inverts on the way, so a 1 bit is a
# lit dot and the stored title is what the VMU shows.
SCREENS = [
    dict(address=0x8C190CE4, what='title'),
    dict(address=0x8C190DA4, what='access'),
]
DRAW = 0x8C1257C0  # every caller loads the address into r4, then jsr's here

# The save table the header builder (0x8C127188) copies from, one per file
# type it's called with: VMS name, description (both Shift-JIS), and the
# memory card name from 0x8C164994. Palettes come from the pointer table at
# 0x8C191058, frames from 0x8C191A6C; every one has 1 frame, speed 5. Type 2,
# VS.COM, copies nothing: the file is VS4.BIN, a VMU program with its own
# header.
SAVES = [
    dict(type=0, what='UPLOAD file', vms=0x8C190E64, desc=0x8C190E76),
    dict(type=1, what='System file', vms=0x8C190EA8, desc=0x8C190EBA),
    dict(type=2, what='VS.COM file'),
    dict(type=3, what='DOWNLOAD file', vms=0x8C190F30, desc=0x8C190F42),
    dict(type=4, what='Capcom network file', vms=0x8C190F74, desc=0x8C190F86),
]
NAMES = 0x8C164994  # memory card names, 16 bytes each
# type → row of NAMES, matched by name (UPLOAD is MVLVS.C2__UP, and so on)
NAME_OF_TYPE = {0: 1, 1: 0, 2: 4, 3: 3, 4: 2}
PALETTES = 0x8C191058
BITMAPS = 0x8C191A6C


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def cstr(b, addr, n):
    raw = at(b, addr, n)
    return raw.split(b'\0')[0]


def screen_image(blk):
    im = Image.new('1', (48, 32), 1)
    im.putdata([0 if c == '1' else 1 for c in ''.join(f'{x:08b}' for x in blk)])
    return im


def callers(b, addr):
    """Literal-pool slots holding `addr`, as memory addresses."""
    want = struct.pack('<I', addr)
    out, i = [], b.find(want)
    while i >= 0:
        if i % 4 == 0:
            out.append(LOAD + i)
        i = b.find(want, i + 1)
    return out


def main(src, vs4, out):
    b = Path(src).read_bytes()
    out = Path(out)
    for sub in ('lcd', 'saves'):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir(parents=True)

    manifest, images = [], []
    for n, s in enumerate(SCREENS):
        blk = at(b, s['address'], SIZE)
        im = screen_image(blk)
        name = f'{n:02d}'
        im.save(out / 'lcd' / f'{name}.png')
        refs = callers(b, s['address'])
        manifest.append(dict(name=name, what=s['what'], address=f'{s["address"]:#x}',
                             literals=[f'{r:#x}' for r in refs], frame_hex=blk.hex()))
        images.append((s['what'], im))
        print(name, s['what'], f'{s["address"]:#x}', f'{len(refs)} literal(s)')

    # The buffer 0x8C1257C0 writes into isn't empty on the disc: it holds the
    # bottom of a screen as bytes (8 = lit), left over from the build. Kept in
    # the manifest for the notes, not imported: the game overwrites it before
    # every send.
    buf = at(b, 0x8C1906E4, 48 * 32)
    leftover = bytes(int(''.join('1' if buf[r * 48 + c * 8 + k] else '0' for k in range(8)), 2)
                     for r in range(32) for c in range(6))
    im = screen_image(leftover)
    im.save(out / 'lcd' / 'buffer.png')
    images.append(('buffer on disc', im))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    titles = {}
    pal_ptrs = struct.unpack('<5I', at(b, PALETTES, 20))
    bmp_ptrs = struct.unpack('<5I', at(b, BITMAPS, 20))
    for s in SAVES:
        t = s['type']
        card = cstr(b, NAMES + 16 * NAME_OF_TYPE[t], 16).decode('ascii')
        if t == 2:
            data = Path(vs4).read_bytes()
            # Its header names it as the save table would, and its icon is
            # the table's: three copies of type 2's palette and frame.
            h = 0x200
            assert data[h + 0x60:h + 0x80] == at(b, pal_ptrs[t], 32)
            assert all(data[h + 0x80 + 512 * k:h + 0x280 + 512 * k] == at(b, bmp_ptrs[t], 512)
                       for k in range(3))
        else:
            hdr = bytearray(0x80)
            hdr[0:16] = cstr(b, s['vms'], 18).ljust(16, b' ')[:16]
            hdr[0x10:0x30] = cstr(b, s['desc'], 34).ljust(32, b' ')[:32]
            struct.pack_into('<HH', hdr, 0x40, 1, 5)
            hdr[0x60:0x80] = at(b, pal_ptrs[t], 32)
            data = bytes(hdr) + at(b, bmp_ptrs[t], 512)
        file = f'{t}-{card.replace("/", "_")}.VMS'
        (out / 'saves' / file).write_bytes(data)
        titles[file] = s['what']
        print(f'save type {t}: {card:12} {s["what"]:20} palette {pal_ptrs[t]:#x} frame {bmp_ptrs[t]:#x}')
    (out / 'saves' / 'save-icons.json').write_text(json.dumps(dict(
        game='Marvel vs. Capcom 2', publisher='Capcom', year=2000, region='ntsc-j',
        disc='/1ST_READ.BIN', titles=titles), ensure_ascii=False, indent=1))

    scale = 3
    cw = 48 * scale + 16
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + 32 * scale + 30), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), 'Marvel vs. Capcom 2: 1ST_READ.BIN', fill='black')
    for k, (what, im) in enumerate(images):
        x = 16 + k * cw
        draw.text((x, 44), what, fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
