"""Check Record of Lodoss War's VMU use against its program.

    python3 check.py <1NOSDC.BIN>

The game draws nothing on the VMU: this prints the evidence (who sends to the
LCD, and that the data pointer is never set) and checks the archive's save
icon against the program's. Addresses are for the Japanese Rev A release;
1NOSDC.BIN, its boot file, loads at 0x8C010000. See this folder's README.
"""
import json
import struct
import sys
from pathlib import Path

LOAD = 0x8C010000
REPO = Path(__file__).resolve().parents[3]

LCD_WRITE = 0x8C2AAF04  # pdLcd's write
WRAPPER = 0x8C013E80  # the game's send: blank screen when its data is NULL
SETTER = 0x8C013C6E  # stores a screen pointer for the send loop (0x8C014004)
SAVE_FRAME, SAVE_PALETTE = 0x8C1426B8, 0x8C1428B8


def literals(b, value):
    want = struct.pack('<I', value)
    out, i = [], b.find(want)
    while i >= 0:
        if i % 4 == 0:
            out.append(LOAD + i)
        i = b.find(want, i + 1)
    return out


def bsr_callers(b, target, span=0x8000):
    out = []
    for a in range(max(LOAD, target - span), min(LOAD + len(b) - 2, target + span), 2):
        w = struct.unpack_from('<H', b, a - LOAD)[0]
        if w >> 12 == 0xB:
            d = w & 0xFFF
            d = d - 0x1000 if d & 0x800 else d
            if a + 4 + 2 * d == target:
                out.append(a)
    return out


def argb4444(c):
    c = c.lstrip('#')
    r, g, bl, a = (int(c[i:i + 2], 16) >> 4 for i in (0, 2, 4, 6))
    return (a << 12 | r << 8 | g << 4 | bl).to_bytes(2, 'little')


def main(src):
    b = Path(src).read_bytes()
    print('pdLcd write loaded from', [hex(a) for a in literals(b, LCD_WRITE)])
    print('send wrapper called from', [hex(a) for a in bsr_callers(b, WRAPPER)])
    refs = literals(b, SETTER) + bsr_callers(b, SETTER)
    print('screen setter referenced from', [hex(a) for a in refs] or 'nowhere')

    icon = json.loads((REPO / 'content/save-icons/record-of-lodoss-war/save-file.json').read_text())
    frame = bytes.fromhex(icon['frames'][0])
    palette = b''.join(argb4444(c) for c in icon['palette'])
    at = lambda addr, n: b[addr - LOAD:addr - LOAD + n]
    ok = at(SAVE_FRAME, 512) == frame and at(SAVE_PALETTE, 32) == palette
    print('save icon', 'matches the program' if ok else 'DIFFERS from the program')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(*sys.argv[1:])
