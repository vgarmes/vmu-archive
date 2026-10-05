/**
 * Turns source files into VMU screen entries in content/icons/.
 *
 *   pnpm icons:import [files or folders…]   (default: inbox/)
 *     --dry-run   print what would be written
 *     --keep      leave sources in place instead of moving them to inbox/imported/
 *
 * Every entry is a 48x32 1-bit VMU LCD screen. Supported sources:
 * - .png  A 48x32 screen; stack frames vertically for animation (48x64 = 2
 *         frames). Dark pixels are lit; set "invert" for the opposite. Any
 *         other size is treated as smaller art: trimmed to its lit pixels and
 *         centred on the screen.
 * - .txt  Rows of "#" (lit) and spaces, up to 48x32, centred. Separate
 *         animation frames with a line containing only "---".
 *
 * Sprite sheets: give a PNG's sidecar a "crops" list and every box becomes its
 * own entry. Each crop takes the same metadata fields, overriding the sheet's:
 *   { "game": "Sonic Adventure", "publisher": "Sega",
 *     "crops": [{ "x": 24, "y": 67, "w": 48, "h": 32, "title": "Sonic" }, …] }
 * A 48x32 box is used as is; any other box is trimmed and centred, so it can
 * be loose.
 *
 * Metadata comes from an optional sidecar with the same basename
 * (sonic.png → sonic.json): { title, game, publisher, year, region, tags,
 * frameDelayMs, invert, replaces }. Without one, the filename is the
 * title. Pixel-identical art that is already in the archive is skipped.
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
		const { x, y, w, h, ...own } = crop
		const pieceMeta: Meta = { ...sheet, ...own }
		return {
			frames: readImage(cropImage(png, crop), pieceMeta),
			meta: pieceMeta,
			label: `${name} @${x},${y}`
		}
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
