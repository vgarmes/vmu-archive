/**
 * Turns dumped Dreamcast save files into entries in content/save-icons/.
 *
 *   pnpm saveicons:import <folder> [--sidecar <save-icons.json>] [--dry-run]
 *
 * The folder holds a game's saves (.VMS, each with its .VMI). A
 * save-icons.json, in the folder or given with --sidecar, says which game
 * they're from (by its name, an alias or its id in content/games.json; a game
 * the registry doesn't know yet is added to it) and names each distinct icon
 * by any one of its saves:
 *
 *   {
 *     "game": "Capcom vs. SNK 2", "publisher": "Capcom", "year": 2001,
 *     "region": "JP",
 *     "titles": { "cvs2jp.VMS": "System file", "cvs2rep1.VMS": "Replay file" }
 *   }
 *
 * A save's icon is read from its header, at the start of the file for a data
 * file or at 0x200 for a VMU program (the .VMI's mode says which; some .VMIs
 * don't flag a program, so a header that makes no sense at one place is
 * looked for at the other): the VMU name (0x00, 16 bytes, Shift-JIS), the
 * description (0x10, 32 bytes), the frame count (0x40) and animation speed
 * (0x42), the 16-colour ARGB4444 palette (0x60) and the 32x32 frames (0x80,
 * 512 bytes each).
 *
 * An ICONDATA_VMS file, a memory card's own icon, is read too, as a
 * "memory-card" entry: 0x00 its name (16 bytes), 0x10 the offset of a 32x32
 * 1-bit icon (128 bytes), 0x14 the offset of a colour one (palette, then
 * 32x32 at 4 bits). Whether the game made it isn't known from the file, so
 * it's imported with "madeByGame": null until a disc shows it.
 *
 * Saves carrying the same icon are one entry, which keeps the save that names
 * it in "titles" as its source. An icon not named in "titles" is left out, so
 * a folder can be imported in part.
 * Icons already in the archive, under any game, are skipped.
 */
import fs from 'node:fs'
import path from 'node:path'
import { slug } from '../src/lib/slug.ts'
import { findGame, gameIdFor, loadRegistry, saveRegistry } from './registry.ts'
import {
	ICON_SIZE,
	SAVE_ICONS_DIR,
	type SaveIcon,
	saveIconHash,
	saveIconProblems
} from './save-icons.ts'

interface Sidecar {
	game: string
	publisher?: string
	year?: number
	region?: SaveIcon['region']
	tags?: string[]
	titles: Record<string, string>
}

interface Read {
	file: string
	kind: SaveIcon['kind']
	vmuName: string
	description: string
	animationSpeed: number
	palette: string[]
	frames: string[]
	vmuIcon?: string
}

const sjis = new TextDecoder('shift_jis')
const text = (b: Buffer) =>
	sjis.decode(b.subarray(0, b.indexOf(0) < 0 ? b.length : b.indexOf(0))).trim()

const argb4444 = (v: number) =>
	'#' +
	[v >> 8, v >> 4, v, v >> 12]
		.map(n => ((n & 15) * 17).toString(16).padStart(2, '0'))
		.join('')

const palette = (d: Buffer, at: number) =>
	Array.from({ length: 16 }, (_, i) => argb4444(d.readUInt16LE(at + 2 * i)))

/** A save header's frame count and eyecatch type, if one is at `at`. */
function headerAt(d: Buffer, at: number) {
	if (d.length < at + 0x80) return null
	const count = d.readUInt16LE(at + 0x40)
	const eyecatch = d.readUInt16LE(at + 0x44)
	return count >= 1 && count <= 48 && eyecatch <= 3 ? count : null
}

function readIcondata(d: Buffer, file: string): Read | null {
	if (d.length < 0x18) return null
	const mono = d.readUInt32LE(0x10)
	const colour = d.readUInt32LE(0x14)
	if (mono !== 0x20 || colour < 0xa0 || colour + 0x220 > d.length) return null
	return {
		file,
		kind: 'memory-card',
		vmuName: text(d.subarray(0, 16)),
		description: '',
		animationSpeed: 0,
		palette: palette(d, colour),
		frames: [d.subarray(colour + 0x20, colour + 0x220).toString('hex')],
		vmuIcon: d.subarray(mono, mono + 128).toString('hex')
	}
}

function readSave(vms: string): Read {
	const dir = path.dirname(vms)
	const file = path.basename(vms)
	const stem = path.basename(vms, path.extname(vms))
	const vmi = fs
		.readdirSync(dir)
		.find(
			f =>
				path.extname(f).toLowerCase() === '.vmi' &&
				path.basename(f, path.extname(f)).toLowerCase() === stem.toLowerCase()
		)
	const mode = vmi ? fs.readFileSync(path.join(dir, vmi)).readUInt16LE(0x64) : 0
	const d = fs.readFileSync(vms)
	const first = mode & 2 ? 0x200 : 0 // a VMU program keeps its header at 0x200
	const h = [first, 0x200 - first].find(at => headerAt(d, at))
	if (h === undefined) {
		const icondata = readIcondata(d, file)
		if (icondata) return icondata
		throw new Error(`${file}: neither a save header nor ICONDATA_VMS`)
	}
	const count = headerAt(d, h)!
	return {
		file,
		kind: 'save',
		vmuName: text(d.subarray(h, h + 0x10)),
		description: text(d.subarray(h + 0x10, h + 0x30)),
		animationSpeed: d.readUInt16LE(h + 0x42),
		palette: palette(d, h + 0x60),
		frames: Array.from({ length: count }, (_, k) =>
			d.subarray(h + 0x80 + 512 * k, h + 0x80 + 512 * (k + 1)).toString('hex')
		)
	}
}

function existingHashes() {
	const hashes = new Map<string, string>()
	if (!fs.existsSync(SAVE_ICONS_DIR)) return hashes
	for (const game of fs.readdirSync(SAVE_ICONS_DIR)) {
		const dir = path.join(SAVE_ICONS_DIR, game)
		if (!fs.statSync(dir).isDirectory()) continue
		for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.json')))
			hashes.set(
				JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')).hash,
				`${game}/${f}`
			)
	}
	return hashes
}

function main() {
	const args = process.argv.slice(2)
	const dryRun = args.includes('--dry-run')
	const at = args.indexOf('--sidecar')
	const sidecarPath = at >= 0 ? args[at + 1] : undefined
	const folder = args.find(
		(a, i) => !a.startsWith('--') && (at < 0 || i !== at + 1)
	)
	if (!folder) {
		console.error(
			'usage: pnpm saveicons:import <folder> [--sidecar <save-icons.json>] [--dry-run]'
		)
		process.exit(1)
	}
	const sidecar: Sidecar = JSON.parse(
		fs.readFileSync(sidecarPath ?? path.join(folder, 'save-icons.json'), 'utf8')
	)
	const saves = fs
		.readdirSync(folder)
		.filter(f => path.extname(f).toLowerCase() === '.vms')
		.sort()
		.map(f => readSave(path.join(folder, f)))

	// One entry per distinct icon, in the order its first save sorts.
	const groups = new Map<string, Read[]>()
	for (const s of saves) {
		const hash = saveIconHash(s.palette, s.frames, s.vmuIcon)
		groups.set(hash, [...(groups.get(hash) ?? []), s])
	}

	// A game the registry doesn't know yet joins it only once one of its icons
	// is written: a folder whose icons are all elsewhere already adds nothing.
	const registry = loadRegistry()
	const isNew = !findGame(registry, sidecar.game)
	const gameId = gameIdFor(registry, sidecar.game, { dryRun: true })
	const have = existingHashes()
	const dir = path.join(SAVE_ICONS_DIR, gameId)
	const taken = new Set(
		fs.existsSync(dir)
			? fs.readdirSync(dir).map(f => f.replace(/\.json$/, ''))
			: []
	)
	let added = 0
	let skipped = 0
	let left = 0
	for (const [hash, group] of groups) {
		const files = group.map(s => s.file)
		if (have.has(hash)) {
			console.log(
				`  skip  ${files[0]} (+${files.length - 1}): same icon as ${have.get(hash)}`
			)
			skipped++
			continue
		}
		const title = files.map(f => sidecar.titles[f]).find(Boolean)
		if (!title) {
			console.log(
				`  leave ${files[0]} (+${files.length - 1}): not named in "titles"`
			)
			left++
			continue
		}
		const first = group[0]
		let id = slug(title)
		for (let n = 2; taken.has(id); n++) id = `${slug(title)}-${n}`
		taken.add(id)
		const icon: SaveIcon = {
			kind: first.kind,
			title,
			gameId,
			publisher: sidecar.publisher,
			year: sidecar.year,
			region: sidecar.region,
			width: ICON_SIZE,
			height: ICON_SIZE,
			bpp: 4,
			palette: first.palette,
			frames: first.frames,
			animationSpeed: first.animationSpeed,
			...(first.kind === 'memory-card'
				? { vmuIcon: first.vmuIcon, madeByGame: null }
				: {}),
			vmuName: first.vmuName,
			description: first.description,
			source: {
				kind: 'save',
				// The save that named it; the others carrying it add nothing.
				file: files.find(f => sidecar.titles[f]) ?? files[0]
			},
			tags: sidecar.tags ?? [],
			hash,
			added: new Date().toISOString().slice(0, 10)
		}
		const problems = saveIconProblems(icon)
		if (problems.length) throw new Error(`${id}: ${problems.join('; ')}`)
		if (!dryRun) {
			if (isNew && !added) saveRegistry(registry)
			fs.mkdirSync(dir, { recursive: true })
			fs.writeFileSync(
				path.join(dir, `${id}.json`),
				JSON.stringify(icon, null, '\t') + '\n'
			)
		}
		console.log(
			`  add   ${files[0]} (+${files.length - 1}) → save-icons/${gameId}/${id}.json (${icon.kind}, ${icon.frames.length} frame${icon.frames.length === 1 ? '' : 's'})`
		)
		added++
	}
	console.log(
		`\n${saves.length} saves, ${groups.size} distinct icons: ${added} added, ${skipped} already in the archive, ${left} not named${dryRun ? ' (dry run)' : ''}`
	)
}

main()
