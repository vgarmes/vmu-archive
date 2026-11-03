"""Find the game code that drives the VMU screen, starting from what a capture shows.

    python3 find_code.py <1ST_READ.BIN> seq <n> <n> …    where are these screen numbers loaded close together?
    python3 find_code.py <1ST_READ.BIN> refs <address>   who calls (or loads the address of) this routine?

`seq` looks for SH-4 `mov #n,Rx` instructions for every number in a known frame
sequence (e.g. the screen indices of a captured animation) within 64 bytes of each
other. A game usually draws each frame with a literal screen number, so the one or
two hits are the animation code. `refs` lists the literal-pool entries holding an
address and the instructions that load them, plus direct bsr/bra branches to it.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sh4 import LOAD, dis  # noqa: E402

WINDOW = 64


def mov_immediates(b):
    found = {}
    for off in range(0, len(b) - 1, 2):
        if b[off + 1] & 0xF0 == 0xE0:  # mov #imm8,Rn is 0xEnii, stored little-endian
            found.setdefault(b[off], []).append(off)
    return found


def seq(b, numbers):
    movs = mov_immediates(b)
    for off in movs.get(numbers[0], []):
        if all(any(abs(o - off) <= WINDOW for o in movs.get(v, [])) for v in numbers[1:]):
            print(f'{LOAD + off:08x}  {dis(b, off)}')


def refs(b, target):
    pools = {off for off in range(0, len(b) - 3, 4) if struct.unpack_from('<I', b, off)[0] == target}
    for off in sorted(pools):
        print(f'{LOAD + off:08x}  literal {target:#x}')
    for off in range(0, len(b) - 1, 2):
        w = struct.unpack_from('<H', b, off)[0]
        top = w >> 12
        if top == 0xD and ((LOAD + off + 4) & ~3) + (w & 0xFF) * 4 - LOAD in pools:
            print(f'{LOAD + off:08x}  {dis(b, off)}')
        elif top in (0xA, 0xB):
            d = w & 0xFFF
            if LOAD + off + 4 + (d - 4096 if d & 0x800 else d) * 2 == target:
                print(f'{LOAD + off:08x}  {dis(b, off)}')


if __name__ == '__main__':
    if len(sys.argv) < 4 or sys.argv[2] not in ('seq', 'refs'):
        sys.exit(__doc__)
    data = Path(sys.argv[1]).read_bytes()
    if sys.argv[2] == 'seq':
        seq(data, [int(v) for v in sys.argv[3:]])
    else:
        refs(data, int(sys.argv[3], 16))
