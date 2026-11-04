"""A small disassembler for the VMU's CPU (Sanyo LC86K), for VMU programs a game
carries (a .VMS image, or one embedded in another file).

    python3 lc86k.py <program> <start> [count]     disassemble from a hex address
    python3 lc86k.py <program> refs <address>      instructions that load an address
                                                   into TRH/TRL (what LDC reads)

Addresses are offsets into the program, which runs from 0 in flash. A program
reads its art with LDC (TRH:TRL + ACC), so an image's address shows up as
`mov #hi,trh` / `mov #lo,trl` near the code that draws it.
"""
import sys
from pathlib import Path

SFR = {
    0x100: 'acc', 0x101: 'psw', 0x102: 'b', 0x103: 'c', 0x104: 'trl', 0x105: 'trh',
    0x106: 'sp', 0x107: 'pcon', 0x108: 'ie', 0x109: 'ip', 0x10d: 'ext', 0x10e: 'ocr',
    0x110: 't0con', 0x111: 't0prr', 0x112: 't0l', 0x113: 't0lr', 0x114: 't0h', 0x115: 't0hr',
    0x118: 't1cnt', 0x11a: 't1lc', 0x11b: 't1l', 0x11c: 't1hc', 0x11d: 't1h',
    0x120: 'mcr', 0x122: 'stad', 0x123: 'cnr', 0x124: 'tdr', 0x125: 'xbnk',
    0x127: 'vccr', 0x130: 'scon0', 0x131: 'sbuf0', 0x132: 'sbr', 0x134: 'scon1',
    0x135: 'sbuf1', 0x144: 'p1', 0x145: 'p1ddr', 0x146: 'p1fcr', 0x14c: 'p3',
    0x14d: 'p3ddr', 0x14e: 'p3int', 0x15c: 'p7', 0x15d: 'i01cr', 0x15e: 'i23cr',
    0x15f: 'isl', 0x163: 'vsel', 0x164: 'vrmad1', 0x165: 'vrmad2', 0x166: 'vtrbf',
    0x167: 'vlreg', 0x17f: 'btcr', 0x000: 'r0', 0x001: 'r1', 0x002: 'r2', 0x003: 'r3',
}
ALU = {0x8: 'add', 0x9: 'addc', 0xA: 'sub', 0xB: 'subc', 0xD: 'or', 0xE: 'and', 0xF: 'xor'}
LOADSTORE = {0x0: 'ld', 0x1: 'st', 0x6: 'inc', 0x7: 'dec', 0xC: 'xch'}
BIT = {0x4: 'bpc', 0x5: 'bpc', 0x6: 'bp', 0x7: 'bp', 0x8: 'bn', 0x9: 'bn',
       0xA: 'not1', 0xB: 'not1', 0xC: 'clr1', 0xD: 'clr1', 0xE: 'set1', 0xF: 'set1'}
SINGLE = {0x00: 'nop', 0x30: 'mul', 0x40: 'div', 0x50: 'ldf', 0x51: 'stf', 0xA0: 'ret',
          0xB0: 'reti', 0xC0: 'ror', 0xC1: 'ldc', 0xD0: 'rorc', 0xE0: 'rol', 0xF0: 'rolc', 0xFF: 'set1?'}


def d9name(a):
    if a in SFR:
        return SFR[a]
    return f'{a:#05x}'


def rel8(pc, n, b):
    return (pc + n + (b - 256 if b > 127 else b)) & 0xFFFF


def decode(p, pc):
    """(length, text) of the instruction at pc."""
    op = p[pc]
    hi, lo = op >> 4, op & 0xF
    b1 = p[pc + 1] if pc + 1 < len(p) else 0
    b2 = p[pc + 2] if pc + 2 < len(p) else 0
    if op in SINGLE and op != 0xFF:
        return 1, SINGLE[op]
    if lo >= 8:
        if hi <= 3:  # CALL/JMP a12
            a = ((pc + 2) & 0xF000) | ((op & 0x10) << 7) | ((op & 7) << 8) | b1
            return 2, f"{'call' if hi in (0, 1) else 'jmp'} {a:#06x}"
        name = BIT[hi]
        d9 = ((op & 0x10) << 4) | b1
        if name in ('bpc', 'bp', 'bn'):
            return 3, f'{name} {d9name(d9)},{op & 7},{rel8(pc, 3, b2):#06x}'
        return 2, f'{name} {d9name(d9)},{op & 7}'
    if op in (0x60, 0x61, 0x70, 0x71):
        return 2, f"{'push' if hi == 6 else 'pop'} {d9name((op & 1) << 8 | b1)}"
    if lo == 1:
        return {
            0x0: (2, f'br {rel8(pc, 2, b1):#06x}'),
            0x1: (3, f'brf {(pc + 2 + (b1 | b2 << 8)) & 0xFFFF:#06x}'),
            0x2: (3, f'jmpf {b1 << 8 | b2:#06x}'),
            0x3: (3, f'be #{b1:#04x},{rel8(pc, 3, b2):#06x}'),
            0x4: (3, f'bne #{b1:#04x},{rel8(pc, 3, b2):#06x}'),
            0x6: (2, '?'), 0x7: (2, '?'),
        }.get(hi, (2, f'{ALU.get(hi, "?")} #{b1:#04x}'))
    if op == 0x10:
        return 3, f'callr {(pc + 2 + (b1 | b2 << 8)) & 0xFFFF:#06x}'
    if op == 0x20:
        return 3, f'callf {b1 << 8 | b2:#06x}'
    if op == 0x80:
        return 2, f'bz {rel8(pc, 2, b1):#06x}'
    if op == 0x90:
        return 2, f'bnz {rel8(pc, 2, b1):#06x}'
    ri = f'@r{lo & 3}'
    d9 = ((op & 1) << 8) | b1
    if hi == 0x2:
        if lo in (2, 3):
            return 3, f'mov #{b2:#04x},{d9name(d9)}'
        return 2, f'mov #{b1:#04x},{ri}'
    if hi == 0x3:
        if lo in (2, 3):
            return 3, f'be {d9name(d9)},{rel8(pc, 3, b2):#06x}'
        return 3, f'be {ri},#{b1:#04x},{rel8(pc, 3, b2):#06x}'
    if hi == 0x4:
        if lo in (2, 3):
            return 3, f'bne {d9name(d9)},{rel8(pc, 3, b2):#06x}'
        return 3, f'bne {ri},#{b1:#04x},{rel8(pc, 3, b2):#06x}'
    if hi == 0x5:
        if lo in (2, 3):
            return 3, f'dbnz {d9name(d9)},{rel8(pc, 3, b2):#06x}'
        return 2, f'dbnz {ri},{rel8(pc, 2, b1):#06x}'
    name = LOADSTORE.get(hi) or ALU.get(hi)
    if hi == 0x6:
        name = 'inc'
    if lo in (2, 3):
        return 2, f'{name} {d9name(d9)}'
    return 1, f'{name} {ri}'


def disasm(p, start, count):
    pc = start
    for _ in range(count):
        n, text = decode(p, pc)
        print(f'{pc:04x}  {p[pc:pc + n].hex():8}  {text}')
        pc += n


def refs(p, addr):
    hi, lo = addr >> 8, addr & 0xFF
    for i in range(len(p) - 2):
        if p[i] == 0x23 and p[i + 1] == 0x05 and p[i + 2] == hi:
            near = [j for j in range(max(0, i - 9), i + 10) if p[j:j + 3] == bytes([0x23, 0x04, lo])]
            if near:
                print(f'{i:04x}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    prog = Path(sys.argv[1]).read_bytes()
    if sys.argv[2] == 'refs':
        refs(prog, int(sys.argv[3], 16))
    else:
        disasm(prog, int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 40)
