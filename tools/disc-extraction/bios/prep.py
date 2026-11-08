"""Turn vmubios.py's and dcboot.py's output into input for `pnpm icons:import`.

    python3 prep.py <vmubios.py out dir> <dcboot.py out dir> <inbox dir>

Writes one PNG and sidecar per piece: the VMU main menu as a screen, and as
sprites the six clock animals, the VMU's two fonts and the Dreamcast BIOS's
129 memory card icons.
"""
import json
import shutil
import sys
from pathlib import Path

# The US BIOS. The Japanese one (vmubios_jp.py) lacks most of these, but a
# region can't say "everywhere but Japan", so the VMU's pieces get none.
VMU = dict(game='Visual Memory Unit', publisher='Sega', year=1999)
VMU_FILE = 'american_v1.05.bin'
# Matches the entry already in the archive ("Menu smile").
DC = dict(game='Dreamcast', publisher='Sega', year=1998)
DC_FILE = 'dc_boot.bin'

VMU_SPRITES = {
    'dog-1': ('Clock dog, frame 1', ['clock', 'animal']),
    'dog-2': ('Clock dog, frame 2', ['clock', 'animal']),
    # The fish's two frames are the same bytes: it swims by bobbing, not posing.
    'fish-1': ('Clock fish', ['clock', 'animal']),
    'bird-1': ('Clock bird, frame 1', ['clock', 'animal']),
    'bird-2': ('Clock bird, frame 2', ['clock', 'animal']),
    'font-8x8': ('Big font', ['font', 'digits']),
    'font-6x8': ('Small font', ['font']),
}


def write(inbox, stem, png, meta):
    shutil.copy(png, inbox / f'{stem}.png')
    (inbox / f'{stem}.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))


def main(vmu_out, dc_out, inbox):
    vmu_out, dc_out, inbox = Path(vmu_out), Path(dc_out), Path(inbox)
    if inbox.exists():
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True)
    vmu = {m['name']: m for m in json.loads((vmu_out / 'manifest.json').read_text())}

    write(inbox, 'vmu-main-menu', vmu_out / 'main-menu.png',
          dict(title='Main menu', **VMU, tags=['bios', 'system', 'menu', 'logo']))
    for name, (title, tags) in VMU_SPRITES.items():
        m = vmu[name]
        meta = dict(title=title, **VMU, tags=['bios'] + tags, sprite=True,
                    source={'file': VMU_FILE, 'entry': m['label'], 'offset': m['address']})
        if m.get('glyph_height'):  # a font, its characters stacked
            meta['glyphs'] = {'height': m['glyph_height']}
        write(inbox, f'vmu-sprite-{name}', vmu_out / f'{name}.png', meta)

    icons = json.loads((dc_out / 'manifest.json').read_text())
    for m in icons:
        write(inbox, f'dc-sprite-{m["name"]}', dc_out / f'{m["name"]}.png',
              dict(title=m['what'], **DC, tags=['bios', 'memory-card', 'icon'] + m['tags'], sprite=True,
                   source={'file': DC_FILE, 'entry': m['index'], 'offset': m['offset']}))
    print(1 + len(VMU_SPRITES) + len(icons), 'pieces to import ->', inbox)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
