"""Pull Capcom vs. SNK: Millennium Fight 2000's VMU screens out of its program.

    python3 vmu.py <1ST_READ.BIN> <out dir>

Writes:
- inbox/*.png and their sidecars, for `pnpm icons:import` (dark = lit);
- buffer.png, what the screen buffer holds on the disc (not imported);
- contact-sheet.png.

Addresses are for the JP Rev A release (Redump `Capcom vs. SNK - Millennium
Fight 2000 (Japan) (Rev A)`); 1ST_READ.BIN loads at 0x8C010000. See
content/games/capcom-vs-snk-millennium-fight-2000.md.
"""
import json
import shutil
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C010000
SIZE = 192  # 48x32 at 1 bit a dot

# Every caller loads a screen's address into r4 and calls 0x8C067018, which
# spreads its bits, high bit first, into a byte buffer at 0x8C1B9A8C (8 for a
# 1 bit, 0 for a 0 bit); 0x8C06705E then hands the buffer to the library's LCD
# write (0x8C1FD888) for one VMU. It's Marvel vs. Capcom 2's code: nothing
# inverts or mirrors, so a 1 bit is a lit dot and the screens show as stored.
SCREENS = [
    dict(address=0x8C1B990C, name='title', title='Title screen', tags=['logo']),
    dict(address=0x8C1B99CC, name='access', title='Access', tags=['memory-card']),
]
BUFFER = 0x8C1B9A8C
# Neither screen has Japanese text (the logo, and ACCESS in English), so no
# region.
BASE = dict(game='capcom-vs-snk-millennium-fight-2000', publisher='Capcom', year=2000)


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


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
    inbox = out / 'inbox'
    shutil.rmtree(inbox, ignore_errors=True)
    inbox.mkdir(parents=True)

    # The logo is loaded from six places and ACCESS from three, all in the
    # memory card code, each passing it straight to the copy routine.
    images = []
    for s in SCREENS:
        blk = at(b, s['address'], SIZE)
        im = screen_image(blk)
        stem = f'cvs-{s["name"]}'
        im.save(inbox / f'{stem}.png')
        meta = dict(title=s['title'], tags=s['tags'], **BASE)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        refs = literals(b, s['address'])
        images.append((s['title'], im))
        print(f'{s["title"]:13} {s["address"]:#x}  loaded from {len(refs)} literal(s)')

    # The buffer isn't empty on the disc: it holds the bottom of a screen as
    # bytes (8 = lit), the letters "VS4", as Marvel vs. Capcom 2's buffer does.
    # The game fills it before every send, so it's never shown.
    buf = at(b, BUFFER, 48 * 32)
    assert set(buf) <= {0, 8}
    leftover = bytes(int(''.join('1' if buf[r * 48 + c * 8 + k] else '0' for k in range(8)), 2)
                     for r in range(32) for c in range(6))
    im = screen_image(leftover)
    im.save(out / 'buffer.png')
    images.append(('buffer on disc', im))

    scale = 3
    cw = 48 * scale + 16
    sheet = Image.new('RGB', (16 + len(images) * cw, 44 + 32 * scale + 30), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), 'Capcom vs. SNK: 1ST_READ.BIN', fill='black')
    for k, (what, im) in enumerate(images):
        x = 16 + k * cw
        draw.text((x, 44), what, fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, 58))
    sheet.save(out / 'contact-sheet.png')
    print(len(SCREENS), 'screens ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
