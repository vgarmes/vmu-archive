"""Pull Space Channel 5 Part 2's VMU screens out of its program, and check its
save icon against the archive's.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes screens/NN.png (dark = lit, as `pnpm icons:import` reads it),
manifest.json and contact-sheet.png.

Redump `Space Channel 5 Part 2 (Japan)`; 1ST_READ.BIN loads at 0x8C010000.
See content/games/space-channel-5-part-2.md.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H, SIZE = 48, 32, 192
REPO = Path(__file__).resolve().parents[3]

# The game's VMU manager (its one object at 0x8C240414) takes a screen number
# (0x8C0E6730) and looks it up at TABLE; 0, or none, is the first. Each frame
# it sends the screen with pdLcd's write for packed screens (0x8C0167DA):
# 1 bit a dot, turned 180 degrees as the LCD takes it.
TABLE, COUNT = 0x8C133D20, 3
USES = {0: 'resting screen: set(0) and the default',
        1: 'set(1) at 0x8C0D1FDE', 2: 'set(2) at 0x8C0D245E'}

# The save header, prebuilt at 0x8C12C190 (used at 0x8C0D254A): palette and
# frames, 2 frames at speed 10.
SAVE_PALETTE, SAVE_FRAMES, SAVE_COUNT, SAVE_SPEED = 0x8C12BCF8, 0x8C12BD18, 2, 10
SAVE_HEADER = 0x8C12C190
SAVE_ICON = REPO / 'content/save-icons/space-channel-5-part-2/save-file.json'


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def argb4444(c):
    c = c.lstrip('#')
    r, g, bl, a = (int(c[i:i + 2], 16) >> 4 for i in (0, 2, 4, 6))
    return (a << 12 | r << 8 | g << 4 | bl).to_bytes(2, 'little')


def check_save(b):
    icon = json.loads(SAVE_ICON.read_text())
    frames = b''.join(bytes.fromhex(f) for f in icon['frames'])
    palette = b''.join(argb4444(c) for c in icon['palette'])
    pal, frm, count_speed = struct.unpack('<III', at(b, SAVE_HEADER + 12, 12))
    ok = (pal == SAVE_PALETTE and frm == SAVE_FRAMES and count_speed == SAVE_SPEED << 16 | SAVE_COUNT
          and at(b, SAVE_PALETTE, 32) == palette and at(b, SAVE_FRAMES, 512 * SAVE_COUNT) == frames
          and len(icon['frames']) == SAVE_COUNT and icon['animationSpeed'] == SAVE_SPEED)
    print('save icon', 'matches the program' if ok else 'DIFFERS from the program')
    return ok


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'screens').mkdir(parents=True, exist_ok=True)
    ptrs = struct.unpack(f'<{COUNT}I', at(b, TABLE, 4 * COUNT))
    assert all(p == ptrs[0] + n * SIZE for n, p in enumerate(ptrs)) and ptrs[-1] + SIZE == TABLE
    manifest, images = [], []
    for n, p in enumerate(ptrs):
        bits = ''.join(f'{x:08b}' for x in at(b, p, SIZE))[::-1]  # 180 degree turn
        im = Image.new('1', (W, H), 1)
        im.putdata([0 if c == '1' else 1 for c in bits])
        im.save(out / 'screens' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', entry=n, address=f'{p:#x}', use=USES[n]))
        images.append(im)
        print(n, f'{p:#x}', USES[n])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    check_save(b)

    scale = 3
    cw = W * scale + 16
    sheet = Image.new('RGB', (16 + COUNT * cw, 44 + H * scale + 30), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'Space Channel 5 Part 2: 1ST_READ.BIN @ {TABLE:#x}', fill='black')
    for n, im in enumerate(images):
        x = 16 + n * cw
        draw.text((x, 44), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')
    print(COUNT, 'screens ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
