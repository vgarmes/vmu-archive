# Sonic Shuffle

Scripts: `tools/disc-extraction/sonic-shuffle/`.

Dump: `Sonic Shuffle (Japan)` (Redump, `.cue`). The two screens are in
English and the logo is the one every release uses, so nothing gets a region.

## What's on the disc

No file holds the VMU art; it's all in `1ST_READ.BIN`, next to the save's
VMS texts (`ｿﾆｯｸ ｼｬｯﾌﾙ` at `0x8C0FCDD0`):

| What                    | Address      | Stored as                     | Archive entry      |
| ----------------------- | ------------ | ----------------------------- | ------------------ |
| Sheet of the hand's art | `0x8C0FCDF4` | 48x32, one byte a dot (8 lit) | the sprites below  |
| Sonic Shuffle logo      | `0x8C0FD3F4` | 48x32, 1 bit a dot            | Sonic Shuffle logo |
| NO CARD                 | `0x8C0FD4B4` | 48x32, 1 bit a dot            | No card (unused)   |

The two screens are listed in a table at `0x8C0FD574`, NO CARD first.

Each port has a 1,552-byte record (four from `0x8C24B144`): a 16-byte header,
then the screen as 1,536 bytes, one a dot, 8 lit and 0 unlit. The game draws
into that buffer and passes it to the library's LCD write (`0x8C014424`) from
`0x8C0A5930`. Nothing turns or inverts it on the way.

## The screens

`0x8C0A5A2E` (record, screen) spreads a screen from the table into the
buffer, high bit first. It copies 32 rows of screen 1 but only 22 of screen 0.

- **Sonic Shuffle logo.** All four callers pass screen 1. `0x8C0A5F80` draws
  it when it sets up a port's record. The per-frame update over the four
  ports (from `0x8C0A5C98`) draws it whenever the port isn't showing a hand.
- **No card.** "NO CARD" over the outline of a card. Nothing passes screen 0,
  so the game never shows it. Had it been shown, its last 10 rows (the bottom
  of the lettering and of the card) wouldn't have been drawn. It's kept whole,
  as stored, and marked unused.

The archive's logo came from a capture and was off by a dot in places: the
"SHUFFLE" lettering and the swoosh under it had shifted one column, and two
rows of "SONIC" had a dot too many. It's now the disc's bitmap,
which the game copies whole.

## The hand

In three of the game's modes (9, 10 and 13), when a check (`0x8C090B62` with 6) passes, the update draws the player's hand instead. The VMU is where each
player keeps their cards out of the others' sight. `0x8C0A59B8` copies the
player's seven card slots (from `0x8C21EF5C` + 512 × player) into the
record's header. `0x8C0A57A4` then builds the screen from pieces of the
sheet. `0x8C0A5554` (record, piece, x, y) copies piece n's rectangle (x, y,
width, height, at `0x8C0FD5AC` + 8n) onto the screen, and `0x8C0A55DA`
clears one.

| Where (x, y)                    | Piece                                  | When                                                            |
| ------------------------------- | -------------------------------------- | --------------------------------------------------------------- |
| 3, 9, 15, 21, 27, 33, 39 at y 6 | a card (6x16), one per slot            | slot holds a card; cleared if empty                             |
| after the last card, y 6        | end of the hand (1x16), its right edge | at least one card                                               |
| a card's x, y 0                 | cursor (7x5)                           | the chosen card, while `0x8C0FD58A` is set                      |
| 2, 23                           | gem (11x9)                             | always                                                          |
| 14, 24                          | a digit, 0 to 5 (5x7)                  | the player's byte at +0x31 isn't 0xFF                           |
| 29, 23 and 39, 24               | ring (9x9) and plus or minus (7x7)     | flag 14 (plus) or 15 (minus) of `0x8C098A46`; cleared otherwise |

A card of value v draws piece v − 1: 1 to 6, then the S card (7) and the
Eggman card (8), both drawn in reverse. `0x8C0A573C` changes what's shown
under some conditions (`0x8C09B5EE`, by player): with status 3 every card is
drawn face down (piece 20), with status 4 or 31 as an Eggman card, and with
flag 4 of `0x8C098A46` set a 1 is drawn as a 4. What those statuses are in
play wasn't traced. Neither were the gem's count and the ring's plus and
minus.

The hand is made from game state, so the archive keeps its pieces rather than
a screen of it.

## Sprites

The 21 pieces cover every lit dot of the sheet, with no overlaps. The 133
dots outside them are all unlit. They're kept as seven sprites, one per set
the code picks from, pieces one under the next in the table's order. `vmu.py`
rebuilds the sheet's 1,536 bytes from them and checks them against the disc.

- **Cards** (pieces 0–7, then 20): 1 to 6, S, Eggman, face down. A card has
  only its left edge; the next card, or the end of the hand, closes it.
- **Digits** (8–13): 0 to 5, looked up through `0x8C0FD670`.
- **Cursor** (14), **end of the hand** (15), **ring** (16), **plus and
  minus** (17, 18), **gem** (19).

## Save icons

`MISCDATA/ICON.FNT` (544 bytes) is the save's icon: its 32-byte palette, then
the 512-byte bitmap. Both match the archive's save icon byte for byte.
