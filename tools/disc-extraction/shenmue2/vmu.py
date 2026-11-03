"""Decode Shenmue II's VMU screens and sprites from /MISC/COLD.BIN.

    python3 vmu.py <COLD.BIN> <out dir>

Shenmue (the first game) stores its art the same way and reads unchanged; see
../shenmue/. The code addresses below are Shenmue II's.

COLD.BIN (a PAKS pack the game loads at boot) holds one IWAD chunk with every
piece of VMU art:

    "IWAD", u32 count, u32 directory offset, …
    directory: count × { char name[8] (space-padded), u32 size, u32 offset }
    entry (at IWAD + offset): u8 width, u8 height, then height rows of
    ceil(width / 8) bytes, high bit first, 1 = lit, stored upright

The game copies it into a buffer it allocates with the tag 'LCDM' (0x8C0C2460)
and looks entries up by name (0x8C0C2420) from a list at 0x8C22EF68. The 48x32
entries are whole screens. The rest are sprites the game draws onto a screen at
run time: BT_L? and BT_S? (large and small digits, looked up by filling in the
"?") for the BT_COUNT counter, and WAZA_* (QTE buttons).

Writes lcd/<NAME>.png (dark = lit, as `pnpm icons:import` reads it; sprites at
their own size), manifest.json and contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def entries(b):
    base = b.find(b'IWAD')
    assert base >= 0 and b.find(b'IWAD', base + 1) < 0, 'expected exactly one IWAD chunk'
    count, diroff = struct.unpack_from('<II', b, base + 4)
    for k in range(count):
        o = base + diroff + k * 16
        name = b[o:o + 8].decode('ascii').rstrip()
        size, off = struct.unpack_from('<II', b, o + 8)
        w, h = b[base + off], b[base + off + 1]
        stride = (w + 7) // 8
        assert size == 2 + stride * h, f'{name}: {size} bytes for {w}x{h}'
        data = b[base + off + 2:base + off + 2 + stride * h]
        rows = [[data[r * stride + c // 8] >> (7 - c % 8) & 1 for c in range(w)] for r in range(h)]
        yield dict(name=name, width=w, height=h, offset=base + off, rows=rows)


def frame_hex(rows):
    bits = ''.join(str(v) for row in rows for v in row)
    return ''.join(f'{int(bits[i:i + 8], 2):02x}' for i in range(0, len(bits), 8))


def main(src, out):
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for e in sorted(entries(Path(src).read_bytes()), key=lambda e: e['name']):
        w, h = e['width'], e['height']
        im = Image.new('1', (w, h), 1)
        im.putdata([0 if v else 1 for row in e['rows'] for v in row])
        im.save(out / 'lcd' / f'{e["name"]}.png')
        screen = (w, h) == (48, 32)
        manifest.append(dict(name=e['name'], kind='screen' if screen else 'sprite', width=w, height=h,
                             offset=e['offset'], frame_hex=frame_hex(e['rows']) if screen else None))
        images.append((e['name'], im))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    scale, cols = 3, 6
    cw, ch = 48 * scale + 16, 32 * scale + 30
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new('RGB', (16 + cols * cw, 44 + rows * ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'COLD.BIN IWAD: {len(images)} entries', fill='black')
    for k, (name, im) in enumerate(images):
        x, y = 16 + k % cols * cw, 44 + k // cols * ch
        draw.text((x, y), f'{name} {im.width}x{im.height}', fill='black')
        sheet.paste(im.convert('RGB').resize((im.width * scale, im.height * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')
    screens = sum(m['kind'] == 'screen' for m in manifest)
    print(screens, 'screens,', len(manifest) - screens, 'sprites ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
