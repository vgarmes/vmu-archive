/**
 * Save icons: the colour icon the Dreamcast's file menu shows for a save, read
 * from the save file's header (or found on a game's disc). Not VMU art: 32x32,
 * 4 bits a pixel through a 16-colour palette, one frame or a few. Kept in
 * content/save-icons/<game id>/<id>.json, one per distinct icon: saves that
 * carry the same icon (every system file of a game, say) share one entry.
 *
 * Written by `pnpm saveicons:import` (scripts/import-saves.ts) and checked by
 * `pnpm content:check`. Run by Node directly: keep the imports relative with
 * their .ts extension.
 */
import { createHash } from 'node:crypto'
import path from 'node:path'
import { frameHexLength } from '../src/lib/pixels.ts'

const ROOT = path.resolve(import.meta.dirname, '..')
export const SAVE_ICONS_DIR = path.join(ROOT, 'content/save-icons')

export const ICON_SIZE = 32

export interface SaveIcon {
	/**
	 * "save": the icon in a save's header, which the game writes.
	 * "memory-card": an ICONDATA_VMS file, a memory card's own icon: the
	 * colour icon the Dreamcast's file menu shows, with a 1-bit one for the
	 * VMU (`vmuIcon`). A game may write one, or a player may make it with a
	 * tool, so `madeByGame` says which, once a disc has shown it.
	 */
	kind: 'save' | 'memory-card'
	/** What the save is, in English ("System file", "Replay file"). */
	title: string
	/** The game's id in the registry, content/games.json. */
	gameId: string
	publisher?: string
	year?: number
	region?: 'JP' | 'US' | 'EU' | 'WW'
	width: 32
	height: 32
	bpp: 4
	/** 16 colours, "#rrggbbaa", from the header's ARGB4444 palette. */
	palette: string[]
	/** The icon's frames, 4 bits a pixel, high nibble first, as stored. */
	frames: string[]
	/**
	 * The header's animation speed, as stored. Only matters with more than one
	 * frame; how it maps to time isn't settled, so no delay is derived here.
	 */
	animationSpeed: number
	/** Memory card icons only: the 1-bit 32x32 icon, 1 = dark, as stored. */
	vmuIcon?: string
	/**
	 * Memory card icons only: true once the icon is found on the game's disc,
	 * false if it's shown to be made elsewhere, null until checked.
	 */
	madeByGame?: boolean | null
	/** The save's texts as the header gives them (Shift-JIS, decoded). */
	vmuName: string
	description: string
	/** Where the icon was read from. */
	source: {
		/** "save": dumped save files; "disc": a game's disc. */
		kind: 'save' | 'disc'
		/** The save files (or disc file) that carry this icon. */
		files: string[]
		/** Where the files were taken from, e.g. a repository's folder. */
		url?: string
		/** The repository's commit the files were taken at. */
		commit?: string
		/** On a disc: the byte offset of the header in that file. */
		offset?: number
	}
	tags: string[]
	/** Content hash of the pixels; the importer skips duplicates. */
	hash: string
	added: string
}

/** Content hash of the pixels; a memory card icon's 1-bit icon counts too. */
export const saveIconHash = (
	palette: string[],
	frames: string[],
	vmuIcon?: string
) =>
	createHash('sha1')
		.update(
			[
				'save-icon',
				palette.join(','),
				frames.join(','),
				...(vmuIcon ? [vmuIcon] : [])
			].join('|')
		)
		.digest('hex')

const REGIONS = ['JP', 'US', 'EU', 'WW']

/** What's wrong with a save icon entry, or nothing. */
export function saveIconProblems(s: SaveIcon): string[] {
	const out: string[] = []
	if (s.kind !== 'save' && s.kind !== 'memory-card')
		out.push('"kind" must be "save" or "memory-card"')
	if (s.kind === 'memory-card') {
		if (
			typeof s.vmuIcon !== 'string' ||
			!/^[0-9a-f]+$/.test(s.vmuIcon) ||
			s.vmuIcon.length !== frameHexLength(ICON_SIZE, ICON_SIZE, 1)
		)
			out.push('a memory card icon needs "vmuIcon", 32x32 at 1 bit a pixel')
		if (!(s.madeByGame === null || typeof s.madeByGame === 'boolean'))
			out.push('"madeByGame" must be true, false or null (not checked yet)')
	} else if (s.vmuIcon !== undefined || s.madeByGame !== undefined)
		out.push('only a memory card icon has "vmuIcon" and "madeByGame"')
	if (!s.title) out.push('no "title"')
	if (!s.gameId) out.push('no "gameId"')
	if (s.region !== undefined && !REGIONS.includes(s.region))
		out.push(`"region" ${s.region} is not one of ${REGIONS.join(', ')}`)
	if (s.width !== ICON_SIZE || s.height !== ICON_SIZE || s.bpp !== 4)
		out.push('a save icon is 32x32 at 4 bits a pixel')
	if (
		!Array.isArray(s.palette) ||
		s.palette.length !== 16 ||
		!s.palette.every(c => /^#[0-9a-f]{8}$/.test(c))
	)
		out.push('"palette" must be 16 colours, "#rrggbbaa"')
	if (!Array.isArray(s.frames) || s.frames.length < 1)
		out.push('"frames" must hold at least one frame')
	else if (
		!s.frames.every(
			f =>
				/^[0-9a-f]+$/.test(f) &&
				f.length === frameHexLength(ICON_SIZE, ICON_SIZE, 4)
		)
	)
		out.push('a frame is not 32x32 at 4 bits a pixel')
	else if (s.hash !== saveIconHash(s.palette, s.frames, s.vmuIcon))
		out.push('"hash" does not match the pixels')
	if (!Number.isInteger(s.animationSpeed) || s.animationSpeed < 0)
		out.push('"animationSpeed" must be a whole number')
	if (typeof s.vmuName !== 'string' || typeof s.description !== 'string')
		out.push('"vmuName" and "description" must be text')
	if (
		!s.source ||
		!['save', 'disc'].includes(s.source.kind) ||
		!Array.isArray(s.source.files) ||
		s.source.files.length === 0
	)
		out.push('"source" needs a "kind" (save or disc) and its "files"')
	if (!Array.isArray(s.tags)) out.push('"tags" must be a list')
	if (!/^\d{4}-\d{2}-\d{2}$/.test(s.added ?? ''))
		out.push('"added" is not a date')
	return out
}
