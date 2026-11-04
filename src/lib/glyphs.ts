/**
 * A font sprite's characters. A font is stored as the game stores it: its
 * characters stacked top to bottom in the game's order, each row as wide as
 * the sprite. `glyphs` gives each character's size: `height` rows (one number
 * for all, or one per character) and `width` pixels drawn from the left
 * (likewise; the sprite's width when left out). Pixels past a character's
 * width are kept in the sprite, as stored, but the game doesn't draw them.
 *
 * Shared by scripts/sprites.ts (Node, run directly) and src/lib/sprites.ts:
 * keep it free of imports and non-erasable TypeScript.
 */
export interface Glyphs {
	height: number | number[]
	width?: number | number[]
}

export interface GlyphBox {
	y: number
	width: number
	height: number
}

const isInt = (v: unknown, min: number) =>
	typeof v === 'number' && Number.isInteger(v) && v >= min

/** What's wrong with a sprite's `glyphs`, or nothing. */
export function glyphProblems(
	g: Glyphs,
	spriteWidth: number,
	spriteHeight: number
): string[] {
	const heights = Array.isArray(g.height) ? g.height : null
	if (heights ? !heights.every(h => isInt(h, 1)) : !isInt(g.height, 1))
		return ['"glyphs.height" must be whole numbers above 0']
	const count = heights ? heights.length : spriteHeight / (g.height as number)
	if (heights) {
		if (heights.reduce((a, b) => a + b, 0) !== spriteHeight)
			return ['"glyphs.height" must add up to the sprite\'s height']
	} else if (!Number.isInteger(count))
		return ['the sprite\'s height must be a multiple of "glyphs.height"']
	if (g.width === undefined) return []
	const widths = Array.isArray(g.width) ? g.width : [g.width]
	if (Array.isArray(g.width) && widths.length !== count)
		return [`"glyphs.width" needs one width per character (${count})`]
	if (!widths.every(w => isInt(w, 1) && w <= spriteWidth))
		return [
			'"glyphs.width" must be whole numbers from 1 to the sprite\'s width'
		]
	return []
}

/** Each character's box, top to bottom. Assumes glyphProblems found nothing. */
export function glyphBoxes(
	g: Glyphs,
	spriteWidth: number,
	spriteHeight: number
): GlyphBox[] {
	const heights = Array.isArray(g.height)
		? g.height
		: Array.from({ length: spriteHeight / g.height }, () => g.height as number)
	const boxes: GlyphBox[] = []
	let y = 0
	heights.forEach((height, i) => {
		const width = Array.isArray(g.width) ? g.width[i] : (g.width ?? spriteWidth)
		boxes.push({ y, width, height })
		y += height
	})
	return boxes
}
