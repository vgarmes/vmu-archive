"""Recover Sword of the Berserk's VMU animations (frame order and timing) from its code.

    python3 anims.py <1ST_READ.BIN> <animations.json>

The routine at 0x8C033034 (US v1.000) runs once per video frame (60 Hz). It keeps a
tick counter (@r13), masks it with 15 (r10) and calls the draw routine (@r11,
0x8C03C89C) with a screen number in r5 when the masked count hits a value:

    mov.l @r13,r0 ; and r10,r0 ; cmp/eq #8,r0 ; bf skip ; … mov #42,r5 ; jsr @r11

(`tst r10,rX` is the same test for count 0.) Each animation is one run of such
calls ending in an unconditional branch to the routine's exit. A frame shows from
its tick until the next frame's tick, wrapping at 16, so 4 ticks = 67 ms.

Calls whose screen number is computed draw the ammo counter's digits (screens
11-20); they are left out. Screens no call ever draws are listed as unused.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'common'))
from sh4 import listing  # noqa: E402

ROUTINE = (0x8C033034, 0x8C033712)  # start of the routine to just past its rts
SHOWN_ELSEWHERE = {7}  # three other callers draw screen 7 once before saving (0x8C03BA70, 0x8C03BB46, 0x8C06C77A)
CYCLE, HZ = 16, 60
SCREENS = 50


def calls(code):
    """Blocks of (tick, screen) draw calls, in code order."""
    blocks, block, tick, screen = [], [], None, None
    for i, (_, text) in enumerate(code):
        prev = code[i - 1][1] if i else ''
        if text.startswith('cmp/eq  #') and prev == 'and     r10,r0':
            tick = int(text.split('#')[1].split(',')[0])
        elif text.startswith('tst     r10,'):
            tick = 0
        elif text.startswith('mov     #') and text.endswith(',r5'):
            screen = int(text.split('#')[1].split(',')[0])
        elif text.endswith(',r5'):
            screen = None  # computed: the ammo counter
        elif text.startswith('jsr     @r11'):
            if screen is not None:
                block.append((tick, screen))
            screen = None
        elif (text.startswith('bra') and not prev.startswith(('bt', 'bf'))) or text == 'rts':
            if block:  # an unconditional branch that isn't skipping a test ends the animation
                blocks.append(block)
            block, tick = [], None
    return blocks


def animation(block):
    frames = sorted(block, key=lambda c: -1 if c[0] is None else c[0])
    if len(frames) == 1:
        return dict(screens=[frames[0][1]], ticks=[frames[0][0]])
    ticks = [t for t, _ in frames]
    holds = [(ticks[(k + 1) % len(ticks)] - t) % CYCLE or CYCLE for k, t in enumerate(ticks)]
    return dict(screens=[s for _, s in frames], ticks=ticks, holds_ticks=holds,
                delays_ms=[round(h * 1000 / HZ) for h in holds])


def main(src, out):
    code = listing(Path(src).read_bytes(), *ROUTINE)
    anims = [animation(b) for b in calls(code)]
    drawn = {s for a in anims for s in a['screens']} | SHOWN_ELSEWHERE | set(range(11, 21))
    result = dict(animations=anims, unused=sorted(set(range(SCREENS)) - drawn))
    Path(out).write_text(json.dumps(result, indent=1))
    for a in anims:
        print(a['screens'], a.get('delays_ms', 'still'))
    print('never drawn:', result['unused'])


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
