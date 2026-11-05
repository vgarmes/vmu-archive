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
		/** The game's name in the archive. */
		name: z.string(),
		/**
		 * The English release's title, when the name is the Japanese one
		 * ("Berserk: Millennium Falcon-hen…" → "Sword of the Berserk…").
		 */
		en: z.string().optional(),
		/**
		 * The Japanese release's title, romanized, when the name is the English
		 * one ("Project Justice" → "Moero! Justice Gakuen").
		 */
		ja: z.string().optional(),
		/**
		 * Its publisher and the year it first came out: the game's, so its
		 * screens, sprites and save icons don't repeat them.
		 */
		publisher: z.string().min(1).optional(),
		year: z.number().int().min(1998).optional(),
		/** Id of the screen its card shows. */
		cover: z.string().optional(),
		/** Other names it goes by in sources, for the importers. */
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
