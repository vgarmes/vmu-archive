# System BIOSes

Not discs: the art built into the VMU and the Dreamcast themselves.

- **VMU BIOS:** `american_v1.05.s` from
  [gyrovorbis/vmu-bios-disassembly](https://github.com/gyrovorbis/vmu-bios-disassembly)
  (read at commit `33343542`), the commented disassembly of the US VMU BIOS
  v1.05. It assembles back to the ROM (md5 `322054c6d7b7ea5fd0388eee7b636fb0`),
  but no ROM is needed: the art is in it as `.byte` data. The sprites' `source`
  names `american_v1.05.bin`, the file its Makefile assembles, and the ROM
  address.
- **Japanese VMU BIOS:** `jp1004-19980930-315-6208-01.bin`, v1.004, 64 KB,
  md5 `1c75e99bdc6d88a855da1ce212c2b38a`. No disassembly: `vmubios_jp.py`
  reads the ROM itself and writes its own inbox.
- **Dreamcast BIOS:** `dc_boot.bin`, 2 MB, md5
  `e10c53c2f8b90bab96ead2d368858623`.

What the scripts found is written up in the notes,
[`content/games/visual-memory-unit.md`](../../../content/games/visual-memory-unit.md)
and [`content/games/dreamcast.md`](../../../content/games/dreamcast.md).

These scripts write PNGs with `png.py` here and don't need Pillow.

## Run

```sh
VMUS=path/to/vmu-bios-disassembly/american_v1.05.s
BOOT=path/to/dc_boot.bin
VMUJ=path/to/jp1004-19980930-315-6208-01.bin
OUT=/tmp/bios
python3 -E vmubios.py "$VMUS" $OUT/vmu   # main menu, clock animals, fonts, contact sheet
python3 -E dcboot.py "$BOOT" $OUT/dc     # the 129 memory card icons, contact sheet
python3 -E prep.py $OUT/vmu $OUT/dc $OUT/inbox
pnpm icons:import $OUT/inbox
python3 -E vmubios_jp.py "$VMUJ" $OUT/vmu-jp  # JP main menu, big font, cat, helicopter
pnpm icons:import $OUT/vmu-jp/inbox
```

Run the Python scripts from this folder.
