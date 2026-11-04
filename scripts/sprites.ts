/**
 * Sprites: art a game draws onto part of the VMU screen at run time (digits,
 * buttons, counters), as opposed to a whole 48x32 screen. They're kept for
 * preservation, at their own size, in content/sprites/<game slug>/<id>.json,
 * and kept out of content/icons/, which stays whole screens only. The site
 * shows them only as a game's Sprites card (src/lib/sprites.ts).
 *
 * Written by `pnpm icons:import` (a sidecar with "sprite": true) and checked by
 * `pnpm content:check`. Run by Node directly, like pixels.ts: keep the imports
 * relative with their .ts extension.
 */
import { createHash } from 'node:crypto'
import path from 'node:path'
import { type Glyphs, glyphProblems } from '../src/lib/glyphs.ts'
import { frameHexLength } from '../src/lib/pixels.ts'

const ROOT = path.resolve(import.meta.dirname, '..')
export const ICONS_DIR = path.join(ROOT, 'content/icons')
export const SPRITES_DIR = path.join(ROOT, 'content/sprites')

export const SCREEN_W = 48
export const SCREEN_H = 32

export interface Sprite {
	title: string
	game: string
	publisher?: string
	year?: number
	region?: 'JP' | 'US' | 'EU' | 'WW'
	width: number
	height: number
	bpp: 1
	/** One frame for now; encoded like a screen's (src/lib/pixels.ts). */
	frames: string[]
	/**
	 * A font: its characters stacked in the game's order, and their sizes
	 * (src/lib/glyphs.ts), so the site can show each as its own cell.
	 */
	glyphs?: Glyphs
	/** Where on the disc it came from, so it can be found again. */
	source?: {
		/** Path on the disc, e.g. "/LCDIMG.BIN". */
		file: string
		/** Its number or name inside that file. */
		entry?: number | string
		/** Byte offset inside that file. */
		offset?: number
	}
	/**
	 * Where the game draws it, when that was read from the code: the archive
	 * screen it goes on and its top-left corner there.
	 */
	drawnAt?: { screen: string; x: number; y: number }[]
	tags: string[]
	/** Content hash of the pixels; the importer uses it to skip duplicates. */
	hash: string
	added: string
}

export const spriteHash = (width: number, height: number, frames: string[]) =>
	createHash('sha1')
		.update(['sprite', width, height, 1, frames.join(',')].join('|'))
		.digest('hex')

const REGIONS = ['JP', 'US', 'EU', 'WW']
const isInt = (v: unknown, min: number) =>
	typeof v === 'number' && Number.isInteger(v) && v >= min

/**
 * What's wrong with a sprite entry, or nothing. `screens` is every id in
 * content/icons/, to check `drawnAt` against.
 */
export function spriteProblems(s: Sprite, screens: Set<string>): string[] {
	const out: string[] = []
	if (!s.title) out.push('no "title"')
	if (!s.game) out.push('no "game"')
	if (s.region !== undefined && !REGIONS.includes(s.region))
		out.push(`"region" ${s.region} is not one of ${REGIONS.join(', ')}`)
	if (s.bpp !== 1) out.push('"bpp" must be 1')
	if (!isInt(s.width, 1) || !isInt(s.height, 1))
		out.push('"width" and "height" must be whole numbers above 0')
	else if (s.width === SCREEN_W && s.height === SCREEN_H)
		out.push('a 48x32 piece is a whole screen: import it to content/icons/')
	if (!Array.isArray(s.frames) || s.frames.length !== 1)
		out.push('"frames" must hold exactly one frame')
	else if (
		!/^[0-9a-f]+$/.test(s.frames[0]) ||
		s.frames[0].length !== frameHexLength(s.width, s.height, 1)
	)
		out.push('the frame does not match width x height')
	else if (s.hash !== spriteHash(s.width, s.height, s.frames))
		out.push('"hash" does not match the pixels')
	if (s.glyphs !== undefined && isInt(s.width, 1) && isInt(s.height, 1))
		out.push(...glyphProblems(s.glyphs, s.width, s.height))
	if (s.source && typeof s.source.file !== 'string')
		out.push('"source" needs a "file"')
	for (const at of s.drawnAt ?? []) {
		if (!screens.has(at.screen))
			out.push(`"drawnAt": no screen ${at.screen} in content/icons/`)
		if (
			!isInt(at.x, 0) ||
			!isInt(at.y, 0) ||
			at.x + s.width > SCREEN_W ||
			at.y + s.height > SCREEN_H
		)
			out.push(
				`"drawnAt" ${at.screen} (${at.x}, ${at.y}) puts it off the 48x32 screen`
			)
	}
	if (!Array.isArray(s.tags)) out.push('"tags" must be a list')
	if (!/^\d{4}-\d{2}-\d{2}$/.test(s.added ?? ''))
		out.push('"added" is not a date')
	return out
}
