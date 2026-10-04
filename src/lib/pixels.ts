/**
 * Pixel art encoding shared by the importer (Node), the build and the browser.
 *
 * Every frame is stored as a hex string of packed palette indices, row-major:
 * - bpp 1 (VMU LCD, 48x32): 8 pixels per byte, leftmost pixel in the high bit.
 *   Index 0 is an unlit dot, 1 a lit one; the colours come from the theme.
 * - bpp 4 (save-file icons, 32x32): 2 pixels per byte, leftmost in the high
 *   nibble — the same layout as the bitmaps in a .VMS header.
 *
 * Keep this file free of imports and non-erasable TypeScript (enums etc.) so
 * Node can run it directly from scripts/import.ts.
 */

export type Bpp = 1 | 4

export interface PixelArt {
	width: number
	height: number
	bpp: Bpp
	/** "#rrggbbaa" per index; only for bpp 4. */
	palette?: string[]
	frames: string[]
	/** Delay between animation frames. */
	frameDelayMs?: number
}

export type Rgba = [number, number, number, number]

/** Hex chars a single frame takes (padded to whole bytes, for odd sprite sizes). */
export const frameHexLength = (w: number, h: number, bpp: Bpp) =>
	Math.ceil((w * h * bpp) / 8) * 2

export function decodeFrame(
	hex: string,
	width: number,
	height: number,
	bpp: Bpp
): Uint8Array {
	const out = new Uint8Array(width * height)
	const mask = (1 << bpp) - 1
	const perByte = 8 / bpp
	for (let i = 0; i < out.length; i++) {
		const byte = parseInt(
			hex.slice(Math.floor(i / perByte) * 2, Math.floor(i / perByte) * 2 + 2),
			16
		)
		const shift = 8 - bpp * ((i % perByte) + 1)
		out[i] = (byte >> shift) & mask
	}
	return out
}

export function encodeFrame(indices: ArrayLike<number>, bpp: Bpp): string {
	const perByte = 8 / bpp
	let hex = ''
	for (let i = 0; i < indices.length; i += perByte) {
		let byte = 0
		for (let j = 0; j < perByte; j++)
			byte = (byte << bpp) | ((indices[i + j] ?? 0) & ((1 << bpp) - 1))
		hex += byte.toString(16).padStart(2, '0')
	}
	return hex
}

export function parseColor(hex: string): Rgba {
	const v = hex.replace('#', '')
	const n = (i: number) => parseInt(v.slice(i, i + 2), 16)
	return [n(0), n(2), n(4), v.length >= 8 ? n(6) : 255]
}

export const toHexColor = ([r, g, b, a]: Rgba) =>
	'#' + [r, g, b, a].map(c => c.toString(16).padStart(2, '0')).join('')

/** Default inks for 1-bit art outside the page (downloads, thumbnails). */
export const LCD_INK: Rgba = [23, 23, 23, 255]
export const TRANSPARENT: Rgba = [0, 0, 0, 0]

/** The colour of every palette index. */
export function colorsOf(art: PixelArt, ink: Rgba = LCD_INK): Rgba[] {
	if (art.bpp === 1) return [TRANSPARENT, ink]
	return (art.palette ?? []).map(parseColor)
}

export const frameCount = (art: PixelArt) => art.frames.length

export interface SvgOptions {
	frame?: number
	/** "flat": crisp square pixels. "lcd": VMU dot matrix with gaps. */
	style?: 'flat' | 'lcd'
	/** Fill for lit 1-bit pixels; any CSS colour (e.g. "currentColor"). */
	on?: string
	/** Fill for unlit dots in "lcd" style; omit to leave them out. */
	off?: string
	/** Extra attributes for the root element, e.g. 'class="w-full"'. */
	attrs?: string
}

/**
 * The art as SVG. Flat style merges horizontal runs of one colour into a
 * single rectangle, so a typical icon is a few hundred path commands rather
 * than one per pixel.
 */
export function toSvg(art: PixelArt, opts: SvgOptions = {}): string {
	const { frame = 0, style = 'flat', on = toHexColor(LCD_INK), off } = opts
	const { width: w, height: h, bpp } = art
	const px = decodeFrame(art.frames[frame], w, h, bpp)
	const fills = bpp === 1 ? ['', on] : (art.palette ?? []).map(svgFill)
	const paths = new Map<number, string>()
	const add = (idx: number, d: string) =>
		paths.set(idx, (paths.get(idx) ?? '') + d)

	const gap = style === 'lcd' ? 0.12 : 0
	const dot = +(1 - gap).toFixed(2)

	for (let y = 0; y < h; y++) {
		let x = 0
		while (x < w) {
			const idx = px[y * w + x]
			let run = 1
			if (style === 'flat')
				while (x + run < w && px[y * w + x + run] === idx) run++
			if (isVisible(art, idx)) {
				const len = style === 'flat' ? run : dot
				add(idx, `M${x} ${y}h${len}v${dot}h-${len}z`)
			}
			x += run
		}
	}

	const viewBox = `0 0 ${w - gap} ${h - gap}`
	let body = ''
	if (style === 'lcd' && off) {
		// Fixed, not random: the server and browser renders must match, and
		// there's only ever one preview per page.
		const id = 'vmu-dots'
		body +=
			`<defs><pattern id="${id}" width="1" height="1" patternUnits="userSpaceOnUse">` +
			`<rect width="${dot}" height="${dot}" fill="${off}"/></pattern></defs>` +
			`<rect width="100%" height="100%" fill="url(#${id})"/>`
	}
	for (const [idx, d] of paths) body += `<path fill="${fills[idx]}" d="${d}"/>`

	const extra = opts.attrs ? ` ${opts.attrs}` : ''
	return (
		`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" ` +
		`width="${w * 8}" height="${h * 8}" shape-rendering="crispEdges"${extra}>` +
		body +
		`</svg>`
	)
}

function isVisible(art: PixelArt, idx: number) {
	if (art.bpp === 1) return idx === 1
	const color = art.palette?.[idx]
	return !!color && parseColor(color)[3] > 0
}

/**
 * The art cropped to the smallest box that holds every visible pixel. One box
 * covers all frames, so an animation stays aligned. Blank art is returned as is.
 */
export function trimArt(art: PixelArt): PixelArt {
	const { width: w, height: h, bpp } = art
	const decoded = art.frames.map(hex => decodeFrame(hex, w, h, bpp))
	let x0 = w,
		y0 = h,
		x1 = -1,
		y1 = -1
	for (const px of decoded)
		for (let y = 0; y < h; y++)
			for (let x = 0; x < w; x++)
				if (isVisible(art, px[y * w + x])) {
					x0 = Math.min(x0, x)
					y0 = Math.min(y0, y)
					x1 = Math.max(x1, x)
					y1 = Math.max(y1, y)
				}
	if (x1 < 0) return art
	const width = x1 - x0 + 1
	const height = y1 - y0 + 1
	const frames = decoded.map(px => {
		const out = new Uint8Array(width * height)
		for (let y = 0; y < height; y++)
			for (let x = 0; x < width; x++)
				out[y * width + x] = px[(y + y0) * w + x + x0]
		return encodeFrame(out, bpp)
	})
	return { ...art, width, height, frames }
}

function svgFill(hex: string) {
	const [r, g, b, a] = parseColor(hex)
	return a === 255
		? `rgb(${r},${g},${b})`
		: `rgba(${r},${g},${b},${+(a / 255).toFixed(3)})`
}

/** RGBA bytes for one frame, each pixel scaled up to a `scale`-sized block. */
export function toRgba(
	art: PixelArt,
	frame = 0,
	scale = 1,
	ink: Rgba = LCD_INK
): Uint8ClampedArray {
	const { width: w, height: h, bpp } = art
	const px = decodeFrame(art.frames[frame], w, h, bpp)
	const colors = colorsOf(art, ink)
	const W = w * scale
	const out = new Uint8ClampedArray(W * h * scale * 4)
	for (let y = 0; y < h * scale; y++) {
		for (let x = 0; x < W; x++) {
			const c =
				colors[px[Math.floor(y / scale) * w + Math.floor(x / scale)]] ??
				TRANSPARENT
			out.set(c, (y * W + x) * 4)
		}
	}
	return out
}

/** The frames as a C source snippet, for VMU homebrew. */
export function toCArray(art: PixelArt, name: string): string {
	const ident =
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, '_')
			.replace(/^_|_$/g, '') || 'icon'
	const bytesPerFrame = frameHexLength(art.width, art.height, art.bpp) / 2
	const lines = [
		`/* ${name}: ${art.width}x${art.height}, ${art.bpp}bpp, ${art.frames.length} frame(s) */`
	]
	if (art.bpp === 4 && art.palette) {
		// VMS headers store colours as ARGB4444.
		const argb = art.palette.map(c => {
			const [r, g, b, a] = parseColor(c).map(v => v >> 4)
			return (
				'0x' +
				((a << 12) | (r << 8) | (g << 4) | b).toString(16).padStart(4, '0')
			)
		})
		lines.push(
			`const unsigned short ${ident}_palette[16] = { ${argb.join(', ')} };`
		)
	}
	lines.push(
		`const unsigned char ${ident}[${art.frames.length}][${bytesPerFrame}] = {`
	)
	for (const hex of art.frames) {
		const bytes = hex.match(/../g)!.map(b => '0x' + b)
		const rows: string[] = []
		for (let i = 0; i < bytes.length; i += 12)
			rows.push('\t\t' + bytes.slice(i, i + 12).join(', '))
		lines.push('\t{\n' + rows.join(',\n') + '\n\t},')
	}
	lines.push('};')
	return lines.join('\n')
}
