"""Pull Space Channel 5's VMU screens out of its program, and check its save
icon against the archive's.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes screens/NN.png (dark = lit, as `pnpm icons:import` reads it),
manifest.json (each table entry, its rectangle and where it's used) and
contact-sheet.png.

Redump `Space Channel 5 (Japan)`; 1ST_READ.BIN loads at 0x8C010000. See
content/games/space-channel-5.md.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
W, H = 48, 32
REPO = Path(__file__).resolve().parents[3]

# The game's copy of Sega's vmslcd.c keeps 15 images, listed at TABLE as
# (rectangle, bitmap) pairs. A rectangle is four s32 (x, y, w, h); its bitmap
# follows it, 1 bit a dot, high bit leftmost, rows of w dots. The blitters
# (0x8C030530, 0x8C03065A) copy it to that place on a blank 48x32 screen.
TABLE, COUNT = 0x8C03C090, 15
IMAGES = (0x8C03B4A8, 0x8C03C090)  # where the images sit, back to back

# How each entry is shown:
# - 0 is drawn by the LCD setup (0x8C0304CC) into the screen the sender
#   (0x8C0307FE) falls back to when nothing else is set: the resting screen.
# - 1 to 3 through show(n) (0x8C030942): 1 at 0x8C010940, 2 at 0x8C010A74 (the
#   save code), 3 at 0x8C02D9F8 (the routine that loads roll.pvm, the staff
#   roll). show(0) goes back to entry 0.
# - 4 to 14 through 0x8C030928, portrait k = entry 4 + k, for the character
#   number a scene object holds (0x8C021E74; mode 2 shows k 0).
USES = {0: 'resting screen (0x8C0304CC)', 1: 'show(1) at 0x8C010940',
        2: 'show(2) at 0x8C010A74, saving', 3: 'show(3) at 0x8C02D9F8, staff roll',
        **{e: f'portrait {e - 4} (0x8C030928)' for e in range(4, 15)}}

# The save header (around 0x8C010786): palette and frames, 3 frames at speed 4.
SAVE_PALETTE, SAVE_FRAMES, SAVE_COUNT, SAVE_SPEED = 0x8C03ADD8, 0x8C03ADF8, 3, 4
SAVE_ICON = REPO / 'content/save-icons/space-channel-5/save-file.json'


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
    ok = (at(b, SAVE_PALETTE, 32) == palette and at(b, SAVE_FRAMES, 512 * SAVE_COUNT) == frames
          and len(icon['frames']) == SAVE_COUNT and icon['animationSpeed'] == SAVE_SPEED)
    print('save icon', 'matches the program' if ok else 'DIFFERS from the program')
    return ok


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'screens').mkdir(parents=True, exist_ok=True)

    entries = [struct.unpack('<II', at(b, TABLE + 8 * i, 8)) for i in range(COUNT)]
    # Every image between IMAGES[0] and the table is in it, once.
    a, walked = IMAGES[0], []
    while a < IMAGES[1]:
        x, y, w, h = struct.unpack('<4i', at(b, a, 16))
        walked.append(a)
        a += 16 + w * h // 8
    assert a == IMAGES[1] and sorted(walked) == sorted(r for r, _ in entries)

    manifest, images = [], []
    for n, (rect, bits) in enumerate(entries):
        x, y, w, h = struct.unpack('<4i', at(b, rect, 16))
        assert bits == rect + 16 and w % 8 == 0 and x + w <= W and y + h <= H
        raw = at(b, bits, w * h // 8)
        im = Image.new('1', (W, H), 1)
        for yy in range(h):
            for xx in range(w):
                if raw[(yy * w + xx) // 8] >> (7 - xx % 8) & 1:
                    im.putpixel((x + xx, y + yy), 0)
        im.save(out / 'screens' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', entry=n, address=f'{rect:#x}', rect=[x, y, w, h], use=USES[n]))
        images.append(im)
        print(n, f'{rect:#x}', (x, y, w, h), USES[n])
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    check_save(b)

    scale, cols = 3, 8
    cw, ch = W * scale + 16, H * scale + 30
    rows = (COUNT + cols - 1) // cols
    sheet = Image.new('RGB', (16 + cols * cw, 44 + rows * ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'Space Channel 5: 1ST_READ.BIN @ {TABLE:#x}', fill='black')
    for n, im in enumerate(images):
        x, y = 16 + n % cols * cw, 44 + n // cols * ch
        draw.text((x, y), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((W * scale, H * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')
    print(COUNT, 'screens ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
