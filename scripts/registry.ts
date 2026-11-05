/**
 * The game registry, content/games.json, for the importers and checks: every
 * game the archive has anything of, keyed by a stable id that its content
 * refers to (`"gameId"`), its page's route and its folders use.
 *
 *   "jet-set-radio": {
 *     "name": "Jet Set Radio",
 *     "aliases": ["Jet Grind Radio", "De La Jet Set Radio"]
 *   }
 *
 * `name` is the game's name in the archive; `en` or `ja` give its other
 * release's title when they differ; `aliases` are other names it goes by in
 * sources (save collections, other releases), so an importer can find it.
 * Renaming a game is a change to its `name` only: its id, route and folders
 * stay. Run by Node directly: keep the imports relative with their .ts
 * extension.
 */
import fs from 'node:fs'
import path from 'node:path'
import { slug } from '../src/lib/slug.ts'

const ROOT = path.resolve(import.meta.dirname, '..')
export const REGISTRY = path.join(ROOT, 'content/games.json')

export interface GameEntry {
	name: string
	en?: string
	ja?: string
	cover?: string
	aliases?: string[]
}

export type Registry = Record<string, GameEntry>

export const loadRegistry = (): Registry =>
	JSON.parse(fs.readFileSync(REGISTRY, 'utf8'))

/** Written sorted by id, so diffs stay small. */
export function saveRegistry(registry: Registry) {
	const sorted = Object.fromEntries(
		Object.entries(registry).sort(([a], [b]) => a.localeCompare(b))
	)
	fs.writeFileSync(REGISTRY, JSON.stringify(sorted, null, '\t') + '\n')
}

/** Names that differ only in case, spacing or punctuation ("vs."/"vs") match. */
const loose = (s: string) => slug(s).replace(/[^a-z0-9]/g, '')

/** Every name a game answers to: its id, name, other titles and aliases. */
const namesOf = (id: string, g: GameEntry) =>
	[id, g.name, g.en, g.ja, ...(g.aliases ?? [])].filter((n): n is string => !!n)

/** The id of the game a name (or id) refers to, if the registry has it. */
export function findGame(registry: Registry, name: string): string | undefined {
	const key = loose(name)
	return Object.entries(registry).find(([id, g]) =>
		namesOf(id, g).some(n => loose(n) === key)
	)?.[0]
}

/**
 * The id for a name, adding the game to the registry (and saying so) when
 * it's new. A new game's id is its name's slug.
 */
export function gameIdFor(
	registry: Registry,
	name: string,
	{ dryRun = false } = {}
): string {
	const found = findGame(registry, name)
	if (found) return found
	const id = slug(name)
	if (registry[id])
		throw new Error(
			`"${name}" isn't in the registry, but its id "${id}" is taken by "${registry[id].name}"`
		)
	registry[id] = { name }
	if (!dryRun) saveRegistry(registry)
	console.log(`  new game  ${id}: "${name}" (added to content/games.json)`)
	return id
}

/** What's wrong with the registry, or nothing. */
export function registryProblems(registry: Registry): string[] {
	const out: string[] = []
	const seen = new Map<string, string>()
	for (const [id, g] of Object.entries(registry)) {
		if (id !== slug(id)) out.push(`games.json: "${id}" is not a slug`)
		if (!g.name) out.push(`games.json: "${id}" has no "name"`)
		if (g.en && g.ja)
			out.push(
				`games.json: "${id}": set en or ja, not both (name is the other)`
			)
		for (const n of namesOf(id, g)) {
			const key = loose(n)
			const other = seen.get(key)
			if (other && other !== id)
				out.push(`games.json: "${n}" names both "${other}" and "${id}"`)
			seen.set(key, id)
		}
	}
	return out
}
