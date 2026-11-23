"""Pull Rainbow Cotton's VMU screens and animations out of its program, and check
its save icon against the archive's.

    python3 vmu.py <folder with TITLE.BIN, GAME.BIN, BO01.BIN, LAST.BIN> <out dir>

Writes screens/NN.png (dark = lit, as `pnpm icons:import` reads it),
manifest.json (every screen and its frame in the archive's hex encoding),
animations.json and contact-sheet.png.

Redump `Rainbow Cotton (Japan)`. The small 1ST_READ.BIN loads the game's
overlays, which all run from 0x8C200000: TITLE.BIN (title and menus), and
GAME.BIN, BO01.BIN and LAST.BIN (the stages). Each links Sega's pdLcd and
carries its own copy of the VMU code and art, at its own addresses. See
content/games/rainbow-cotton.md.
"""
import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

LOAD = 0x8C200000
SCREENS, SIZE = 16, 192  # 48x32, 1 bit a dot, high bit leftmost, 1 lit
ANIMS = 11
HZ = 60
REPO = Path(__file__).resolve().parents[3]

# Per overlay: the screens, the animation table (11 pointers) and the player
# that steps it once a game loop (all for the record; the bytes are checked
# to be the same in every overlay).
OVERLAYS = {
    'TITLE.BIN': dict(screens=0x8C2122E4, table=0x8C2130B4, player=0x8C20B1D0, start=0x8C20B250),
    'GAME.BIN': dict(screens=0x8C2C95B8, table=0x8C2CA388, player=0x8C218DE0, start=0x8C218E60),
    'BO01.BIN': dict(screens=0x8C2CA998, table=None, player=0x8C218DE0, start=0x8C218E60),
    'LAST.BIN': dict(screens=0x8C2C8F64, table=0x8C2C9D34, player=0x8C217220, start=0x8C2172A0),
}
# What each overlay passes to its start routine (r4), read at each call.
STARTED = {
    'TITLE.BIN': {0},
    'GAME.BIN': set(range(1, 11)),
    'BO01.BIN': set(range(1, 11)),
    'LAST.BIN': set(range(1, 11)),
}
END_LOOP, END_NEXT = -2, -1  # back to the first step; on to the queued animation

# The save header (0x8C20B4F0 in TITLE.BIN): palette and frames, 2 frames at
# speed 10, named from 0x8C20CB24 and 0x8C20CB34.
SAVE_PALETTE, SAVE_FRAMES, SAVE_COUNT, SAVE_SPEED = 0x8C213CF0, 0x8C213D10, 2, 10
SAVE_NAMES = 0x8C20CB24
SAVE_ICON = REPO / 'content/save-icons/rainbow-cotton/save-file.json'


def at(b, addr, n):
    return b[addr - LOAD:addr - LOAD + n]


def animations(b, table, bank):
    out = []
    for p in struct.unpack('<11I', at(b, table, 4 * ANIMS)):
        steps = []
        while True:
            scr, ticks = struct.unpack('<Ii', at(b, p, 8))
            p += 8
            if ticks < 0:
                break
            assert (scr - bank) % SIZE == 0
            steps.append(((scr - bank) // SIZE, ticks))
        out.append(dict(screens=[s for s, _ in steps], ticks=[t for _, t in steps],
                        delays_ms=[round(t * 1000 / HZ) for _, t in steps],
                        loop=ticks == END_LOOP))
    return out


def argb4444(c):
    c = c.lstrip('#')
    r, g, bl, a = (int(c[i:i + 2], 16) >> 4 for i in (0, 2, 4, 6))
    return (a << 12 | r << 8 | g << 4 | bl).to_bytes(2, 'little')


def check_save(b):
    icon = json.loads(SAVE_ICON.read_text())
    frames = b''.join(bytes.fromhex(f) for f in icon['frames'])
    palette = b''.join(argb4444(c) for c in icon['palette'])
    ok = (at(b, SAVE_PALETTE, 32) == palette and at(b, SAVE_FRAMES, 512 * SAVE_COUNT) == frames
          and len(icon['frames']) == SAVE_COUNT and icon['animationSpeed'] == SAVE_SPEED
          and at(b, SAVE_NAMES, 16).split(b'\0')[0].decode() == icon['vmuName'])
    print('save icon', 'matches the program' if ok else 'DIFFERS from the program')
    return ok


def main(src, out):
    src, out = Path(src), Path(out)
    (out / 'screens').mkdir(parents=True, exist_ok=True)
    files = {name: (src / name).read_bytes() for name in OVERLAYS}

    bank = None
    for name, o in OVERLAYS.items():
        blk = at(files[name], o['screens'], SCREENS * SIZE)
        assert bank is None or blk == bank, f'{name} has other screens'
        bank = blk
    anims = None
    for name, o in OVERLAYS.items():
        if o['table']:
            a = animations(files[name], o['table'], o['screens'])
            assert anims is None or a == anims, f'{name} has other animations'
            anims = a
    for k, a in enumerate(anims):
        a.update(number=k, startedIn=[n for n, s in STARTED.items() if k in s])
        print(k, a['screens'], a['ticks'], 'loops' if a['loop'] else 'then the queued one', a['startedIn'])
    assert {s for a in anims for s in a['screens']} == set(range(SCREENS)), 'every screen is played'
    assert all(a['startedIn'] for a in anims), 'every animation is started'

    manifest, images = [], []
    for n in range(SCREENS):
        raw = bank[n * SIZE:(n + 1) * SIZE]
        im = Image.new('1', (48, 32), 1)
        im.putdata([0 if raw[(y * 48 + x) // 8] >> (7 - x % 8) & 1 else 1 for y in range(32) for x in range(48)])
        im.save(out / 'screens' / f'{n:02d}.png')
        manifest.append(dict(name=f'{n:02d}', address=f'{OVERLAYS["TITLE.BIN"]["screens"] + n * SIZE:#x}',
                             frame_hex=raw.hex()))
        images.append(im)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    (out / 'animations.json').write_text(json.dumps(dict(animations=anims), indent=1))
    check_save(files['TITLE.BIN'])

    scale, cols = 3, 8
    cw, ch = 48 * scale + 16, 32 * scale + 30
    rows = (SCREENS + cols - 1) // cols
    sheet = Image.new('RGB', (16 + cols * cw, 44 + rows * ch), '#f5f2e9')
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 14), f'Rainbow Cotton: TITLE.BIN @ {OVERLAYS["TITLE.BIN"]["screens"]:#x}', fill='black')
    for n, im in enumerate(images):
        x, y = 16 + n % cols * cw, 44 + n // cols * ch
        draw.text((x, y), f'#{n:02d}', fill='black')
        sheet.paste(im.convert('RGB').resize((48 * scale, 32 * scale), Image.NEAREST), (x, y + 14))
    sheet.save(out / 'contact-sheet.png')
    print(SCREENS, 'screens,', len(anims), 'animations ->', out)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
