"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per 48x32 screen the archive doesn't have yet. The
sprites (digits and QTE buttons) are left out: the game draws them onto other
screens at run time. Every screen gets region JP, the English ones included:
they come from the Japanese release, which carries both languages.
"""
import json
import shutil
import sys
from pathlib import Path

GAME = 'Shenmue II'
GAME_ID = 'shenmue-ii'  # its id in content/games.json
REPO = Path(__file__).resolve().parents[3]
BASE = dict(game=GAME, publisher='Sega', year=2001, region='JP')
CARD = ['memory-card']
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
    'BT_START': ('Battle start', ['status']),
    'BT_COUNT': ('Defeated', ['status']),
    'BT_END': ('All defeated', ['status']),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            have.update(data['frames'])
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for m in json.loads((out / 'manifest.json').read_text()):
        if m['kind'] != 'screen':
            continue
        if m['frame_hex'] in have:
            print('already in the archive:', m['name'])
            continue
        title, tags = TITLES[m['name']]
        stem = f'shenmue2-{m["name"].lower()}'
        shutil.copy(out / 'lcd' / f'{m["name"]}.png', inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
