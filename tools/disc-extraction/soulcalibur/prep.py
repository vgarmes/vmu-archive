"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

One 5-frame animation per character. No timing yet: the game's playback speed
hasn't been measured, so the entries carry none and the site plays them at its
default. No region: the chibis are the same in every release.
"""
import json
import shutil
import sys
from pathlib import Path

GAME = 'Soul Calibur'


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    manifest = json.loads((out / 'manifest.json').read_text())
    for m in manifest:
        stem = f'soul-calibur-{m["file"][:-4]}'
        shutil.copy(out / 'lcd' / m['file'], inbox / f'{stem}.png')
        tag = m['character'].lower().replace(' ', '-')
        meta = dict(title=m['character'], game=GAME, publisher='Namco', year=1999, tags=['character', tag])
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(len(manifest), 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
