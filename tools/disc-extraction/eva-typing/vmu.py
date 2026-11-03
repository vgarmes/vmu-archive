"""Decode Shinseiki Evangelion: Typing E-Keikaku's VMU screens from /TYPE_E.EXE.

    python3 vmu.py <TYPE_E.EXE> <out dir>

JP v1.001. The game is a Windows CE program, not a 1ST_READ.BIN: TYPE_E.EXE is
an SH-4 PE file with image base 0x10000, and it reaches the VMU through
MAPLEDEV.dll. Addresses below are virtual addresses in that image; this script
maps them to file offsets through the PE section table.

The routine at 0x48670 shows screen n on a VMU: it sends 192 bytes from
0x5BEC0 + 192 * n (base literal at 0x487D0, stride literal at 0x487BC). The six
screens sit back to back in .data, packed 1 bit per pixel (high bit first,
1 = lit) and rotated 180 degrees as the VMU's LCD takes them. Reversing the
whole bit stream turns one upright.

    0  title logo   sent to every VMU by a device loop (0x48244), and after
                    each save or load
    1  ACCESS       while saving or loading
    2  SAVE OK!     3  SAVE NG!     4  LOAD OK!     5  LOAD NG!

Every index is passed to 0x48670 somewhere in 0x19E00-0x1A630. Nothing animates.

Writes lcd/NN.png (dark = lit, as `pnpm icons:import` reads it), manifest.json and
contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SHOW = 0x48670        # shows screen n
BASE_LITERAL = 0x487D0  # holds the address of screen 0
STRIDE_LITERAL = 0x487BC  # mov.w literal: bytes per screen
SIZE = 192
SCREENS = ['Title logo', 'ACCESS', 'SAVE OK!', 'SAVE NG!', 'LOAD OK!', 'LOAD NG!']


def sections(b):
    pe = struct.unpack_from('<I', b, 0x3C)[0]
    assert b[pe:pe + 4] == b'PE\0\0' and struct.unpack_from('<H', b, pe + 4)[0] == 0x1A6, 'not an SH-4 PE'
    count, opt = struct.unpack_from('<H', b, pe + 6)[0], struct.unpack_from('<H', b, pe + 20)[0]
    base = struct.unpack_from('<I', b, pe + 24 + 28)[0]
    out = []
    for i in range(count):
        _, vsize, rva, rsize, raw = struct.unpack_from('<8sIIII', b, pe + 24 + opt + 40 * i)
        out.append((base + rva, max(vsize, rsize), raw))
    return out


def offset(secs, va):
    for start, size, raw in secs:
        if start <= va < start + size:
            return raw + va - start
    raise ValueError(f'{va:#x} is in no section')


def frame_hex(blk):
    bits = ''.join(f'{x:08b}' for x in blk)[::-1]  # 180 degree turn
    return ''.join(f'{int(bits[i:i + 8], 2):02x}' for i in range(0, len(bits), 8))


def main(src, out):
    b = Path(src).read_bytes()
    secs = sections(b)
    first = struct.unpack_from('<I', b, offset(secs, BASE_LITERAL))[0]
    stride = struct.unpack_from('<h', b, offset(secs, STRIDE_LITERAL))[0]
    assert stride == SIZE, f'stride {stride}'
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for n, what in enumerate(SCREENS):
        va = first + n * SIZE
        off = offset(secs, va)
        hx = frame_hex(b[off:off + SIZE])
        bits = bin(int(hx, 16))[2:].zfill(48 * 32)
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if c == '1' else 1 for c in bits])
        im.save(out / 'lcd' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', kind='screen', what=what, width=48, height=32,
                             address=f'{va:#x}', offset=off, frame_hex=hx))
        images.append(im)
        print(n, f'{va:#x}', what)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    scale = 3
    cw, ch = 48 * scale + 16, 32 * scale + 30
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'TYPE_E.EXE, shown by {SHOW:#x}: {len(images)} screens', fill='black')
    for n, im in enumerate(images):
        x = 16 + n * cw
        draw.text((x, 44), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')
    print(len(images), 'screens ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
