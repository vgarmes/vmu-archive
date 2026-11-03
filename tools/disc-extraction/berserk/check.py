"""Compare the archive's Berserk entries with the disc and the game code.

    python3 check.py <out dir from lcdimg.py + anims.py>

For every entry: which disc screens its frames are (or "not on disc"), and whether
its frames and timing match the animation the code plays, allowing the loop to
start on a different frame and comparing holds in 60 Hz ticks.
"""
import sys

from archive import archive_entries, load


def rotations(seq):
    return [seq[k:] + seq[:k] for k in range(len(seq))]


def main(out):
    screens, found = load(out)
    plays = {frozenset(a['screens']): a for a in found['animations']}
    for entry_id, data, frames in archive_entries(screens):
        if None in frames:
            print(f'{entry_id}: not on disc (another release?)')
            continue
        anim = plays.get(frozenset(frames))
        delays = data.get('frameDelaysMs') or [data.get('frameDelayMs')] * len(frames)
        if len(frames) == 1:
            parent = next((a for a in found['animations'] if frames[0] in a['screens']), None)
            if frames[0] in found['unused']:
                note = 'never drawn by the code' + ('' if data.get('unused') else ' (missing "unused")')
            elif parent and len(parent['screens']) > 1:
                note = f'one frame of {parent["screens"]}'
            else:
                note = 'still, as the code draws it'
        elif anim is None:
            note = 'NOT an animation the code plays'
        else:
            # Compare in 60 Hz ticks: 133 and 134 ms are both 8 ticks (133.3 ms).
            ticks = [round(d * 60 / 1000) for d in delays]
            ok = list(zip(frames, ticks)) in rotations(list(zip(anim['screens'], anim['holds_ticks'])))
            note = 'matches the code' if ok else f'code plays {anim["screens"]} at {anim["delays_ms"]} ms'
        print(f'{entry_id}: screens {frames} -> {note}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
