"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes one PNG and sidecar per screen, leaving out the blank one.
"""
import json
import shutil
import sys
from pathlib import Path

# Released in Japan alone.
BASE = dict(game='Cool Cool Toon', publisher='SNK', year=2000, region='ntsc-j')
META = {
    1: ('Story', ['menu']),
    2: ('Cool Cool Toon logo', ['logo']),
    3: ('Save', ['status']),
    4: ('Notty', ['menu']),
    5: ('Flitz', ['menu']),
}


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for m in json.loads((out / 'manifest.json').read_text()):
        if m['blank']:
            continue
        title, tags = META[m['entry']]
        stem = f'cool-cool-toon-{m["entry"]:02d}-' + title.lower().replace(' ', '-')
        shutil.copy(out / 'screens' / f'{m["name"]}.png', inbox / f'{stem}.png')
        (inbox / f'{stem}.json').write_text(json.dumps(dict(title=title, **BASE, tags=tags),
                                                       ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
