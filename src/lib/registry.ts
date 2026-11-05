import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { z } from 'zod'

/**
 * The game registry, content/games.json: every game the archive has anything
 * of, keyed by the stable id its content refers to (`gameId`) and its page
 * and folders use. See scripts/registry.ts for how importers add to it.
 */
const schema = z.record(
	z.string(),
	z.strictObject({
		/** The title the site shows, in English when the game has one. */
		name: z.string(),
		/**
		 * Its Japanese release's title, romanized, when it differs from `name`
		 * ("Project Justice" → "Moero! Justice Gakuen"); shown beneath it.
		 */
		ja: z.string().min(1).optional(),
		/**
		 * Its publisher and the year it first came out: the game's, so its
		 * screens, sprites and save icons don't repeat them.
		 */
		publisher: z.string().min(1).optional(),
		year: z.number().int().min(1998).optional(),
		/** Id of the screen its card shows. */
		cover: z.string().optional(),
		/**
		 * Its other names: titles in other regions or on other platforms, names
		 * sources use ("Jet Grind Radio"). The search finds the game by them.
		 */
		aliases: z.array(z.string()).optional()
	})
)

export type GameEntry = z.infer<typeof schema>[string]

let cache: Record<string, GameEntry> | undefined

export function getRegistry() {
	cache ??= schema.parse(
		JSON.parse(
			fs.readFileSync(path.join(process.cwd(), 'content/games.json'), 'utf8')
		)
	)
	return cache
}

/** A game's entry; content always names a game that's in the registry. */
export function getGameEntry(id: string): GameEntry {
	const entry = getRegistry()[id]
	if (!entry) throw new Error(`content/games.json: no game "${id}"`)
	return entry
}
