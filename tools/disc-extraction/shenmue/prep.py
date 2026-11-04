"""Turn ../shenmue2/vmu.py's output for Shenmue into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Shenmue keeps its VMU art in the same IWAD chunk of /MISC/COLD.BIN as Shenmue
II, under the same 46 names, so Shenmue II's decoder reads it unchanged.

Writes one PNG and sidecar per 48x32 screen whose pixels the archive doesn't
have yet, under any game: twelve of them (the save, load and PK screens) are
pixel for pixel Shenmue II's and are already filed there. Every screen gets
region JP, the English ones included: they come from the Japanese release,
which carries both languages.

Also writes three sprites with "sprite": true, each a set of named entries the
game looks up together, one under the next in the order below with their size
in "glyphs": the two digit sets, as fonts (the counter fills the digit into the
name), and the QTE buttons.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Shenmue'
REPO = Path(__file__).resolve().parents[3]
BASE = dict(game=GAME, publisher='Sega', year=1999, region='JP')
CARD = ['memory-card']
BATTLE = ['status']
# name: (title, tags)
TITLES = {
    'SHENMUE': ('Title screen', ['logo']),
    'PK': ('PK', []),
    'LOAD_JP': ('Loading', CARD),
    'LOAD_US': ('Loading', CARD),
    'SAVE_JP': ('Saving', CARD),
    'SAVE_US': ('Saving', CARD),
    'OK_JP': ('Save complete', CARD),
    'OK_US': ('OK', CARD),
    'NG_JP': ('Save failed', CARD),
    'NG_US': ('NG', CARD),
    'RSM_JP': ('Please wait', CARD),
    'RSM_US': ('Please wait', CARD),
    'RSM_OK': ('Complete', CARD),
    'RSM_NG': ('Failed', CARD),
    'BT_START': ('70 Man Battle start', BATTLE),
    'BT_COUNT': ('70 Man Battle count', BATTLE),
    'BT_END': ('70 Man Battle cleared', BATTLE),
}
DIGITS = [str(n) for n in range(10)]
# The QTE buttons in the order of the game's name list (0x8C273144).
BUTTONS = ['KB', 'KF', 'BA', 'BB', 'BX', 'BY', 'BL', 'BR', 'BP']
# (stem, title, the name the game looks up, entry names, tags)
SHEETS = [
    ('digits-large', '70 Man Battle digits, large', 'BT_L?', [f'BT_L{d}' for d in DIGITS],
     ['battle', 'font', 'digits']),
    ('digits-small', '70 Man Battle digits, small', 'BT_S?', [f'BT_S{d}' for d in DIGITS],
     ['battle', 'font', 'digits']),
    ('qte-buttons', 'QTE buttons', 'WAZA_*', [f'WAZA_{b}' for b in BUTTONS], ['qte']),
]


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    manifest = {m['name']: m for m in json.loads((out / 'manifest.json').read_text())}
    have = {}
    for path in (REPO / 'content/icons').glob('*.json'):
        for frame in json.loads(path.read_text()).get('frames', []):
            have[frame] = path.stem
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for name, m in manifest.items():
        if m['kind'] != 'screen':
            continue
        if m['frame_hex'] in have:
            print(f'already in the archive: {name} = {have[m["frame_hex"]]}')
            continue
        title, tags = TITLES[name]
        stem = f'shenmue-{name.lower()}'
        shutil.copy(out / 'lcd' / f'{name}.png', inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1

    for stem, title, lookup, names, tags in SHEETS:
        parts = [manifest[n] for n in names]
        w, h = parts[0]['width'], parts[0]['height']
        assert all((p['width'], p['height']) == (w, h) for p in parts), f'{stem}: mixed sizes'
        sheet = Image.new('1', (w, h * len(parts)), 1)
        for k, n in enumerate(names):
            sheet.paste(Image.open(out / 'lcd' / f'{n}.png'), (0, h * k))
        sheet.save(inbox / f'shenmue-sprite-{stem}.png')
        meta = dict(title=title, **BASE, tags=tags, sprite=True, glyphs={'height': h},
                    source={'file': '/MISC/COLD.BIN', 'entry': lookup, 'offset': parts[0]['offset']})
        (inbox / f'shenmue-sprite-{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
