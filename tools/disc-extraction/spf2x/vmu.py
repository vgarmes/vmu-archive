"""Pull Super Puzzle Fighter II X for Matching Service's VMU screens and save
icons out of its program.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes:
- lcd/NN.png, one per screen (dark = lit, as `pnpm icons:import` reads it),
  lcd/buffer.png (what the send buffer holds on the disc, for the notes) and
  manifest.json;
- saves/*.VMS and saves/save-icons.json: each save the game writes, its
  header rebuilt the way the game builds it (for `pnpm saveicons:import`);
- contact-sheet.png.

Addresses are for the JP release (Redump `Super Puzzle Fighter II X for
Matching Service (Japan)`, T-1250M V1.001); 1ST_READ.BIN loads at 0x8C010000.
See content/games/super-puzzle-fighter-ii-x-for-matching-service.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SIZE = 192  # 48x32 at 1 bit a dot

# Four screens back to back. 0x8C0CF2B2 spreads a screen's bits into the byte
# buffer BUFFER (8 for a 1 bit, 0 for a 0 bit) and 0x8C0CF31C sends it; all
# seven sends are an expand of the title or ACCESS followed by a send. OK! and
# ERROR! follow them but nothing loads their address.
SCREENS = [
    dict(address=0x8C1747FC, what='title', shown=True),
    dict(address=0x8C1748BC, what='access', shown=True),
    dict(address=0x8C17497C, what='ok', shown=False),
    dict(address=0x8C174A3C, what='error', shown=False),
]
EXPAND = 0x8C0CF2B2
BUFFER = 0x8C1741FC

# The header builder (0x8C0CF362) by file type: VMU name and description
# (both Shift-JIS), the palette from the pointers at 0x8C1741EC and the frame
# from 0x8C1741F4; one frame, speed 5. The memory card names are at 0x8C174B1C.
SAVES = [
    dict(type=0, what='Save file', card=0x8C174B1C, vms=0x8C173D24, desc=0x8C173D36),
    dict(type=1, what='Capcom network file', card=0x8C174B2C, vms=0x8C173D68, desc=0x8C173D7A),
]
PALETTES = 0x8C1741EC
BITMAPS = 0x8C1741F4


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def cstr(b, addr, n):
    return at(b, addr, n).split(b'\0')[0]


def screen_image(blk):
    im = Image.new('1', (48, 32), 1)
    im.putdata([0 if c == '1' else 1 for c in ''.join(f'{x:08b}' for x in blk)])
    return im


def literals(b, addr):
    """Literal-pool slots holding `addr`, as memory addresses."""
    want = struct.pack('<I', addr)
    out, i = [], b.find(want)
    while i >= 0:
        if i % 4 == 0:
            out.append(LOAD + i)
        i = b.find(want, i + 1)
    return out


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    for sub in ('lcd', 'saves'):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir(parents=True)

    manifest, images = [], []
    for n, s in enumerate(SCREENS):
        blk = at(b, s['address'], SIZE)
        refs = literals(b, s['address'])
        assert bool(refs) == s['shown'], (s['what'], refs)
        im = screen_image(blk)
        name = f'{n:02d}'
        im.save(out / 'lcd' / f'{name}.png')
        manifest.append(dict(name=name, what=s['what'], address=f'{s["address"]:#x}',
                             shown=s['shown'], literals=[f'{r:#x}' for r in refs],
                             frame_hex=blk.hex()))
        images.append((s['what'], im))
        print(name, s['what'], f'{s["address"]:#x}', f'{len(refs)} literal(s)')

    # The buffer holds a line drawing on the disc, as bytes (8 = lit, 0 not).
    # The game fills it before every send, so it's never shown; kept for the
    # notes, not imported.
    buf = at(b, BUFFER, 48 * 32)
    assert set(buf) <= {0, 8}
    leftover = bytes(int(''.join('1' if buf[r * 48 + c * 8 + k] else '0' for k in range(8)), 2)
                     for r in range(32) for c in range(6))
    im = screen_image(leftover)
    im.save(out / 'lcd' / 'buffer.png')
    images.append(('buffer on disc', im))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    titles = {}
    pal_ptrs = struct.unpack('<2I', at(b, PALETTES, 8))
    bmp_ptrs = struct.unpack('<2I', at(b, BITMAPS, 8))
    for s in SAVES:
        t = s['type']
        card = cstr(b, s['card'], 16).decode('ascii')
        hdr = bytearray(0x80)
        hdr[0:16] = cstr(b, s['vms'], 18).ljust(16, b' ')[:16]
        hdr[0x10:0x30] = cstr(b, s['desc'], 34).ljust(32, b' ')[:32]
        struct.pack_into('<HH', hdr, 0x40, 1, 5)
        hdr[0x60:0x80] = at(b, pal_ptrs[t], 32)
        data = bytes(hdr) + at(b, bmp_ptrs[t], 512)
        file = f'{t}-{card}.VMS'
        (out / 'saves' / file).write_bytes(data)
        titles[file] = s['what']
        print(f'save type {t}: {card:12} {s["what"]:20} palette {pal_ptrs[t]:#x} frame {bmp_ptrs[t]:#x}')
    (out / 'saves' / 'save-icons.json').write_text(json.dumps(dict(
        game='Super Puzzle Fighter II X for Matching Service', publisher='Capcom', year=2001,
        region='ntsc-j', disc='/1ST_READ.BIN', titles=titles), ensure_ascii=False, indent=1))

    scale = 3
    cw = 48 * scale + 16
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + 32 * scale + 30), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), 'Super Puzzle Fighter II X for Matching Service: 1ST_READ.BIN', fill='black')
    for k, (what, im) in enumerate(images):
        x = 16 + k * cw
        draw.text((x, 44), what, fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')
    print(len(SCREENS), 'screens,', len(SAVES), 'saves ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
