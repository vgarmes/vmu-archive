"""Pull Vampire Chronicle for Matching Service's VMU screens and saves out of
its program.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes:
- inbox/*.png and their sidecars, for `pnpm icons:import` (dark = lit);
- saves/*.VMS and saves/save-icons.json, each save's header rebuilt the way
  the game builds it, for `pnpm saveicons:import`;
- contact-sheet.png, with what the screen buffer holds on the disc.

Addresses are for the Japanese release (Redump `Vampire Chronicle for
Matching Service (Japan)`); 1ST_READ.BIN loads at 0x8C010000. See
content/games/vampire-chronicle-for-matching-service.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SIZE = 192  # 48x32 at 1 bit a dot

# Four screens back to back after the screen buffer, stored as shown. Every
# caller loads a screen's address into r4 and calls 0x8C0AAE3A, which spreads
# its bits into the byte buffer at 0x8C2275F4 (8 for a 1 bit, 0 for a 0 bit)
# for the library's LCD write: Marvel vs. Capcom 2's code, so a 1 bit is lit.
# Only the logo and ACCESS are ever passed to it.
SCREENS = [
    dict(address=0x8C227BF4, name='title', title='Title screen', tags=['logo']),
    dict(address=0x8C227CB4, name='access', title='Access', tags=['memory-card']),
    dict(address=0x8C227D74, name='ok', title='OK', tags=['memory-card'], unused=True),
    dict(address=0x8C227E34, name='error', title='Error', tags=['memory-card'], unused=True),
]
BUFFER = 0x8C2275F4
GAME = dict(game='Vampire Chronicle for Matching Service', publisher='Capcom', year=2000, region='ntsc-j')

# The header builder (0x8C0AAEE0) copies a VMU name, description and the
# 16-byte code after them by save type, then the palette and frame from the
# pointers at 0x8C2275E4 and 0x8C2275EC: one frame, animation speed 5.
SAVES = [
    dict(type=0, title='Save file', card='VAMPIRE_.SYS', vms=0x8C22711C, desc=0x8C22712E),
    dict(type=1, title='Capcom network file', card='CAP_NET_.NET', vms=0x8C227160, desc=0x8C227172),
]
PALETTES = 0x8C2275E4
BITMAPS = 0x8C2275EC


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def cstr(b, addr, n):
    return at(b, addr, n).split(b'\0')[0]


def screen_image(blk):
    im = Image.new('1', (48, 32), 1)
    im.putdata([0 if c == '1' else 1 for c in ''.join(f'{x:08b}' for x in blk)])
    return im


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    for sub in ('inbox', 'saves'):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir(parents=True)

    images = []
    for s in SCREENS:
        im = screen_image(at(b, s['address'], SIZE))
        stem = f'vampire-{s["name"]}'
        im.save(out / 'inbox' / f'{stem}.png')
        meta = dict(title=s['title'], tags=s['tags'], **GAME)
        if s.get('unused'):
            meta['unused'] = True
        (out / 'inbox' / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        images.append((s['title'], im))
        print(f'{s["title"]:13} {s["address"]:#x}{"  unused" if s.get("unused") else ""}')

    # The buffer isn't empty on the disc: it holds a screen as bytes (8 =
    # lit), left over from the build. The game fills it before every send.
    buf = at(b, BUFFER, 48 * 32)
    assert set(buf) <= {0, 8}
    leftover = bytes(int(''.join('1' if buf[r * 48 + c * 8 + k] else '0' for k in range(8)), 2)
                     for r in range(32) for c in range(6))
    images.append(('buffer on disc', screen_image(leftover)))

    pals = struct.unpack('<2I', at(b, PALETTES, 8))
    bmps = struct.unpack('<2I', at(b, BITMAPS, 8))
    titles = {}
    for s in SAVES:
        t = s['type']
        hdr = bytearray(0x80)
        hdr[0:16] = cstr(b, s['vms'], 18).ljust(16, b' ')[:16]
        hdr[0x10:0x30] = cstr(b, s['desc'], 34).ljust(32, b' ')[:32]
        struct.pack_into('<HH', hdr, 0x40, 1, 5)
        hdr[0x60:0x80] = at(b, pals[t], 32)
        file = f'{t}-{s["card"].replace(".", "_")}.VMS'
        (out / 'saves' / file).write_bytes(bytes(hdr) + at(b, bmps[t], 512))
        titles[file] = s['title']
        print(f'save type {t}: {s["card"]:12} palette {pals[t]:#x} frame {bmps[t]:#x}')
    (out / 'saves' / 'save-icons.json').write_text(json.dumps(
        dict(**GAME, disc='/1ST_READ.BIN', titles=titles), ensure_ascii=False, indent=1))

    scale = 3
    cw = 48 * scale + 16
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + 32 * scale + 30), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), 'Vampire Chronicle: 1ST_READ.BIN', fill='black')
    for k, (what, im) in enumerate(images):
        x = 16 + k * cw
        draw.text((x, 44), what, fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
