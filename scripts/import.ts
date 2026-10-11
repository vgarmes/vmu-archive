/**
 * Turns source files into VMU screen entries in content/icons/.
 *
 *   pnpm icons:import [files or folders…]   (default: inbox/)
 *     --dry-run   print what would be written
 *     --keep      leave sources in place instead of moving them to inbox/imported/
 *
 * Every entry is a 48x32 1-bit VMU LCD screen. Supported sources:
 * - .png  A 48x32 screen; stack frames vertically for animation (48x64 = 2
 *         frames). Dark pixels are lit; set "invert" for the opposite.
 *         Anything bigger at a 3:2 ratio is a scaled-up screenshot of a whole
 *         screen (e.g. an emulator capture at 4.5x, 216x144): a uniform border
 *         is stripped, the majority colour is unlit whether it's light or dark,
 *         and "invert" flips that. Any other size is treated as smaller art:
 *         trimmed to its lit pixels and centred on the screen.
 * - .txt  Rows of "#" (lit) and spaces, up to 48x32, centred. Separate
 *         animation frames with a line containing only "---".
 *
 * Sprite sheets: give a PNG's sidecar a "crops" list and every box becomes its
 * own entry. Each crop takes the same metadata fields, overriding the sheet's:
 *   { "game": "Sonic Adventure", "publisher": "Sega",
 *     "crops": [{ "x": 24, "y": 67, "w": 48, "h": 32, "title": "Sonic" }, …] }
 * A 48x32 box is used as is; any other box is trimmed and centred, so it can
 * be loose. For a sheet with one animation per row, give a 48x32 crop
 * "frames": n and it reads n boxes left to right, "step" pixels apart
 * (default: the box width), as one animated entry:
 *   { "x": 2, "y": 36, "w": 48, "h": 32, "frames": 8, "step": 50, "title": "Bow" }
 *
 * Metadata comes from an optional sidecar with the same basename
 * (sonic.png → sonic.json): { title, game, publisher, year, region, tags,
 * frameDelayMs, posterFrame, invert, replaces }. "posterFrame" is the frame
 * (from 0) the grid shows at rest, for animations whose first frame is a poor
 * thumbnail. Without a sidecar, the filename is the title. Pixel-identical art
 * that is already in the archive is skipped.
 *
 * To change an existing piece — e.g. add the missing frames of an animation —
 * import the full art with `"replaces": "<existing id>"` in its sidecar. The
 * id, added date and unchanged metadata carry over.
 */
import { createHash } from 'node:crypto'
import fs from 'node:fs'
import path from 'node:path'
import pngjs from 'pngjs'
import { encodeFrame } from '../src/lib/pixels.ts'

const ROOT = path.resolve(import.meta.dirname, '..')
const OUT_DIR = path.join(ROOT, 'content/icons')
const INBOX = path.join(ROOT, 'inbox')
const DONE = path.join(INBOX, 'imported')

const W = 48
const H = 32
const SOURCE_EXT = new Set(['.png', '.txt'])

interface Meta {
	title?: string
	game?: string
	publisher?: string
	year?: number
	region?: 'JP' | 'US' | 'EU' | 'WW'
	tags?: string[]
	frameDelayMs?: number
	/** Frame (from 0) the grid shows when the animation isn't playing. */
	posterFrame?: number
	invert?: boolean
	/** Id of an existing entry to replace (e.g. to add animation frames). */
	replaces?: string
	/** Boxes to cut out of a sprite sheet PNG, one entry each. */
	crops?: Crop[]
}

interface Crop extends Omit<Meta, 'crops'> {
	x: number
	y: number
	w: number
	h: number
	/** Read this many boxes to the right as one animation's frames. */
	frames?: number
	/** Distance between those boxes, in pixels (default: `w`). */
	step?: number
}

interface Image {
	width: number
	height: number
	data: Uint8Array
}

/** Lit pixels (1) of each frame, row-major, W x H. */
type Frames = number[][]

// ---------------------------------------------------------------- reading

/** A dark, opaque pixel is a lit dot (unless the art is inverted). */
function isLit(img: Image, x: number, y: number, invert = false) {
	const i = (y * img.width + x) * 4
	const [r, g, b, a] = img.data.subarray(i, i + 4)
	return (a >= 128 && 0.299 * r + 0.587 * g + 0.114 * b < 128) !== invert
}

function readImage(img: Image, meta: Meta): Frames {
	if (img.width === W && img.height % H === 0) {
		const frames: Frames = []
		for (let f = 0; f < img.height / H; f++) {
			const bits: number[] = []
			for (let y = 0; y < H; y++)
				for (let x = 0; x < W; x++)
					bits.push(isLit(img, x, f * H + y, meta.invert) ? 1 : 0)
			frames.push(bits)
		}
		return frames
	}
	if (img.width > W || img.height > H) {
		const screen = readScreenshot(img, meta.invert)
		if (screen) return [screen]
	}
	// Smaller art: trim to its lit pixels, then centre it on the screen.
	let x0 = Infinity,
		y0 = Infinity,
		x1 = -1,
		y1 = -1
	for (let y = 0; y < img.height; y++)
		for (let x = 0; x < img.width; x++)
			if (isLit(img, x, y, meta.invert)) {
				x0 = Math.min(x0, x)
				y0 = Math.min(y0, y)
				x1 = Math.max(x1, x)
				y1 = Math.max(y1, y)
			}
	if (x1 < 0) throw new Error('no lit pixels in this area')
	const rows: boolean[][] = []
	for (let y = y0; y <= y1; y++) {
		const row: boolean[] = []
		for (let x = x0; x <= x1; x++) row.push(isLit(img, x, y, meta.invert))
		rows.push(row)
	}
	return [centre(rows)]
}

const rgbOf = (img: Image, x: number, y: number) => {
	const i = (y * img.width + x) * 4
	return (img.data[i] << 16) | (img.data[i + 1] << 8) | img.data[i + 2]
}

const lumaOf = (img: Image, x: number, y: number) => {
	const i = (y * img.width + x) * 4
	return 0.299 * img.data[i] + 0.587 * img.data[i + 1] + 0.114 * img.data[i + 2]
}

/**
 * The screen area of a scaled screenshot: the image minus uniform rows and
 * columns along its edges (an emulator's frame), stripped until it's 3:2.
 * Null if it doesn't get there or is under 2x.
 */
function screenBox(img: Image) {
	const counts = new Map<number, number>()
	for (let y = 0; y < img.height; y++)
		for (let x = 0; x < img.width; x++) {
			const c = rgbOf(img, x, y)
			counts.set(c, (counts.get(c) ?? 0) + 1)
		}
	const background = [...counts].sort((a, b) => b[1] - a[1])[0][0]

	let [x0, y0, x1, y1] = [0, 0, img.width, img.height]
	/** The single colour of a row (or column), or null if it has several. */
	const uniform = (row: boolean, at: number) => {
		const c = row ? rgbOf(img, x0, at) : rgbOf(img, at, y0)
		const len = row ? x1 - x0 : y1 - y0
		for (let i = 1; i < len; i++)
			if ((row ? rgbOf(img, x0 + i, at) : rgbOf(img, at, y0 + i)) !== c)
				return null
		return c
	}
	while ((x1 - x0) * 2 !== (y1 - y0) * 3) {
		const rows = (x1 - x0) * 2 < (y1 - y0) * 3
		const first = rows ? uniform(true, y0) : uniform(false, x0)
		const last = rows ? uniform(true, y1 - 1) : uniform(false, x1 - 1)
		if (first === null && last === null) break
		// A frame differs from the screen's background, so strip that side first.
		const takeLast =
			first === null ||
			(last !== null && first === background && last !== background)
		if (rows) takeLast ? y1-- : y0++
		else takeLast ? x1-- : x0++
	}
	const w = x1 - x0
	const h = y1 - y0
	// A resized capture may be a pixel or so off 3:2.
	if (Math.abs(w * 2 - h * 3) > 3 || w < W * 2) return null
	return { x0, y0, w, h }
}

/** A whole screen from a scaled screenshot, or null if it isn't one. */
function readScreenshot(img: Image, invert = false): number[] | null {
	const box = screenBox(img)
	if (!box) return null
	const { x0, y0, w, h } = box

	// Lit is whichever side of the mid-grey has fewer pixels.
	let lo = Infinity,
		hi = -Infinity,
		light = 0
	for (let y = y0; y < y0 + h; y++)
		for (let x = x0; x < x0 + w; x++) {
			const l = lumaOf(img, x, y)
			lo = Math.min(lo, l)
			hi = Math.max(hi, l)
		}
	const mid = (lo + hi) / 2
	for (let y = y0; y < y0 + h; y++)
		for (let x = x0; x < x0 + w; x++) if (lumaOf(img, x, y) > mid) light++
	const litIsLight = light * 2 < w * h
	const isOn = (x: number, y: number) =>
		(lumaOf(img, x0 + x, y0 + y) > mid === litIsLight) !== invert

	// Sample a 3x3 spread inside every cell. At a non-integer scale the grid
	// can sit a little off, so try a few shifts and keep the one where the
	// cells read most consistently.
	const sx = w / W
	const sy = h / H
	const at = (v: number, max: number) =>
		Math.min(max - 1, Math.max(0, Math.floor(v)))
	let best = { bits: [] as number[], mixed: Infinity }
	for (const dy of [0, -0.25, 0.25])
		for (const dx of [0, -0.25, 0.25]) {
			const bits: number[] = []
			let mixed = 0
			for (let r = 0; r < H; r++)
				for (let c = 0; c < W; c++) {
					let on = 0
					for (const fy of [0.3, 0.5, 0.7])
						for (const fx of [0.3, 0.5, 0.7])
							if (isOn(at((c + fx + dx) * sx, w), at((r + fy + dy) * sy, h)))
								on++
					if (on % 9) mixed++
					bits.push(on > 4 ? 1 : 0)
				}
			if (mixed < best.mixed) best = { bits, mixed }
		}
	if (!best.bits.includes(1))
		throw new Error('no lit pixels in this screenshot')
	return best.bits
}

function readTxt(text: string): Frames {
	return text
		.replace(/\r/g, '')
		.split(/^---$/m)
		.map(block => {
			const lines = block.replace(/^\n+|\n+$/g, '').split('\n')
			return centre(lines.map(line => [...line].map(c => c === '#')))
		})
}

/** Art up to 48x32, centred on a blank screen. */
function centre(rows: boolean[][]): number[] {
	const w = Math.max(...rows.map(r => r.length))
	const h = rows.length
	if (w > W || h > H) throw new Error(`art is ${w}x${h}; the screen is 48x32`)
	const offX = Math.floor((W - w) / 2)
	const offY = Math.floor((H - h) / 2)
	const bits = new Array<number>(W * H).fill(0)
	rows.forEach((row, y) =>
		row.forEach((lit, x) => {
			if (lit) bits[(y + offY) * W + x + offX] = 1
		})
	)
	return bits
}

function cropImage(img: Image, { x, y, w, h }: Crop): Image {
	if (x < 0 || y < 0 || x + w > img.width || y + h > img.height)
		throw new Error(
			`crop ${w}x${h} at ${x},${y} is outside the ${img.width}x${img.height} image`
		)
	const data = new Uint8Array(w * h * 4)
	for (let row = 0; row < h; row++) {
		const from = ((y + row) * img.width + x) * 4
		data.set(img.data.subarray(from, from + w * 4), row * w * 4)
	}
	return { width: w, height: h, data }
}

/** The pieces a source file yields: one, or one per crop of a sprite sheet. */
function readSource(
	file: string,
	meta: Meta
): { frames: Frames; meta: Meta; label: string }[] {
	const name = path.basename(file)
	const buf = fs.readFileSync(file)
	if (path.extname(file).toLowerCase() === '.txt')
		return [{ frames: readTxt(buf.toString('utf8')), meta, label: name }]

	const png = pngjs.PNG.sync.read(buf)
	if (!meta.crops) return [{ frames: readImage(png, meta), meta, label: name }]
	const { crops, ...sheet } = meta
	return crops.map(crop => {
		const { x, y, w, h, frames: count = 1, step = w, ...own } = crop
		const pieceMeta: Meta = { ...sheet, ...own }
		const label = `${name} @${x},${y}`
		if (count === 1)
			return {
				frames: readImage(cropImage(png, crop), pieceMeta),
				meta: pieceMeta,
				label
			}
		// Frames are used as is, never trimmed one by one, so they stay aligned.
		if (w !== W || h !== H)
			throw new Error(`${label}: a crop with "frames" must be ${W}x${H}`)
		const frames = Array.from(
			{ length: count },
			(_, i) =>
				readImage(cropImage(png, { x: x + i * step, y, w, h }), pieceMeta)[0]
		)
		return { frames, meta: pieceMeta, label: `${label} ×${count}` }
	})
}

// ---------------------------------------------------------------- main

const slug = (s: string) =>
	s
		.normalize('NFKD')
		.toLowerCase()
		// "Tony Hawk's" → tony-hawks, not tony-hawk-s.
		.replace(/['’]/g, '')
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-|-$/g, '') || 'icon'

/**
 * A readable id from the game and title ("ikaruga-title-screen"), without
 * repeating the game when the title already starts with it, "-sprite" for
 * entries tagged as small sprites, and -2, -3… when it's taken, so pieces
 * with the same title keep their import order. Chosen once: editing a title later keeps the id (and so the
 * thumbnail URL and ?screen= links).
 */
function newId(
	game: string,
	title: string,
	tags: string[],
	taken: Set<string>
) {
	const g = slug(game)
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
			.filter(f => SOURCE_EXT.has(path.extname(f).toLowerCase()))
			.map(f => path.join(input, f))
	})
}

function main() {
	const args = process.argv.slice(2)
	const dryRun = args.includes('--dry-run')
	const keep = args.includes('--keep')
	const inputs = args.filter(a => !a.startsWith('--'))
	const files = collect(inputs.length ? inputs : [INBOX])
	if (!files.length) {
		console.log('Nothing to import. Drop .png or .txt files into inbox/.')
		return
	}

	fs.mkdirSync(OUT_DIR, { recursive: true })
	const hashes = existingHashes()
	const taken = new Set(
		fs
			.readdirSync(OUT_DIR)
			.filter(f => f.endsWith('.json'))
			.map(f => f.replace(/\.json$/, ''))
	)
	let added = 0
	let updated = 0
	let skipped = 0
	let failed = 0

	for (const file of files) {
		const ext = path.extname(file).toLowerCase()
		const base = file.slice(0, -ext.length)
		const sidecar = fs.existsSync(`${base}.json`) ? `${base}.json` : null
		let pieces: ReturnType<typeof readSource>
		try {
			const meta: Meta = sidecar
				? JSON.parse(fs.readFileSync(sidecar, 'utf8'))
				: {}
			pieces = readSource(file, meta)
		} catch (err) {
			console.error(`  fail  ${path.basename(file)}: ${(err as Error).message}`)
			failed++
			continue
		}

		let fileFailed = false
		for (const { frames: bits, meta, label } of pieces) {
			try {
				const frames = bits.map(f => encodeFrame(f, 1))
				const hash = hashOf(frames)
				const dupe = hashes.get(hash)
				if (dupe) {
					console.log(`  skip  ${label}: same pixels as ${dupe}`)
					skipped++
					continue
				}

				// Replacing keeps the id (so URLs don't change), the added date and
				// any metadata the sidecar doesn't override.
				let prev: Record<string, unknown> = {}
				if (meta.replaces) {
					const prevFile = path.join(OUT_DIR, `${meta.replaces}.json`)
					if (!fs.existsSync(prevFile))
						throw new Error(`"replaces": no entry ${meta.replaces}.json`)
					prev = JSON.parse(fs.readFileSync(prevFile, 'utf8'))
					hashes.delete(prev.hash as string)
				}
				const pick = <K extends keyof Meta>(k: K) =>
					meta[k] ?? (prev[k] as Meta[K] | undefined)

				const posterFrame = pick('posterFrame')
				if (
					posterFrame !== undefined &&
					(!Number.isInteger(posterFrame) ||
						posterFrame < 0 ||
						posterFrame >= frames.length)
				)
					throw new Error(
						`"posterFrame": ${posterFrame} is not one of its ${frames.length} frames (0-${frames.length - 1})`
					)

				const title = pick('title') || path.basename(base)
				const id =
					meta.replaces ??
					newId(pick('game') || title, title, pick('tags') ?? [], taken)
				const entry = {
					title,
					game: pick('game') || title,
					publisher: pick('publisher'),
					year: pick('year'),
					region: pick('region'),
					width: W,
					height: H,
					bpp: 1,
					frames,
					frameDelayMs: frames.length > 1 ? pick('frameDelayMs') : undefined,
					posterFrame: frames.length > 1 ? posterFrame : undefined,
					tags: pick('tags') ?? [],
					hash,
					added:
						(prev.added as string | undefined) ??
						new Date().toISOString().slice(0, 10)
				}
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
				fileFailed = true
			}
		}

		// Sources stay in the inbox until every piece imported cleanly.
		if (
			!dryRun &&
			!keep &&
			!fileFailed &&
			path.dirname(path.resolve(file)) === INBOX
		) {
			fs.mkdirSync(DONE, { recursive: true })
			for (const f of [file, sidecar].filter(Boolean) as string[])
				fs.renameSync(f, path.join(DONE, path.basename(f)))
		}
	}

	console.log(
		`\n${dryRun ? '[dry run] ' : ''}${added} added, ${updated} updated, ${skipped} duplicate${skipped === 1 ? '' : 's'}, ${failed} failed`
	)
	if (failed) process.exitCode = 1
}

main()
