/**
 * Checks the game registry, the sprites and the save icons, which no other
 * step reads closely enough to catch a mistake in them:
 *
 *   pnpm content:check
 *
 * - content/games.json, the registry (see scripts/registry.ts), is sound,
 *   every game in it has some content, and every screen, sprite and save icon
 *   names a game that's in it (`gameId`), leaving the game's publisher and
 *   year to it.
 * - Every content/sprites/<game id>/*.json is well formed (see
 *   scripts/sprites.ts), sits in its game's folder, and is drawn only on
 *   screens that exist.
 * - Every content/save-icons/<game id>/*.json is well formed (see
 *   scripts/save-icons.ts), sits in its game's folder, and is stored once.
 * - Every content/games/<game id>.md is a registered game's notes.
 */
import fs from 'node:fs'
import path from 'node:path'
import { loadRegistry, registryProblems } from './registry.ts'
import {
	SAVE_ICONS_DIR,
	type SaveIcon,
	saveIconProblems
} from './save-icons.ts'
import {
	ICONS_DIR,
	SPRITES_DIR,
	type Sprite,
	spriteProblems
} from './sprites.ts'

const jsonFiles = (dir: string) =>
	fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.json')) : []

const registry = loadRegistry()
const problems: string[] = [...registryProblems(registry)]
const used = new Set<string>()
const known = (where: string, entry: { gameId: string }) => {
	const { gameId } = entry
	used.add(gameId)
	if (!registry[gameId])
		problems.push(`${where}: no game "${gameId}" in content/games.json`)
	for (const key of ['publisher', 'year'])
		if (key in entry)
			problems.push(
				`${where}: "${key}" is the game's; it goes in content/games.json`
			)
}

const screens = new Set<string>()
for (const file of jsonFiles(ICONS_DIR)) {
	screens.add(file.replace(/\.json$/, ''))
	known(
		`icons/${file}`,
		JSON.parse(fs.readFileSync(path.join(ICONS_DIR, file), 'utf8'))
	)
}

/** Each JSON in content/<root>/<game id>/, with where it is. */
function* inGameFolders<T>(root: string, label: string) {
	if (!fs.existsSync(root)) return
	for (const dir of fs.readdirSync(root)) {
		const full = path.join(root, dir)
		if (!fs.statSync(full).isDirectory()) {
			if (dir !== '.gitkeep')
				problems.push(`${label}/${dir}: not in a game's folder`)
			continue
		}
		for (const file of jsonFiles(full)) {
			const where = `${label}/${dir}/${file}`
			let entry: T
			try {
				entry = JSON.parse(fs.readFileSync(path.join(full, file), 'utf8'))
			} catch (err) {
				problems.push(`${where}: ${(err as Error).message}`)
				continue
			}
			yield { dir, where, entry }
		}
	}
}

let sprites = 0
for (const { dir, where, entry: s } of inGameFolders<Sprite>(
	SPRITES_DIR,
	'sprites'
)) {
	sprites++
	known(where, s)
	if (s.gameId && s.gameId !== dir)
		problems.push(`${where}: "${s.gameId}" belongs in sprites/${s.gameId}/`)
	for (const p of spriteProblems(s, screens)) problems.push(`${where}: ${p}`)
}

let saveIcons = 0
const saveHashes = new Map<string, string>()
for (const { dir, where, entry: s } of inGameFolders<SaveIcon>(
	SAVE_ICONS_DIR,
	'save-icons'
)) {
	saveIcons++
	known(where, s)
	if (s.gameId && s.gameId !== dir)
		problems.push(`${where}: "${s.gameId}" belongs in save-icons/${s.gameId}/`)
	const twin = saveHashes.get(s.hash)
	if (twin) problems.push(`${where}: same icon as ${twin}`)
	saveHashes.set(s.hash, where)
	for (const p of saveIconProblems(s)) problems.push(`${where}: ${p}`)
}

const notesDir = path.resolve(import.meta.dirname, '../content/games')
for (const file of fs.readdirSync(notesDir).filter(f => f.endsWith('.md')))
	if (!registry[file.replace(/\.md$/, '')])
		problems.push(`games/${file}: no game with this id in content/games.json`)

for (const id of Object.keys(registry))
	if (!used.has(id))
		problems.push(`games.json: "${id}" has no screens, sprites or save icons`)

for (const p of problems) console.error(`  fail  ${p}`)
console.log(
	`${Object.keys(registry).length} games, ${screens.size} screens, ${sprites} sprite${sprites === 1 ? '' : 's'}, ${saveIcons} save icon${saveIcons === 1 ? '' : 's'}: ${problems.length ? `${problems.length} problem${problems.length === 1 ? '' : 's'}` : 'ok'}`
)
if (problems.length) process.exitCode = 1
