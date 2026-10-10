# VMU Archive

A searchable archive of Dreamcast VMU screen art — every piece is a 48×32,
1-bit VMU LCD screen — with downloads as PNG, SVG, GIF or a C array.

Browse it at **[vmu-archive.vercel.app](https://vmu-archive.vercel.app)**.

## Contributing

Missing a game or a screen?
[Open an issue with a screenshot](https://github.com/vgarmes/vmu-archive/issues/new?template=submit-art.yml)
— an emulator capture or a photo of a real VMU is enough. If you'd rather add
it yourself, follow [Adding art](#adding-art) and open a pull request.

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

1. Drop files into `inbox/`:
   - `.png` — a 48×32 screen (dark pixels are lit). Stack frames vertically
     for animation (48×64 = 2 frames). Smaller art is trimmed and centred on
     the screen.
   - `.txt` — rows of `#` and spaces, frames separated by `---`.
2. Optionally add a sidecar with the same name (`sonic.png` → `sonic.json`):
   ```json
   {
     "title": "Chao Garden",
     "game": "Sonic Adventure",
     "publisher": "Sega",
     "year": 1998,
     "region": "JP",
     "tags": ["chao"],
     "invert": false,
     "frameDelayMs": 200
   }
   ```
3. Run `pnpm icons:import` (`--dry-run` to preview, `--keep` to leave the
   sources in place). Each piece becomes `content/icons/<game>-<title>.json`
   (a readable id, chosen once and kept if the title changes; pieces with
   the same title get -2, -3… in import order);
   sources move to `inbox/imported/`. Pixel-identical art is skipped.
4. Commit the new JSON files.

### Sprite sheets

For a PNG with many pieces, list the boxes in its sidecar and each one becomes
its own entry. Crops take the same fields as the sidecar and override it:

```json
{
  "publisher": "Sega",
  "crops": [
    {
      "x": 24,
      "y": 67,
      "w": 48,
      "h": 32,
      "title": "Sonic",
      "game": "Sonic Adventure"
    }
  ]
}
```

A 48×32 box is used as is. Any other box is trimmed to its lit pixels and
centred on a 48×32 screen, so boxes can be loose. Re-running a sheet is safe;
the sheet stays in `inbox/` until every crop imports cleanly.

### Animations and fixing existing art

To add frames to a piece that's already in the archive, import the **full**
animation with a sidecar naming the entry to replace:

```json
{ "replaces": "crazy-taxi-title-screen", "frameDelayMs": 400 }
```

The id (and so the URL), added date and unchanged metadata are kept.

## How it works

| Piece                                              | Where                                |
| -------------------------------------------------- | ------------------------------------ |
| Frame encoding, SVG / RGBA / C export, trimming    | `src/lib/pixels.ts`                  |
| Reading + validating entries at build time         | `src/lib/icons.ts`                   |
| Search index (metadata only, fetched once)         | `src/app/search-index.json/route.ts` |
| Native-size PNG thumbnails                         | `src/app/thumbs/[file]/route.ts`     |
| Search, filter, grid (batches of 60 as you scroll) | `src/components/Archive.tsx`         |
| Preview, trim option, download menu (Base UI)      | `src/components/IconDetail.tsx`      |
| Importer                                           | `scripts/import.ts`                  |

Everything is prerendered by `next build` into `out/`; downloads are generated
in the browser from the frame data.

## License

The code is [MIT](LICENSE). The VMU art belongs to its publishers and rights
holders (Sega and others) and is collected here for preservation and
reference, not for commercial use. If you hold the rights to a piece and want
it removed, [open an issue](https://github.com/vgarmes/vmu-archive/issues).
