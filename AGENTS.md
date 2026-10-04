<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## Project notes

- Every entry in `content/icons/*.json` is a 48x32 1-bit VMU screen (the
  schema in `src/lib/icons.ts` enforces it). Add art with `pnpm icons:import`;
  don't hand-write frames.
- `src/lib/pixels.ts` is run by Node directly from the importer: keep it free
  of imports and non-erasable TypeScript.
- The site is a static export (`output: 'export'`): every dynamic route needs
  `generateStaticParams` and route handlers need `dynamic = 'force-static'`.
- `gifenc` is CommonJS; import it dynamically in client code only.
- The owner makes the commits in this repo; don't add AI co-author trailers.
