"""Turn Neoseeker's Shenmue Goodies page into input for `pnpm icons:import`.

    python3 goodies.py <saved page .html> <inbox dir>

The Goodies characters were downloads (Shenmue Passport's online service, closed
in 2002), so they're on no disc. The source is the Neoseeker wiki's list,
https://shenmue.neoseeker.com/wiki/Shenmue_Goodies, saved from a browser as
"Webpage, Complete": the .html plus its "<name>_files" folder of images.

Each row of the page's table is a character: a name, an animation (a 48x32 GIF)
and a still. Writes:

- every 48x32 animation as a screen: a PNG with its frames stacked, and the GIF's
  delays as frameDelayMs or frameDelaysMs. Ryo Hazuki replaces the archive's
  existing entry, which came from a preview GIF with made-up timing.
- the stills that use the whole 48x32 screen (the four built-in characters'
  portraits) as screens.
- the other stills as sprites: they're faces drawn 32 (a few 33) pixels wide and
  centred on a 48x32 canvas by the wiki, so they're cut back to the drawn columns.
- the page's 32x32 face icons (SHNM_<id>_<name>.gif) as sprites. A face that's
  pixel for pixel a still's is skipped by the importer as a duplicate.
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Shenmue'
# No region: the Goodies were an online download, not part of any one release.
BASE = dict(game=GAME, publisher='Sega', year=1999)
# The archive's Ryo Hazuki predates this import; his animation replaces it.
REPLACES = {'Ryo Hazuki': 'shenmue-ryo-hazuki'}
BUILT_IN = {'Ryo Hazuki', 'Ling Sha Hua', 'Ren Wuying', 'Niao Sun'}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def lit(im):
    return [1 if v < 128 else 0 for v in im.convert('L').getdata()]


def rows_of(page):
    h = page.read_text(encoding='utf-8', errors='replace')
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S):
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)
        if len(cells) < 3:
            continue
        name = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', cells[0])).split())
        imgs = [[Path(html.unescape(s)).name for s in re.findall(r'<img[^>]*?src="([^"]+)"', c)] for c in cells[1:3]]
        if name and name != 'Character' and (imgs[0] or imgs[1]):
            yield name, imgs[0], imgs[1]


def frames_of(path):
    im = Image.open(path)
    out = []
    for k in range(getattr(im, 'n_frames', 1)):
        im.seek(k)
        out.append((im.convert('L').point(lambda v: 0 if v < 128 else 255).convert('1'), im.info.get('duration', 100)))
    return out


def write(inbox, stem, image, meta):
    image.save(inbox / f'{stem}.png')
    (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))


def main(page, inbox):
    page, inbox = Path(page), Path(inbox)
    files = page.parent / f'{page.stem}_files'
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    counts = dict(animations=0, portraits=0, faces=0)
    for name, anims, stills in rows_of(page):
        tags = ['character', slug(name)]
        for src in anims + stills:
            path = files / src
            im = Image.open(path)
            if im.size == (48, 32) and getattr(im, 'n_frames', 1) > 1:
                fr = frames_of(path)
                strip = Image.new('1', (48, 32 * len(fr)), 1)
                for k, (f, _) in enumerate(fr):
                    strip.paste(f, (0, 32 * k))
                delays = [d for _, d in fr]
                timing = {'frameDelayMs': delays[0]} if len(set(delays)) == 1 else {'frameDelaysMs': delays}
                meta = dict(title=name, **BASE, tags=tags, **timing)
                if name in REPLACES:  # keeps the entry's id, tags and poster frame
                    meta['replaces'] = REPLACES[name]
                    del meta['tags']
                write(inbox, f'goodies-{slug(name)}', strip, meta)
                counts['animations'] += 1
            elif im.size == (48, 32):
                px = lit(im)
                cols = [x for x in range(48) if any(px[y * 48 + x] for y in range(32))]
                if name in BUILT_IN:
                    write(inbox, f'goodies-{slug(name)}-portrait', frames_of(path)[0][0],
                          dict(title=f'{name} portrait', **BASE, tags=tags + ['portrait']))
                    counts['portraits'] += 1
                else:
                    x0, x1 = min(cols[0], 8), max(cols[-1], 39)
                    face = frames_of(path)[0][0].crop((x0, 0, x1 + 1, 32))
                    write(inbox, f'goodies-sprite-{slug(name)}-face', face,
                          dict(title=f'{name} face', **BASE, tags=tags + ['face'], sprite=True))
                    counts['faces'] += 1
            elif im.size == (32, 32):
                write(inbox, f'goodies-sprite-{slug(name)}-face-icon', frames_of(path)[0][0],
                      dict(title=f'{name} face', **BASE, tags=tags + ['face'], sprite=True))
                counts['faces'] += 1
            else:
                print('skipped', src, im.size)
    print(counts, '->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
