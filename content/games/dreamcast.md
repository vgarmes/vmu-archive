# Dreamcast

Scripts: `tools/disc-extraction/bios/`.

Source: the console's boot ROM, `dc_boot.bin` (2 MB, md5
`e10c53c2f8b90bab96ead2d368858623`). Its companion `dc_flash.bin` only holds
settings (region, language, date), no art.

## Menu smile

The archive's "Menu smile" isn't stored plainly in `dc_boot.bin`: no packing,
flip or inversion of it turns up. Parts of the ROM are compressed (the bytes
from `0x0F0000` to `0x100000` look random), so it's probably packed there. Not
traced yet.

## Memory card icons

From `0x17EF50` the ROM holds 129 icons, 32x32 and one colour, 128 bytes each,
stored upright in the archive's own encoding. The bytes before and after are
noise. They're the icons the BIOS's memory card screen offers when it asks
"Please use the controller to select an icon", and it shows them on the TV, not
on the VMU, so they're kept as sprites, each with its number in the set.

| Numbers | What                                                                                                    |
| ------- | ------------------------------------------------------------------------------------------------------- |
| 0–5     | A circled cross, an hourglass in four frames, a Visual Memory                                           |
| 6–85    | Pictures: planets, faces, animals, food, music, vehicles, objects, weather, stars, card suits and faces |
| 86–95   | Digits 0–9                                                                                              |
| 96–121  | Letters A–Z                                                                                             |
| 122–128 | Fill patterns                                                                                           |

The first six look like the screen's own symbols (an empty slot, a busy
hourglass, the card itself) rather than icons to pick; the code that shows them
wasn't traced, so they're kept with the rest. Number 31, a round face with
gears, is marked unidentified.
