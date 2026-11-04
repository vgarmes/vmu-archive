"""Decode Jet Set Radio's VMU screens from /1ST_READ.BIN.

    python3 vmu.py <1ST_READ.BIN> <out dir>

JP release. 1ST_READ.BIN loads at 0x8C010000.

Twelve screens sit back to back at 0x8C1C0330, each 192 bytes packed 1 bit per
pixel, high bit first, 1 = lit, turned 180° (the way the VMU's LCD takes it).
Right after them come the tables the code reads them through:

    0x8C1C0C30  screens by number: 0x8C0AA990 shows entry n (n = 0-4 is
                called: logo, OK, NG, Now Saving, Now Loading)
    0x8C1C0C80  animations: 0x8C0AA9D4 plays a null-terminated list of
                screens, one step every r5 ticks. Only list 0 (the radio,
                0x8C1C0C4C) is played, by 0x8C017E72 with r5 = 6.

Writes lcd/NN.png (dark = lit, upright, as `pnpm icons:import` reads it),
manifest.json, animations.json and contact-sheet.png.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SCREENS, COUNT, SIZE = 0x8C1C0330, 12, 192
SHOW_TABLE, SHOWN = 0x8C1C0C30, 5
ANIM_TABLE = 0x8C1C0C80
WHAT = ['Logo'] + [f'Radio, pose {k}' for k in range(1, 8)] + ['Now Saving', 'Now Loading', 'OK', 'NG']
# 0x8C0AA85C (state 3) steps when the task's counter mod the period is 0, and
# 0x8C017E72 asks for a period of 6: 100 ms a step if the task runs every
# frame at 60 Hz. Assumed, not measured.
RADIO_PERIOD = 6
TICK_MS = 1000 / 60


def u32(b, addr):
    return struct.unpack_from('<I', b, addr - LOAD)[0]


def screen_number(ptr):
    n, r = divmod(ptr - SCREENS, SIZE)
    if r or not 0 <= n < COUNT:
        sys.exit(f'{ptr:#x} is not one of the screens')
    return n


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for n in range(COUNT):
        off = SCREENS - LOAD + n * SIZE
        raw = b[off:off + SIZE]
        # Turn 180°: reverse the byte order, then the bits in each byte.
        upright = bytes(int(f'{x:08b}'[::-1], 2) for x in raw[::-1])
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if c == '1' else 1 for c in ''.join(f'{x:08b}' for x in upright)])
        im.save(out / 'lcd' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', what=WHAT[n], address=f'{SCREENS + n * SIZE:#x}',
                             offset=off, frame_hex=upright.hex()))
        images.append(im)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    shown = [screen_number(u32(b, SHOW_TABLE + 4 * k)) for k in range(SHOWN)]
    radio, ptr = [], u32(b, ANIM_TABLE)
    while u32(b, ptr):
        radio.append(screen_number(u32(b, ptr)))
        ptr += 4
    animations = [dict(name=WHAT[n].lower().replace(' ', '-'), screens=[n]) for n in shown]
    animations.append(dict(name='radio', screens=radio, delay_ms=round(RADIO_PERIOD * TICK_MS)))
    (out / 'animations.json').write_text(json.dumps(dict(animations=animations), indent=1))
    for a in animations:
        print(a['name'], a['screens'])

    scale = 3
    cw, ch = 48 * scale + 16, 32 * scale + 30
    cols = 6
    sheet = Image.new('RGB', (16 + cols * cw, 44 + 2 * ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'1ST_READ.BIN: {COUNT} screens at {SCREENS:#x}', fill='black')
    for n, im in enumerate(images):
        x, y = 16 + (n % cols) * cw, 44 + (n // cols) * ch
        draw.text((x, y), f'#{n:02d} {WHAT[n]}', fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')
    print(COUNT, 'screens ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
