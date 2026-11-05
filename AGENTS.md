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
  sprite: `content/sprites/<game slug>/*.json` at its own size, imported with
  `"sprite": true` (see `scripts/sprites.ts`). They're kept for preservation
  and `pnpm content:check` validates them. The site only shows them: the build
  packs each game's into `/sprites/<game slug>.png` (`src/lib/sprites.ts`),
  shown in the Sprites and Fonts tabs of its page; that sheet is never committed.
- Save icons (the colour icon the Dreamcast's file menu shows for a save) are
  `content/save-icons/<game slug>/*.json`, 32x32 at 4 bits a pixel with their
  palette (see `scripts/save-icons.ts`), one per distinct icon. Import them
  from dumped saves with `pnpm saveicons:import <folder>` (`.VMS`/`.VMI` and a
  `save-icons.json`, see `scripts/import-saves.ts`); they're shown on
  `/save-icons` and beside the title of their game's page, never inverted in dark mode.
- Findings about a game (format, timing, unused screens) go in its notes,
  `content/games/<game slug>.md`; its README in `tools/disc-extraction/<game>/`
  only names the dump and how to run the scripts.
- A game's English/Japanese (romanized) titles and card cover live in
  `content/games.json`, keyed by the icons' `game` (see `src/lib/games.ts`).
  The site has one page per game, `/games/<game slug>`, which shows its notes.
- `src/lib/pixels.ts` is run by Node directly from the importer: keep it free
  of imports and non-erasable TypeScript.
- The site is a static export (`output: 'export'`): every dynamic route needs
  `generateStaticParams` and route handlers need `dynamic = 'force-static'`.
- `gifenc` is CommonJS; import it dynamically in client code only.
- The owner makes the commits in this repo; don't add AI co-author trailers.
