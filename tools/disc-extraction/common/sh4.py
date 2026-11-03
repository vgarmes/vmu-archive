"""Minimal SH-4 disassembler for the Dreamcast's main CPU: the common integer
instructions, enough to follow control flow and see constants. Unknown words
print as `.word`.

    python3 sh4.py <1ST_READ.BIN> <start address> <end address>

Addresses are memory addresses (hex); 1ST_READ.BIN loads at 0x8C010000.
"""
import struct
import sys
from pathlib import Path

LOAD = 0x8C010000  # where the boot loader puts 1ST_READ.BIN


def _s8(v):
    return v - 256 if v & 0x80 else v


def _s12(v):
    return v - 4096 if v & 0x800 else v


def dis(b, off, load=LOAD):
    """Disassemble the instruction at file offset `off` of `b`, loaded at `load`."""
    w = struct.unpack_from('<H', b, off)[0]
    pc = load + off
    n, m, i8, d4 = (w >> 8) & 15, (w >> 4) & 15, w & 0xFF, w & 15
    top = w >> 12

    def lit(addr, fmt):
        o = addr - load
        return struct.unpack_from(fmt, b, o)[0] if 0 <= o <= len(b) - struct.calcsize(fmt) else None

    if top == 0xE:
        return f'mov     #{_s8(i8)},r{n}'
    if top == 0x9:
        a = pc + 4 + i8 * 2
        return f'mov.w   @({hex(a)}),r{n}    ; ={lit(a, "<h")}'
    if top == 0xD:
        a = ((pc + 4) & ~3) + i8 * 4
        v = lit(a, '<I')
        return f'mov.l   @({hex(a)}),r{n}    ; ={hex(v) if v is not None else "?"}'
    if top == 0x7:
        return f'add     #{_s8(i8)},r{n}'
    if top == 0xA:
        return f'bra     {hex(pc + 4 + _s12(w & 0xFFF) * 2)}'
    if top == 0xB:
        return f'bsr     {hex(pc + 4 + _s12(w & 0xFFF) * 2)}'
    if top == 0x8:
        target = hex(pc + 4 + _s8(i8) * 2)
        return {0x9: f'bt      {target}', 0xB: f'bf      {target}', 0xD: f'bt/s    {target}', 0xF: f'bf/s    {target}',
                0x8: f'cmp/eq  #{_s8(i8)},r0', 0x0: f'mov.b   r0,@({d4},r{m})', 0x1: f'mov.w   r0,@({d4 * 2},r{m})',
                0x4: f'mov.b   @({d4},r{m}),r0', 0x5: f'mov.w   @({d4 * 2},r{m}),r0'}.get(n, f'.word {w:04x}')
    if top == 0x1:
        return f'mov.l   r{m},@({d4 * 4},r{n})'
    if top == 0x5:
        return f'mov.l   @({d4 * 4},r{m}),r{n}'
    if top == 0x6:
        return {0x3: f'mov     r{m},r{n}', 0x2: f'mov.l   @r{m},r{n}', 0x1: f'mov.w   @r{m},r{n}', 0x0: f'mov.b   @r{m},r{n}',
                0x6: f'mov.l   @r{m}+,r{n}', 0xC: f'extu.b  r{m},r{n}', 0xD: f'extu.w  r{m},r{n}',
                0xE: f'exts.b  r{m},r{n}', 0xF: f'exts.w  r{m},r{n}'}.get(d4, f'.word {w:04x}')
    if top == 0x2:
        return {0x2: f'mov.l   r{m},@r{n}', 0x1: f'mov.w   r{m},@r{n}', 0x0: f'mov.b   r{m},@r{n}', 0x6: f'mov.l   r{m},@-r{n}',
                0x8: f'tst     r{m},r{n}', 0x9: f'and     r{m},r{n}', 0xB: f'or      r{m},r{n}'}.get(d4, f'.word {w:04x}')
    if top == 0x3:
        return {0x0: f'cmp/eq  r{m},r{n}', 0x2: f'cmp/hs  r{m},r{n}', 0x3: f'cmp/ge  r{m},r{n}', 0x6: f'cmp/hi  r{m},r{n}',
                0x7: f'cmp/gt  r{m},r{n}', 0xC: f'add     r{m},r{n}', 0x8: f'sub     r{m},r{n}'}.get(d4, f'.word {w:04x}')
    if top == 0x4:
        return {0x0B: f'jsr     @r{n}', 0x2B: f'jmp     @r{n}', 0x22: f'sts.l   pr,@-r{n}', 0x26: f'lds.l   @r{n}+,pr',
                0x15: f'cmp/pl  r{n}', 0x11: f'cmp/pz  r{n}', 0x10: f'dt      r{n}', 0x08: f'shll2   r{n}', 0x00: f'shll    r{n}',
                0x01: f'shlr    r{n}', 0x18: f'shll8   r{n}', 0x28: f'shll16  r{n}', 0x09: f'shlr2   r{n}'}.get(w & 0xFF, f'.word {w:04x}')
    if top == 0x0:
        if w == 0x000B:
            return 'rts'
        if w == 0x0009:
            return 'nop'
        named = {0xC: f'mov.b   @(r0,r{m}),r{n}', 0xD: f'mov.w   @(r0,r{m}),r{n}', 0xE: f'mov.l   @(r0,r{m}),r{n}',
                 0x4: f'mov.b   r{m},@(r0,r{n})', 0x6: f'mov.l   r{m},@(r0,r{n})', 0x7: f'mul.l   r{m},r{n}'}
        if d4 in named:
            return named[d4]
        return {0x29: f'movt    r{n}', 0x2A: f'sts     pr,r{n}'}.get(w & 0xFF, f'.word {w:04x}')
    if top == 0xC:
        return {0x8: f'tst     #{i8},r0', 0x9: f'and     #{i8},r0', 0xB: f'or      #{i8},r0',
                0x7: f'mova    @({hex(((pc + 4) & ~3) + i8 * 4)}),r0'}.get(n, f'.word {w:04x}')
    return f'.word {w:04x}'


def listing(b, start, end, load=LOAD):
    """(address, text) for every instruction between two memory addresses."""
    return [(a, dis(b, a - load, load)) for a in range(start, end, 2)]


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    data = Path(sys.argv[1]).read_bytes()
    for addr, text in listing(data, int(sys.argv[2], 16), int(sys.argv[3], 16)):
        print(f'{addr:08x}  {struct.unpack_from("<H", data, addr - LOAD)[0]:04x}  {text}')
