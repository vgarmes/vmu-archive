"""Turn the extraction output into input for `pnpm icons:import`.

    python3 prep.py <out dir from lcdimg.py + anims.py> <inbox dir>

Writes one PNG (frames stacked, in play order) and sidecar per animation, and one
per screen the code never draws (marked "unused"). Anything already in the archive
is skipped: an animation counts as present when an entry uses the same disc
screens, whichever frame it starts on. Titles and tags come from TITLES; the rest
are "Puck".

Also writes the ten 4x5 digits of the ammo counter as sprites ("sprite": true),
which the importer keeps in content/sprites/ at their own size; it skips the ones
already there. Which digit each entry is hasn't been checked, so they're titled
by entry number.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

from archive import GAME, archive_entries, load

TITLES = {3: ('NG', ['memory-card']), 5: ('All OK', []), 7: ('Do not touch', []), 10: ('Title screen', None)}
# No region: nothing here is known to be missing from the PAL release.
BASE = dict(game=GAME, publisher='ASCII', year=1999)


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    screens, found = load(out)
    have = {frozenset(s) for _, _, s in archive_entries(screens)}
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)

    pieces = [(a['screens'], a.get('delays_ms'), False) for a in found['animations']]
    pieces += [([n], None, True) for n in found['unused']]
    written = 0
    for frames, delays, unused in pieces:
        if frozenset(frames) in have:
            continue
        title, extra = TITLES.get(frames[0], ('Puck', []))
        tags = ['logo'] if extra is None else ['character', 'puck', *extra]
        stem = f'berserk-{"-".join(f"{n:02d}" for n in frames)}'
        sheet = Image.new('1', (48, 32 * len(frames)), 1)
        for k, n in enumerate(frames):
            sheet.paste(Image.open(out / 'lcd' / f'{n:02d}.png').convert('1'), (0, 32 * k))
        sheet.save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags)
        if delays:
            meta.update({'frameDelayMs': delays[0]} if len(set(delays)) == 1 else {'frameDelaysMs': delays})
        if unused:
            meta['unused'] = True
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    manifest = json.loads((out / 'manifest.json').read_text())
    for m in manifest:
        if m['kind'] != 'glyph':
            continue
        n = int(m['name'])
        shutil.copy(out / 'lcd' / f"{m['name']}.png", inbox / f'berserk-sprite-{n:02d}.png')
        meta = dict(title=f'Digit (entry {n})', **BASE, tags=['digit', 'ammo-counter'], sprite=True,
                    source={'file': '/LCDIMG.BIN', 'entry': n, 'offset': m['offset']})
        (inbox / f'berserk-sprite-{n:02d}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
