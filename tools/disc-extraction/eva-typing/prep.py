"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen the archive doesn't have yet.
"""
import json
import shutil
import sys
from pathlib import Path

GAME = 'Shinseiki Evangelion: Typing E-Keikaku'
GAME_ID = 'shinseiki-evangelion-typing-e-keikaku'  # its id in content/games.json
REPO = Path(__file__).resolve().parents[3]
# Only released in Japan, and the logo is Japanese.
BASE = dict(game=GAME, publisher='Gainax', year=2001, region='JP')
TITLES = {
    0: ('Title screen', ['logo']),
    1: ('Access', ['memory-card']),
    2: ('Save OK', ['memory-card']),
    3: ('Save NG', ['memory-card']),
    4: ('Load OK', ['memory-card']),
    5: ('Load NG', ['memory-card']),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    have = set()
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            have.update(data.get('frames', []))
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for m in json.loads((out / 'manifest.json').read_text()):
        n = int(m['name'])
        if m['frame_hex'] in have:
            print('already in the archive:', m['what'])
            continue
        title, tags = TITLES[n]
        stem = f'eva-typing-{n:02d}'
        shutil.copy(out / 'lcd' / f'{n:02d}.png', inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
