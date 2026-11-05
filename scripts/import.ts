/**
 * Turns screens extracted from a disc into entries in content/icons/.
 *
 *   pnpm icons:import <files or folders…>
 *     --dry-run   print what would be written
 *
 * The per-game scripts in tools/disc-extraction/ write the sources: a .png per
 * piece, 48 pixels wide and 32 tall per frame, frames stacked top to bottom
 * (48x64 = 2 frames). Dark pixels are lit.
 *
 * Metadata comes from a sidecar with the same basename (title-screen.png →
 * title-screen.json): { title, game, publisher, year, region, tags, unused,
 * frameDelayMs, frameDelaysMs, posterFrame, replaces }. "game" names the game
 * by its name, an alias or its id in content/games.json; the entry stores its
 * id ("gameId"), and a game the registry doesn't know yet is added to it.
 * "publisher" and "year" are the game's, so they go on its registry entry,
 * not the piece's (see `setGameDetails` in ./registry.ts).
 * "frameDelaysMs" gives
 * each frame its own delay, one per frame, for frames that last different
 * times. Back-to-back copies of a frame are merged into one frame held for
 * their combined delay, so a pose held by repeating it is stored once, with a
 * longer delay. "posterFrame" is the frame (from 0) the grid shows at rest, for
 * animations whose first frame is a poor thumbnail. Without a sidecar, the
 * filename is the title. Pixel-identical art already in the archive is skipped.
 *
 * To change an existing piece — e.g. add the missing frames of an animation —
 * import the full art with `"replaces": "<existing id>"` in its sidecar. The
 * id, added date and unchanged metadata carry over.
 *
 * A banner the game scrolls through the screen is imported as one strip: a
 * .png 32 pixels tall and as wide as the art, with
 * `"scroll": { "stepPx": 1, "delayMs": 17 }` in its sidecar (how far the
 * window moves per update, and how often). It's stored once and cut into
 * frames when the site loads it; see `scrollFrames` in src/lib/pixels.ts.
 * Art that moves down the screen instead (a vertical scroller's course) is a
 * .png 48 pixels wide and as tall as the art, with `"direction": "down"` added
 * to its "scroll": the window climbs it from the bottom.
 *
 * A sprite — art the game draws onto part of a screen, like the digits of a
 * counter — is imported at its own size with `"sprite": true` in its sidecar.
 * It goes to content/sprites/<game id>/ for preservation; the site never
 * shows it (see scripts/sprites.ts). Its sidecar can also say where it came
 * from, `"source": { "file": "/LCDIMG.BIN", "entry": 11 }`, and where the game
 * draws it, `"drawnAt": [{ "screen": "<icon id>", "x": 30, "y": 2 }]`. A font
 * is one sprite, its characters stacked in the game's order, with their sizes
 * in `"glyphs": { "height": 8, "width": 4 }` (see src/lib/glyphs.ts); its
 * `"drawnAt"` entries name the character with `"glyph"`. The Sprites and Fonts tabs
 * leaves out whatever is drawn on a screen, since the screen shows it.
 */
import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import pngjs from 'pngjs'
import { DEFAULT_FRAME_DELAY_MS, encodeFrame } from '../src/lib/pixels.ts'
import { isRegion, REGIONS, type Region } from '../src/lib/regions.ts'
import { slug } from '../src/lib/slug.ts'
import {
	gameIdFor,
	loadRegistry,
	saveRegistry,
	setGameDetails
} from './registry.ts'
import {
	ICONS_DIR,
	SPRITES_DIR,
	type Sprite,
	spriteHash,
	spriteProblems
} from './sprites.ts'

const ROOT = path.resolve(import.meta.dirname, '..')
const OUT_DIR = ICONS_DIR

const W = 48
const H = 32

interface Meta {
	title?: string
	/** The game's name, an alias or its id in content/games.json. */
	game?: string
	/** The game's, written to its entry in content/games.json. */
	publisher?: string
	/** The game's first release, written to its entry in content/games.json. */
	year?: number
	/** Only when the piece is in one region's release alone. */
	region?: Region
	tags?: string[]
	/** The game's code never shows this screen (checked in the code). */
	unused?: boolean
	frameDelayMs?: number
	/** Delay of each frame, one per frame, when they differ. */
	frameDelaysMs?: number[]
	/** Frame (from 0) the grid shows when the animation isn't playing. */
	posterFrame?: number
	/** Id of an existing entry to replace (e.g. to add animation frames). */
	replaces?: string
	/** The art is a strip the window scrolls through, not stacked frames. */
	scroll?: { stepPx: number; delayMs: number; direction?: 'left' | 'down' }
	/** Art drawn onto part of a screen, kept at its own size in content/sprites/. */
	sprite?: boolean
	/** Sprites only: where on the disc it came from. */
	source?: Sprite['source']
	/** Sprites only: where the game draws it. */
	drawnAt?: Sprite['drawnAt']
	/** Sprites only: a font's character sizes. */
	glyphs?: Sprite['glyphs']
}

// ---------------------------------------------------------------- reading

/** Lit pixels (1) of each frame of a 48-wide stack of 32-tall screens, row-major. */
function readPng(buf: Buffer): number[][] {
	const img = pngjs.PNG.sync.read(buf)
	if (img.width !== W || img.height === 0 || img.height % H !== 0)
		throw new Error(
			`is ${img.width}x${img.height}; expected ${W} wide and a multiple of ${H} tall`
		)
	// A dark, opaque pixel is a lit dot.
	const isLit = (x: number, y: number) => {
		const i = (y * img.width + x) * 4
		const [r, g, b, a] = img.data.subarray(i, i + 4)
		return a >= 128 && 0.299 * r + 0.587 * g + 0.114 * b < 128
	}
	const frames: number[][] = []
	for (let f = 0; f < img.height / H; f++) {
		const bits: number[] = []
		for (let y = 0; y < H; y++)
			for (let x = 0; x < W; x++) bits.push(isLit(x, f * H + y) ? 1 : 0)
		frames.push(bits)
	}
	return frames
}

/**
 * A strip for a scroll, encoded like a frame: 32 tall and at least a screen
 * wide, or for a "down" scroll 48 wide and at least a screen tall.
 */
function readStrip(
	buf: Buffer,
	down: boolean
): { width: number; height: number; strip: string } {
	const img = pngjs.PNG.sync.read(buf)
	if (
		down ? img.width !== W || img.height < H : img.height !== H || img.width < W
	)
		throw new Error(
			down
				? `is ${img.width}x${img.height}; a "down" scroll strip is ${W} wide and at least ${H} tall`
				: `is ${img.width}x${img.height}; a scroll strip is ${H} tall and at least ${W} wide`
		)
	const bits: number[] = []
	for (let y = 0; y < img.height; y++)
		for (let x = 0; x < img.width; x++) {
			const i = (y * img.width + x) * 4
			const [r, g, b, a] = img.data.subarray(i, i + 4)
			bits.push(a >= 128 && 0.299 * r + 0.587 * g + 0.114 * b < 128 ? 1 : 0)
		}
	return { width: img.width, height: img.height, strip: encodeFrame(bits, 1) }
}

/** One frame at the PNG's own size, for a sprite. */
function readSprite(buf: Buffer) {
	const img = pngjs.PNG.sync.read(buf)
	const bits: number[] = []
	for (let y = 0; y < img.height; y++)
		for (let x = 0; x < img.width; x++) {
			const i = (y * img.width + x) * 4
			const [r, g, b, a] = img.data.subarray(i, i + 4)
			bits.push(a >= 128 && 0.299 * r + 0.587 * g + 0.114 * b < 128 ? 1 : 0)
		}
	return { width: img.width, height: img.height, frame: encodeFrame(bits, 1) }
}

/** Every sprite's hash, as "<game id>/<id>.json", to skip duplicates. */
function existingSprites() {
	const hashes = new Map<string, string>()
	if (!fs.existsSync(SPRITES_DIR)) return hashes
	for (const dir of fs.readdirSync(SPRITES_DIR)) {
		const full = path.join(SPRITES_DIR, dir)
		if (!fs.statSync(full).isDirectory()) continue
		for (const file of fs.readdirSync(full).filter(f => f.endsWith('.json'))) {
			const { hash } = JSON.parse(
				fs.readFileSync(path.join(full, file), 'utf8')
			)
			if (hash) hashes.set(hash, `${dir}/${file}`)
		}
	}
	return hashes
}

// ---------------------------------------------------------------- main

/**
 * A readable id from the game and title ("ikaruga-title-screen"), without
 * repeating the game when the title already starts with it, "-sprite" for
 * entries tagged as small sprites, and -2, -3… when it's taken, so pieces
 * with the same title keep their import order. Chosen once: editing a title later keeps the id (and so the
 * thumbnail URL and ?screen= links).
 */
function newId(
	gameId: string,
	title: string,
	tags: string[],
	taken: Set<string>
) {
	const g = gameId
	const t = slug(title)
	const base = (
		(t === g || t.startsWith(`${g}-`) ? t : `${g}-${t}`) +
		(tags.includes('sprite') ? '-sprite' : '')
	)
		.slice(0, 80)
		.replace(/-$/, '')
	let id = base
	for (let n = 2; taken.has(id); n++) id = `${base}-${n}`
	taken.add(id)
	return id
}

/**
 * Back-to-back copies of a frame become one frame shown for their combined
 * delay: an animation that holds a pose by repeating it is stored with the
 * pose once. A frame that comes back later (A B A) stays, since that's motion,
 * not a hold. `from` is the index each merged frame started at.
 */
function mergeHolds(frames: string[], delays: number[]) {
	const out = {
		frames: [] as string[],
		delays: [] as number[],
		from: [] as number[]
	}
	frames.forEach((hex, i) => {
		const last = out.frames.length - 1
		if (last >= 0 && out.frames[last] === hex) out.delays[last] += delays[i]
		else {
			out.frames.push(hex)
			out.delays.push(delays[i])
			out.from.push(i)
		}
	})
	return out
}

/** Kept identical to earlier versions so existing entries still match. */
const hashOf = (frames: string[]) =>
	createHash('sha1')
		.update([W, H, 1, '', frames.join(',')].join('|'))
		.digest('hex')

function existingHashes() {
	const hashes = new Map<string, string>()
	for (const file of fs.readdirSync(OUT_DIR).filter(f => f.endsWith('.json'))) {
		const { hash } = JSON.parse(
			fs.readFileSync(path.join(OUT_DIR, file), 'utf8')
		)
		if (hash) hashes.set(hash, file)
	}
	return hashes
}

function collect(inputs: string[]): string[] {
	return inputs.flatMap(input => {
		const stat = fs.statSync(input)
		if (!stat.isDirectory()) return [input]
		return fs
			.readdirSync(input)
			.filter(f => path.extname(f).toLowerCase() === '.png')
			.map(f => path.join(input, f))
	})
}

function main() {
	const args = process.argv.slice(2)
	const dryRun = args.includes('--dry-run')
	// Sidecars name their game by name, alias or id; a new one joins the registry.
	const registry = loadRegistry()
	const gameIdOf = (name: string) => gameIdFor(registry, name, { dryRun })
	// A sidecar's publisher and year go on its game in the registry.
	const recordDetails = (gameId: string, meta: Meta) => {
		const changed = setGameDetails(registry, gameId, meta)
		if (changed && !dryRun) saveRegistry(registry)
	}
	const inputs = args.filter(a => !a.startsWith('--'))
	if (!inputs.length) {
		console.log(
			'Usage: pnpm icons:import <files or folders…> [--dry-run]\nSources come from the scripts in tools/disc-extraction/.'
		)
		process.exitCode = 1
		return
	}
	const files = collect(inputs)
	if (!files.length) {
		console.log('Nothing to import: no .png files there.')
		return
	}

	fs.mkdirSync(OUT_DIR, { recursive: true })
	const hashes = existingHashes()
	const spriteHashes = existingSprites()
	const screenIds = new Set(
		fs
			.readdirSync(OUT_DIR)
			.filter(f => f.endsWith('.json'))
			.map(f => f.replace(/\.json$/, ''))
	)
	const taken = new Set(screenIds)
	let added = 0
	let updated = 0
	let skipped = 0
	let failed = 0

	for (const file of files) {
		const label = path.basename(file)
		const base = file.slice(0, -path.extname(file).length)
		const sidecar = fs.existsSync(`${base}.json`) ? `${base}.json` : null
		try {
			const meta: Meta = sidecar
				? JSON.parse(fs.readFileSync(sidecar, 'utf8'))
				: {}
			if (meta.region !== undefined && !isRegion(meta.region))
				throw new Error(
					`"region" ${JSON.stringify(meta.region)} is not one of ${REGIONS.join(', ')} (leave it out when the piece is in every release)`
				)

			// Replacing keeps the id (so URLs don't change), the added date and
			// any metadata the sidecar doesn't override.
			let prev: Record<string, unknown> = {}
			if (meta.replaces) {
				const prevFile = path.join(OUT_DIR, `${meta.replaces}.json`)
				if (!fs.existsSync(prevFile))
					throw new Error(`"replaces": no entry ${meta.replaces}.json`)
				prev = JSON.parse(fs.readFileSync(prevFile, 'utf8'))
			}
			const pick = <K extends keyof Meta>(k: K) =>
				meta[k] ?? (prev[k] as Meta[K] | undefined)
			const addedDate = () =>
				(prev.added as string | undefined) ??
				new Date().toISOString().slice(0, 10)

			if (meta.sprite) {
				const bad = (
					[
						'replaces',
						'scroll',
						'unused',
						'frameDelayMs',
						'frameDelaysMs',
						'posterFrame'
					] as const
				).filter(k => meta[k] !== undefined)
				if (bad.length)
					throw new Error(
						`a sprite doesn't take ${bad.map(k => `"${k}"`).join(', ')}`
					)
				const { width, height, frame } = readSprite(fs.readFileSync(file))
				const frames = [frame]
				const hash = spriteHash(width, height, frames)
				const dupe = spriteHashes.get(hash)
				if (dupe) {
					console.log(`  skip  ${label}: same pixels as sprites/${dupe}`)
					skipped++
					continue
				}
				const title = meta.title || path.basename(base)
				const gameId = gameIdOf(meta.game || title)
				const dir = path.join(SPRITES_DIR, gameId)
				const takenHere = new Set(
					fs.existsSync(dir)
						? fs.readdirSync(dir).map(f => f.replace(/\.json$/, ''))
						: []
				)
				let id = slug(title)
				for (let n = 2; takenHere.has(id); n++) id = `${slug(title)}-${n}`
				const sprite: Sprite = {
					title,
					gameId,
					region: meta.region,
					width,
					height,
					bpp: 1,
					frames,
					glyphs: meta.glyphs,
					source: meta.source,
					drawnAt: meta.drawnAt,
					tags: meta.tags ?? [],
					hash,
					added: new Date().toISOString().slice(0, 10)
				}
				const problems = spriteProblems(sprite, screenIds)
				if (problems.length) throw new Error(problems.join('; '))
				recordDetails(gameId, meta)
				if (!dryRun) {
					fs.mkdirSync(dir, { recursive: true })
					fs.writeFileSync(
						path.join(dir, `${id}.json`),
						JSON.stringify(sprite, null, '\t') + '\n'
					)
				}
				spriteHashes.set(hash, `${gameId}/${id}.json`)
				console.log(
					`  add   ${label} → sprites/${gameId}/${id}.json (sprite, ${width}x${height})`
				)
				added++
				continue
			}

			if (meta.scroll) {
				const { stepPx, delayMs, direction } = meta.scroll
				if (![stepPx, delayMs].every(v => Number.isInteger(v) && v > 0))
					throw new Error('"scroll" needs whole, positive stepPx and delayMs')
				if (
					direction !== undefined &&
					direction !== 'left' &&
					direction !== 'down'
				)
					throw new Error(
						'"scroll.direction" is "left" (the default) or "down"'
					)
				if (meta.frameDelayMs !== undefined || meta.frameDelaysMs !== undefined)
					throw new Error('a scroll times itself with scroll.delayMs')
				const down = direction === 'down'
				const { width, height, strip } = readStrip(fs.readFileSync(file), down)
				// Sideways strips keep the hash they always had.
				const hash = createHash('sha1')
					.update(
						(down
							? ['scroll', 'down', width, height, 1, stepPx, strip]
							: ['scroll', width, H, 1, stepPx, strip]
						).join('|')
					)
					.digest('hex')
				const dupe = hashes.get(hash)
				if (dupe && dupe !== `${meta.replaces}.json`) {
					console.log(`  skip  ${label}: same strip as ${dupe}`)
					skipped++
					continue
				}
				if (meta.replaces) hashes.delete(prev.hash as string)
				const title = pick('title') || path.basename(base)
				const gameId = meta.game
					? gameIdOf(meta.game)
					: ((prev.gameId as string | undefined) ?? gameIdOf(title))
				const id =
					meta.replaces ?? newId(gameId, title, pick('tags') ?? [], taken)
				const entry = {
					title,
					gameId,
					region: pick('region'),
					width: W,
					height: H,
					bpp: 1,
					scroll: down
						? { width, height, direction, stepPx, delayMs, strip }
						: { width, stepPx, delayMs, strip },
					posterFrame: meta.posterFrame,
					tags: pick('tags') ?? [],
					unused: pick('unused') || undefined,
					hash,
					added: addedDate()
				}
				recordDetails(gameId, meta)
				if (!dryRun)
					fs.writeFileSync(
						path.join(OUT_DIR, `${id}.json`),
						JSON.stringify(entry, null, '\t') + '\n'
					)
				hashes.set(hash, `${id}.json`)
				const frames = Math.ceil(
					down ? (height + H) / stepPx : (width + W) / stepPx
				)
				console.log(
					`  ${meta.replaces ? 'update' : 'add  '} ${label} → ${id}.json (scroll${down ? ' down' : ''}, ${down ? height : width}px strip, ${frames} frames)`
				)
				if (meta.replaces) updated++
				else added++
				continue
			}

			const read = readPng(fs.readFileSync(file)).map(f => encodeFrame(f, 1))

			// Timing: the new art's, else the replaced entry's while it still
			// fits.
			const ownTiming =
				meta.frameDelayMs !== undefined || meta.frameDelaysMs !== undefined
			const frameDelayMs = ownTiming
				? meta.frameDelayMs
				: (prev.frameDelayMs as number | undefined)
			const frameDelaysMs = ownTiming
				? meta.frameDelaysMs
				: (prev.frameDelaysMs as number[] | undefined)
			if (frameDelaysMs && frameDelayMs !== undefined)
				throw new Error('set "frameDelayMs" or "frameDelaysMs", not both')
			if (frameDelaysMs) {
				if (frameDelaysMs.length !== read.length) {
					if (!ownTiming)
						throw new Error(
							`the replaced entry has ${frameDelaysMs.length} frame delays but this art has ${read.length} frames; set "frameDelaysMs" or "frameDelayMs"`
						)
					throw new Error(
						`"frameDelaysMs" has ${frameDelaysMs.length} delays for ${read.length} frames`
					)
				}
				if (!frameDelaysMs.every(d => Number.isInteger(d) && d > 0))
					throw new Error('"frameDelaysMs" must be whole milliseconds above 0')
			}

			// A sidecar's poster frame counts the frames as read, before merging.
			const ownPoster = meta.posterFrame
			if (
				ownPoster !== undefined &&
				(!Number.isInteger(ownPoster) ||
					ownPoster < 0 ||
					ownPoster >= read.length)
			)
				throw new Error(
					`"posterFrame": ${ownPoster} is not one of its ${read.length} frames (0-${read.length - 1})`
				)

			const merged = mergeHolds(
				read,
				frameDelaysMs ?? read.map(() => frameDelayMs ?? DEFAULT_FRAME_DELAY_MS)
			)
			const frames = merged.frames
			const delays = merged.delays
			// One delay for all is stored as frameDelayMs; left unset if it was.
			const even = delays.every(d => d === delays[0])
			const timing =
				frames.length < 2
					? {}
					: even
						? {
								frameDelayMs:
									frameDelaysMs || merged.from.length !== read.length
										? delays[0]
										: frameDelayMs
							}
						: { frameDelaysMs: delays }

			const posterFrame =
				ownPoster !== undefined
					? merged.from.findLastIndex(start => start <= ownPoster)
					: (prev.posterFrame as number | undefined)
			if (posterFrame !== undefined && posterFrame >= frames.length)
				throw new Error(
					`the replaced entry's "posterFrame" ${posterFrame} is past this art's ${frames.length} frames; set "posterFrame"`
				)

			const hash = hashOf(frames)
			const dupe = hashes.get(hash)
			// Same pixels as the entry being replaced is fine: it updates the rest.
			if (dupe && dupe !== `${meta.replaces}.json`) {
				console.log(`  skip  ${label}: same pixels as ${dupe}`)
				skipped++
				continue
			}
			if (meta.replaces) hashes.delete(prev.hash as string)

			const title = pick('title') || path.basename(base)
			const gameId = meta.game
				? gameIdOf(meta.game)
				: ((prev.gameId as string | undefined) ?? gameIdOf(title))
			const id =
				meta.replaces ?? newId(gameId, title, pick('tags') ?? [], taken)
			const entry = {
				title,
				gameId,
				region: pick('region'),
				width: W,
				height: H,
				bpp: 1,
				frames,
				...timing,
				posterFrame: frames.length > 1 ? posterFrame : undefined,
				tags: pick('tags') ?? [],
				unused: pick('unused') || undefined,
				hash,
				added: addedDate()
			}
			recordDetails(gameId, meta)
			if (!dryRun)
				fs.writeFileSync(
					path.join(OUT_DIR, `${id}.json`),
					JSON.stringify(entry, null, '\t') + '\n'
				)
			hashes.set(hash, `${id}.json`)
			const count = `${frames.length} frame${frames.length > 1 ? 's' : ''}`
			console.log(
				`  ${meta.replaces ? 'update' : 'add  '} ${label} → ${id}.json (${count})`
			)
			if (meta.replaces) updated++
			else added++
		} catch (err) {
			console.error(`  fail  ${label}: ${(err as Error).message}`)
			failed++
		}
	}

	console.log(
		`\n${dryRun ? '[dry run] ' : ''}${added} added, ${updated} updated, ${skipped} duplicate${skipped === 1 ? '' : 's'}, ${failed} failed`
	)
	if (failed) process.exitCode = 1
}

main()
