"""Decode Ikaruga's VMU screens and chain digits from /1ST_READ.BIN.

    python3 vmu.py <1ST_READ.BIN> <out dir>

JP v1.002. 1ST_READ.BIN loads at 0x8C010000. Every piece is packed 1 bit per
pixel, high bit first, 1 = lit, stored upright: the archive's own encoding.

0x8C06D0D0 steps one VMU (0 or 1, one per controller) through a state machine;
its state byte is at 0x8C1CB8C0 + VMU and its jump table at 0x8C06D120. Every
state that draws copies a 48x32 screen into the VMU's buffer (0x8C06CE88, which
turns it 180 degrees when 0x8C04AEA4 says the VMU is upside down), then hands
over to state 9, which sends it (pdLcd's write, 0x8C04B026, called nowhere else)
and waits until the send is done:

    1  title           0x8C0CFD30
    2  chain counter   0x8C06CF58: background 0x8C0D03B0, then digits
    3  SAVE, frame f   0x8C0CFDF0 + 192 * f, f = byte at 0x8C1CB8C8 + VMU
    4  count to 15, then f ^= 1 and back to 3: SAVE alternates its two frames
    5  LOAD            0x8C0CFF70, always
    6  count to 15, then f ^= 1 and back to 5, but 5 never reads f
    7  OK              0x8C0D00F0
    8  NG              0x8C0D01B0

So the second LOAD screen, 0x8C0D0030 (the bird in another pose), is never drawn.

The chain counter writes the value at 0x8C1D13E8 + 60 + 2 * VMU as up to three
16x16 digits over the top half of the background, right-aligned at x = 0, 16
and 32 with leading zeros left blank. The digits are 0-9 at 0x8C0D0270, 32 bytes
each, 2 bytes per row.

Writes lcd/NN.png (dark = lit, as `pnpm icons:import` reads it), digits.png (the
ten digits as stored, one under the next, 16x160), manifest.json and
contact-sheet.png.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SIZE = 192
# (address, what, state that draws it, drawn?)
SCREENS = [
    (0x8C0CFD30, 'Title logo', 1, True),
    (0x8C0CFDF0, 'SAVE, frame 0', 3, True),
    (0x8C0CFEB0, 'SAVE, frame 1', 3, True),
    (0x8C0CFF70, 'LOAD', 5, True),
    (0x8C0D0030, 'LOAD, second pose', None, False),
    (0x8C0D00F0, 'OK', 7, True),
    (0x8C0D01B0, 'NG', 8, True),
    (0x8C0D03B0, 'CHAIN, under the digits', 2, True),
]
DIGITS, DIGIT_W, DIGIT_H = 0x8C0D0270, 16, 16
DIGIT_X = (0, 16, 32)


def bitmap(data, w, h):
    im = Image.new('1', (w, h), 1)
    im.putdata([0 if (data[i // 8] >> (7 - i % 8)) & 1 else 1 for i in range(w * h)])
    return im


def chain(b, value):
    """The chain screen as the game draws it for `value` (0-999)."""
    im = bitmap(b[0x8C0D03B0 - LOAD:][:SIZE], 48, 32)
    text = str(value)
    for k, ch in enumerate(text.rjust(3)):
        if ch != ' ':
            off = DIGITS - LOAD + 32 * int(ch)
            im.paste(bitmap(b[off:off + 32], DIGIT_W, DIGIT_H), (DIGIT_X[k], 0))
    return im


def main(src, out):
    b = Path(src).read_bytes()
    out = Path(out)
    (out / 'lcd').mkdir(parents=True, exist_ok=True)
    manifest, images = [], []
    for n, (addr, what, state, drawn) in enumerate(SCREENS):
        blk = b[addr - LOAD:addr - LOAD + SIZE]
        im = bitmap(blk, 48, 32)
        im.save(out / 'lcd' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', kind='screen', what=what, state=state, drawn=drawn,
                             address=f'{addr:#x}', offset=addr - LOAD, frame_hex=blk.hex()))
        images.append((f'#{n:02d}', im))
        print(n, f'{addr:#x}', what, '' if drawn else '(never drawn)')

    # The digits as stored: 0 to 9 one under the next, 2 bytes a row, so the
    # sprite is the 320 bytes at DIGITS as they are.
    off = DIGITS - LOAD
    bitmap(b[off:off + 32 * 10], DIGIT_W, 10 * DIGIT_H).save(out / 'digits.png')
    manifest.append(dict(name='digits', kind='sprite', what='Chain digits 0-9', width=DIGIT_W,
                         height=10 * DIGIT_H, address=f'{DIGITS:#x}', offset=off))
    # Side by side, for the contact sheet only.
    digits = Image.new('1', (10 * DIGIT_W, DIGIT_H), 1)
    for d in range(10):
        digits.paste(bitmap(b[off + 32 * d:off + 32 * (d + 1)], DIGIT_W, DIGIT_H), (d * DIGIT_W, 0))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))

    images += [('chain 7', chain(b, 7)), ('chain 42', chain(b, 42)), ('chain 123', chain(b, 123))]
    scale, per = 3, 6
    cw, ch = 48 * scale + 16, 32 * scale + 30
    rows = (len(images) + per - 1) // per
    sheet = Image.new('RGB', (16 + per * cw, 44 + rows * ch + DIGIT_H * scale + 40), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'1ST_READ.BIN, drawn by 0x8C06D0D0: {len(SCREENS)} screens, then examples of the chain counter',
              fill='black')
    for k, (label, im) in enumerate(images):
        x, y = 16 + (k % per) * cw, 44 + (k // per) * ch
        draw.text((x, y), label, fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, y + 14))
    y = 44 + rows * ch
    draw.text((16, y), f'digits @ {DIGITS:#x}', fill='black')
    sheet.paste(digits.convert('RGB').resize((digits.width * scale, DIGIT_H * scale), Image.NEAREST), (16, y + 14))
    sheet.save(out / 'contact-sheet.png')
    print(len(SCREENS), 'screens and 10 digits ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
