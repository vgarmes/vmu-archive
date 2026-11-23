"""Pull Cool Cool Toon's VMU screens out of its program and its save icons out
of /CCT/VM_ICON_*.HBN.

    python3 vmu.py <folder with 1ST_READ.BIN and CCT/VM_ICON_*.HBN> <out dir>

Writes screens/NN.png (dark = lit, as `pnpm icons:import` reads it),
manifest.json, saves/*.VMS with saves/save-icons.json (for
`pnpm saveicons:import`), and contact-sheet.png.

Redump `Cool Cool Toon (Japan)`; 1ST_READ.BIN loads at 0x8C010000. See
content/games/cool-cool-toon.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H, SIZE = 48, 32, 192
REPO = Path(__file__).resolve().parents[3]

# Six packed screens (1 bit a dot, high bit leftmost, upright) from 0x8C09F3B8,
# their pointers following at TABLE. 0x8C0596BC sends screen k to one player's
# VMU and 0x8C0596EE to all eight, through 0x8C054E30, which turns a screen
# 180 degrees for a VMU that needs it and hands it to pdLcd's packed write.
TABLE, COUNT = 0x8C09F838, 6

# The VMU icons: MBIN files holding four LZSS-packed sections, three 32x32
# frames at 4 bits a dot (512 bytes each) and a 16-colour palette (32 bytes).
# The archive's save icon, read from a dumped COOLCOOL.SYS, is VM_ICON_MAN's.
ICONS = ['BOY', 'GIRL', 'MAN', 'WOMAN']
SAVE_ICON = REPO / 'content/save-icons/cool-cool-toon/system-file.json'
SPEED = 10  # as the dumped save has it


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def lzss(src, size):
    """The packing of the MBIN sections: flags low bit first, 1 a literal; a
    reference is 12 bits of window position then 4 of length - 3; a 4 KiB
    window, zeroed, written from 0xFEE."""
    ring, r, out, i, flags, n = bytearray(4096), 0xFEE, bytearray(), 0, 0, 0
    while len(out) < size:
        if n == 0:
            flags, i, n = src[i], i + 1, 8
        bit, flags, n = flags & 1, flags >> 1, n - 1
        if bit:
            pos, ln = None, 1
        else:
            pos, ln = src[i] << 4 | src[i + 1] >> 4, (src[i + 1] & 15) + 3
            i += 2
        for k in range(ln):  # byte by byte: a reference can overlap what it writes
            if pos is None:
                c = src[i]
                i += 1
            else:
                c = ring[(pos + k) & 4095]
            out.append(c)
            ring[r] = c
            r = (r + 1) & 4095
    return bytes(out[:size])


def mbin(d):
    assert d[:4] == b'MBIN' and struct.unpack_from('<I', d, 4)[0] == 4
    sizes = struct.unpack_from('<4I', d, 0x20)
    offs = list(struct.unpack_from('<4I', d, 0x30)) + [len(d)]
    assert sizes == (512, 512, 512, 32)
    return [lzss(d[offs[k]:offs[k + 1]], sizes[k]) for k in range(4)]


def argb4444(c):
    c = c.lstrip('#')
    r, g, bl, a = (int(c[i:i + 2], 16) >> 4 for i in (0, 2, 4, 6))
    return (a << 12 | r << 8 | g << 4 | bl).to_bytes(2, 'little')


def main(src, out):
    src, out = Path(src), Path(out)
    b = (src / '1ST_READ.BIN').read_bytes()
    for sub in ('screens', 'saves'):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir(parents=True)

    ptrs = struct.unpack(f'<{COUNT}I', at(b, TABLE, 4 * COUNT))
    assert all(p == ptrs[0] + n * SIZE for n, p in enumerate(ptrs)) and ptrs[-1] + SIZE == TABLE
    manifest, images = [], []
    for n, p in enumerate(ptrs):
        raw = at(b, p, SIZE)
        im = Image.new('1', (W, H), 1)
        im.putdata([0 if raw[(y * W + x) // 8] >> (7 - x % 8) & 1 else 1 for y in range(H) for x in range(W)])
        im.save(out / 'screens' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', entry=n, address=f'{p:#x}', blank=not any(raw)))
        images.append(im)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    have = json.loads(SAVE_ICON.read_text())
    have_frames = b''.join(bytes.fromhex(f) for f in have['frames'])
    have_palette = b''.join(argb4444(c) for c in have['palette'])
    titles = {}
    for who in ICONS:
        *frames, palette = mbin((src / 'CCT' / f'VM_ICON_{who}.HBN').read_bytes())
        same = b''.join(frames) == have_frames and palette == have_palette
        print(who, 'is the archived save icon' if same else 'differs from the archived save icon')
        if same:
            continue
        hdr = bytearray(0x80)
        hdr[0:16] = have['vmuName'].encode('shift_jis').ljust(16, b' ')[:16]
        hdr[0x10:0x30] = have['description'].encode('shift_jis').ljust(32, b' ')[:32]
        struct.pack_into('<HH', hdr, 0x40, len(frames), SPEED)
        hdr[0x60:0x80] = palette
        (out / 'saves' / f'{who}.VMS').write_bytes(bytes(hdr) + b''.join(frames))
        titles[f'{who}.VMS'] = f'System file ({who.lower()})'
    (out / 'saves' / 'save-icons.json').write_text(json.dumps(dict(
        game='Cool Cool Toon', publisher='SNK', year=2000, region='ntsc-j', disc='/CCT/VM_ICON_*.HBN',
        titles=titles), ensure_ascii=False, indent=1))

    scale = 3
    cw = W * scale + 16
    sheet = Image.new('RGB', (16 + COUNT * cw, 44 + H * scale + 30), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'Cool Cool Toon: 1ST_READ.BIN @ {ptrs[0]:#x}', fill='black')
    for n, im in enumerate(images):
        x = 16 + n * cw
        draw.text((x, 44), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')
    print(COUNT, 'screens,', len(titles), 'new save icons ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
