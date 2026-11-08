<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Project notes

- Every entry in `content/icons/*.json` is a 48x32 1-bit VMU screen (the
  schema in `src/lib/icons.ts` enforces it). An entry stores its `frames`, or a
  `scroll`: one wider strip that `getIcons()` cuts into 48x32 frames on load,
  so code after that only sees frames. Add art with `pnpm icons:import`;
  don't hand-write frames.
- Smaller art a game draws onto part of a screen (digits, buttons) is a
  sprite: `content/sprites/<game id>/*.json` at its own size, imported with
  `"sprite": true` (see `scripts/sprites.ts`). They're kept for preservation
  and `pnpm content:check` validates them. The site only shows them: the build
  packs each game's into `/sprites/<game id>.png` (`src/lib/sprites.ts`),
  shown in the Sprites and Fonts tabs of its page; that sheet is never committed.
- Save icons (the colour icon the Dreamcast's file menu shows for a save) are
  `content/save-icons/<game id>/*.json`, 32x32 at 4 bits a pixel with their
  palette (see `scripts/save-icons.ts`), one per distinct icon. Import them
  from dumped saves with `pnpm saveicons:import <folder>` (`.VMS`/`.VMI` and a
  `save-icons.json`, see `scripts/import-saves.ts`); they're shown on
  `/save-icons` and beside the title of their game's page, never inverted in dark mode.
- Findings about a game (format, timing, unused screens) go in its notes,
  `content/games/<game id>.md`; its README in `tools/disc-extraction/<game>/`
  only names the dump and how to run the scripts.
- `content/games.json` is the game registry: every game under a stable id,
  with its name (the title shown, English when there is one), `ja` (the
  Japanese title, shown beneath it), publisher, year, aliases (its other
  names, which the search finds it by: "Jet Grind Radio") and card cover (see
  `scripts/registry.ts`). A piece's `region` (`ntsc-j`, `ntsc-u` or `pal`,
  from `src/lib/regions.ts`) is set only when it's in that region's release
  alone: `ntsc-j` when it's Japan's only, which mostly means it has Japanese
  text; `ntsc-u` or `pal` only with evidence the other release lacks it.
  Without one, a piece is taken to be in every release, whichever disc it
  came from. Content refers to a
  game by that id (`"gameId"`), never by name, and doesn't repeat its
  publisher or year (`pnpm content:check` fails if it does); a sidecar's
  `"publisher"`/`"year"` are written to the registry. Folders and the page route
  (`/games/<game id>`, which shows its notes) use it too. Importers resolve a
  sidecar's `"game"` name or alias through the registry.
- A `content/changelog.json` entry's body is one or two short sentences:
  what arrived and anything notable about it. Don't list the screens or
  sprites by name; the game's page shows them and its notes explain them.
- `src/lib/pixels.ts` is run by Node directly from the importer: keep it free
  of imports and non-erasable TypeScript.
- The site is a static export (`output: 'export'`): every dynamic route needs
  `generateStaticParams` and route handlers need `dynamic = 'force-static'`.
- `gifenc` is CommonJS; import it dynamically in client code only.
- The owner makes the commits in this repo; don't add AI co-author trailers.
