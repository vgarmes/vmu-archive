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
 * Packed in rows, tallest first and in file order within a height, so a game's
 * like-sized sprites (Shenmue's faces) sit together. The layout is only where
 * each sprite is in the PNG; the page arranges them itself. A font whose
 * character sizes are known (`glyphs`, see ./glyphs) becomes one cell per
 * character, in the game's order.
 */

const DIR = path.join(process.cwd(), 'content/sprites')

/** Width the sheet is packed to; any will do, the page doesn't show it whole. */
const SHEET_WIDTH = 512
/** Transparent pixels between sprites, so a cell never bleeds into the next. */
const GAP = 1
/**
 * A tall strip without `glyphs` (Shenmue's font, 8x2304, whose character
 * sizes aren't decoded) is cut into FOLD_HEIGHT-row pieces that wrap like any
 * other sprite. The cuts can fall inside a character.
 */
const FOLD_HEIGHT = 32

export interface SpriteCell {
	/** The sprite's title; a folded strip's pieces each carry it. */
	title: string
	x: number
	y: number
	width: number
	height: number
}

export interface SpriteSheet {
	width: number
	height: number
	cells: SpriteCell[]
	/** Lit pixels as 0/1, row-major, width x height. */
	pixels: Uint8Array
	/** Sprite files, before folding. */
	count: number
}

interface Piece {
	title: string
	width: number
	height: number
	pixels: Uint8Array
}

const byName = new Intl.Collator('en', { numeric: true })

function readPieces(dir: string): { pieces: Piece[]; count: number } {
	const files = fs
		.readdirSync(dir)
		.filter(f => f.endsWith('.json'))
		.sort(byName.compare)
	const pieces = files.flatMap(file => {
		const s = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8')) as {
			title: string
			width: number
			height: number
			frames: string[]
			glyphs?: Glyphs
		}
		const px = decodeFrame(s.frames[0], s.width, s.height, 1)
		// A font: each character its own piece, as wide as the game draws it,
		// titled with its number in the game's table (from 0).
		if (s.glyphs)
			return glyphBoxes(s.glyphs, s.width, s.height).map((g, i) => {
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
	})
	// Stable: file order stays within a height.
	pieces.sort((a, b) => b.height - a.height)
	return { pieces, count: files.length }
}

function pack(pieces: Piece[], count: number): SpriteSheet {
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
	return { width, height, cells, pixels, count }
}

let cache: Map<string, SpriteSheet> | undefined

function load() {
	if (cache) return cache
	cache = new Map()
	if (!fs.existsSync(DIR)) return cache
	for (const game of fs.readdirSync(DIR).sort()) {
		const dir = path.join(DIR, game)
		if (!fs.statSync(dir).isDirectory()) continue
		const { pieces, count } = readPieces(dir)
		if (pieces.length) cache.set(game, pack(pieces, count))
	}
	return cache
}

/** Game slugs with at least one sprite. */
export const getSpriteGames = () => [...load().keys()]

export const getSpriteSheet = (gameSlug: string) => load().get(gameSlug)
