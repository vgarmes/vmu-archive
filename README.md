# VMU Archive

A searchable archive of Dreamcast VMU screen art — every piece is a 48×32,
1-bit VMU LCD screen — with downloads as PNG, SVG or GIF.

Browse it at **[vmu-archive.vercel.app](https://vmu-archive.vercel.app)**.

## Contributing

Missing a game?
[Request it](https://github.com/vgarmes/vmu-archive/issues/new?template=request-game.yml).
New screens are extracted from the game's disc, with the order and timing its
own code uses; see [Adding art](#adding-art).

## Development

[Next.js](https://nextjs.org) (App Router, static export), React, Tailwind,
[Fuse.js](https://www.fusejs.io) for search and [Base UI](https://base-ui.com)
for the download menu.

```sh
pnpm install
pnpm dev            # http://localhost:3000 (pass --port to change it)
pnpm build          # static site in out/
pnpm typecheck
```

## Adding art

Art comes from disc dumps, through a per-game folder in
[`tools/disc-extraction/`](tools/disc-extraction/) (its README has the method).
What each game's scripts found is written up in its notes,
`content/games/<game id>.md`, shown on the game's page.

Every game is in `content/games.json`, the registry, under a stable id that
its screens, sprites and save icons refer to (`"gameId"`) and that gives its
URL, `/games/<game id>`, and folders. `name` is its name in the archive;
`aliases` are other names sources use for it, so the importers can find it.
Set `en` when the name is the Japanese one, `ja` when it's the English one.
`cover` picks the screen its card shows (an icon id); by default that's its
title screen, else its logo. A sidecar's `"game"` can be a name, an alias or
an id; a game the registry doesn't know yet is added to it with its name's
slug as id. Renaming a game only changes its `name`.

1. Run the game's scripts. They write one `.png` per piece, 48 pixels wide and
   32 tall per frame with frames stacked top to bottom (dark pixels are lit),
   and a sidecar with the same name (`title-screen.png` → `title-screen.json`):
   ```json
   {
     "title": "Title screen",
     "game": "Power Stone 2",
     "publisher": "Capcom",
     "year": 2000,
     "tags": ["logo"],
     "frameDelayMs": 133
   }
   ```
   Set `"region"` only on a screen that belongs to one release, `"unused"` on
   one the game's code never shows. For frames that last different times, give
   `"frameDelaysMs"` instead: one delay per frame. Back-to-back copies of a
   frame are merged into one frame held for their combined delay.
2. Run `pnpm icons:import <folder>` (`--dry-run` to preview). Each piece
   becomes `content/icons/<game>-<title>.json` (a readable id, chosen once and
   kept if the title changes; pieces with the same title get -2, -3… in import
   order). Pixel-identical art is skipped.
3. Commit the new JSON files.

### Scrolling banners

Some games slide one wide image through the screen instead of showing frames
(Sakura Taisen 3's attack names). Import the image as it is, 32 pixels tall and
as wide as the art, with the window's movement in the sidecar:

```json
{ "title": "Gigantesque ciseau", "scroll": { "stepPx": 1, "delayMs": 17 } }
```

`stepPx` is how far the window moves per update and `delayMs` how often. The
entry stores the strip once; the site cuts it into 48×32 frames when it loads,
entering from the right edge and leaving past the left one, and rests on the
frame where the strip starts. Downloads give the strip itself (or the
animation, as a GIF or an animated SVG), never its frames one by one.

Art that moves down the screen instead, like the course of Power Stone Mini's
Falcon game, is a strip 48 pixels wide and as tall as the art, with
`"direction": "down"` in its `scroll`. The window climbs it from the bottom: the
art enters from the top edge, and the entry rests on the strip's bottom screen.

### Pictures in a game's notes

A game's notes (`content/games/<game id>.md`) can show pictures that explain
something but aren't archive entries, like a sequence rebuilt from the code. Put
them in `public/notes/<game id>/` at native size, near-black on transparent
like the thumbnails, and link them relative to the notes file:

```md
![Falcon's sequence](../../public/notes/power-stone/falcon.gif 'Falcon')
```

The site serves them from `/notes/…`, shows them 4× without smoothing, side by
side, and inverts them in dark mode; on GitHub the relative link works as is.

### Animations and fixing existing art

To change a piece that's already in the archive (swap one made from a
screenshot for the disc's version, or add the frames it was missing), import
the **full** art with a sidecar naming the entry to replace:

```json
{ "replaces": "crazy-taxi-title-screen", "frameDelayMs": 400 }
```

The id (and so the URL), added date and unchanged metadata are kept.

## Posting an update

Add an entry to the top of `content/changelog.json`; it shows on
[/changelog](https://vmu-archive.vercel.app/changelog):

```json
{
  "date": "2026-11-01",
  "title": "Carrier",
  "body": "The title screen from Jaleco's survival horror Carrier."
}
```

`body` is optional. Entries are sorted by date, and entries on the same date
show under one heading, newest first (so add yours at the top).

## How it works

| Piece                                           | Where                             |
| ----------------------------------------------- | --------------------------------- |
| Frame encoding, SVG / RGBA / C export, trimming | `src/lib/pixels.ts`               |
| Reading + validating entries at build time      | `src/lib/icons.ts`                |
| Games: titles, covers, notes (Markdown → HTML)  | `src/lib/games.ts`                |
| Native-size PNG thumbnails                      | `src/app/thumbs/[file]/route.ts`  |
| Home: game grid and title search                | `src/components/GameIndex.tsx`    |
| Game page: notes, screen search and grid        | `src/app/games/[slug]/page.tsx`   |
| Screen grid (batches of 60 as you scroll)       | `src/components/IconGrid.tsx`     |
| Preview, trim option, download menu (Base UI)   | `src/components/SpriteDrawer.tsx` |
| Importer                                        | `scripts/import.ts`               |

Everything is prerendered by `next build` into `out/`; downloads are generated
in the browser from the frame data.

## License

The code is [MIT](LICENSE). The VMU art belongs to its publishers and rights
holders (Sega and others) and is collected here for preservation and
reference, not for commercial use. If you hold the rights to a piece and want
it removed, [open an issue](https://github.com/vgarmes/vmu-archive/issues).
