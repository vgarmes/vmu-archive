"""Decode Sword of the Berserk's VMU screens from /LCDIMG.BIN.

    python3 lcdimg.py <LCDIMG.BIN> <out dir>

Format: u32 count, then `count` u32 offsets; each entry is a width byte, a height
byte, then one byte per pixel (0 = off, 0x0f = on), rows stored right-to-left
(the art is mirrored). The table says 49 entries but a 50th follows the last one
and the game draws it, so entries are read until the file ends.

Writes lcd/NN.png (un-mirrored, dark = lit, as `pnpm icons:import` reads it),
manifest.json (every entry, with its frame in the archive's hex encoding) and
contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def entries(b):
    count = struct.unpack_from('<I', b, 0)[0]
    offsets = list(struct.unpack_from(f'<{count}I', b, 4))
    pos = offsets[-1]
    while True:  # follow entries past the table until the file ends
        w, h = b[pos], b[pos + 1]
        pos += 2 + w * h
        if pos + 2 > len(b):
            break
        offsets.append(pos)
    for i, off in enumerate(offsets):
        w, h = b[off], b[off + 1]
        pixels = b[off + 2:off + 2 + w * h]
        assert len(pixels) == w * h and set(pixels) <= {0, 0x0F}, f'entry {i} is not a bitmap'
        rows = [[1 if v else 0 for v in pixels[r * w:(r + 1) * w]][::-1] for r in range(h)]  # un-mirror
        yield dict(index=i, offset=off, width=w, height=h, in_table=i < count, rows=rows)


def frame_hex(rows):
    bits = ''.join(str(v) for row in rows for v in row)
    return ''.join(f'{int(bits[i:i + 8], 2):02x}' for i in range(0, len(bits), 8))


def main(src, out):
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for e in entries(Path(src).read_bytes()):
        w, h = e['width'], e['height']
        im = Image.new('1', (w, h), 1)
        im.putdata([0 if v else 1 for row in e['rows'] for v in row])
        name = f"{e['index']:02d}"
        im.save(out / 'lcd' / f'{name}.png')
        screen = (w, h) == (48, 32)
        manifest.append(dict(name=name, kind='screen' if screen else 'glyph', width=w, height=h,
                             offset=e['offset'], in_table=e['in_table'],
                             frame_hex=frame_hex(e['rows']) if screen else None))
        images.append((name, im, screen))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    screens = [i for i in images if i[2]]
    glyphs = [i for i in images if not i[2]]
    scale, cols = 3, 6
    cw, ch = 48 * scale + 16, 32 * scale + 30
    rows = (len(screens) + cols - 1) // cols
    sheet = Image.new('RGB', (16 + cols * cw, 44 + rows * ch + 50), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'/LCDIMG.BIN: {len(screens)} screens, {len(glyphs)} glyphs', fill='black')
    for k, (name, im, _) in enumerate(screens):
        x, y = 16 + k % cols * cw, 44 + k // cols * ch
        draw.text((x, y), f'#{name}', fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, y + 14))
    x = 16
    for _, im, _ in glyphs:
        sheet.paste(im.convert('RGB').resize((im.width * 6, im.height * 6), Image.NEAREST), (x, 44 + rows * ch))
        x += im.width * 6 + 8
    sheet.save(out / 'contact-sheet.png')
    print(len(screens), 'screens,', len(glyphs), 'glyphs ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
