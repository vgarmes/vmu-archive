/**
 * Checks the sprites, which the site never reads, so nothing else would catch
 * a mistake in them:
 *
 *   pnpm content:check
 *
 * Every content/sprites/<game slug>/*.json is well formed (see
 * scripts/sprites.ts), sits in its game's folder, and is drawn only on screens
 * that exist.
 */
import fs from 'node:fs'
import path from 'node:path'
import { slug } from '../src/lib/slug.ts'
import {
	ICONS_DIR,
	SPRITES_DIR,
	type Sprite,
	spriteProblems
} from './sprites.ts'

const jsonFiles = (dir: string) =>
	fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.json')) : []

const problems: string[] = []
const screens = new Set<string>()
for (const file of jsonFiles(ICONS_DIR)) {
	screens.add(file.replace(/\.json$/, ''))
}

let sprites = 0
if (fs.existsSync(SPRITES_DIR))
	for (const dir of fs.readdirSync(SPRITES_DIR)) {
		const full = path.join(SPRITES_DIR, dir)
		if (!fs.statSync(full).isDirectory()) {
			if (dir !== '.gitkeep')
				problems.push(`sprites/${dir}: not in a game's folder`)
			continue
		}
		for (const file of jsonFiles(full)) {
			const where = `sprites/${dir}/${file}`
			let s: Sprite
			try {
				s = JSON.parse(fs.readFileSync(path.join(full, file), 'utf8'))
			} catch (err) {
				problems.push(`${where}: ${(err as Error).message}`)
				continue
			}
			sprites++
			if (s.game && slug(s.game) !== dir)
				problems.push(
					`${where}: "${s.game}" belongs in sprites/${slug(s.game)}/`
				)
			for (const p of spriteProblems(s, screens))
				problems.push(`${where}: ${p}`)
		}
	}

for (const p of problems) console.error(`  fail  ${p}`)
console.log(
	`${sprites} sprite${sprites === 1 ? '' : 's'}: ${problems.length ? `${problems.length} problem${problems.length === 1 ? '' : 's'}` : 'ok'}`
)
if (problems.length) process.exitCode = 1
