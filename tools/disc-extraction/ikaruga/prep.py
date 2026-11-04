"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per piece the archive doesn't have yet: the screens,
SAVE as its two-frame animation, and the chain digits as a sprite.

SAVE's timing comes from the code, not a capture: each frame is drawn, sent, then
held while a counter runs to 15, so it stays up at least 17 steps. That assumes
the state machine steps once per 60 Hz video frame (its caller loops on
0x8C011272, which wasn't identified), so 283 ms is a best guess until measured.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Ikaruga'
REPO = Path(__file__).resolve().parents[3]
# Matches the entry already in the archive. The logo and English text are the
# same in every release, so no region.
BASE = dict(game=GAME, publisher='Treasure', year=2001)
SAVE_MS = 283  # 17 steps of 60 Hz; see above
# (stem, screens from vmu.py, title, tags, extra metadata)
PIECES = [
    ('title', [0], 'Title screen', ['logo'], {}),
    ('save', [1, 2], 'Save', ['memory-card'], {'frameDelayMs': SAVE_MS}),
    ('load', [3], 'Load', ['memory-card'], {}),
    # State 6 flips the frame byte as SAVE's does, but state 5 always draws
    # the first pose: this one is never shown.
    ('unused-load', [4], 'Load', ['memory-card'], {'unused': True}),
    ('ok', [5], 'OK', ['memory-card'], {}),
    ('ng', [6], 'NG', ['memory-card'], {}),
    # Shown with the chain under way; the digits are drawn over its top half.
    ('chain', [7], 'Chain counter', ['status'], {}),
]


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    manifest = {m['name']: m for m in json.loads((out / 'manifest.json').read_text())}
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['game'] == GAME:
            have.update(data.get('frames', []))
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for stem, screens, title, tags, extra in PIECES:
        frames = [manifest[f'{n:02d}'] for n in screens]
        if all(f['frame_hex'] in have for f in frames):
            print('already in the archive:', title)
            continue
        strip = Image.new('1', (48, 32 * len(screens)), 1)
        for k, n in enumerate(screens):
            strip.paste(Image.open(out / 'lcd' / f'{n:02d}.png'), (0, 32 * k))
        strip.save(inbox / f'ikaruga-{stem}.png')
        meta = dict(title=title, **BASE, tags=tags, **extra)
        (inbox / f'ikaruga-{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1

    d = manifest['digits']
    shutil.copy(out / 'digits.png', inbox / 'ikaruga-sprite-digits.png')
    # A font of ten 16x16 digits, stored one under the next.
    meta = dict(title='Chain counter digits', **BASE, tags=['font', 'digits'], sprite=True,
                glyphs={'height': 16}, source={'file': '/1ST_READ.BIN', 'offset': d['offset']})
    (inbox / 'ikaruga-sprite-digits.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
