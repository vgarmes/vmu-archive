"""Turn vmu.py's output into input for `pnpm icons:import`.

    python3 prep.py <out dir from vmu.py> <inbox dir>

Writes the screens listed in PICKS, one still each, the animations in ANIMS and
the faces in BLINKS, converted with the rule a Flycast capture confirmed (value
below 8 = lit). Value 8 is only in the second crest; VALUE8_LIT counts it as lit
there, which no capture has checked.

Timing: the title intro was measured on a recording. The power-on animation and
the カジノ大戦 intros open the same way, so they borrow its 100 ms a frame and
4 s hold; the faces blink with an assumed 3 s open, 150 ms closed; the map
alternates about 267 / 67 ms, read off a recording. Only the title is verified.

Also writes the sprites in SPRITES with "sprite": true, which the importer keeps
at their own size in content/sprites/.

Also writes the battle banners in BANNERS as scroll strips: the game slides
each one through the screen 1 px per 60 Hz tick (measured on a Flycast
recording of Gigantesque ciseau), so they import with stepPx 1 and delayMs 17.
A heroine's second and third banners are also in Ogami's files (attacks
together), so they carry both characters' tags.
"""
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

GAME = 'Sakura Taisen 3: Paris wa Moete Iru ka'
GAME_ID = 'sakura-taisen-3-paris-wa-moete-iru-ka'  # its id in content/games.json
REPO = Path(__file__).resolve().parents[3]
BASE = dict(game=GAME, publisher='Sega', year=2001, region='JP')
FACES = {
    'mgkg_coq': ('Coquelicot', 'coquelicot'),
    'mgkg_eri': ('Erica', 'erica'),
    'mgkg_gly': ('Glycine', 'glycine'),
    'mgkg_han': ('Hanabi', 'hanabi'),
    'mgkg_oga': ('Ogami', 'ogami'),
    'mgkg_rob': ('Lobelia', 'lobelia'),
}
# (entry name, frame in its strip, title, tags)
PICKS = [
    ('system-01', 0, 'Crest', ['logo']),
    ('system-02', 0, 'Message', []),
    ('system-03', 0, 'Crest', ['logo']),  # the crest again, its outer ring in value 8
]
VALUE8_LIT = {'system-03'}


def intro(n):
    """The title intro's rhythm: 100 ms a frame, the last held 4 s."""
    return [100] * (n - 1) + [4000]


# Animations: (entries, in order, title, tags, delay per frame in ms, poster frame,
# id of the entry it replaces or None). An entry may be a strip of several frames.
ANIMS = [
    # Logo intro: a line opens to a lit screen, the logo unfolds from it. Measured: each
    # frame lasts 100 ms (6 ticks), then the logo stays up about 4 s before the map.
    (['system-04'], 'Title screen', ['logo'], intro(11), 10,
     'sakura-taisen-3-paris-wa-moete-iru-ka-title-screen'),
    # Power-on: a line opens into a double frame. Timing assumed (intro rhythm).
    (['system-00'], 'Power-on', [], intro(6), 5, None),
    # The カジノ大戦 minigames' logo intros, one entry per step. Timing assumed. Titled by
    # reading only: the logo shows the kanji, and its trailing digit would end up in the id
    # twice ("kajino-taisen-2-2").
    *[([f'kajino{i}-{k:02d}' for k in range(10)], f'Kajino Taisen{"" if i == 1 else f" {i}"}',
       ['logo', 'minigame'], intro(10), 9, None) for i in (1, 2, 3)],
    # Strategy map: the corner marks alternate, about 267 / 67 ms in a recording; the
    # units the game draws on top at run time aren't part of it.
    (['smap01-00', 'smap01-01'], 'Strategy map', ['map'], [267, 67], 0, None),
]
# Faces: each eyes-open entry and the eyes-closed one after it, as a blink. Replaces the
# still of the eyes-open frame. Timing assumed.
BLINK_MS = [3000, 150]
BLINKS = [(stem, k, title, tag) for stem, (title, tag) in FACES.items() for k in (0, 2, 4, 6)]
# Sprites: art the game draws onto part of a screen, kept at its own size in
# content/sprites/. (entry name, title, tags)
SPRITES = [
    # The battle screen is built from this sheet at run time: DESTROY and TARGET
    # panels, HP and MP labels, small digits 0-9, large digits 0-5 and X, large
    # slanted digits 0-9. Kept whole, as stored; where each piece goes wasn't traced.
    ('smap01-02', 'Battle screen parts', ['battle', 'digits', 'sheet']),
]
LIT_BELOW = 8 * 17  # vmu.py stores brightness v as grey level v * 17
SCROLL = dict(stepPx=1, delayMs=17)
# (entry name, title as drawn, tags). Titles keep the art's spelling (no accents).
BANNERS = [
    ('boss_crow_n-00', 'Les destinees', ['boss']),
    ('boss_lion_n-00', 'Royal rage', ['boss']),
    ('boss_rabbit_n-00', 'Gigantesque ciseau', ['boss']),
    ('boss_scorpion_n-00', 'Les fleurs du mal', ['boss']),
    ('boss_snake_n-00', 'Le chant de la terre', ['boss']),
    ('coquelicot_f1_n-00', 'Magique bonbon', ['coquelicot']),
    ('coquelicot_f1_n-01', 'Lever le rideau', ['coquelicot', 'ogami']),
    ('coquelicot_f1_n-02', 'Amour escarpolette', ['coquelicot', 'ogami']),
    ('erica_f1_n-00', 'Sacre de lumiere', ['erica']),
    ('erica_f1_n-01', 'Paradisiaque porte', ['erica', 'ogami']),
    ('erica_f1_n-02', 'Alleluia', ['erica', 'ogami']),
    ('glycine_f1_n-00', 'Grosse Vague', ['glycine']),
    ('glycine_f1_n-01', 'Bleu raz de maree', ['glycine', 'ogami']),
    ('glycine_f1_n-02', 'Pegase aile', ['glycine', 'ogami']),
    # Japanese titles carry their reading: ids are slugs, and slugs keep only Latin letters.
    ('hanabi_f1_n-00', '北大路花火 一の舞 金枝玉葉 (Kitaōji Hanabi Ichi no Mai Kinshi Gyokuyō)', ['hanabi']),
    ('hanabi_f1_n-01', '落花流水 (Rakka Ryūsui)', ['hanabi', 'ogami']),
    ('hanabi_f1_n-02', '君と彷徨う恋の道かな (Kimi to Samayou Koi no Michi kana)', ['hanabi', 'ogami']),
    ('lobelia_f1_n-00', 'Fiamma Unghia', ['lobelia']),
    ('lobelia_f1_n-01', 'Combustione', ['lobelia', 'ogami']),
    ('lobelia_f1_n-02', 'Pericolo gioco', ['lobelia', 'ogami']),
    ('ogami_f1a_n-00', "狼虎滅却 刀光剣影 (Rōko Mekkyaku Tōkō Ken'ei)", ['ogami']),
    ('ogami_f1b_n-00', '狼虎滅却 疾風迅雷 (Rōko Mekkyaku Shippū Jinrai)', ['ogami']),
    ('ogami_f1c_n-00', "狼虎滅却 金甌無欠 (Rōko Mekkyaku Kin'ō Muketsu)", ['ogami']),
]


def frames_of(out, manifest, names):
    """The listed entries' frames stacked top to bottom, as 1-bit art (black = lit)."""
    parts = []
    for name in names:
        m = manifest[name]
        assert not m['unverified'], f'{name} uses value 8, which no capture covers yet'
        assert m['frames'], f'{name} is not made of 48x32 frames'
        parts.append(Image.open(out / 'lcd' / f'{name}.png').convert('L').point(lambda p: 0 if p < LIT_BELOW else 255))
    im = Image.new('L', (48, sum(p.height for p in parts)))
    y = 0
    for p in parts:
        im.paste(p, (0, y))
        y += p.height
    return im


def main(out, inbox):
    out, inbox = Path(out), Path(inbox)
    manifest = {m['name']: m for m in json.loads((out / 'manifest.json').read_text())}
    have, ids = set(), {}
    for path in (REPO / 'content/icons').glob('*.json'):
        data = json.loads(path.read_text())
        if data['gameId'] == GAME_ID:
            have.update(data.get('frames', []))  # scroll entries store a strip instead
            if len(data.get('frames', [])) == 1:
                ids[data['frames'][0]] = path.stem  # stills, to replace with their animation
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    written = 0
    for name, frame, title, tags in PICKS:
        m = manifest[name]
        assert not m['unverified'] or name in VALUE8_LIT, f'{name} uses value 8, which no capture covers yet'
        if m['frame_hex'][frame] in have:
            print('already in the archive:', name)
            continue
        below = LIT_BELOW + 17 if name in VALUE8_LIT else LIT_BELOW
        strip = Image.open(out / 'lcd' / f'{name}.png').convert('L')
        im = strip.crop((0, 32 * frame, 48, 32 * frame + 32)).point(lambda p: 0 if p < below else 255)
        stem = f'sakura3-{name}-{frame:02d}'
        im.convert('1').save(inbox / f'{stem}.png')
        (inbox / f'{stem}.json').write_text(json.dumps(dict(title=title, **BASE, tags=tags), ensure_ascii=False, indent=1))
        written += 1
    for names, title, tags, delays, poster, replaces in ANIMS:
        im = frames_of(out, manifest, names)
        assert len(delays) == im.height // 32, f'{names[0]}: {im.height // 32} frames, {len(delays)} delays'
        stem = f'sakura3-anim-{names[0]}'
        im.convert('1').save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags, frameDelaysMs=delays, posterFrame=poster)
        if replaces:
            meta['replaces'] = replaces
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    for stem_, k, title, tag in BLINKS:
        names = [f'{stem_}-{k:02d}', f'{stem_}-{k + 1:02d}']
        still = ids.get(manifest[names[0]]['frame_hex'][0])
        im = frames_of(out, manifest, names)
        stem = f'sakura3-blink-{names[0]}'
        im.convert('1').save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=['character', 'portrait', tag], frameDelaysMs=BLINK_MS, posterFrame=0)
        if still:
            meta['replaces'] = still
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    for name, title, tags in BANNERS:
        m = manifest[name]
        assert m['height'] == 32 and m['frames'] == 0, f'{name} is not a banner strip'
        im = Image.open(out / 'lcd' / f'{name}.png').convert('L').point(lambda p: 0 if p < LIT_BELOW else 255)
        stem = f'sakura3-banner-{name}'
        im.convert('1').save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=['banner', *tags], scroll=SCROLL)
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    for name, title, tags in SPRITES:
        m = manifest[name]
        assert not m['unverified'], f'{name} uses value 8, which no capture covers yet'
        im = Image.open(out / 'lcd' / f'{name}.png').convert('L').point(lambda p: 0 if p < LIT_BELOW else 255)
        stem = f'sakura3-sprite-{name}'
        im.convert('1').save(inbox / f'{stem}.png')
        meta = dict(title=title, **BASE, tags=tags, sprite=True,
                    source={'file': '/' + m['source'], 'entry': m['entry'], 'offset': m['offset']})
        (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        written += 1
    print(written, 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
