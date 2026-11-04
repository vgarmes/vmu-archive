import 'server-only'
import fs from 'node:fs'
import path from 'node:path'
import { type Glyphs, glyphBoxes } from './glyphs'
import { decodeFrame } from './pixels'

/**
 * A game's sprites (content/sprites/<game slug>/*.json, see scripts/sprites.ts)
 * packed into one sheet, read at build time. /sprites/<game slug>.png is the
 * sheet; the game page lays each sprite out as its own cell cut from it, so
 * they rewrap with the window instead of the sheet scaling.
 *
 * Fonts (sprites tagged "font") are kept apart from the other sprites, for
 * the page's Fonts card: one group per font, in file order. A font whose
 * character sizes are known (`glyphs`, see ./glyphs) becomes one cell per
 * character, in the game's order; any other is one cell.
 *
 * The other sprites are packed tallest first and in file order within a
 * height, so a game's like-sized sprites (Shenmue's faces) sit together. The
 * layout is only where each piece is in the PNG; the page arranges them.
 *
 * Whatever the game draws onto a screen the archive has (`drawnAt`, for a
 * font per character) is left out: that screen already shows it. A game with
 * nothing left gets no sheet, and neither card.
 */

const DIR = path.join(process.cwd(), 'content/sprites')

/** Width the sheet is packed to; any will do, the page doesn't show it whole. */
const SHEET_WIDTH = 512
/** Transparent pixels between sprites, so a cell never bleeds into the next. */
const GAP = 1
/**
 * A tall strip without `glyphs` is cut into FOLD_HEIGHT-row pieces that wrap
 * like any other sprite. The cuts can fall inside a character.
 */
const FOLD_HEIGHT = 32

export interface SpriteCell {
	/** The sprite's title (a font's: and the glyph's number). */
	title: string
	x: number
	y: number
	width: number
	height: number
}

export interface FontCells {
	title: string
	/** Its characters in the game's order, or the font whole if not split. */
	cells: SpriteCell[]
	/** Whether the cells are characters (the font has `glyphs`). */
	split: boolean
}

export interface SpriteSheet {
	width: number
	height: number
	/** Lit pixels as 0/1, row-major, width x height. */
	pixels: Uint8Array
	/** The sprites that aren't fonts, tallest first. */
	cells: SpriteCell[]
	/** Sprite files behind `cells`, before folding into cells. */
	count: number
	fonts: FontCells[]
}

interface Piece {
	title: string
	width: number
	height: number
	pixels: Uint8Array
}

interface Font {
	title: string
	pieces: Piece[]
	split: boolean
}

const byName = new Intl.Collator('en', { numeric: true })

interface SpriteFile {
	title: string
	width: number
	height: number
	frames: string[]
	tags: string[]
	glyphs?: Glyphs
	drawnAt?: { glyph?: number }[]
}

function readPieces(dir: string): {
	sprites: Piece[]
	count: number
	fonts: Font[]
} {
	const files = fs
		.readdirSync(dir)
		.filter(f => f.endsWith('.json'))
		.sort(byName.compare)
		.map(
			file =>
				JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8')) as SpriteFile
		)
	const isFont = (s: SpriteFile) => s.tags.includes('font')
	const perFile = files.filter(s => !isFont(s)).map(piecesOf)
	const sprites = perFile.flat()
	// Stable: file order stays within a height.
	sprites.sort((a, b) => b.height - a.height)
	const fonts = files
		.filter(isFont)
		.map(s => ({ title: s.title, pieces: piecesOf(s), split: !!s.glyphs }))
		.filter(f => f.pieces.length)
	// Sprites with something still shown.
	return { sprites, count: perFile.filter(p => p.length).length, fonts }
}

function piecesOf(s: SpriteFile): Piece[] {
	// Drawn onto a screen the archive has: that screen already shows it.
	const drawn = s.drawnAt ?? []
	if (drawn.some(at => at.glyph === undefined)) return []
	const px = decodeFrame(s.frames[0], s.width, s.height, 1)
	// A font: each character its own piece, as wide as the game draws it,
	// titled with its number in the game's table (from 0). Characters drawn
	// on a screen are left out, and so are blank ones: spaces and the empty
	// slots a font keeps so codes line up. The JSON keeps them all, and the
	// gaps in the numbering show where they are.
	if (s.glyphs) {
		const drawnGlyphs = new Set(drawn.map(at => at.glyph))
		const glyphs = glyphBoxes(s.glyphs, s.width, s.height)
			.map((g, i) => {
				const pixels = new Uint8Array(g.width * g.height)
				for (let row = 0; row < g.height; row++)
					pixels.set(
						px.subarray((g.y + row) * s.width, (g.y + row) * s.width + g.width),
						row * g.width
					)
				return {
					title: `${s.title}, glyph ${i}`,
					width: g.width,
					height: g.height,
					pixels
				}
			})
			.filter((g, i) => !drawnGlyphs.has(i) && g.pixels.includes(1))
		return glyphs
	}
	const whole = { title: s.title, width: s.width, height: s.height }
	// Only tall, narrow strips; a parts sheet stays whole.
	if (s.height <= FOLD_HEIGHT || s.height < 4 * s.width)
		return [{ ...whole, pixels: px }]
	const parts: Piece[] = []
	for (let top = 0; top < s.height; top += FOLD_HEIGHT) {
		const height = Math.min(FOLD_HEIGHT, s.height - top)
		parts.push({
			...whole,
			height,
			pixels: px.subarray(top * s.width, (top + height) * s.width)
		})
	}
	return parts
}

/** Packs the pieces in order; their cells come back in the same order. */
function pack(pieces: Piece[]) {
	const width = Math.max(SHEET_WIDTH, ...pieces.map(p => p.width))
	const cells: SpriteCell[] = []
	let x = 0
	let y = 0
	let rowHeight = 0
	for (const p of pieces) {
		if (x > 0 && x + p.width > width) {
			x = 0
			y += rowHeight + GAP
			rowHeight = 0
		}
		cells.push({ title: p.title, x, y, width: p.width, height: p.height })
		x += p.width + GAP
		rowHeight = Math.max(rowHeight, p.height)
	}
	const height = y + rowHeight
	const pixels = new Uint8Array(width * height)
	pieces.forEach((p, i) => {
		const c = cells[i]
		for (let row = 0; row < p.height; row++)
			pixels.set(
				p.pixels.subarray(row * p.width, (row + 1) * p.width),
				(c.y + row) * width + c.x
			)
	})
	return { width, height, cells, pixels }
}

function sheetOf(dir: string): SpriteSheet | undefined {
	const { sprites, count, fonts } = readPieces(dir)
	const fontPieces = fonts.flatMap(f => f.pieces)
	if (!sprites.length && !fontPieces.length) return undefined
	const { cells, ...sheet } = pack([...sprites, ...fontPieces])
	let next = sprites.length
	return {
		...sheet,
		cells: cells.slice(0, sprites.length),
		count,
		fonts: fonts.map(f => ({
			title: f.title,
			split: f.split,
			cells: cells.slice(next, (next += f.pieces.length))
		}))
	}
}

let cache: Map<string, SpriteSheet> | undefined

function load() {
	if (cache) return cache
	cache = new Map()
	if (!fs.existsSync(DIR)) return cache
	for (const game of fs.readdirSync(DIR).sort()) {
		const dir = path.join(DIR, game)
		if (!fs.statSync(dir).isDirectory()) continue
		const sheet = sheetOf(dir)
		if (sheet) cache.set(game, sheet)
	}
	return cache
}

/** Game slugs with at least one sprite. */
export const getSpriteGames = () => [...load().keys()]

export const getSpriteSheet = (gameSlug: string) => load().get(gameSlug)
